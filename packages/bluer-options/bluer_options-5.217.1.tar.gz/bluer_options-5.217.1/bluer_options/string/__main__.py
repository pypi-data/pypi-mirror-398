import argparse
import random
import os

from blueness import module

from bluer_options import NAME
from bluer_options import string

NAME = module.name(__file__, NAME)

list_of_tasks = "after | before | pretty_date | random"


parser = argparse.ArgumentParser(NAME)
parser.add_argument(
    "task",
    type=str,
    help=list_of_tasks,
)
parser.add_argument(
    "--include_time",
    type=int,
    help="0|1",
    default=1,
)
parser.add_argument(
    "--length",
    type=int,
    default=16,
)
parser.add_argument(
    "--string",
    type=str,
)
parser.add_argument(
    "--substring",
    type=str,
)
parser.add_argument(
    "--unique",
    type=int,
    help="0|1",
    default=0,
)
parser.add_argument(
    "--float",
    type=int,
    help="0|1",
    default=0,
)
parser.add_argument(
    "--int",
    type=int,
    help="0|1",
    default=0,
)
parser.add_argument(
    "--min",
    type=float,
    default=0.0,
)
parser.add_argument(
    "--max",
    type=float,
    default=100.0,
)
args = parser.parse_args()

success = args.task in list_of_tasks.split(" | ")
if args.task == "after":
    print(string.after(args.string, args.substring))
elif args.task == "before":
    print(string.before(args.string, args.substring))
elif args.task == "pretty_date":
    print(
        string.pretty_date(
            as_filename=True,
            include_time=args.include_time == 1,
            unique=args.unique == 1,
        )
    )
elif args.task == "random":
    random.seed(os.getpid())

    print(
        ("{:0.8f}" if args.float == 1 else "{:0.0f}").format(
            random.uniform(
                args.min,
                args.max,
            )
        )
        if args.float == 1 or args.int == 1
        else string.random(args.length)
    )
else:
    print(f"-{NAME}: {args.task}: command not found")

if not success:
    print(f"-{NAME}: {args.task}: failed")
