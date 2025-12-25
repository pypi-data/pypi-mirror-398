import argparse

from blueness import module
from blueness.argparse.generic import sys_exit

from bluer_options import NAME
from bluer_options.options.classes import Options
from bluer_options.logger import logger

NAME = module.name(__file__, NAME)

list_of_tasks = "choice|get"

parser = argparse.ArgumentParser(NAME)
parser.add_argument(
    "task",
    type=str,
    default="",
    help=list_of_tasks,
)
parser.add_argument(
    "--options",
    type=str,
    default="",
)
parser.add_argument(
    "--keyword",
    type=str,
    default="",
)
parser.add_argument(
    "--choices",
    type=str,
    default="",
)
parser.add_argument(
    "--default",
    type=str,
    default="",
)
parser.add_argument(
    "--delim",
    type=str,
    default=",",
)
parser.add_argument(
    "--is_int",
    type=int,
    default=0,
    help="0|1",
)
args = parser.parse_args()

delim = " " if args.delim == "space" else args.delim

success = True if args.task in list_of_tasks.split("|") else None
if args.task == "choice":
    options = Options(args.options)

    found = False
    for keyword in args.choices.split(","):
        if options.get(keyword, 0):
            print(keyword)
            found = True
            break

    if not found:
        print(args.default)
elif args.task == "get":
    output = Options(args.options).get(args.keyword, args.default)
    print((int(output) if output else 0) if args.is_int == 1 else output)


sys_exit(logger, NAME, args.task, success)
