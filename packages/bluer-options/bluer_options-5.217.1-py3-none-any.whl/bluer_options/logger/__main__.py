import argparse

from blueness import module
from blueness.argparse.generic import sys_exit

from bluer_options import NAME
from bluer_options.logger.watch import watch
from bluer_options.logger import logger

NAME = module.name(__file__, NAME)

parser = argparse.ArgumentParser(NAME)
parser.add_argument(
    "task",
    type=str,
    help="watch",
)
parser.add_argument(
    "--seconds",
    type=int,
    default=1,
    help="in seconds.",
)
args = parser.parse_args()

success = False
if args.task == "watch":
    success = watch(seconds=args.seconds)
else:
    success = None

sys_exit(logger, NAME, args.task, success)
