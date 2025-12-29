import argparse

from blueness import module
from blueness.argparse.generic import sys_exit

from bluer_ugv import NAME
from bluer_ugv import env
from bluer_ugv.swallow.session.classical.ultrasonic_sensor.review import review
from bluer_ugv.swallow.session.classical.ultrasonic_sensor.testing import test
from bluer_ugv.logger import logger

NAME = module.name(__file__, NAME)

parser = argparse.ArgumentParser(NAME)
parser.add_argument(
    "task",
    type=str,
    help="review|test",
)
parser.add_argument(
    "--max_m",
    type=float,
    default=env.BLUER_UGV_ULTRASONIC_SENSOR_MAX_M,
    help="detection threshold in meters.",
)
parser.add_argument(
    "--object_name",
    type=str,
)
parser.add_argument(
    "--log",
    type=int,
    default=1,
    help="0 | 1.",
)
parser.add_argument(
    "--export",
    type=int,
    default=1,
    help="0 | 1",
)
parser.add_argument(
    "--gif",
    type=int,
    default=1,
    help="0 | 1",
)
parser.add_argument(
    "--rm_blank",
    type=int,
    default=1,
    help="0 | 1.",
)
parser.add_argument(
    "--frame_count",
    type=int,
    default=100,
    help="-1: all",
)
args = parser.parse_args()

success = False
if args.task == "review":
    success = review(
        object_name=args.object_name,
        export_gif=args.gif == 1,
        frame_count=args.frame_count,
        rm_blank=args.rm_blank == 1,
    )
elif args.task == "test":
    success = test(
        object_name=args.object_name,
        max_m=args.max_m,
        export=args.export == 1,
        export_gif=args.gif == 1,
        frame_count=args.frame_count,
        log=args.log == 1,
        rm_blank=args.rm_blank == 1,
    )
else:
    success = None

sys_exit(logger, NAME, args.task, success)
