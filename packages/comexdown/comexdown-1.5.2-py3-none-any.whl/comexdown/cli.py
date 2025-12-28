#!/usr/bin/env python3

"""usage: comexdown { trade | table } <arguments>

  comexdown trade <year> ... -o <output>

  comexdown table <table name> -o <output>

"""


import argparse
from pathlib import Path

from comexdown import get_complete, get_table, get_year, get_year_nbm
from comexdown.tables import AUX_TABLES, TABLES


def expand_years(args_years: str) -> list[int]:
    years = []
    for arg in args_years:
        if ":" in arg:
            start, end = arg.split(":")
            start, end = int(start), int(end)
            if start > end:
                years += list(range(start, end - 1, -1))
            else:
                years += list(range(start, end + 1))
        else:
            years.append(int(arg))
    return years


# =============================================================================
# ----------------------------TRANSACTION TRADE DATA---------------------------
# =============================================================================
def download_trade(args: argparse.Namespace):
    if not args.exp and not args.imp:
        exp = imp = True
    else:
        exp, imp = args.exp, args.imp

    mun = args.mun

    if args.years == ["complete"]:
        get_complete(
            exp=exp,
            imp=imp,
            mun=mun,
            path=args.path,
        )
        return

    for year in expand_years(args.years):
        if year < 1989:
            print("Year not available!", year)
            continue
        if year < 1997:
            if mun:
                print(
                    f"Municipality data for this year ({year}) not available!"
                    "\nDownloading national data instead..."
                )
            get_year_nbm(
                year=year,
                exp=exp,
                imp=imp,
                path=args.path,
            )
        else:
            get_year(
                year=year,
                exp=exp,
                imp=imp,
                mun=mun,
                path=args.path,
            )


# =============================================================================
# ----------------------------AUXILIARY CODE TABLES----------------------------
# =============================================================================
def download_tables(args: argparse.Namespace):
    if args.tables == []:
        print_code_tables()
    if "all" in args.tables:
        for table in AUX_TABLES:
            get_table(
                table=table,
                path=args.path,
            )
        return
    for table in args.tables:
        get_table(
            table=table,
            path=args.path,
        )


def print_code_tables():
    print("\nAvailable code tables:")
    for table in TABLES:
        print(f"\n  {table: <11}{TABLES[table]['name']}")
        description = TABLES[table]["description"]
        len_description = len(description)
        i = 0
        if len_description > 70:
            print(13 * " ", end="")
            for word in description.split(" "):
                i += len(word) + 1
                if i < 70:
                    print(word, end=" ")
                else:
                    print(word)
                    print(13 * " ", end="")
                    i = 0
            print("")
        else:
            print(12 * " ", description)
    print("")


def download_help(args: argparse.Namespace):
    print(__doc__)


# =============================================================================
# ------------------------------------PARSERS----------------------------------
# =============================================================================
def set_download_trade_subparser(
    download_subs: argparse.ArgumentParser,
    default_output: Path,
):
    # !!! DOWNLOAD TRADE TRANSACTIONS DATA
    download_trade_parser = download_subs.add_parser(
        "trade", description="Download Exports & Imports data")
    download_trade_parser.add_argument(
        "years",
        action="store",
        nargs="+",
        help="Year (or year range) or list of years (year ranges) to download",
    )
    download_trade_parser.add_argument("-exp", action="store_true")
    download_trade_parser.add_argument("-imp", action="store_true")
    download_trade_parser.add_argument("-mun", action="store_true")
    download_trade_parser.add_argument("-nbm", action="store_true")
    download_trade_parser.add_argument(
        "-o",
        action="store",
        dest="path",
        type=Path,
        default=default_output,
        help="Output path directory where files will be saved",
    )
    download_trade_parser.set_defaults(func=download_trade)


def set_download_table_subparser(
    download_subs: argparse.ArgumentParser,
    default_output: Path,
):
    # !!! DOWNLOAD CODE TABLES
    download_table_parser = download_subs.add_parser(
        "table", description="Download code tables for Brazil's foreign data")
    download_table_parser.add_argument(
        "tables",
        action="store",
        nargs="*",
        default=[],
        help=(
            "Name (or list of names) of table to download ('all' to download "
            "all tables)"
        ),
    )
    download_table_parser.add_argument(
        "-o",
        action="store",
        dest="path",
        type=Path,
        default=default_output,
        help="Output path directory where files will be saved",
    )
    download_table_parser.set_defaults(func=download_tables)


def set_parser() -> argparse.ArgumentParser:
    default_output = Path(".", "data", "secex-comex")

    parser = argparse.ArgumentParser(
        description="Download Brazil's foreign trade data")
    parser.set_defaults(func=download_help)

    subparsers = parser.add_subparsers()

    set_download_trade_subparser(subparsers, default_output)
    set_download_table_subparser(subparsers, default_output)

    return parser


def main():
    parser = set_parser()
    args = parser.parse_args()

    args.func(args)


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt as ki:
        print(f"\n\n{ki}\n\n")
        print("\n\n\nEXITING...\n\n\n")
