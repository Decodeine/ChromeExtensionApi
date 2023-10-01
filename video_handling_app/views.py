from django.http import JsonResponse
from django.conf import settings
from django.core.files.storage import FileSystemStorage
from moviepy.editor import VideoFileClip
import requests
from celery import shared_task
import logging
import base64
import os

logger = logging.getLogger(__name__)

# Define the allowed video file extensions
ALLOWED_VIDEO_EXTENSIONS = ['.mp4', '.avi', '.mov']  # Add more if needed

def has_allowed_extension(file_name):
    return any(file_name.endswith(ext) for ext in ALLOWED_VIDEO_EXTENSIONS)

def upload_video(request):
    if request.method == 'POST':
        uploaded_file = request.FILES.get('video_file')
        video_blob = request.POST.get('video_blob')  # Assuming the blob is sent as 'video_blob'

        if not uploaded_file and not video_blob:
            return JsonResponse({"error": "No video file or blob uploaded."}, status=400)

        if uploaded_file:
            if not has_allowed_extension(uploaded_file.name.lower()):
                return JsonResponse({"error": "Invalid video file format."}, status=400)

            # Save the uploaded video file using Django's FileSystemStorage
            fs = FileSystemStorage(location=settings.MEDIA_ROOT + '/videos')  # Specify the storage location
            saved_file = fs.save(uploaded_file.name, uploaded_file)

            # Construct the URL to access the saved video
            video_url = fs.url(saved_file)

        if video_blob:
            # Decode the base64 blob data
            video_data = base64.b64decode(video_blob)

            # Create a temporary MP4 file to save the video data
            temp_video_path = os.path.join(settings.MEDIA_ROOT, 'temp_video.mp4')

            with open(temp_video_path, 'wb') as temp_video_file:
                temp_video_file.write(video_data)

            # Construct the URL to access the saved video
            video_url = temp_video_path  # You can modify this based on your storage

        # Extract audio from the video
        audio_path = settings.MEDIA_ROOT + '/audio/' + uploaded_file.name.replace('.', '_') + '.mp3'
        extract_audio(saved_file if uploaded_file else temp_video_path, audio_path)

        # Transcribe the extracted audio
        transcription = transcribe_audio(audio_path)

        return JsonResponse({"message": "Video uploaded successfully", "video_url": video_url, "transcription": transcription})
    
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
                'Authorization': 'Bearer 11MPTEENHW7V3T43FGMVIP3NYS35VDQM',  # Replace with your actual API key
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





