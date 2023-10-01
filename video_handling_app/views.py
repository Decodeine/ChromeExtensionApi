from django.http import JsonResponse
from django.conf import settings
from django.core.files.storage import FileSystemStorage
from moviepy.editor import VideoFileClip
import requests
from celery import shared_task


# Define the allowed video file extensions
ALLOWED_VIDEO_EXTENSIONS = ['.mp4', '.avi', '.mov']  # Add more if needed

def has_allowed_extension(file_name):
    return any(file_name.endswith(ext) for ext in ALLOWED_VIDEO_EXTENSIONS)

def upload_video(request):
    if request.method == 'POST':
        uploaded_file = request.FILES.get('video_file')
        
        if not uploaded_file:
            return JsonResponse({"error": "No video file uploaded."}, status=400)

        if not has_allowed_extension(uploaded_file.name.lower()):
            return JsonResponse({"error": "Invalid video file format."}, status=400)

        # Save the uploaded video file using Django's FileSystemStorage
        fs = FileSystemStorage(location=settings.MEDIA_ROOT + '/videos')  # Specify the storage location
        saved_file = fs.save(uploaded_file.name, uploaded_file)

        # Construct the URL to access the saved video
        video_url = fs.url(saved_file)

        # Extract audio from the video
        audio_path = settings.MEDIA_ROOT + '/audio/' + uploaded_file.name.replace('.','_') + '.mp3'
        extract_audio(saved_file, audio_path)

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
    # Read the audio file
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

    # Get the transcription result
    if response.status_code == 200:
        transcription = response.json()['text']
        return transcription
    else:
        return None  # Handle API request error




