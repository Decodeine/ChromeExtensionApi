# video_playback_app/urls.py
from django.urls import path
from . import views

urlpatterns = [
    path('play/<str:video_id>/', views.play_video, name='play_video'),
]
