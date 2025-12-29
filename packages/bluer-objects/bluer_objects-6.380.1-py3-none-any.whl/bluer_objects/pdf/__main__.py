import argparse

from blueness import module
from blueness.argparse.generic import sys_exit

from bluer_objects import NAME
from bluer_objects.pdf.convert.batch import batch as batch_convert
from bluer_objects.pdf.convert.convert import convert
from bluer_objects.logger import logger

NAME = module.name(__file__, NAME)

parser = argparse.ArgumentParser(NAME)
parser.add_argument(
    "task",
    type=str,
    help="convert",
)
parser.add_argument(
    "--path_prefix",
    type=str,
)
parser.add_argument(
    "--object_name",
    type=str,
)
parser.add_argument(
    "--suffixes",
    type=str,
)
parser.add_argument(
    "--combine",
    type=int,
    default=0,
    help="0 | 1",
)

parser.add_argument(
    "--count",
    type=int,
    default=-1,
    help="-1: all",
)
parser.add_argument(
    "--list_missing",
    type=int,
    default=1,
    help="0 | 1",
)
parser.add_argument(
    "--use_metadata",
    type=int,
    default=0,
    help="0 | 1",
)
args = parser.parse_args()

success = False
if args.task == "convert":
    if args.use_metadata == 1:
        success = batch_convert(
            object_name=args.object_name,
            combine=args.combine == 1,
            count=args.count,
            list_missing=args.list_missing == 1,
        )
    else:
        success = convert(
            path_prefix=args.path_prefix,
            list_of_suffixes=args.suffixes.split(","),
            object_name=args.object_name,
            combine=args.combine == 1,
            count=args.count,
        )
else:
    success = None

sys_exit(logger, NAME, args.task, success)
