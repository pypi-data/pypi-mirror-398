import requests
from colorama import init, Fore, Style
import argparse
import pyfiglet
from lolpython import lol_py
import sys

init(autoreset=True)

def main():
    parser = argparse.ArgumentParser(description="Ban checker")
    parser.add_argument("uid", type=str, help="FF UID", default=404)
    args = parser.parse_args()
    if args.uid == 404:
        print(Fore.BLUE+Style.BRIGHT+"[USAGE] : is_ban <UID>")
        sys.exit(1)
    uid = args.uid
    try:
        ascii_art = pyfiglet.figlet_format("Open-FF")
        lol_py(ascii_art)
        print()
        lol_py("Created by Abdul Moeez. FF UID is 12544204952")
        print()
        url = f"https://bancheckbackend.tsunstudio.pw/bancheck?key=saeed&uid={uid}"
        response = requests.get(url)
        print(Fore.YELLOW + "[•] Fetching info ...")

        data = response.json()

        print(Fore.CYAN + Style.BRIGHT + f"[✓] FF UID STATUS : {data['status']}")
        print(Fore.CYAN + Style.BRIGHT + f"[✓] Ban period : {data['ban_period']}")

    except Exception as e:
        print(Fore.RED + f"[!] ERROR : {e}")
        sys.exit(1)

if __name__ == '__main__':
    main()
