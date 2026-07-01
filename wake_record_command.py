#!/usr/bin/env python3

import time
import wave
import numpy as np
import sounddevice as sd

from openwakeword.model import Model


# =============================
# Configuration
# =============================

DEVICE_ID = 1                 # Logitech C920 microphone
SAMPLE_RATE = 16000
BLOCK_SIZE = 2560

WAKEWORD_NAME = "hey_mycroft"

WAKEWORD_THRESHOLD = 0.9
REARM_SCORE_THRESHOLD = 0.2

COMMAND_AUDIO = "/home/ubuntu/command.wav"
READY_FLAG = "/home/ubuntu/command_ready.flag"

COMMAND_RECORD_DURATION = 5

REARM_DELAY_SECONDS = 3


# =============================
# State variables
# =============================

model = Model()

armed = True
recording_command = False
command_blocks = []
command_start_time = None


# =============================
# Helper functions
# =============================

def save_wav(filename, audio_blocks, sample_rate):
    audio_data = np.concatenate(audio_blocks)

    with wave.open(filename, "wb") as wav_file:
        wav_file.setnchannels(1)
        wav_file.setsampwidth(2)  # 16-bit audio
        wav_file.setframerate(sample_rate)
        wav_file.writeframes(audio_data.tobytes())


def create_ready_flag():
    time.sleep(0.5)

    with open(READY_FLAG, "w") as flag_file:
        flag_file.write("ready\n")

    print(f"Ready flag written to: {READY_FLAG}")


def audio_callback(indata, frames, time_info, status):
    global armed
    global recording_command
    global command_blocks
    global command_start_time

    if status:
        return

    audio_float = indata[:, 0]
    audio_int16 = (audio_float * 32767).astype(np.int16)

    current_time = time.time()

    # -----------------------------
    # Record command after wake word
    # -----------------------------
    if recording_command:
        command_blocks.append(audio_int16.copy())

        if current_time - command_start_time >= COMMAND_RECORD_DURATION:
            print("\nCommand recording finished.")

            save_wav(
                COMMAND_AUDIO,
                command_blocks,
                SAMPLE_RATE
            )

            print(f"Saved command audio to: {COMMAND_AUDIO}")

            create_ready_flag()

            print(f"Waiting {REARM_DELAY_SECONDS} seconds before re-arming...")

            time.sleep(REARM_DELAY_SECONDS)

            recording_command = False
            command_blocks = []
            command_start_time = None
            armed = False

            print("Waiting until wake word score is low again...\n")

        return

    # -----------------------------
    # Wake word detection
    # -----------------------------
    prediction = model.predict(audio_int16)

    wake_score = prediction.get(WAKEWORD_NAME, 0.0)

    # If detector is not armed, wait until score drops
    if not armed:
        if wake_score < REARM_SCORE_THRESHOLD:
            armed = True
            print("Wake word detector re-armed.")
        return

    # Detect wake word only when armed
    if wake_score > WAKEWORD_THRESHOLD:
        armed = False

        print(
            f"\nWake word detected: {WAKEWORD_NAME} "
            f"(score={wake_score:.3f})"
        )

        print("Recording command now...")
        print("Speak your command, for example: Move left")

        recording_command = True
        command_blocks = []
        command_start_time = current_time


# =============================
# Main
# =============================

def main():
    print("\n====================================")
    print(" TurtleBot4 OpenWakeWord Recorder")
    print("====================================")
    print(f"Listening for wake word: {WAKEWORD_NAME}")
    print("After detection, speak only the command.")
    print("Example: Move left / Move forward / Stop / What do you see?")
    print("Press CTRL+C to stop.\n")

    try:
        with sd.InputStream(
            device=DEVICE_ID,
            channels=1,
            samplerate=SAMPLE_RATE,
            blocksize=BLOCK_SIZE,
            callback=audio_callback
        ):
            while True:
                time.sleep(0.1)

    except KeyboardInterrupt:
        print("\nStopping wake word recorder...")


if __name__ == "__main__":
    main()

