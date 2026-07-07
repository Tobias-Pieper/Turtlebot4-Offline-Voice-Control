# Turtlebot4-Offline-Voice-Control 🎙️

An offline speech-controlled interface for the **TurtleBot4** using **ROS2 Jazzy**, **OpenWakeWord**, **Whisper**, **Piper TTS**, and **OpenCV**.

The project enables natural voice interaction with the TurtleBot4 without requiring any cloud services. Users can control the robot, start docking, stop ongoing actions, and ask the robot what it currently sees using its onboard camera.

---

## Features

- 🎤 Offline wake-word detection using **OpenWakeWord**
- 🗣️ Offline speech-to-text using **OpenAI Whisper**
- 🔊 Offline text-to-speech using **Piper TTS**
- 🤖 Voice-controlled robot motion
- ⚓ Native TurtleBot4 docking and undocking
- 🛑 Emergency stop
- 👁️ Vision-based "What do you see?" command
- 🟦 ArUco marker detection
- 🎨 Dominant color detection
- 🌐 Fully offline operation

---

# Demonstration

Example interaction:

```
User:
Hey Mycroft

Robot:
Listening...

User:
Move forward

Robot:
Moving forward.
```

```
User:
Hey Mycroft

Robot:
Listening...

User:
Dock

Robot:
Docking.
```

```
User:
Hey Mycroft

Robot:
What do you see?

Robot:
I did not detect an ArUco marker.
I mostly see green.
```

---

# System Architecture

```
                +----------------------+
                |   Logitech C920 Mic  |
                +----------+-----------+
                           |
                           v
                 OpenWakeWord (TB4)
                           |
                    Wake Word detected
                           |
                           v
                  Record command.wav
                           |
                  command_ready.flag
                           |
                           v
        SCP Transfer to Laptop (SSH)
                           |
                           v
                    Whisper STT
                           |
                           v
                 Command Parser
                           |
            +--------------+--------------+
            |                             |
            v                             v
    voice_motion_node          vision_answer_node
            |                             |
            v                             v
     TurtleBot4 Motion            OAK-D Camera
            |                             |
            +--------------+--------------+
                           |
                           v
                     Piper TTS
                           |
                           v
                  Bluetooth Speaker
```

---

# Software

| Software | Purpose |
|----------|---------|
| Ubuntu 24.04 LTS | Operating system |
| ROS2 Jazzy | Robot middleware |
| Python 3 | Main programming language |
| OpenWakeWord | Wake-word detection |
| Whisper | Speech-to-text |
| Piper TTS | Text-to-speech |
| OpenCV | Computer vision |
| cv_bridge | ROS2 ↔ OpenCV conversion |
| NumPy | Image processing |
| SSH / SCP | File transfer |
| Colcon | ROS2 build system |

---

# Hardware

- TurtleBot4
- iRobot Create3
- OAK-D Camera
- Logitech C920 Microphone
- Bluetooth Speaker
- Ubuntu Laptop

---

# Voice Commands

| Command | Action |
|----------|--------|
| Move forward | Drive forward |
| Move backward | Drive backward |
| Turn left | Rotate left |
| Turn right | Rotate right |
| Stop | Emergency stop |
| Dock | Start docking |
| Undock | Leave docking station |
| What do you see? | Vision analysis |

---

# Vision

The vision node supports:

- ArUco marker detection
- Dominant color detection

Suggested marker IDs:

| ID | Object |
|----|--------|
| 1 | Charging Station |
| 2 | Field Entrance |
| 3 | Water Tank |
| 4 | Obstacle |
| 5 | Service Station |
| 6 | Tractor |

---

# Project Structure

```
voice_control/
│
├── wake_record_command.py
├── process_latest_command.py
├── voice_motion_node.py
├── vision_answer_node.py
│
├── models/
│   ├── Whisper
│   └── Piper
│
└── README.md
```

---

# How it works

1. OpenWakeWord continuously listens for the wake word.
2. After detection, the TurtleBot4 records a voice command.
3. A `command_ready.flag` is created after recording finishes.
4. The laptop waits for the flag.
5. The command audio is copied using SCP.
6. Whisper converts speech into text.
7. The parser maps spoken phrases to robot commands.
8. The command is published to `/voice_command`.
9. Motion or vision nodes execute the command.
10. Piper generates spoken feedback.

---

# Authors

**Tobias Pieper**

M.Sc. Digital Farming

University of Applied Sciences Weihenstephan-Triesdorf (HSWT)
