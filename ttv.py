import os
import math
import requests
import time
from moviepy.editor import VideoFileClip,AudioFileClip, concatenate_videoclips
from azure.identity import DefaultAzureCredential
from pydub import AudioSegment

# Constants - Replace with your values
AZURE_SORA_ENDPOINT = "<YOUR_AZURE_SORA_ENDPOINT>"
AZURE_SORA_DEPLOYMENT = "<YOUR_AZURE_SORA_DEPLOYMENT>"
AZURE_SPEECH_KEY = "<YOUR_AZURE_SORA_SPEECH KEY>"
AZURE_SPEECH_REGION = "<YOUR_AZURE_SPEECH_REGION>"
os.environ["AZURE_OPENAI_KEY"] = "<YOUR_AZURE_OPENAI_KEY>"

def split_script(script, max_duration=20, wpm=150):
    words = script.split()
    max_words = int(wpm * (max_duration / 60.0))
    return [' '.join(words[i:i+max_words]) for i in range(0, len(words), max_words)]

def generate_tts_audio(script_text, index):
    output_file = f"audio_{index}.mp3"
    tts_url = f"https://{AZURE_SPEECH_REGION}.tts.speech.microsoft.com/cognitiveservices/v1"
    headers = {
        'Ocp-Apim-Subscription-Key': AZURE_SPEECH_KEY,
        'Content-Type': 'application/ssml+xml',
        'X-Microsoft-OutputFormat': 'audio-16khz-32kbitrate-mono-mp3'
    }
    ssml = f"""
    <speak version='1.0' xml:lang='en-US'>
        <voice xml:lang='en-US' xml:gender='Female' name='en-US-JennyNeural'>
            {script_text}
        </voice>
    </speak>
    """
    response = requests.post(tts_url, headers=headers, data=ssml.encode('utf-8'))
    with open(output_file, 'wb') as f:
        f.write(response.content)
    return output_file

def submit_sora_job(prompt, duration=10, width=1080, height=1080):
    url = f"{AZURE_SORA_ENDPOINT}/jobs?api-version=preview"
    headers = {
        "Content-Type": "application/json",
        "api-key": os.getenv("AZURE_OPENAI_KEY")
    }
    payload = {
        "model": "sora",
        "prompt": prompt,
        "n_seconds": duration,
        "n_variants": 1,
        "width": width,
        "height": height
    }
    response = requests.post(url, headers=headers, json=payload)
    response.raise_for_status()
    return response.json()["id"]



def poll_until_done(job_id):
    status_url = f"{AZURE_SORA_ENDPOINT}/jobs/{job_id}?api-version=preview"
    headers = {"Api-key": os.getenv("AZURE_OPENAI_KEY")}
    print(f"Polling job {job_id}...")
    while True:
        response = requests.get(status_url, headers=headers)
        response.raise_for_status()
        data = response.json()
        if data["status"] == "succeeded":
            generation_id = data["generations"][0]["id"]
            return generation_id
        elif data["status"] in ["failed", "cancelled"]:
            raise RuntimeError(f"Video job failed with status: {data['status']}")
        time.sleep(5)

def download_file(generation_id,raw_video_path):
    video_url = f"{AZURE_SORA_ENDPOINT}/{generation_id}/content/video?api-version=preview"
    print("Downloading Video...")
    headers = {"Api-key": os.getenv("AZURE_OPENAI_KEY")}
    video_response = requests.get(video_url, headers=headers)

    if video_response.ok:
        output_filename = raw_video_path
        with open(output_filename, "wb") as file:
            file.write(video_response.content)
        print(f"🎥 Video saved as '{output_filename}'")
    else:
        print(f"❌ Failed to download video: {video_response.status_code}")
        print(video_response.text)

def combine_video_audio(video_path, audio_path, output_path):

    video_clip = VideoFileClip(video_path)
    audio_clip = AudioFileClip(audio_path)

    if audio_clip.duration < video_clip.duration:
        print(f"📏 Padding audio: {audio_clip.duration:.2f}s → {video_clip.duration:.2f}s")
        original_audio = AudioSegment.from_file(audio_path)
        silence = AudioSegment.silent(duration=(video_clip.duration - audio_clip.duration) * 1000)
        padded_audio = original_audio + silence
        padded_audio_file = "padded_" + os.path.basename(audio_path)
        padded_audio.export(padded_audio_file, format="mp3")

        if not os.path.exists(padded_audio_file):
            raise FileNotFoundError(f"❌ Failed to create padded audio: {padded_audio_file}")

        audio_clip = AudioFileClip(padded_audio_file)

    final_clip = video_clip.set_audio(audio_clip)
    print(f"💾 Saving to: {os.path.abspath(output_path)}")

    final_clip.write_videofile(output_path, codec="libx264", audio_codec="aac", temp_audiofile='temp-audio.m4a',remove_temp=True)

    if not os.path.exists(output_path):
        raise FileNotFoundError(f"❌ Final output video not created: {output_path}")

    print(f"🎬 Final video with audio saved as {output_path}")

def merge_videos(video_files, output_file="final_output.mp4"):
    clips = [VideoFileClip(f) for f in video_files]
    final_clip = concatenate_videoclips(clips)
    final_clip.write_videofile(output_file, codec="libx264", audio=False)

def main(script_input):
    segments = [script_input]  # Split script if longer
    final_segments = []

    for i, part in enumerate(segments):
        print(f"\n🎬 Processing segment {i+1}")
        audio_file = generate_tts_audio(part, i)
        job_id = submit_sora_job(prompt=part, duration=5)
        generation_id = poll_until_done(job_id)
        raw_video_path = f"raw_segment_{i+1}.mp4"
        final_segment_path = f"segment_{i+1}.mp4"

        download_file(generation_id, raw_video_path)
        combine_video_audio(raw_video_path, audio_file, final_segment_path)

        final_segments.append(final_segment_path)
    if len(final_segments) > 1:
        print("\n🎞️ Merging all segments...")
        merge_videos(final_segments)
    else:
        os.rename(final_segments[0], "final_output.mp4")

    print("✅ Final video: final_output.mp4")

# Example
if __name__ == "__main__":
    input_script = """Hello, Welcome to healthcare management"""
    main(input_script)
