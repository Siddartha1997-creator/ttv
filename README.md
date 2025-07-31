# ttv

# 🎬 Script to Video Generator using Sora & TTS  
Developed by **Siddartha Suthraye**

This tool automates the process of generating lip-synced videos from textual scripts using TTS (Text-to-Speech) and OpenAI's Sora API. It takes scene-wise scripts as input and produces a polished final video by combining generated visuals and audio.

---

## 🧠 Features

- Accepts scene-wise scripts with corresponding dialogue.
- Uses TTS to generate realistic audio.
- Submits each scene to Sora to create a video with accurate lip-syncing.
- Waits for video generation to complete.
- Merges the generated video with the audio.
- Concatenates all scene-wise clips into a single final video.

---

## 📁 Project Structure

project/
│
├── scripts/
│ └── scenes.json # Input file: [{"scene": "...", "voice": "..."}, ...]
│
├── output/
│ ├── scene_1.mp4 # Individual scene videos
│ ├── scene_1_audio.mp3 # TTS audio
│ ├── final_output.mp4 # Merged final video
│
├── main.py # Main script runner
├── utils.py # Helper functions for TTS, Sora, merge
├── requirements.txt # Python dependencies
└── README.md # You are here


---

## 📝 Input Format (`scripts/script.txt`)

```json
[
  {
    "scene": "Doctor talking to a patient about healthcare eligibility",
    "voice": "Let's explore how 270/271 transactions simplify eligibility checks."
  },
  {
    "scene": "Patient using a mobile app to check insurance",
    "voice": "With just a few clicks, patients can verify their benefits."
  }
]
