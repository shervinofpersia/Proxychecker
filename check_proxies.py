#!/usr/bin/env python3
"""
اسکریپت تست ارتباط پراکسی‌های SOCKS:
socks://Og@62.220.126.56:PORT
محدوده پورت: 30000 تا 39999
پورت‌های پاسخ‌دهنده را در فایل alive.txt ذخیره می‌کند.
"""

import asyncio
import os
import sys

HOST = "62.220.126.56"
PORT_START = 30000
PORT_END = 39999
USERNAME = "Og"
OUTPUT_DIR = "alive_proxies"
OUTPUT_FILE = os.path.join(OUTPUT_DIR, "alive.txt")
TIMEOUT = 2.0          # ثانیه
CONCURRENCY = 300      # تعداد اتصال هم‌زمان


async def check_port(semaphore: asyncio.Semaphore, port: int) -> str | None:
    """تلاش برای اتصال TCP به پورت مشخص؛ در صورت موفقیت آدرس ساکس را برمی‌گرداند."""
    async with semaphore:
        try:
            # فقط تست باز بودن پورت
            reader, writer = await asyncio.wait_for(
                asyncio.open_connection(HOST, port),
                timeout=TIMEOUT
            )
            writer.close()
            await writer.wait_closed()
            return f"socks://{USERNAME}@{HOST}:{port}"
        except Exception:
            # هر نوع خطا (timeout، refusal و ...) یعنی پورت در دسترس نیست
            return None


async def main():
    semaphore = asyncio.Semaphore(CONCURRENCY)
    ports = range(PORT_START, PORT_END + 1)

    print(f"شروع بررسی {len(ports)} پورت...")
    tasks = [check_port(semaphore, p) for p in ports]
    results = await asyncio.gather(*tasks)

    # فیلتر پاسخ‌های موفق (رشته‌های غیر None)
    alive = [addr for addr in results if addr is not None]

    # ذخیره‌سازی در فایل
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        f.write("\n".join(alive) + "\n")

    print(f"تعداد پراکسی‌های فعال: {len(alive)}")
    print(f"لیست در {OUTPUT_FILE} ذخیره شد.")


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("لغو توسط کاربر.")
        sys.exit(1)
