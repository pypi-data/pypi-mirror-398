import argparse

from blueness import module
from blueness.argparse.generic import sys_exit

from bluer_options import NAME
from bluer_options.host import get_name
from bluer_options.logger import logger

NAME = module.name(__file__, NAME)

parser = argparse.ArgumentParser(NAME)
parser.add_argument(
    "task",
    type=str,
    default="get",
    help="get",
)
parser.add_argument(
    "--keyword",
    type=str,
    help="name",
)
args = parser.parse_args()


success = False
# bash-tested in test_bluer_ai_host in bluer-objects.
if args.task == "get":
    success = True
    output = f"unknown-{args.keyword}"

    if args.keyword == "name":
        output = get_name()

    print(output)
else:
    success = None


sys_exit(logger, NAME, args.task, success, log=False)
