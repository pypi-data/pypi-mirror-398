from typing import Tuple
import numpy as np

from bluer_options.timer import Timer
from bluer_algo.env import BLUER_ALGO_TRACKER_DEFAULT_ALGO
from bluer_algo.tracker.classes.target import Target
from bluer_algo.tracker.factory import get_tracker_class
from bluer_algo.socket.message import SocketMessage
from bluer_sbc.imager.camera import instance as camera

from bluer_ugv import env
from bluer_ugv.swallow.session.classical.camera.generic import ClassicalCamera
from bluer_ugv.swallow.session.classical.camera.generic import ClassicalCamera
from bluer_ugv.swallow.session.classical.keyboard.classes import ClassicalKeyboard
from bluer_ugv.swallow.session.classical.leds import ClassicalLeds
from bluer_ugv.swallow.session.classical.setpoint.classes import ClassicalSetPoint
from bluer_ugv.swallow.session.classical.mode import OperationMode
from bluer_ugv.swallow.targeting import DEFAULT_TARGETING_PORT
from bluer_ugv.logger import logger


class ClassicalTrackingCamera(ClassicalCamera):
    def __init__(
        self,
        keyboard: ClassicalKeyboard,
        leds: ClassicalLeds,
        setpoint: ClassicalSetPoint,
        object_name: str,
    ):
        super().__init__(keyboard, leds, setpoint, object_name)

        self.track_window: Tuple[int, int, int, int] = None

        self.tracking_timer = Timer(
            period=env.BLUER_UGV_CAMERA_ACTION_PERIOD,
            name="{}.tracking".format(self.__class__.__name__),
            log=True,
        )

        self.tracker = get_tracker_class(BLUER_ALGO_TRACKER_DEFAULT_ALGO)[1]()

    def initialize(self) -> bool:
        if not super().initialize():
            return False

        return self.select_target()

    def select_target(self) -> bool:
        success, image = camera.capture(
            close_after=False,
            open_before=False,
            log=True,
        )
        if not success:
            return success

        self.leds.set_all(True)
        success, self.track_window = Target.select(
            np.flip(image, axis=2),
            local=False,
            port=DEFAULT_TARGETING_PORT,
        )
        self.leds.set_all(False)
        if not success:
            return success

        logger.info(f"track_window: {self.track_window}")

        self.tracker.start(
            frame=image,
            track_window=self.track_window,
        )

        return True

    def update(self) -> bool:
        if not super().update():
            return False

        mode = self.keyboard.get("mode", OperationMode.NONE)
        if mode == OperationMode.TRAINING:
            return self.update_training()

        if self.setpoint.speed <= 0:
            return True

        if mode == OperationMode.ACTION:
            return self.update_action()

        return True

    def update_action(self) -> bool:
        if not self.tracking_timer.tick():
            return True

        self.leds.flash("red")

        success, image = camera.capture(
            close_after=False,
            open_before=False,
            log=True,
        )
        if not success:
            return success

        debug_mode = self.keyboard.get("debug_mode", False)
        _, self.track_window, output_image = self.tracker.track(
            frame=image,
            track_window=self.track_window,
            log=debug_mode,
        )
        logger.info(f"🎯 {self.track_window}")

        if debug_mode:
            if not self.send_debug_data(
                SocketMessage(
                    {
                        "image": output_image,
                    }
                )
            ):
                logger.warning("failed to send debug data.")

        if not self.tracker.tracking:
            logger.warning("🎯 lost target")
            self.leds.flash_all()
            return True

        x, _, w, _ = self.track_window
        if x + w // 2 > image.shape[1] * 2 / 3:
            self.setpoint.put(
                what="steering",
                value=-env.BLUER_UGV_SWALLOW_STEERING_SETPOINT,
                log=True,
            )
        elif x + w // 2 < image.shape[1] * 1 / 3:
            self.setpoint.put(
                what="steering",
                value=env.BLUER_UGV_SWALLOW_STEERING_SETPOINT,
                log=True,
            )

        return True

    def update_training(self) -> bool:
        self.keyboard.set("mode", OperationMode.NONE)
        return self.select_target()
