#!/usr/bin/env python3
"""
اسکریپت تست پراکسی SOCKS5 با هندشیک واقعی و احراز هویت کاربر.
socks://Og@62.220.126.56:PORT
محدوده پورت: 30000 تا 39999
پورت‌های زنده در فایل alive_proxies/alive.txt ذخیره می‌شوند.
"""

import asyncio
import os
import sys

HOST = "62.220.126.56"
PORT_START = 30000
PORT_END = 39999
USERNAME = "Og"
PASSWORD = ""           # رمز خالی
OUTPUT_DIR = "alive_proxies"
OUTPUT_FILE = os.path.join(OUTPUT_DIR, "alive.txt")
TIMEOUT = 3.0           # ثانیه
CONCURRENCY = 200       # تعداد هم‌زمان (کمتر از قبل به خاطر افزایش بار شبکه)


async def socks5_ping(host: str, port: int, username: str, password: str) -> bool:
    """
    انجام هندشیک کامل SOCKS5 (با احراز هویت username/password) و
    ارسال یک درخواست CONNECT به 0.0.0.0:0 و بررسی دریافت پاسخ.
    در صورت موفقیت True برمی‌گرداند.
    """
    try:
        reader, writer = await asyncio.wait_for(
            asyncio.open_connection(host, port), timeout=TIMEOUT
        )

        # مرحله ۱: ارسال سلام و انتخاب متد احراز هویت
        # پشتیبانی از متد username/password (0x02)
        greeting = bytes([0x05, 0x01, 0x02])
        writer.write(greeting)
        await writer.drain()

        # خواندن پاسخ انتخاب متد (۲ بایت)
        resp = await asyncio.wait_for(reader.readexactly(2), timeout=TIMEOUT)
        version, method = resp[0], resp[1]
        if version != 0x05 or method == 0xFF:
            writer.close()
            return False
        if method != 0x02:
            # اگر متد دیگری برگرداند، fail
            writer.close()
            return False

        # مرحله ۲: احراز هویت username/password
        user_bytes = username.encode()
        pass_bytes = password.encode()
        # ساختار: 0x01 | len(user) | user | len(pass) | pass
        auth_msg = bytes([0x01, len(user_bytes)]) + user_bytes + bytes([len(pass_bytes)]) + pass_bytes
        writer.write(auth_msg)
        await writer.drain()

        # خواندن پاسخ احراز هویت (۲ بایت: version, status)
        auth_resp = await asyncio.wait_for(reader.readexactly(2), timeout=TIMEOUT)
        if auth_resp[0] != 0x01 or auth_resp[1] != 0x00:
            writer.close()
            return False

        # مرحله ۳ (تأیید نهایی): ارسال درخواست CONNECT و بررسی دریافت پاسخ
        # مقصد: 0.0.0.0:0 (آدرس نامعتبر – فقط برای تست پاسخ سرور)
        connect_req = bytes([
            0x05, 0x01, 0x00,       # VER, CMD=CONNECT, RSV
            0x01,                   # ATYP = IPv4
            0x00, 0x00, 0x00, 0x00, # IP 0.0.0.0
            0x00, 0x00              # Port 0
        ])
        writer.write(connect_req)
        await writer.drain()

        # انتظار برای حداقل ۵ بایت اول پاسخ (تا header کامل دریافت شود)
        header = await asyncio.wait_for(reader.readexactly(5), timeout=TIMEOUT)
        # اگر به اینجا رسید یعنی پاسخ دریافت شده → پراکسی زنده است
        writer.close()
        return True

    except Exception:
        return False


async def main():
    semaphore = asyncio.Semaphore(CONCURRENCY)

    async def worker(port: int) -> str | None:
        async with semaphore:
            alive = await socks5_ping(HOST, port, USERNAME, PASSWORD)
            return f"socks://{USERNAME}@{HOST}:{port}" if alive else None

    ports = range(PORT_START, PORT_END + 1)
    print(f"شروع بررسی {len(ports)} پورت با هندشیک SOCKS5 ...")
    tasks = [worker(p) for p in ports]
    results = await asyncio.gather(*tasks)

    alive = [addr for addr in results if addr is not None]

    os.makedirs(OUTPUT_DIR, exist_ok=True)
    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        f.write("\n".join(alive) + "\n")

    print(f"پراکسی‌های فعال (هندشیک موفق): {len(alive)}")
    print(f"خروجی در: {OUTPUT_FILE}")


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("لغو توسط کاربر.")
        sys.exit(1)
