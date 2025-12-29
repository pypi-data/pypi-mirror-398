from .shellerator import *

def main():
    with resources.files('shellerator').joinpath('shells.json').open('r') as f:
        shells=json.load(f)
    revshells = shells['revshells']
    bindshells = shells['bindshells']
    webshells = shells['webshells']

    #parser = argparse.ArgumentParser(description='Easily generate a reverse shell, webshell or bindshell', formatter_class=argparse.RawTextHelpFormatter)
    parser = argparse.ArgumentParser(description='Easily generate a reverse shell, webshell or bindshell', formatter_class=lambda prog: argparse.HelpFormatter(prog, width=100, max_help_position=40))
    parser.add_argument('-l', '--list', dest='LIST', action='store_true', help='Display all type of shells supported by Shellerator')
    # Can't choose bind shell, reverse shell and webshell simultaneously
    shelltype = parser.add_mutually_exclusive_group()
    shelltype.add_argument('-b', '--bind-shell', dest='SHELLTYPE', action='store_const', const='bindshells', help='Generate a bind shell (you connect to the target)')
    shelltype.add_argument('-r', '--reverse-shell', dest='SHELLTYPE', action='store_const', const='revshells', help='Generate a reverse shell (the target connects to you) (Default)')
    shelltype.add_argument('-wsh', '--web-shell', dest='SHELLTYPE', action='store_const', const='webshells', help='Generate a webshell')
    parser.add_argument('-v','--verbose', action='store_true', help="Enable verbosity")
    # Sets reverse shell as the default shell type
    parser.set_defaults(SHELLTYPE='revshells')
    # Creates group of options for bindshell
    bindshell = parser.add_argument_group('Bindshell options')
    # typeoption, portoption  options will be needed for bindshells and revshells (https://stackoverflow.com/questions/23775378/allowing-same-option-in-different-argparser-group)
    typeoption = bindshell.add_argument('-t', '--type', dest='TYPE', type=str.lower, help='Type of shell to generate')
    portoption = bindshell.add_argument('-lp', '--lport', dest='LPORT', type=str, help='Listener Port')
    revshell = parser.add_argument_group('Reverse shell options')
    revshell._group_actions.append(typeoption)
    revshell._group_actions.append(portoption)
    revshell.add_argument('-lh', '--lhost', dest='LHOST', type=str, help='Listener IP address')
    # Only the type of shell must be specified for webshells (IP address and port are not needed)
    webshell = parser.add_argument_group('Webshell options')
    webshell._group_actions.append(typeoption)
    args = parser.parse_args()
    if args.LIST:
        list_shells(revshells, bindshells, webshells)
        sys.exit(0)
    if args.SHELLTYPE == 'revshells' and not args.LHOST:
        args.LHOST = select_address()
    if args.SHELLTYPE != 'webshells' and not args.LPORT:
        menu_list = [
            'HTTP (80)',
            'HTTPS (443)',
            'DNS (53)',
            'L33t (1337)'
        ]
        args.LPORT = menu_with_custom_choice("Listener port?", menu_list)
    if not args.TYPE:
        shells_dict = globals()[args.SHELLTYPE]
        menu_list = sorted(list(shells_dict.keys()))
        args.TYPE = menu('What type of shell do you want?', menu_list)
    
    # Checking user specified arguments (shell type, port number and IP address)
    check_shell_args(shells, args)

    print(f"{Fore.RED + Style.BRIGHT}[{args.SHELLTYPE.capitalize()}]{Style.RESET_ALL}")
    if args.SHELLTYPE == "revshells":
        for shell_index, revshell in enumerate(revshells[args.TYPE]):
            shell = revshell['command'].replace('{LHOST}', args.LHOST).replace('{LPORT}', args.LPORT)
            #shell = revshell['command'].format(LHOST=args.LHOST, LPORT=args.LPORT)
            #comment = "" if not args.verbose else revshell['comments'].strip()
            comment = revshell['comments'].strip()
            if platform.system() != "Windows" and args.TYPE == "powershell" and shell_index == 4:
                # Create and write into a temporary file
                with tempfile.NamedTemporaryFile(delete=False, mode="w", encoding="utf-8") as f:
                    f.write(revshells[args.TYPE][0]['command'].replace("'",'"').replace('{LHOST}', args.LHOST).replace('{LPORT}', args.LPORT))
                # pwsh_base64_revshell
                shell = "powershell -e " + subprocess.check_output(f"cat {f.name} | iconv -t utf-16le | base64 -w0", shell=True, text=True).strip()
                subprocess.run(["rm", f.name], check=True)
            print(format_shell(shell_index, shell, comment)) if shell != "" else ""
        
        # Display listeners
        print(f"\n{Fore.RED + Style.BRIGHT}[Listeners] {Style.RESET_ALL}")
        listeners = get_listeners(args.LPORT, args.verbose)
        for listener_index, command in enumerate(listeners):
            print(f"{Fore.BLUE + Style.BRIGHT}[{listener_index + 1}]{Style.RESET_ALL} {command}: {listeners[command]}")
        # Display tricks to upgrade TTY
        print(upgrade_tty(args.verbose))
    elif args.SHELLTYPE == "bindshells":
        for shell_index, bindshell in enumerate(bindshells[args.TYPE]):
            shell = bindshell['command'].replace('{LPORT}', args.LPORT)
            #shell = bindshell['command'].replace('{LHOST}', args.LHOST).replace('{LPORT}', args.LPORT)
            #shell = bindshell['command'].format(LPORT=args.LPORT)
            #comment = "" if not args.verbose else bindshell['comments'].strip()
            comment = bindshell['comments'].strip()
            print(format_shell(shell_index, shell, comment))
        # Display tricks to upgrade TTY
        print(upgrade_tty(args.verbose))
    
    else:
        for shell_index, webshell in enumerate(webshells[args.TYPE]):
            shell = webshell['command']
            #comment = "" if not args.verbose else webshell['comments'].strip()
            comment = webshell['comments'].strip()
            print(format_shell(shell_index, shell, comment))
        # Display tricks to upgrade TTY
        print(upgrade_tty(args.verbose))

if __name__ == "__main__":
	main()
