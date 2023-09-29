from django.http import HttpResponse
from django.conf import settings
import os


ALLOWED_VIDEO_EXTENSIONS = ['.mp4', '.avi', '.mov']

def has_allowed_extension(file_name):
    return any(file_name.endswith(ext) for ext in ALLOWED_VIDEO_EXTENSIONS)

def play_video(request, video_id):
    # Construct the path to the video file based on the video_id
    video_file_path = os.path.join(settings.MEDIA_ROOT, 'videos', video_id)

    # Check if the video file exists
    if not os.path.isfile(video_file_path):
        return HttpResponse("Video not found", status=404)

    # Extract the file extension from the video_id
    _, file_extension = os.path.splitext(video_id)
    
    # Check if the file extension is allowed
    if not has_allowed_extension(file_extension.lower()):
        
        return HttpResponse("Unsupported video format", status=415)

    # Determine the content type based on the file extension
    content_type = None

    if file_extension.lower() == '.mp4':
        content_type = 'video/mp4'
    elif file_extension.lower() == '.avi':
        content_type = 'video/x-msvideo'
    elif file_extension.lower() == '.mov':
        content_type = 'video/quicktime'

    # Open the video file for reading
    with open(video_file_path, 'rb') as video_file:
        response = HttpResponse(video_file.read(), content_type=content_type)
        return response
