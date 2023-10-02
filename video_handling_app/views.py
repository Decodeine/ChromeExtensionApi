from django.http import JsonResponse
from django.conf import settings
from moviepy.editor import VideoFileClip, concatenate_videoclips
import requests
from celery import shared_task
import logging
import base64
import os
import subprocess
import tempfile
from django.http import HttpResponseNotFound
from django.core.files.base import ContentFile
from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework import status

logger = logging.getLogger(__name__)

# Define the allowed video file extensions
ALLOWED_VIDEO_EXTENSIONS = ['.mp4', '.avi', '.mov', '.webm']  # Add more if needed

def has_allowed_extension(file_name):
    return any(file_name.endswith(ext) for ext in ALLOWED_VIDEO_EXTENSIONS)

def extract_audio(video_path, audio_path):
    video_clip = VideoFileClip(video_path)
    audio_clip = video_clip.audio
    audio_clip.write_audiofile(audio_path)

def convert_webm_to_mp4(input_file, output_file):
    try:
        subprocess.run(['ffmpeg', '-i', input_file, '-c:v', 'libx264', '-c:a', 'aac', '-strict', 'experimental', output_file], check=True)
        return True
    except subprocess.CalledProcessError as e:
        print(f"Error converting WebM to MP4: {e}")
        return False

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
        return "Transcription failed" 
     
#function to receive complete video blob in post request body
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


#function to receive the video blob in chunks concatenate and process
@api_view(['POST'])
def append_video(request):
    if request.method == 'POST':
        existing_video_blob = request.FILES.get('existing_video')  # Assuming the existing video blob is sent as 'existing_video'
        new_video_blob = request.FILES.get('new_video')  # Assuming the new video blob is sent as 'new_video'

        if not existing_video_blob or not new_video_blob:
            return JsonResponse({"error": "Both existing and new video blobs are required."}, status=400)

        # Decode the base64 blob data
        existing_video_data = existing_video_blob.read()
        new_video_data = new_video_blob.read()

        # Create temporary files to store video data
        with tempfile.NamedTemporaryFile(delete=False) as existing_tempfile:
            existing_tempfile.write(existing_video_data)
            existing_tempfile_path = existing_tempfile.name

        with tempfile.NamedTemporaryFile(delete=False) as new_tempfile:
            new_tempfile.write(new_video_data)
            new_tempfile_path = new_tempfile.name

        # Load video clips using moviepy
        existing_clip = VideoFileClip(existing_tempfile_path)
        new_clip = VideoFileClip(new_tempfile_path)

        # Concatenate video clips
        final_clip = concatenate_videoclips([existing_clip, new_clip])

        # Save the concatenated video into your file storage
        final_video_path = os.path.join(settings.MEDIA_ROOT, 'videos', 'final_video.mp4')
        final_clip.write_videofile(final_video_path, codec='libx264')

        # Clean up temporary files
        os.remove(existing_tempfile_path)
        os.remove(new_tempfile_path)

        return JsonResponse({"message": "Video appended successfully"}, status=status.HTTP_200_OK)
    
    return JsonResponse({"error": "Only POST requests are allowed"}, status=400)
