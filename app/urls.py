from django.urls import path
from .views import transcribe_and_synthesize

urlpatterns = [
    path('synthesize-speech/', transcribe_and_synthesize, name='transcribe_and_synthesize'),
]