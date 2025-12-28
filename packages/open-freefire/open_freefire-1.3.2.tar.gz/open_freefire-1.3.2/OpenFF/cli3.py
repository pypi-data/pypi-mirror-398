def main():
    try:
        content = """
OpenFF

Introduction

OpenFF is a Python package that allows users to fetch any FF account info directly from Python.

Created by Abdul Moeez in Pakistan.

Example FF UID: 12544204952.



---

Usage

OpenFF contains two functions:

1. show_info(uid, region)


2. is_ban(uid)


---


CLI Usage

OpenFF 1.2.0 contain cli commands:

show_info <UID> --reg<REG>

UID arg is require.
If you not use `--reg` so it was use "PK" as default.

is_ban <UID>

UID arg is require.

---

OpenFF 1.3.1 contain.

When you run `open-freefire` in terminal so that show entire README.md on your terminal.

---


Function: show_info()

Parameters:

uid (int) → FF UID (example: 12544204952)

region (str) → Region code (example: "PK")


Returns:

Account information in JSON format.


Example:


import OpenFF

info = OpenFF.show_info(12544204952, "PK")
print(info)


---

Function: is_ban()

Parameters:

uid (int) → FF UID (example: 12544204952)


Returns:

Ban status of the account in JSON format.


Example:


import OpenFF

ban_status = OpenFF.is_ban(12544204952)
print(ban_status)


---

Notes

UID must be an integer (11 digits)

Region must be a string

Functions have automatic error handling



---

Thanks

Thanks for using my Python package! 🎉
        """
        print(content)
    except Exception as e:
        print("Error")
