#!/usr/bin/env python3

import os
import time
import subprocess

import whisper
import rclpy

from rclpy.node import Node
from std_msgs.msg import String


TB4_IP = "172.21.190.27"
TB4_USER = "ubuntu"

REMOTE_AUDIO = "/home/ubuntu/command.wav"
REMOTE_FLAG = "/home/ubuntu/command_ready.flag"

LOCAL_AUDIO = "/home/tobi/command.wav"

PIPER_MODEL = "/home/tobi/piper_voices/en_US-lessac-medium.onnx"
TTS_AUDIO = "/tmp/tb4_tts.wav"

CHECK_INTERVAL = 1.0


COMMAND_KEYWORDS = {
    "STOP": [
        "stop",
        "halt",
        "emergency stop",
    ],

    "LEFT": [
        "move left",
        "turn left",
    ],

    "RIGHT": [
        "move right",
        "turn right",
    ],

    "FORWARD": [
        "go forward",
        "move forward",
    ],

    "BACKWARD": [
        "go backward",
        "move backward",
        "move back",
        "go back",
    ],

    "DOCK": [
        "dock",
        "go home",
        "return home",
        "move home",
        "dog",
        "dug",
    ],

    "UNDOCK": [
        "undock",
        "leave dock",
        "leave the dock",
        "exit dock",
        "exit",
        "un-dock",
    ],

    "LOOK":[
        "what do you see",
        "what  can you see",
        "look",
        "see",
        "sea",
    ],
}


TTS_MESSAGES = {
    "STOP": "Emergency stop activated.",
    "LEFT": "Turning left.",
    "RIGHT": "Turning right.",
    "FORWARD": "Moving forward.",
    "BACKWARD": "Moving backward.",
    "DOCK": "Docking.",
    "UNDOCK": "Undocking.",
    "UNKNOWN": "Please repeat your command.",
    "LOOK": "Let me check.",
}


def parse_command(text):
    for command, keywords in COMMAND_KEYWORDS.items():
        for keyword in keywords:
            if keyword in text:
                return command

    return "UNKNOWN"


def speak(text):
    try:
        subprocess.run(
            [
                "piper",
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
        print(f"TTS error: {error}")


class VoiceCommandPublisher(Node):

    def __init__(self):
        super().__init__("voice_command_publisher")

        self.publisher = self.create_publisher(
            String,
            "/voice_command",
            10
        )

    def publish_command(self, command):
        msg = String()
        msg.data = command

        self.publisher.publish(msg)

        self.get_logger().info(
            f"Published command: {command}"
        )

        time.sleep(0.5)


def flag_exists():
    cmd = (
        f"ssh {TB4_USER}@{TB4_IP} "
        f"'test -f {REMOTE_FLAG} && echo READY'"
    )

    result = subprocess.run(
        cmd,
        shell=True,
        capture_output=True,
        text=True,
    )

    return "READY" in result.stdout


def delete_flag():
    cmd = (
        f"ssh {TB4_USER}@{TB4_IP} "
        f"'rm -f {REMOTE_FLAG}'"
    )

    subprocess.run(
        cmd,
        shell=True,
    )


def copy_audio():
    cmd = (
        f"scp "
        f"{TB4_USER}@{TB4_IP}:{REMOTE_AUDIO} "
        f"{LOCAL_AUDIO}"
    )

    subprocess.run(
        cmd,
        shell=True,
        check=True,
    )

    if not os.path.exists(LOCAL_AUDIO):
        raise FileNotFoundError(
            f"Audio file not found: {LOCAL_AUDIO}"
        )

    print(f"Audio copied to: {LOCAL_AUDIO}")


def main():
    print("\nLoading Whisper model...")
    model = whisper.load_model("base")

    rclpy.init()
    node = VoiceCommandPublisher()

    print("\n====================================")
    print(" TB4 Voice Command Listener with TTS")
    print("====================================")
    print("Waiting for command_ready.flag...")
    print("Press CTRL+C to stop.\n")

    try:
        while True:
            if flag_exists():
                print("\nNew command detected!")

                copy_audio()
                delete_flag()

                print("\nTranscribing audio...")

                result = model.transcribe(
                    LOCAL_AUDIO,
                    language="en",
                    fp16=False,
                )

                text = result["text"].lower().strip()

                print(f"\nDetected text: {text}")

                command = parse_command(text)

                if command == "UNKNOWN":
                    print("Unknown command.")
                    speak(TTS_MESSAGES["UNKNOWN"])

                else:
                    print(f"Command: {command}")

                    speak(TTS_MESSAGES[command])

                    node.publish_command(command)

                print("\nWaiting for next command...")

            time.sleep(CHECK_INTERVAL)

    except KeyboardInterrupt:
        print("\nStopping listener...")

    finally:
        node.destroy_node()
        rclpy.shutdown()


if __name__ == "__main__":
    main()
