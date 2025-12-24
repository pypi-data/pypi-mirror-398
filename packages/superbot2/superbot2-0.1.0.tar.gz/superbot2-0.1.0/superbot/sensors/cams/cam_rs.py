import numpy as np
import cv2
from typing import Any, cast

from loguru import logger

try:
    import pyrealsense2 as rs
except ImportError:
    print("Warning: pyrealsense2 not available. Camera functionality will be limited.")
    rs = None

# Help static analyzers: treat rs as dynamic Any when available
if rs is not None:
    rs = cast(Any, rs)


class CameraWrapper:
    def __init__(
        self,
        devices=None,
        width=640,
        height=480,
        fps=30,
        num_realsense=0,
        cv_format="MJPEG",
    ):
        self.width = width
        self.height = height
        self.fps = fps
        self.num_realsense = max(0, int(num_realsense))
        self.cv_format = cv_format
        self.cameras = []  # list of dicts: {type: 'rs'|'cv', handle: pipeline|cap}
        self.device_ids = devices if devices is not None else []
        self._open_cameras()
        print(f"successfully opened {len(self.cameras)} cameras!")

    def _open_cameras(self):
        if not self.device_ids:
            print("No devices provided for CameraWrapper")
            return

        for idx, dev in enumerate(self.device_ids):
            # Decide camera type
            use_realsense = idx < self.num_realsense

            if use_realsense:
                if rs is None:
                    print(
                        f"pyrealsense2 not available, skipping RealSense device at index {idx} (id: {dev})"
                    )
                    continue
                try:
                    serial = str(dev)
                    pipeline = rs.pipeline()  # type: ignore[attr-defined]
                    config = rs.config()  # type: ignore[attr-defined]
                    config.enable_device(serial)
                    config.enable_stream(rs.stream.color, self.width, self.height, rs.format.bgr8, self.fps)  # type: ignore[attr-defined]
                    pipeline.start(config)
                    self.cameras.append({"type": "rs", "handle": pipeline})
                    print(f"RealSense camera {serial} opened successfully")
                except Exception as e:
                    print(f"Failed to open RealSense camera {dev}: {e}")
            else:
                try:
                    device_index = int(dev)
                    print(f"Ready to read deive: {device_index}")
                    cap = cv2.VideoCapture(device_index)

                    if self.cv_format == "MJPEG":
                        cap.set(cv2.CAP_PROP_FOURCC, cv2.VideoWriter_fourcc(*"MJPG"))  # type: ignore[attr-defined]
                    elif self.cv_format == "YUYV":
                        cap.set(cv2.CAP_PROP_FOURCC, cv2.VideoWriter_fourcc(*"YUYV"))  # type: ignore[attr-defined]

                    cap.set(cv2.CAP_PROP_FRAME_WIDTH, self.width)
                    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, self.height)
                    cap.set(cv2.CAP_PROP_FPS, self.fps)

                    if not cap.isOpened():
                        raise ValueError(f"Cannot open OpenCV camera {device_index}")

                    self.cameras.append({"type": "cv", "handle": cap})
                    print(f"OpenCV camera {device_index} opened successfully")
                except Exception as e:
                    print(f"Failed to open OpenCV camera {dev}: {e}")

    def get_images(self):
        images = []
        if len(self.cameras) == 0:
            # Return dummy images if no cameras available - use 640x480 which is expected by the model
            for _ in range(max(1, len(self.device_ids))):
                dummy_img = np.zeros((self.height, self.width, 3), dtype=np.uint8)
                dummy_img[:, :, :] = 128  # Gray color instead of black
                images.append(dummy_img)
            return images

        for cam in self.cameras:
            if cam["type"] == "rs":
                try:
                    pipeline = cam["handle"]
                    frames = pipeline.wait_for_frames()
                    color_frame = frames.get_color_frame()
                    if not color_frame:
                        dummy_img = np.zeros(
                            (self.height, self.width, 3), dtype=np.uint8
                        )
                        dummy_img[:, :, :] = 128
                        images.append(dummy_img)
                    else:
                        img = np.asanyarray(color_frame.get_data())
                        images.append(img)
                except Exception as e:
                    print(f"Error reading from RealSense: {e}")
                    dummy_img = np.zeros((self.height, self.width, 3), dtype=np.uint8)
                    dummy_img[:, :, :] = 128
                    images.append(dummy_img)
            elif cam["type"] == "cv":
                cap = cam["handle"]
                ret, frame = cap.read()
                if not ret or frame is None:
                    dummy_img = np.zeros((self.height, self.width, 3), dtype=np.uint8)
                    dummy_img[:, :, :] = 128
                    images.append(dummy_img)
                else:
                    images.append(frame)
        return images

    def release(self):
        for cam in self.cameras:
            if cam["type"] == "rs":
                try:
                    cam["handle"].stop()
                except Exception:
                    pass
            elif cam["type"] == "cv":
                try:
                    cam["handle"].release()
                except Exception:
                    pass
        self.cameras = []
