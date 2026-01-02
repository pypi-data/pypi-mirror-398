import os
import sys
import time
from datetime import datetime, timedelta

from cryptography.fernet import Fernet
from rich import print
from rich.console import Console
from rich.prompt import Prompt
from tinydb import Query, TinyDB

# JSON Storage for capsules
database = TinyDB("db.json")
message = Query()


# Key for encryption and decryption
def checkKey():
    keyFile = "key.txt"
    if os.path.exists(keyFile) and os.path.getsize(keyFile) == 0:
        # Generate key
        key = Fernet.generate_key()
        with open(keyFile, "wb") as keyFile:
            keyFile.write(key)


def checkCapsule():
    # Check current time
    now_time = datetime.now().timestamp()

    # Accessing JSON Data
    parse = database.all()

    # Check the dictionary for possible unlockable capsules using a loop
    for i, unlock in enumerate(parse, start=0):
        unlock_time = float(parse[i]["time_limit"])
        if now_time >= unlock_time:
            print("[green][bold]You can now unlock your Capsule No." + f" {i + 1}")
        if now_time < unlock_time:
            print(
                "[red][bold]Your capsule No.[/][/]"
                + f" {i + 1} [red][bold]is not unlockable yet.[/][/]"
            )


def interactive(console: Console):
    while True:
        console.clear()

        checkKey()

        # Main Menu
        action = Prompt.ask(
            "[bold][cyan]Time Capsule[/][/] \n[bold][white]Select an option:[/][/] \n\n[green]1.[/] [yellow]Create capsule[/]\n[green]2.[/] [yellow]Check for unlockable capsules[/]\n[green]3.[/] [yellow]Decapsulate[/]",
            choices=["1", "2", "3", "exit"],
        )

        if action == "exit":
            break
        elif action == "1":
            print("\n[white][bold]Dear Future Me,[/]")

            # Input & Encryption'
            keyFile = "key.txt"

            # Parse key from key.txt
            with open(keyFile, "rb") as keyFile:
                readKey = keyFile.read()
                f = Fernet(readKey)
            message = f.encrypt(input().encode())
            user_input = input("Set time limit: (i.e 2 50 30 (day/hour/minute)) ")
            days, hours, minutes = map(int, user_input.split())
            time_limit = datetime.now() + timedelta(
                days=days, hours=hours, minutes=minutes
            )
            if isinstance(time_limit, datetime):
                database.insert(
                    {
                        "message": str(message),
                        "time_limit": time_limit.timestamp(),
                        "current_time": str(datetime.now()),
                    }
                )
                print("[red][bold]Your message has been capsulized!")

            else:
                print("[red]Invalid time format. Please enter amount of days.[/]")
        elif action == "2":
            checkCapsule()
            time.sleep(5)
        elif action == "3":
            print("[white][bold]Which capsule do you want to unlock?[/][/]")
            num = int(input(":")) - 1
            # Check current time
            now_time = datetime.now().timestamp()

            # Accessing JSON Data
            parse = database.all()
            unlock_time = float(parse[num]["time_limit"])
            if now_time >= unlock_time:
                # Input & Encryption'
                keyFile = "key.txt"

                # Parse key from key.txt
                with open(keyFile, "rb") as keyFile:
                    readKey = keyFile.read()

                f = Fernet(readKey)

                var = False
                while var == False:
                    decryptedMessage = str(
                        f.decrypt(parse[num]["message"][2:-1].encode())
                    )
                    print(
                        "[green][bold]Your capsule No.[/][/]"
                        + f" {
                            num + 1
                        } [green][bold]has been unlocked![/][/]\n\n[white][bold]Dear Future Me,[/][/]\n{
                            decryptedMessage[2:-1]
                        }\n[gray]Press enter to exit[/]"
                    )

                    var = str(input())
                    if var:
                        sys.exit()

            else:
                print(
                    "[red][bold]Your capsule No.[/][/]"
                    + f" {num} [red][bold]is not unlockable yet.[/][/]"
                )


# Define the interactive function.
def main() -> None:
    console = Console()
    interactive(console)


# Run the main function if this script is executed.
if __name__ == "__main__":
    main()
