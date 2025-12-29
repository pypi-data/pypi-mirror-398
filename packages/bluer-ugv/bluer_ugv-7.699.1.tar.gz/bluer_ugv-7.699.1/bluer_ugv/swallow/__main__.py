import argparse

from blueness import module
from blueness.argparse.generic import sys_exit

from bluer_ugv import NAME
from bluer_ugv.swallow.targeting import select_target, DEFAULT_TARGETING_PORT
from bluer_ugv.swallow.debug import debug, DEFAULT_DEBUG_PORT
from bluer_ugv.logger import logger

NAME = module.name(__file__, NAME)

parser = argparse.ArgumentParser(NAME)
parser.add_argument(
    "task",
    type=str,
    help="debug|select_target",
)
parser.add_argument(
    "--host",
    type=str,
)
parser.add_argument(
    "--loop",
    type=int,
    default=1,
    help="0 | 1",
)
parser.add_argument(
    "--object_name",
    type=str,
)
parser.add_argument(
    "--save_images",
    type=int,
    default=1,
    help="0 | 1",
)
parser.add_argument(
    "--generate_gif",
    type=int,
    default=1,
    help="0 | 1",
)
parser.add_argument(
    "--port",
    type=int,
    default=-1,
)
args = parser.parse_args()

success = False
if args.task == "debug":
    success = debug(
        object_name=args.object_name,
        generate_gif=args.generate_gif == 1,
        save_images=args.save_images == 1,
        port=DEFAULT_DEBUG_PORT if args.port == -1 else args.port,
    )
elif args.task == "select_target":
    success = select_target(
        host=args.host,
        loop=args.loop == 1,
        port=DEFAULT_TARGETING_PORT if args.port == -1 else args.port,
    )
else:
    success = None

sys_exit(logger, NAME, args.task, success)
