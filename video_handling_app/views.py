from django.http import JsonResponse
from django.conf import settings
from moviepy.editor import VideoFileClip
import requests
from celery import shared_task
import logging
import base64
import os
import tempfile

logger = logging.getLogger(__name__)

# Define the allowed video file extensions
ALLOWED_VIDEO_EXTENSIONS = ['.mp4', '.avi', '.mov', '.webm']  # Add more if needed

def has_allowed_extension(file_name):
    return any(file_name.endswith(ext) for ext in ALLOWED_VIDEO_EXTENSIONS)

def upload_video(request):
    if request.method == 'POST':
        video_blob = request.FILES.get('recording')  # Assuming the blob is sent as 'recording'

        if not video_blob:
            return JsonResponse({"error": "No video blob uploaded."}, status=400)

        # Decode the base64 blob data
        video_data = video_blob.read()

        # Create a temporary directory
        temp_dir = tempfile.mkdtemp()

        # Define the temporary video file path
        temp_video_path = os.path.join(temp_dir, 'temp_video.mp4')
        print(f"temp_video_path: {temp_video_path}")

        try:
            with open(temp_video_path, 'wb') as temp_video_file:
                temp_video_file.write(video_data)
            print("Temporary video file created successfully.")

            # Extract audio from the video
            audio_path = os.path.join(settings.MEDIA_ROOT, 'audio', 'temp_audio.mp3')
            extract_audio(temp_video_path, audio_path)

            # Transcribe the extracted audio
            transcription = transcribe_audio(audio_path)

            return JsonResponse({"message": "Video blob uploaded successfully", "transcription": transcription})
        except Exception as e:
            print(f"Error creating temporary video file: {str(e)}")
            return JsonResponse({"error": "Failed to process the video blob."}, status=500)
    
    return JsonResponse({"error": "Only POST requests are allowed"}, status=400)

# Rest of your code remains the same

def extract_audio(video_path, audio_path):
    video_clip = VideoFileClip(video_path)
    audio_clip = video_clip.audio
    audio_clip.write_audiofile(audio_path)



@shared_task
def transcribe_audio(audio_path):
    try:
        with open(audio_path, 'rb') as audio_file:
            audio_data = audio_file.read()

        # Make a POST request to the Whisper API
        response = requests.post(
            'https://api.openai.com/v1/whisper/recognize',
            headers={
                'Authorization': 'Bearer FQEXULQHB7WCH2GUYHAYSLX1NGC8MBVQ',  # Replace with your actual API key
            },
            files={
                'audio': ('audio.mp3', audio_data),
            },
        )

        if response.status_code == 200:
            transcription = response.json()['text']
        else:
            transcription = "Transcription failed"  # Handle the error case here

        return transcription

    except Exception as e:
        # Handle any exceptions that may occur during the process
        logger.error(f"Error in transcribe_audio task: {str(e)}")
        return "Transcription failed"  # Handle the error case here




