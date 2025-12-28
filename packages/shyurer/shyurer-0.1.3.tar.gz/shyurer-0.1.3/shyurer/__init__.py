import os
import time
import random

# ================= COLOR DETECTION =================
COLOR = True
try:
    from colorama import Fore, Style, init
    init(autoreset=True)
except Exception:
    COLOR = False

# Tắt màu / banner nếu cần
if os.getenv("NO_COLOR") or os.getenv("SHYURER_NO_BANNER"):
    COLOR = False

# ================= PREVENT DUPLICATE PRINT =================
if not os.environ.get("SHYURER_BANNER_PRINTED"):
    os.environ["SHYURER_BANNER_PRINTED"] = "1"

    ASCII = [
        r" ____  _",
        r"/ ___|| |__  _   _ _   _ _ __ ___ _ __",
        r"\___ \| '_ \| | | | | | | '__/ _ \ '__|",
        r" ___) | | | | |_| | |_| | | |  __/ |",
        r"|____/|_| |_|\__, |\__,_|_|  \___|_|",
        r"             |___/",
    ]

    COLOR_POOL = [
        Fore.RED,
        Fore.GREEN,
        Fore.YELLOW,
        Fore.BLUE,
        Fore.MAGENTA,
        Fore.CYAN,
        Fore.WHITE,
    ] if COLOR else []

    def rainbow_print(text):
        """In mỗi ký tự một màu"""
        if not COLOR:
            print(text)
            return

        for ch in text:
            if ch == " ":
                print(" ", end="")
            else:
                print(random.choice(COLOR_POOL) + ch + Style.RESET_ALL, end="")
            time.sleep(0.004)
        print()

    # In ASCII rainbow
    for line in ASCII:
        rainbow_print(line)
        time.sleep(0.08)

    time.sleep(0.2)

    # DÒNG CUỐI: CHỈ MÀU XANH LÁ
    if COLOR:
        print(Fore.GREEN + "by Hoàng Quang Huy • @shyurer...\n" + Style.RESET_ALL)
    else:
        print("by Hoàng Quang Huy • @shyurer...\n")

__version__ = "0.1.3"
