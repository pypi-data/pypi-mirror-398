import argparse

from blueness import module
from blueness.argparse.generic import sys_exit

from bluer_objects import NAME
from bluer_objects.assets.functions import publish
from bluer_objects.logger import logger

NAME = module.name(__file__, NAME)

parser = argparse.ArgumentParser(NAME)
parser.add_argument(
    "task",
    type=str,
    help="publish",
)
parser.add_argument(
    "--arg",
    type=bool,
    default=0,
    help="0|1",
)
parser.add_argument(
    "--object_name",
    type=str,
)
parser.add_argument(
    "--extensions",
    type=str,
    default="png",
    help="png+txt",
)
parser.add_argument(
    "--prefix",
    type=str,
    default="",
)
parser.add_argument(
    "--asset_name",
    type=str,
    default="",
)
args = parser.parse_args()

success = False
if args.task == "publish":
    success = publish(
        object_name=args.object_name,
        list_of_extensions=args.extensions.split("+"),
        prefix=args.prefix,
        asset_name=args.asset_name,
    )
else:
    success = None

sys_exit(logger, NAME, args.task, success)
