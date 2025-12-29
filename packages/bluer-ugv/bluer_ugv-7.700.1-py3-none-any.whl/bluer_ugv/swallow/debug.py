from blueness import module
import numpy as np
import cv2
from typing import List, Dict

from bluer_options import string
from bluer_objects import file
from bluer_objects import objects
from bluer_objects.logger.stitch import stitch_images
from bluer_objects.graphics.gif import generate_animated_gif
from bluer_algo.socket.connection import SocketConnection, DEFAULT_PORT
from bluer_algo.socket.message import SocketMessage

from bluer_ugv import NAME
from bluer_ugv.logger import logger


NAME = module.name(__file__, NAME)

DEFAULT_DEBUG_PORT = DEFAULT_PORT


def debug(
    object_name: str,
    generate_gif: bool = True,
    save_images: bool = True,
    port: int = DEFAULT_DEBUG_PORT,
) -> bool:
    logger.info(
        "{}.debug -{}{}{}> {}".format(
            NAME,
            f"port={port}-",
            "images-" if save_images else "",
            "gif-" if generate_gif else "",
            object_name,
        )
    )

    socket = SocketConnection.listen_on(port=port)

    title = f"debug: port={port} -> {object_name} ..."

    cv2.namedWindow(title)
    logger.info("Ctrl+C to exit...")

    blank_image = np.zeros((480, 640, 3), np.uint8)

    image = blank_image.copy()
    dict_of_images: Dict[str, np.ndarray] = {}

    list_of_images: List[str] = []
    try:
        while True:
            cv2.imshow(title, np.flip(image, axis=2))
            cv2.waitKey(1)

            success, message = socket.receive_data(SocketMessage)
            if not success:
                break

            assert isinstance(message, SocketMessage)

            logger.info(f"message from {message.hostname}.")

            if "image" not in message.payload:
                logger.warning("no image.")
                continue

            dict_of_images[message.hostname] = message.payload["image"]

            image = stitch_images(
                [image for _, image in sorted(dict_of_images.items())]
            )

            if save_images:
                filename = objects.path_of(
                    filename="{}.png".format(string.timestamp()),
                    object_name=object_name,
                )

                if not file.save_image(filename, image, log=True):
                    break

                list_of_images.append(filename)
    except KeyboardInterrupt:
        logger.info("Ctrl+C, stopping.")

    cv2.destroyWindow(title)

    if generate_gif:
        if not generate_animated_gif(
            list_of_images,
            objects.path_of(
                filename=f"{object_name}.gif",
                object_name=object_name,
            ),
        ):
            return False

    return True
