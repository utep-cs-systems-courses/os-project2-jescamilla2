#! /usr/bin/env python3

import os, sys, re

""" ----helper functions begin here----"""

"""
execute commands and handle piping
pr, pw are file descriptors for read, write
os.dup2(fd, fd2, inheritable=True):
     duplicates fd to fd2, closing fd2 if necessary.
     return fd2
     the new file descriptor is inheritable by default
"""
def sh_pipe(pid, args, pr, pw):

    if pid < 0:
        os.write(2, ("fork failed, returning %d\n" % pid).encode())
        sys.exit(1)

    elif pid == 0:                                       # child process
        os.dup2(pw, 1)                                   # stdout goes to pipe now
        for fd in (pr, pw):
            os.close(fd)

        args = args[:args.index("|")]                    # everything before the "|"

        for dir in re.split(":", os.environ['PATH']):    # try each directory in path
            program = "%s/%s" % (dir, args[0])

            try:
                os.execve(program, args, os.environ)     # try to exec program
            except FileNotFoundError:                    # ... expected
                pass                                     # ... fail quietly

        os.write(2, ("Child: Could not exec %s\n" % args[0]).encode())
        sys.exit(1)                                      # terminate with error

    else:                                                # parent process
        os.dup2(pr, 0)                                   # stdin comes from pipe now
        for fd in (pr, pw):
            os.close(fd)

        args = args[args.index("|")+1:]                  # everything after the "|"

        for dir in re.split(":", os.environ['PATH']):    # try each directory in path
            program = "%s/%s" % (dir, args[0])

            try:
                os.execve(program, args, os.environ)     # try to exec program
            except FileNotFoundError:                    # ... expected
                pass                                     # ... fail quietly

        os.write(2, ("Parent: Could not exec %s\n" % args[0]).encode())
        sys.exit(1)                                      # terminate with error

"""
Function to redirect a program's output to a file.
Uses os.execve(path, args, environ) command
pid: process_id
args: arrays such as [program_name, arg1, arg2, ...]
"""
def sh_redirect(pid, args):

    if pid < 0:
        os.write(2, ("fork failed, returning %d\n" % pid).encode())
        sys.exit(1)

    elif pid == 0:                                       # child process
        redirect_path = args[-1]                         # get everything after '>'
        os.close(1)                                      # close stdout

        try:
            os.open(redirect_path, os.O_CREAT | os.O_WRONLY)
            os.set_inheritable(1, True)                  # 1 is opened file. make inheritable
        except FileNotFoundError:
            os.write(1, ("%s: No such file or directory" %redirect_path).encode())

        args = args[:args.index(">")]                    # everything before '>'

        for dir in re.split(":", os.environ['PATH']):    # try each directory in path
            program = "%s/%s" % (dir, args[0])

            try:
                os.execve(program, args, os.environ)     # try to exec program
            except FileNotFoundError:                    # ... expected
                pass                                     # ... fail quietly

        os.write(2, ("Child: Could not exec %s\n" % args[0]).encode())
        sys.exit(1)                                      # terminate with error

    else:
        childPidCode = os.wait()

"""
Function to execute a program.
Uses os.execve(path, args, environ) command
pid: process_id
args: array such as [program_name, arg1, arg2, ...]
"""
def sh_exec(pid, args):
    
    if pid < 0:
        os.write(2, ("fork failed, returning %d\n" % pid).encode())
        sys.exit(1)

    elif pid == 0:                                       # child process
        for dir in re.split(":", os.environ['PATH']):    # try each directory in path
            program = "%s/%s" % (dir, args[0])

            try:
                os.execve(program, args, os.environ)     # try to exec program
            except FileNotFoundError:                    # ... expected
                pass                                     # ... fail quietly

        os.write(2, ("Child: Could not exec %s\n" % args[0]).encode())
        sys.exit(1)                                      # terminate with error

    else:
        childPidCode = os.wait()

"""
Function to change directory.                            
"""
def sh_cd(path):
    try:
        os.chdir(path)
    except:
        print("cd: no such file or directory: {}".format(path))

"""
Function to print help instructions                      
"""
def sh_help():
    print("Your standard shell in python.")

"""
The main program                                         
"""
if '__main__' == __name__:

    while True:
        if "PS1" not in os.environ:                      
            path = os.getcwd() + " $ "
            os.write(1, path.encode())
        else:
            os.environ["PS1"]

        command = os.read(0, 1000).decode().split()      # read up to 1000 bytes

        if command[0] == "exit":
            print("Program terminated with exit code 0.")
            sys.exit(0)
        elif command[0] == "cd":                         # simple change directory
            sh_cd(command[1])
        elif command[0] == "help":                       # some help instructions
            sh_help()
        else:
            if "|" in command:                           # use pipes
                pr, pw = os.pipe()                       # create the pipe

                for f in (pr, pw):                       # make them inheritable
                    os.set_inheritable(f, True)

                rc = os.fork()                           # fork a child
                sh_pipe(rc, command, pr, pw)             # run function to execute commands

            elif ">" in command:                         # redirection
                rc = os.fork()                           # fork a child
                sh_redirect(rc, command)                 # execute the command

            else:                                        # simple command execution
                rc = os.fork()                           # fork a child
                sh_exec(rc, command)                     # execute the command
