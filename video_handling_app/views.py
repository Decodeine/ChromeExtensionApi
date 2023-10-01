from django.http import JsonResponse
from django.conf import settings
from moviepy.editor import VideoFileClip
import requests
from celery import shared_task
import logging
import base64
import os

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

        # Create a temporary video file to save the video data
        temp_video_path = os.path.join(settings.MEDIA_ROOT, 'temp_video.mp4')

        with open(temp_video_path, 'wb') as temp_video_file:
            temp_video_file.write(video_data)

        # Extract audio from the video
        audio_path = os.path.join(settings.MEDIA_ROOT, 'audio', 'temp_audio.mp3')
        extract_audio(temp_video_path, audio_path)

        # Transcribe the extracted audio
        transcription = transcribe_audio(audio_path)

        return JsonResponse({"message": "Video blob uploaded successfully", "transcription": transcription})
    
    return JsonResponse({"error": "Only POST requests are allowed"}, status=400)


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

        # Your existing code for making the API request

        if response.status_code == 200:
            transcription = response.json()['text']
            return transcription
        else:
            logger.error(f"API request failed with status code {response.status_code}")
    except Exception as e:
        logger.error(f"Error in transcribe_audio task: {str(e)}")

    return None





