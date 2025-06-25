import sys

def typer(base,conduit:type) -> tuple:
    try:
        return (conduit(base),True)
    except:
        return (0,False)

def argparse(args,types:list[type]) -> tuple:
    tmp = []
    failed = [0,False]
    
    if len(types) > len(args):
        failed = [0,True]

    args = args[:len(types)]

    for idx,i in enumerate(args):
        typed = typer(i,types[idx])
        if typed[1] == False:
            failed[0] = idx
            failed[1] = True
        tmp.append(typed)
    return (tmp,failed)

def main():
    while True:
        sys.stdout.write("$ ")
        cmd = input().split(" ")
        match cmd[0]:
            case "exit":
                args = argparse(cmd[1:],[int])
                if args[1][1] == True or args[0][0][1] == False:
                    print("Argument failure")
                else:
                    exit(args[0][0][0])
            case "echo":
                args = argparse(cmd[1:],[str])
                if args[1][1] == True or args[0][0][1] == False:
                    print("Argument failure")
                else:
                    print(args[0][0][0])

            case _:
                print(f"{' '.join(cmd)}: command not found")


if __name__ == "__main__":
    main()
