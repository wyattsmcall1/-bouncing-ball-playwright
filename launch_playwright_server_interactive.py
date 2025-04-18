# Launch logic for server and browser using Playwright

import os
import subprocess
import shutil
import socket
import asyncio
import threading
from pathlib import Path
from queue import Queue
import base64
import hashlib

from playwright.async_api import async_playwright
from cryptography.hazmat.primitives import serialization
from cryptography.x509 import load_pem_x509_certificate

# --- Output directory ---
OUTPUT_DIR = "/app/tests/output"
os.makedirs(OUTPUT_DIR, exist_ok=True)

# --- IP and certificate setup ---
def get_container_ip():
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        s.connect(("8.8.8.8", 80))
        return s.getsockname()[0]
    finally:
        s.close()

HOST_IP = os.environ.get("HOST_IP", get_container_ip())
CERT_PATH = f"/app/{HOST_IP}.pem"
KEY_PATH = f"/app/{HOST_IP}-key.pem"

def generate_cert_for_ip(ip):
    subprocess.run(["mkcert", "-cert-file", CERT_PATH, "-key-file", KEY_PATH, ip], check=True)

generate_cert_for_ip(HOST_IP)

# --- SPKI fingerprint for pinning ---
def get_spki_base64(cert_path):
    with open(cert_path, "rb") as f:
        cert = load_pem_x509_certificate(f.read())
    pubkey = cert.public_key()
    spki = pubkey.public_bytes(
        encoding=serialization.Encoding.DER,
        format=serialization.PublicFormat.SubjectPublicKeyInfo
    )
    return base64.b64encode(hashlib.sha256(spki).digest()).decode("ascii")

# --- Wait for QUIC startup log ---
def wait_for_quic_log_line(log_queue, timeout=10):
    start = asyncio.get_event_loop().time()
    while asyncio.get_event_loop().time() - start < timeout:
        try:
            line = log_queue.get(timeout=0.5)
            print("[QUIC LOG]", line.strip())
            if "QUIC server running" in line:
                return True
        except Exception:
            pass
    return False

# --- Launch Browser and Connect ---
async def launch_browser_and_connect():
    server_proc = subprocess.Popen(
        [
            "python3", "server/app.py",
            "--host", "0.0.0.0",
            "--cert", CERT_PATH,
            "--key", KEY_PATH
        ],
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        bufsize=1,
        universal_newlines=True
    )

    log_queue = Queue()
    threading.Thread(
        target=lambda: [log_queue.put(line) for line in iter(server_proc.stdout.readline, '')],
        daemon=True
    ).start()

    if not wait_for_quic_log_line(log_queue):
        print("QUIC server did not start in time")
        server_proc.terminate()
        return

    async with async_playwright() as p:
        chrome_profile = "/tmp/chrome-profile"
        shutil.rmtree(chrome_profile, ignore_errors=True)

        def trust_mkcert_root_chromium(profile_dir):
            print(f"[DEBUG] Trusting mkcert root in Chromium profile: {profile_dir}")
            caroot = subprocess.check_output(["mkcert", "-CAROOT"], text=True).strip()
            root_ca_path = os.path.join(caroot, "rootCA.pem")
            cert_db_path = os.path.join(profile_dir, "Default")
            os.makedirs(cert_db_path, exist_ok=True)

            subprocess.run([
                "certutil", "-d", f"sql:{cert_db_path}",
                "-A", "-t", "C,", "-n", "mkcert-root", "-i", root_ca_path
            ], check=True)

        trust_mkcert_root_chromium(chrome_profile)

        spki_base64 = get_spki_base64(CERT_PATH)

        context = await p.chromium.launch_persistent_context(
            user_data_dir=chrome_profile,
            headless=False,
            ignore_https_errors=True,
            args=[
                "--no-sandbox",
                "--enable-quic",
                "--enable-logging",
                "--log-level=0",
                "--v=1",
                "--enable-features=WebTransport,WebTransportQUIC",
                f"--origin-to-force-quic-on={HOST_IP}:8080",
                f"--ignore-certificate-errors-spki-list={spki_base64}",
                "--allow-insecure-localhost",
            ]
        )

        # Patch index.html with correct IP
        index_path = Path("/app/server/static/index.html")
        index_html = index_path.read_text()
        patched_html = index_html.replace("%%HOST_IP%%", HOST_IP)
        print("[DEBUG] Final WebTransport URL snippet:")
        print([line for line in patched_html.splitlines() if "url =" in line][0])
        index_path.write_text(patched_html)

        # Launch the page
        page = context.pages[0] if context.pages else await context.new_page()
        page.on("console", lambda msg: print(">>", msg.text))

        await page.goto(f"http://{HOST_IP}:8000", wait_until="domcontentloaded")
        await page.wait_for_function("document.readyState === 'complete'")
        await page.wait_for_function("window.transport && typeof window.transport.ready === 'object'", timeout=30000)

        await asyncio.sleep(3)

        await page.screenshot(path=f"{OUTPUT_DIR}/screenshot.png")
        print("[DEBUG] Screenshot saved.")

        await context.close()
        server_proc.terminate()
        server_proc.wait(timeout=5)

# --- Entry point ---
if __name__ == "__main__":
    asyncio.run(launch_browser_and_connect())
