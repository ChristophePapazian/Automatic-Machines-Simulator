# V1.2 2019/09/19 Christophe Papazian

import argparse
from sys import argv, exit

from am.am_parser import am_from_string
from am.commands import load_commands, COMMANDS


def main():
    main_parser = argparse.ArgumentParser()

    subparsers = main_parser.add_subparsers(dest="command", required=True)

    load_commands()

    for name, (args, fct) in COMMANDS.items():
        parser = subparsers.add_parser(name, aliases=[name[:3]], help=fct.__doc__)
        parser.set_defaults(func=fct)
        parser.add_argument("filename", help="input filename containing machine description")
        parser.add_argument("-n", "--name", help="name of the machine used", default=None)
        for short, long, help, default, action in args:
            parser.add_argument(short, long, help=help, default=default, action=action)

    args = main_parser.parse_args(argv[1:])

    def get_name(filename, name):
        with open(filename, 'r') as input:
            lm = am_from_string(input.read())
            if name:
                try:
                    return [m for m in lm if m.name == name][-1]
                except IndexError:
                    print(f"no {name} machine found. Names available are :")
                    for m in lm:
                        print(m.name)
                    exit(1)
            elif len(lm) == 1:
                return lm[0]
            else:
                print(f"{len(lm)} machines found. Names available are (use -n name):")
                for m in lm:
                    print(
                        f"{m.name:12} with {m.nb_tapes} tape{'s,' if m.nb_tapes > 1 else ', '} {len(m.transitions):3} states and {len(m.end_states):2} final state{'s.' if len(m.end_states) > 1 else '.'}")
                exit(1)

    m = get_name(args.filename, args.name)
    args.func(m, args=args, **vars(args))


if __name__ == '__main__':
    main()
