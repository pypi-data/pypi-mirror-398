import argparse
from typing import List

from .utils import get_states, get_lgas, search_lga, search_states


def _print_list(items: List[str]) -> None:
    for it in items:
        print(it)


def main() -> None:
    parser = argparse.ArgumentParser(prog="nigeria-states-lgas",
                                     description="Query Nigerian states and LGAs")
    sub = parser.add_subparsers(dest="cmd")

    sub.add_parser("states", help="List all states")

    lgas_p = sub.add_parser("lgas", help="List LGAs for a state")
    lgas_p.add_argument("state", help="State name")

    search_p = sub.add_parser("search-lga", help="Search which state(s) an LGA belongs to")
    search_p.add_argument("lga", help="LGA name or fragment to search for")
    search_p.add_argument("--fuzzy", action="store_true", help="Enable fuzzy matching")

    states_p = sub.add_parser("search-states", help="Search states by prefix or fuzzy match")
    states_p.add_argument("prefix", help="Prefix or name to search for")
    states_p.add_argument("--fuzzy", action="store_true", help="Enable fuzzy matching")

    args = parser.parse_args()

    if args.cmd == "states":
        _print_list(get_states())
    elif args.cmd == "lgas":
        _print_list(get_lgas(args.state))
    elif args.cmd == "search-lga":
        results = search_lga(args.lga, fuzzy=bool(args.fuzzy))
        _print_list(results)
    elif args.cmd == "search-states":
        results = search_states(args.prefix, fuzzy=bool(args.fuzzy))
        _print_list(results)
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
