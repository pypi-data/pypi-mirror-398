import os
import time

# ================= COLOR DETECTION =================
COLOR = True
try:
    from colorama import Fore, Style, init
    init(autoreset=True)
except Exception:
    COLOR = False

# Tắt màu / banner nếu user muốn
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

    COLORS = [
        Fore.CYAN,
        Fore.BLUE,
        Fore.MAGENTA,
        Fore.YELLOW,
        Fore.GREEN,
        Fore.CYAN,
    ] if COLOR else []

    for i, line in enumerate(ASCII):
        if COLOR:
            print(COLORS[i % len(COLORS)] + line + Style.RESET_ALL)
        else:
            print(line)
        time.sleep(0.1)

    time.sleep(0.2)

    if COLOR:
        print(Fore.GREEN + "Shyurer Engine • Bot starting...\n")
    else:
        print("Shyurer Engine • Bot starting...\n")

__version__ = "0.1.1"
