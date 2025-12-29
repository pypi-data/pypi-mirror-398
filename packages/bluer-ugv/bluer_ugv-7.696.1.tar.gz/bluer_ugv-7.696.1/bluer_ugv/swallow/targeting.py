from blueness import module
import numpy as np

from bluer_options.terminal import hr
from bluer_algo.socket.connection import SocketConnection
from bluer_algo.tracker.classes.target import Target

from bluer_ugv import NAME
from bluer_ugv.logger import logger


NAME = module.name(__file__, NAME)

DEFAULT_TARGETING_PORT = 8002


def select_target(
    host: str,
    loop: bool = True,
    port: int = DEFAULT_TARGETING_PORT,
) -> bool:
    logger.info(
        "{}.select_target on {} port={}{}".format(
            NAME,
            host,
            port,
            " on a loop." if loop else "",
        )
    )

    try:
        while loop:
            socket = SocketConnection.listen_on(port=port)
            success, image = socket.receive_data(np.ndarray)
            if not success:
                return success

            success, track_window = Target.select(
                image,
                title=f"select the target for {host} port={port}...",
            )
            if not success:
                return success

            socket = SocketConnection.connect_to(
                host,
                port=port,
            )
            if not socket.send_data(track_window):
                return False

            hr_line = hr(
                width=12,
                mono=True,
            )
            logger.info(f"{hr_line} Ctrl+C to exit {hr_line}")
    except KeyboardInterrupt:
        logger.info("Ctrl+C, stopping.")

    return True
