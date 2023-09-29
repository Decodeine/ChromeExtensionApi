from django.http import JsonResponse
from django.conf import settings
from django.core.files.storage import FileSystemStorage


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

        return JsonResponse({"message": "Video uploaded successfully", "video_url": video_url})
    
    return JsonResponse({"error": "Only POST requests are allowed"}, status=400)
