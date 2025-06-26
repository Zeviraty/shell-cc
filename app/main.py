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
global append
append = False

def cmdprint(txt,out=None):
    global append
    if out == None:
        print(txt)
    else:
        print(append)
        if append:
            open(out,'a').write(txt+"\n")
        else:
            open(out,'w').write(txt+"\n")

def main():
    global append
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
        
        stdout_file = None
        stderr_file = None
        append = False
        clean_tokens = []
        
        i = 0
        while i < len(tokens):
            if tokens[i] in ('>', '1>'):
                if i + 1 < len(tokens):
                    stdout_file = tokens[i+1]
                    i += 2
                else:
                    print("Syntax error: no output file specified for stdout redirection")
                    break
            elif tokens[i] in ('>>','1>>'):
                append = True
                if i + 1 < len(tokens):
                    stdout_file = tokens[i+1]
                    i += 2
                else:
                    print("Syntax error: no output file specified for stdout redirection")
                    break
            elif tokens[i] == '2>':
                if i + 1 < len(tokens):
                    stderr_file = tokens[i+1]
                    i += 2
                else:
                    print("Syntax error: no output file specified for stderr redirection")
                    break
            elif tokens[i] == '2>>':
                if i + 1 < len(tokens):
                    stderr_file = tokens[i+1]
                    i += 2
                    append = True
                else:
                    print("Syntax error: no output file specified for stderr redirection")
                    break
            else:
                clean_tokens.append(tokens[i])
                i += 1
        
        if len(clean_tokens) == 0:
            continue
        
        cmd = clean_tokens
        split = cmd[1:]
        
        current_length = readline.get_current_history_length()
        delta = current_length - initial_history_length
        if delta > 0:
            if os.environ.get("HISTFILE") is not None and os.path.exists(os.environ.get("HISTFILE")):
                readline.append_history_file(delta, os.environ.get("HISTFILE"))
        initial_history_length = current_length
        
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
                if len(split) == 0:
                    cmdprint("", stdout_file)
                else:
                    cmdprint(" ".join(split), stdout_file)
                if stderr_file:
                    open(stderr_file, "w").close()
            case "type":
                args = argparse(split,[str])
                if args[1][1] == True or args[0][0][1] == False:
                    cmdprint("Argument failure", stdout_file)
                else:
                    if args[0][0][0] in builtins:
                        cmdprint(f"{args[0][0][0]} is a shell builtin", stdout_file)
                    elif args[0][0][0] in cmds.keys():
                        cmdprint(f"{args[0][0][0]} is {cmds[args[0][0][0]]}/{args[0][0][0]}", stdout_file)
                    else:
                        cmdprint(f"{args[0][0][0]}: not found", stdout_file)
            case "pwd":
                cmdprint(os.getcwd(), stdout_file)
            case "cd":
                args = argparse(split,[str])
                if args[1][1] == True or args[0][0][1] == False:
                    cmdprint("Argument failure", stdout_file)
                else:
                    if os.path.exists(os.path.expanduser(args[0][0][0])):
                        os.chdir(os.path.expanduser(args[0][0][0]))
                    else:
                        cmdprint(f"cd: {args[0][0][0]}: No such file or directory", stdout_file)
            case "history":
                if len(split) > 1:
                    args = argparse(split,[str,str])
                    if args[1][1] == True or args[0][0][1] == False:
                        cmdprint("Argument failure", stdout_file)
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
                            cmdprint("Argument failure", stdout_file)
                else:
                    args = argparse(split,[int])
                    if args[1][1] == True or args[0][0][1] == False:
                        for i in range(readline.get_current_history_length()):
                            if readline.get_history_item(i) == None: continue
                            cmdprint(f"    {i}  {readline.get_history_item(i)}", stdout_file)
                        cmdprint(f"    {i}  history", stdout_file)
                    else:
                        count = args[0][0][0]
                        length = readline.get_current_history_length()
                        start = max(length - count + 1, 1)
                        for i in range(start, length + 1):
                            line = readline.get_history_item(i)
                            if line is not None:
                                cmdprint(f"    {i}  {line}", stdout_file)
            case _:
                if cmd[0] in cmds.keys():
                    try:
                        result = subprocess.run(
                            cmd,
                            stdout=subprocess.PIPE,
                            stderr=subprocess.PIPE,
                            text=True
                        )

                        if result.stdout:
                            for line in result.stdout.splitlines():
                                cmdprint(line, stdout_file)
                        elif stdout_file:
                            open(stdout_file, "w").close()

                        if result.stderr:
                            for line in result.stderr.splitlines():
                                cmdprint(line, stderr_file)
                        elif stderr_file:
                            open(stderr_file, "w").close()

                    except Exception as e:
                        cmdprint(f"{cmd[0]}: {e}", stderr_file)
                else:
                    cmdprint(f"{cmd[0]}: command not found", stderr_file)

if __name__ == "__main__":
    main()
