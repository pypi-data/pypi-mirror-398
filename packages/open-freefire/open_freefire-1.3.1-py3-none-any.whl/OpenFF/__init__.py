import requests
import sys

def show_info(uid, reg):
    try:
        print("Created by MOEEZ | FF UID : 12544204952")

        # Type check
        if not isinstance(uid, int):
            raise TypeError(f"{uid} is not int")

        # Length check
        if len(str(uid)) != 11:
            raise Exception(f"{uid} is invalid")

        if not isinstance(reg, str):
            raise TypeError(f"{reg} is not str")

        # Fetch info
        res = requests.get(f"https://info-ob49.vercel.app/api/account/?uid={uid}&region={reg}")
        if not res.ok:
            raise Exception("Info fetching failed, please try again.")

        data = res.json()
        return data

    except Exception as e:
        print(f"OPEN-FF ERR [SHOWINFO] : {e}")
        sys.exit(1)


def is_ban(uid):
    try:
        print("Created by MOEEZ | FF UID : 12544204952")

        # Type check
        if not isinstance(uid, int):
            raise TypeError(f"{uid} is not int")

        # Length check
        if len(str(uid)) != 11:
            raise Exception(f"{uid} is invalid")

        # Fetch ban info
        url = f"https://bancheckbackend.tsunstudio.pw/bancheck?key=saeed&uid={uid}"
        response = requests.get(url)
        if not response.ok:
            raise Exception("Ban checking failed, please try again.")

        data = response.json()
        return data

    except Exception as e:
        print(f"OPEN-FF ERR [ISBAN] : {e}")
        sys.exit(1)
