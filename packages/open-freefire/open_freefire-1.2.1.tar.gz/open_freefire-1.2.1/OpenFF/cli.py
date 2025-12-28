import argparse
from colorama import Fore, init, Style
import requests
import datetime
import pyfiglet
from lolpython import lol_py
import sys


def show_info(uid, reg):
    try:
        ascii_art = pyfiglet.figlet_format("Open-FF")
        lol_py(ascii_art)

        print()
        lol_py("Created by Abdul Moeez. FF UID : 12544204952 : [REG] ~ PK")
        print()

        print(Fore.YELLOW + f"[•] Fetching info of {uid} ...")
        response = requests.get(
            f"https://info-ob49.vercel.app/api/account/?uid={uid}&region={reg}"
        )

        data = response.json()

        print(Fore.BLUE + str(response.status_code))

        for section, value in data.items():
            print(Fore.CYAN + Style.BRIGHT + "\n--- " + section + " ---")

            udt = ""
            if isinstance(value, dict):
                for k, v in value.items():
                    if k in ["lastLoginAt", "createAt"]:
                        dt = datetime.datetime.fromtimestamp(int(v))
                        udt = str(v)
                        v = dt.strftime("%Y-%m-%d %I:%M:%S %p")

                    print(
                        Fore.GREEN + k + " : ",
                        Fore.BLUE + Style.BRIGHT + str(v),
                        Fore.BLUE + Style.BRIGHT + f"   {udt}",
                    )
                    udt = ""
            else:
                print(Fore.GREEN + str(value))

    except Exception:
        print(Fore.RED + Style.BRIGHT + "[!] Info fetching failed due to server load. Try again pls!")
        sys.exit(1)


def main():
    init(autoreset=True)

    parser = argparse.ArgumentParser(description="FF CLI")
    parser.add_argument("uid", type=int, help="FF UID")
    parser.add_argument("--reg", type=str, help="FF UID REGION", default="PK")

    try:
        args = parser.parse_args()
        show_info(args.uid, args.reg)

    except Exception as e:
        print(Fore.RED + Style.BRIGHT + f"[!] ERROR : {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
