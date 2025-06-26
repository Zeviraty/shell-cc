import sys
import os
import re
import subprocess
import readline

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
                i += 1
                continue
            elif quote_char == c:
                quote_char = None
                i += 1
                continue
            else:
                # quote inside another quote type — treat literally
                buffer += c
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

def complete(text, state):
    if not hasattr(complete, "_cmds"):
        path = os.environ["PATH"].split(":")
        cmds = set()
        for x in path:
            try:
                for y in os.listdir(x):
                    if os.access(os.path.join(x, y), os.X_OK):
                        cmds.add(y)
            except:
                continue
        complete._cmds = cmds

    results = [x + " " for x in [*complete._cmds, *builtins] if x.startswith(text)] + [None]
    if results == [None]:
        print("\x07")
    return results[state]

def display_completions(substitution, matches, longest_match_length):
    print("\n" + "  ".join(matches))  # two spaces
    sys.stdout.write(readline.get_line_buffer())
    sys.stdout.flush()

global builtins
builtins = ["exit","echo","type","pwd"]

def main():
    readline.set_completer(complete)
    readline.parse_and_bind("tab: complete")
    readline.set_completion_display_matches_hook(display_completions)
    while True:
        cmd = smart_split(input("$ "))
        split = cmd[1:]
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
                    if args[0][0][0] in builtins:
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
                    subprocess.run(cmd)
                else:
                    print(f"{' '.join(cmd)}: command not found")


if __name__ == "__main__":
    main()
