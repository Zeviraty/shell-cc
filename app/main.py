import sys
import os
import re
import subprocess
import readline
import shlex

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
        path = os.environ.get("PATH", "").split(":")
        cmds = set()
        for directory in path:
            try:
                for file in os.listdir(directory):
                    full_path = os.path.join(directory, file)
                    if os.access(full_path, os.X_OK) and not os.path.isdir(full_path):
                        cmds.add(file)
            except Exception:
                continue
        complete._cmds = cmds

    matches = [cmd for cmd in complete._cmds.union(builtins) if cmd.startswith(text)]

    if state == 0:
        if not matches:
            print("\x07", end='', flush=True)

        if len(matches) == 1:
            complete._matches = [matches[0] + ' ']
        else:
            complete._matches = matches

    try:
        return complete._matches[state]
    except IndexError:
        return None

global builtins
builtins = ["exit","echo","type","pwd","history"]

def cmdprint(txt,out=None):
    if out == None:
        print(txt)
    else:
        open(out,'a').write(out+"\n")

def main():
    histfile = os.environ.get("HISTFILE")
    if histfile:
        try:
            readline.read_history_file(histfile)
        except:
            pass
    initial_history_length = readline.get_current_history_length()
    saved_history_length = initial_history_length
    readline.set_auto_history(False)
    readline.set_completer(complete)
    readline.parse_and_bind("tab: complete")
    readline.set_completer_delims(' \t\n')
    while True:
        user_input = input("$ ")
        readline.add_history(user_input)
        tokens = shlex.split(user_input)
        if not tokens:
            continue
        cmd = smart_split(user_input)
        redirect_index = None
        redirect_file = None
        for i, token in enumerate(tokens):
            if token == '>' or token == '1>':
                redirect_index = i
                break

        if redirect_index is not None:
            if redirect_index + 1 < len(tokens):
                redirect_file = tokens[redirect_index + 1]
                cmd_tokens = tokens[:redirect_index]
            else:
                print("Syntax error: no output file specified for redirection")
                continue
        else:
            cmd_tokens = tokens
        if not cmd_tokens:
            continue
        cmd = cmd_tokens
        current_length = readline.get_current_history_length()
        delta = current_length - initial_history_length
        if delta > 0:
            if os.environ.get("HISTFILE") != None and os.path.exists(os.environ.get("HISTFILE")):
                readline.append_history_file(delta,os.environ.get("HISTFILE"))
        initial_history_length = current_length
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
                    cmdprint("",redirect_file)
                else:
                    cmdprint(" ".join(split),redirect_file)
            case "type":
                args = argparse(split,[str])
                if args[1][1] == True or args[0][0][1] == False:
                    cmdprint("Argument failure",redirect_file)
                else:
                    if args[0][0][0] in builtins:
                        cmdprint(f"{args[0][0][0]} is a shell builtin",redirect_file)
                    elif args[0][0][0] in cmds.keys():
                        cmdprint(f"{args[0][0][0]} is {cmds[args[0][0][0]]}/{args[0][0][0]}",redirect_file)
                    else:
                        cmdprint(f"{args[0][0][0]}: not found",redirect_file)
            case "pwd":
                cmdprint(os.getcwd(),redirect_file)
            case "cd":
                args = argparse(split,[str])
                if args[1][1] == True or args[0][0][1] == False:
                    cmdprint("Argument failure",redirect_file)
                else:
                    if os.path.exists(os.path.expanduser(args[0][0][0])):
                        os.chdir(os.path.expanduser(args[0][0][0]))
                    else:
                        cmdprint(f"cd: {args[0][0][0]}: No such file or directory",redirect_file)
            case "history":
                if len(split) > 1:
                    args = argparse(split,[str,str])
                    if args[1][1] == True or args[0][0][1] == False:
                        cmdprint("Argument failure",redirect_file)
                    else:
                        if args[0][0][0] == "-r":
                            readline.read_history_file(args[0][1][0])
                        elif args[0][0][0] == "-w":
                            readline.write_history_file(args[0][1][0])
                        elif args[0][0][0] == "-a":
                            current_length = readline.get_current_history_length()
                            delta = current_length - saved_history_length
                            if delta > 0:
                                readline.append_history_file(delta, args[0][1][0])
                                saved_history_length = current_length
                        else:
                            cmdprint("Argument failure",redirect_file)
                else:
                    args = argparse(split,[int])
                    if args[1][1] == True or args[0][0][1] == False:
                        for i in range(readline.get_current_history_length()):
                            if readline.get_history_item(i) == None: continue
                            cmdprint(f"    {i}  {readline.get_history_item(i)}",redirect_file)
                        cmdprint(f"    {i}  history",redirect_file)
                    else:
                        count = args[0][0][0]
                        length = readline.get_current_history_length()
                        start = max(length - count + 1, 1)
                        for i in range(start, length + 1):
                            line = readline.get_history_item(i)
                            if line is not None:
                                cmdprint(f"    {i}  {line}",redirect_file)
            case _:
                if cmd_name in cmds.keys():
                    try:
                        if redirect_file:
                            with open(redirect_file, "w") as f:
                                result = subprocess.run(cmd_tokens, stdout=f, stderr=subprocess.PIPE, text=True)
                                if result.stderr:
                                    print(result.stderr, end="")
                        else:
                            subprocess.run(cmd_tokens)
                    except Exception as e:
                        print(f"{cmd_name}: {e}")
                else:
                    print(f"{cmd_name}: command not found")


if __name__ == "__main__":
    main()
