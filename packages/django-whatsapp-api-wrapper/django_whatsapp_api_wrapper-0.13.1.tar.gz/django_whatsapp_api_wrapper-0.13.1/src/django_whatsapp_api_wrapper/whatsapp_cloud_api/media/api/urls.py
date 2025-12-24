from django.urls import path

from .views import (
    MediaUploadView,
    MediaGetUrlView,
    MediaDeleteView,
    MediaDownloadView,
)


urlpatterns = [
    path("upload/", MediaUploadView.as_view(), name="wa_media_upload"),
    path("<str:media_id>/", MediaGetUrlView.as_view(), name="wa_media_get_url"),
    path("<str:media_id>/delete/", MediaDeleteView.as_view(), name="wa_media_delete"),
    path("download/", MediaDownloadView.as_view(), name="wa_media_download"),
]


