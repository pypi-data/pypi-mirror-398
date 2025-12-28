import os

# ===== detect color support =====
COLOR = True
try:
    from colorama import Fore, Style, init
    init(autoreset=True)
except Exception:
    COLOR = False

if os.getenv("NO_COLOR") or os.getenv("SHYURER_NO_BANNER"):
    COLOR = False

# ===== prevent duplicate print =====
if not os.environ.get("SHYURER_BANNER_PRINTED"):
    os.environ["SHYURER_BANNER_PRINTED"] = "1"

    ASCII = [
        " ____  _",
        "/ ___|| |__  _   _ _   _ _ __ ___ _ __",
        "\\___ \\| '_ \\| | | | | | | '__/ _ \\ '__|",
        " ___) | | | | |_| | |_| | | |  __/ |",
        "|____/|_| |_|\\__, |\\__,_|_|  \\___|_|",
        "             |___/",
    ]

    COLORS = [
        Fore.CYAN,
        Fore.BLUE,
        Fore.MAGENTA,
        Fore.YELLOW,
        Fore.GREEN,
    ] if COLOR else []

    for i, line in enumerate(ASCII):
        if COLOR:
            print(COLORS[i % len(COLORS)] + line + Style.RESET_ALL)
        else:
            print(line)

    if COLOR:
        print(Fore.GREEN + "Shyurer Engine • Bot starting...\n")
    else:
        print("Shyurer Engine • Bot starting...\n")

__version__ = "0.1.0"
