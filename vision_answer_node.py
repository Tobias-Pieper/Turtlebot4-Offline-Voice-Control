#!/usr/bin/env python3

import subprocess
import time

import cv2
import numpy as np

import rclpy
from rclpy.node import Node
from rclpy.qos import QoSProfile, ReliabilityPolicy, HistoryPolicy

from std_msgs.msg import String
from sensor_msgs.msg import Image
from cv_bridge import CvBridge


CAMERA_TOPIC = "/oakd/rgb/preview/image_raw"
VOICE_COMMAND_TOPIC = "/voice_command"

PIPER_MODEL = "/home/tobi/piper_voices/en_US-lessac-medium.onnx"
TTS_AUDIO = "/tmp/tb4_vision_tts.wav"


ARUCO_LABELS = {
    1: "the charging station",
    2: "the field entrance",
    3: "the target object",
    4: "an obstacle",
}


class VisionAnswerNode(Node):

    def __init__(self):
        super().__init__("vision_answer_node")

        self.bridge = CvBridge()
        self.latest_frame = None

        camera_qos = QoSProfile(
            reliability=ReliabilityPolicy.BEST_EFFORT,
            history=HistoryPolicy.KEEP_LAST,
            depth=1,
        )

        self.image_sub = self.create_subscription(
            Image,
            CAMERA_TOPIC,
            self.image_callback,
            camera_qos,
        )

        self.voice_sub = self.create_subscription(
            String,
            VOICE_COMMAND_TOPIC,
            self.voice_command_callback,
            10,
        )

        self.get_logger().info("VisionAnswerNode started.")
        self.get_logger().info(f"Listening to camera topic: {CAMERA_TOPIC}")
        self.get_logger().info(f"Listening to command topic: {VOICE_COMMAND_TOPIC}")

    def image_callback(self, msg):
        try:
            self.latest_frame = self.bridge.imgmsg_to_cv2(
                msg,
                desired_encoding="bgr8",
            )

        except Exception as error:
            self.get_logger().error(
                f"Could not convert image: {error}"
            )

    def speak(self, text):
        self.get_logger().info(f"TTS: {text}")

        try:
            subprocess.run(
                [
                    "/home/tobi/tb4_voice_env/bin/piper",
                    "--model",
                    PIPER_MODEL,
                    "--output_file",
                    TTS_AUDIO,
                ],
                input=text.encode("utf-8"),
                check=True,
            )

            subprocess.run(
                [
                    "aplay",
                    TTS_AUDIO,
                ],
                check=True,
            )

        except Exception as error:
            self.get_logger().error(
                f"TTS error: {error}"
            )

    def detect_aruco_marker(self, frame):
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)

        aruco_dict = cv2.aruco.Dictionary_get(
            cv2.aruco.DICT_4X4_50
        )

        parameters = cv2.aruco.DetectorParameters_create()

        corners, ids, rejected = cv2.aruco.detectMarkers(
            gray,
            aruco_dict,
            parameters=parameters,
        )

        if ids is None or len(ids) == 0:
            return None

        marker_id = int(ids[0][0])

        label = ARUCO_LABELS.get(
            marker_id,
            f"marker {marker_id}"
        )

        return marker_id, label

    def detect_dominant_color(self, frame):
        hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)

        color_ranges = {
            "red": [
                ((0, 70, 50), (10, 255, 255)),
                ((170, 70, 50), (180, 255, 255)),
            ],
            "green": [
                ((35, 50, 50), (85, 255, 255)),
            ],
            "blue": [
                ((90, 50, 50), (130, 255, 255)),
            ],
            "yellow": [
                ((20, 70, 70), (35, 255, 255)),
            ],
            "white": [
                ((0, 0, 180), (180, 40, 255)),
            ],
            "black": [
                ((0, 0, 0), (180, 255, 60)),
            ],
        }

        color_scores = {}

        for color_name, ranges in color_ranges.items():
            total_pixels = 0

            for lower, upper in ranges:
                lower_np = np.array(lower, dtype=np.uint8)
                upper_np = np.array(upper, dtype=np.uint8)

                mask = cv2.inRange(
                    hsv,
                    lower_np,
                    upper_np,
                )

                total_pixels += int(np.sum(mask > 0))

            color_scores[color_name] = total_pixels

        dominant_color = max(
            color_scores,
            key=color_scores.get,
        )

        return dominant_color, color_scores[dominant_color]

    def answer_what_do_you_see(self):
        if self.latest_frame is None:
            self.get_logger().warn("No camera image received yet.")
            self.speak("I do not have a camera image yet.")
            return

        frame = self.latest_frame.copy()

        marker_result = self.detect_aruco_marker(frame)

        if marker_result is not None:
            marker_id, label = marker_result

            answer = (
                f"I see an ArUco marker. "
                f"It is marker {marker_id}. "
                f"This is {label}."
            )

            self.get_logger().info(answer)
            self.speak(answer)
            return

        dominant_color, pixel_count = self.detect_dominant_color(frame)

        answer = (
            f"I did not detect an ArUco marker. "
            f"I mostly see {dominant_color}."
        )

        self.get_logger().info(
            f"{answer} Pixel count: {pixel_count}"
        )

        self.speak(answer)

    def voice_command_callback(self, msg):
        command = msg.data.strip().upper()

        if command != "LOOK":
            return

        self.get_logger().info("LOOK command received.")
        self.answer_what_do_you_see()


def main(args=None):
    rclpy.init(args=args)

    node = VisionAnswerNode()

    try:
        rclpy.spin(node)

    except KeyboardInterrupt:
        pass

    finally:
        node.destroy_node()
        rclpy.shutdown()


if __name__ == "__main__":
    main()
