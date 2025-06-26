import sys
import os
import re

def typer(base,conduit:type) -> tuple:
    try:
        return (conduit(base),True)
    except:
        return (0,False)

def smart_split(text):
    tokens = []
    buffer = ''
    quote_char = None
    i = 0
    length = len(text)

    while i < length:
        c = text[i]

        if c == '\\':
            i += 1
            if i >= length:
                buffer += '\\'
                break

            next_char = text[i]

            if quote_char == '"':
                # Only escape these in double quotes: \ " $
                if next_char in ['\\', '"']:
                    buffer += next_char
                else:
                    buffer += '\\' + next_char
            elif quote_char is None:
                # Outside any quotes: escape any character
                buffer += next_char
            elif quote_char == "'":
                # Inside single quotes: backslash is literal
                buffer += '\\' + next_char
            i += 1
            continue

        if c in ("'", '"'):
            if quote_char is None:
                quote_char = c
            elif quote_char == c:
                quote_char = None
            else:
                buffer += c  # quote inside other quote type
            i += 1
            continue

        if c.isspace() and quote_char is None:
            if buffer:
                tokens.append(buffer)
                buffer = ''
            while i < length and text[i].isspace():
                i += 1
            continue

        buffer += c
        i += 1

    if buffer:
        tokens.append(buffer)

    return tokens

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
        cmd = smart_split(input())
        split = cmd[1:]
        print(cmd)
        path = os.environ["PATH"].split(":")
        cmds = {}
        for x in path:
            try:
                ls = os.listdir(os.path.join(x))
            except:
                continue
            for y in ls:
                if os.access(os.path.join(x,y), os.X_OK):
                    cmds[y] = os.path.join(x)
        match cmd[0]:
            case "exit":
                args = argparse(split,[int])
                if args[1][1] == True or args[0][0][1] == False:
                    exit(0)
                else:
                    exit(args[0][0][0])
            case "echo":
                if len(cmd[1:]) == 0:
                    print()
                else:
                    print(" ".join(split))
            case "type":
                args = argparse(split,[str])
                if args[1][1] == True or args[0][0][1] == False:
                    print("Argument failure")
                else:
                    if args[0][0][0] in ["exit","echo","type","pwd"]:
                        print(f"{args[0][0][0]} is a shell builtin")
                    elif args[0][0][0] in cmds.keys():
                        print(f"{args[0][0][0]} is {cmds[args[0][0][0]]}/{args[0][0][0]}")
                    else:
                        print(f"{args[0][0][0]}: not found")
            case "pwd":
                print(os.getcwd())
            case "cd":
                args = argparse(split,[str])
                if args[1][1] == True or args[0][0][1] == False:
                    print("Argument failure")
                else:
                    if os.path.exists(os.path.expanduser(args[0][0][0])):
                        os.chdir(os.path.expanduser(args[0][0][0]))
                    else:
                        print(f"cd: {args[0][0][0]}: No such file or directory")
            case _:
                if cmd[0] in cmds.keys():
                    os.system(f"'{cmd[0]}' {' '.join(cmd[1:])}")
                else:
                    print(f"{' '.join(cmd)}: command not found")


if __name__ == "__main__":
    main()
