import streamlit as st
import os
import tempfile
from moviepy.editor import VideoFileClip, AudioFileClip
from gtts import gTTS
import speech_recognition as sr

import requests
import json

# Streamlit app title
st.title("Video Upload, Transcription, and Audio Replacement")

# Step 1: Video upload
video_file = st.file_uploader("Upload a video", type=["mp4", "mov", "avi", "mkv"])

# Add a checkbox to trigger processing
if video_file and st.checkbox("Process the uploaded video"):

    # Step 2: Display the uploaded video
    st.video(video_file)

    # Step 3: Save the uploaded video to a temporary file
    with tempfile.NamedTemporaryFile(delete=False, suffix=".mp4") as temp_video_file:
        temp_video_file.write(video_file.read())
        temp_video_path = temp_video_file.name

    # Step 4: Convert video to audio using MoviePy
    st.write("Extracting audio from the video...")

    try:
        with VideoFileClip(temp_video_path) as video_clip:
            audio_path = temp_video_path.replace(".mp4", ".wav")
            video_clip.audio.write_audiofile(audio_path)
            st.write("Audio extracted successfully!")
    except Exception as e:
        st.error(f"Error in audio extraction: {e}")
        audio_path = None

    # Step 5: Transcribe the audio file
    if audio_path:
        st.write("Transcribing audio...")
        try:
            # Initialize the recognizer
            recognizer = sr.Recognizer()

            # Load and record the audio file
            with sr.AudioFile(audio_path) as source:
                audio = recognizer.record(source)

            # Perform transcription using Google Web Speech API
            transcript_text = recognizer.recognize_google(audio)
            api_key = 'AIzaSyAflUliiU8ORPPBDwGy9WHISeGF5M9qKyE'
            url = f'https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash-latest:generateContent?key={api_key}'

# The payload (data) for the request
            payload = {
    "contents": [
        {
            "parts": [
                {"text": f"""Correct grammatical mistakes, remove filler words like 'umms' and 'hmms' from this and only give the corrected text back: {transcript_text}"""}
            ]
        }
    ]
}

# Headers
            headers = {
    'Content-Type': 'application/json'
}

# Make the POST request
            response = requests.post(url, json=payload, headers=headers)

# Check if the request was successful
            if response.status_code == 200:
    # Process the response (assuming it's JSON)
                result = response.json()
                print(result)
            else:
                print(f"Error: {response.status_code}, {response.text}")
            # Correct grammatical mistakes using generative AI
           
            transcript_text = response.text
            st.write("Transcription complete!")
            st.text_area("Transcript", value=transcript_text, height=300)

            # Step 6: Convert transcript to speech using gTTS
            st.write("Converting transcript to speech...")

            try:
                # Convert transcript to audio
                tts = gTTS(text=transcript_text, lang='en', slow=False)
                new_audio_path = audio_path.replace(".wav", "_new.mp3")
                tts.save(new_audio_path)
                st.write("Speech synthesis complete!")

                # Step 7: Replace the original audio with the new audio
                st.write("Replacing the original audio with the new one...")

                try:
                    # Load the new audio and replace it in the video
                    with AudioFileClip(new_audio_path) as new_audio_clip:
                        with VideoFileClip(temp_video_path) as video_clip:
                            final_video = video_clip.set_audio(new_audio_clip)
                            new_video_path = temp_video_path.replace(".mp4", "_with_new_audio.mp4")
                            final_video.write_videofile(new_video_path)

                    st.success("Video with new audio created successfully!")

                    # Step 8: Provide the option to download the video with new audio
                    with open(new_video_path, "rb") as file:
                        st.download_button(
                            label="Download Video with New Audio",
                            data=file,
                            file_name="video_with_new_audio.mp4",
                            mime="video/mp4"
                        )

                except Exception as e:
                    st.error(f"Error in replacing audio: {e}")

            except Exception as e:
                st.error(f"Error in converting transcript to speech: {e}")

        except Exception as e:
            st.error(f"Error during transcription: {e}")

    # Clean up: Delete the temporary video and audio files after ensuring resources are closed
    try:
        if video_clip:
            video_clip.close()  # Ensure the video clip is closed
        if os.path.exists(temp_video_path):
            os.remove(temp_video_path)
        if os.path.exists(audio_path):
            os.remove(audio_path)
    except Exception as cleanup_error:
        st.error(f"Error during cleanup: {cleanup_error}")

else:
    st.warning("Please upload a video file and select the checkbox to process.")
