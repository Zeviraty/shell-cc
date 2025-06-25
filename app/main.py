import sys


def main():
    while True:
        sys.stdout.write("$ ")
        cmd = input().split(" ")
        match cmd[0]:
            case _:
                print(f"{' '.join(cmd)}: command not found")


if __name__ == "__main__":
    main()
