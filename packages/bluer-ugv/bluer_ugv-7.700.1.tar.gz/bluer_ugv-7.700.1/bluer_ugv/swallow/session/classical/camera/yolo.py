from typing import List
import threading

from bluer_options.timer import Timer
from bluer_options import string
from bluer_objects.storage.policies import DownloadPolicy
from bluer_objects import storage
from bluer_objects.metadata import post_to_object, get_from_object
from bluer_sbc.imager.camera import instance as camera
from bluer_sbc.env import BLUER_SBC_CAMERA_WIDTH
from bluer_algo.yolo.dataset.classes import YoloDataset
from bluer_algo.yolo.model.predictor import YoloPredictor
from bluer_algo.socket.message import SocketMessage

from bluer_ugv import env
from bluer_ugv.swallow.session.classical.camera.generic import ClassicalCamera
from bluer_ugv.swallow.session.classical.keyboard.classes import ClassicalKeyboard
from bluer_ugv.swallow.session.classical.leds import ClassicalLeds
from bluer_ugv.swallow.session.classical.setpoint.classes import ClassicalSetPoint
from bluer_ugv.swallow.session.classical.mode import OperationMode
from bluer_ugv.logger import logger


class ClassicalYoloCamera(ClassicalCamera):
    def __init__(
        self,
        keyboard: ClassicalKeyboard,
        leds: ClassicalLeds,
        setpoint: ClassicalSetPoint,
        object_name: str,
    ):
        super().__init__(keyboard, leds, setpoint, object_name)

        self.prediction_timer = Timer(
            period=env.BLUER_UGV_CAMERA_ACTION_PERIOD,
            name="{}.prediction".format(self.__class__.__name__),
            log=True,
        )
        self.training_timer = Timer(
            period=env.BLUER_UGV_CAMERA_TRAINING_PERIOD,
            name="{}.training".format(self.__class__.__name__),
            log=True,
        )

        self.dataset = YoloDataset(
            object_name=self.object_name,
            create=True,
        )

        assert super().initialize()

        if not storage.download(
            env.BLUER_UGV_SWALLOW_YOLO_MODEL,
            policy=DownloadPolicy.DOESNT_EXIST,
        ):
            logger.error("cannot download the model.")

        success, self.predictor = YoloPredictor.load(
            object_name=env.BLUER_UGV_SWALLOW_YOLO_MODEL,
            image_size=BLUER_SBC_CAMERA_WIDTH,
        )
        if not success:
            logger.error("cannot create the predictor.")

        self.running = True
        self.thread = threading.Thread(target=self.loop, daemon=True)
        self.thread.start()

    # the parent method is called in the constructor
    def initialize(self) -> bool:
        return True

    def cleanup(self):
        return True

    # the parent method is called in stop()
    def stop(self):
        self.running = False
        self.thread.join()

        logger.info(f"{self.__class__.__name__}.stopped.")

        super().cleanup()

        if not self.dataset.save(
            verbose=True,
        ):
            logger.error("cannot save the dataset.")

        if self.dataset.empty:
            return

        dataset_list: List[str] = get_from_object(
            object_name=env.BLUER_UGV_SWALLOW_YOLO_DATASET_LIST,
            key="dataset-list",
            default=[],
            download=True,
        )
        dataset_list.append(self.object_name)
        if not post_to_object(
            object_name=env.BLUER_UGV_SWALLOW_YOLO_DATASET_LIST,
            key="dataset-list",
            value=dataset_list,
            upload=True,
            verbose=True,
        ):
            logger.error("failed to add object to dataset list.")

    def loop(self):
        logger.info(f"{self.__class__.__name__}.loop started.")

        while self.running:
            mode = self.keyboard.get("mode", OperationMode.NONE)

            success = True
            if mode == OperationMode.ACTION:
                success = self.loop_action()

            if mode == OperationMode.TRAINING:
                success = self.loop_training()

            if not success:
                logger.error(f"loop failed, mode: {mode.name.lower()}.")

    def loop_action(self) -> bool:
        if not self.prediction_timer.tick():
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
        success, metadata = self.predictor.predict(
            image=image,
            return_annotated_image=debug_mode,
            annotated_image_scale=2,
        )
        if not success:
            return success

        if debug_mode:
            if not self.send_debug_data(
                SocketMessage(
                    {
                        "image": metadata["annotated_image"],
                    }
                )
            ):
                logger.warning("failed to send debug data.")

        if not metadata["detections"]:
            logger.info("no detections.")
            return True

        detection = metadata["detections"][0]
        logger.info("confidence: {:.2f}".format(detection["confidence"]))
        detection_x_center = (detection["bbox_xyxy"][0] + detection["bbox_xyxy"][2]) / 2
        if detection_x_center < image.shape[1] / 2:
            self.setpoint.put(
                what="steering",
                value=env.BLUER_UGV_SWALLOW_STEERING_SETPOINT,
                log=True,
                steering_expires_in=env.BLUER_UGV_SWALLOW_STEERING_YOLO_EXPIRY,
            )
        else:
            self.setpoint.put(
                what="steering",
                value=-env.BLUER_UGV_SWALLOW_STEERING_SETPOINT,
                log=True,
                steering_expires_in=env.BLUER_UGV_SWALLOW_STEERING_YOLO_EXPIRY,
            )

        return True

    def loop_training(self) -> bool:
        if not (self.training_timer.tick() or self.keyboard.last_key != ""):
            return True

        self.leds.flash("red")

        filename = "{}.png".format(
            string.pretty_date(
                as_filename=True,
                unique=True,
            )
        )

        success, _ = camera.capture(
            close_after=False,
            open_before=False,
            object_name=self.object_name,
            filename=filename,
            log=True,
        )
        if not success:
            return success

        # TODO: dataset +=

        self.training_timer.reset()

        return True
