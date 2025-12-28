import os

if not os.environ.get("SHYURER_BANNER"):
    os.environ["SHYURER_BANNER"] = "1"
    print(r"""
 ____  _
/ ___|| |__  _   _ _   _ _ __ ___ _ __
\___ \| '_ \| | | | | | | '__/ _ \ '__|
 ___) | | | | |_| | |_| | | |  __/ |
|____/|_| |_|\__, |\__,_|_|  \___|_|
             |___/
""")
