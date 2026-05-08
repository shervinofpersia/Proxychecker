import socks
import socket
from concurrent.futures import ThreadPoolExecutor, as_completed
import sys

TARGET_IP = "62.220.126.92"
USERNAME = "Og"
PASSWORD = ""  # رمز خالی
TEST_HOST = "google.com"
TEST_PORT = 80
TIMEOUT = 5
THREADS = 200
START_PORT = 20000
END_PORT = 30000
OUTPUT_FILE = "good_socks5.txt"

def test_proxy(port):
    """یک پروکسی SOCKS5 را تست می‌کند و در صورت موفقیت، آدرس کامل آن را برمی‌گرداند."""
    proxy_addr = TARGET_IP
    proxy_port = port

    s = socks.socksocket()
    s.set_proxy(socks.SOCKS5, proxy_addr, proxy_port, username=USERNAME, password=PASSWORD)
    s.settimeout(TIMEOUT)

    try:
        s.connect((TEST_HOST, TEST_PORT))
        s.close()
        return f"socks5://{USERNAME}@{TARGET_IP}:{port}"
    except Exception:
        return None
    finally:
        s.close()

def main():
    print(f"[*] Start scanning {START_PORT}-{END_PORT} on {TARGET_IP} with user '{USERNAME}'")
    working = []
    ports = range(START_PORT, END_PORT + 1)

    with ThreadPoolExecutor(max_workers=THREADS) as executor:
        future_to_port = {executor.submit(test_proxy, port): port for port in ports}
        for future in as_completed(future_to_port):
            result = future.result()
            if result:
                working.append(result)
                print(f"[+] {result}")
                # بلافاصله نوشتن توی فایل برای نمایش زنده
                with open(OUTPUT_FILE, 'a') as f:
                    f.write(result + "\n")

    print(f"\n[✓] Scan finished. Found {len(working)} working proxies. Results in {OUTPUT_FILE}")
    if not working:
        # اگر هیچی پیدا نشد، فایل خالی بسازیم که خطا نده
        open(OUTPUT_FILE, 'w').close()

if __name__ == "__main__":
    # فایل خروجی را از قبل خالی می‌کنیم
    with open(OUTPUT_FILE, 'w') as f:
        pass
    main()
