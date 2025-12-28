from enum import Enum


class MimeType(Enum):
    """Enum for Google Drive MIME types."""

    APPLICATION_JSON = "application/json"
    APPLICATION_PDF = "application/pdf"
    APPLICATION_MSWORD = "application/msword"
    APPLICATION_VND_OPENXMLFORMATS_OFFICEDOCUMENT_WORDPROCESSINGML_DOCUMENT = (
        "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
    )
    APPLICATION_VND_GOOGLE_APPS_DOCUMENT = "application/vnd.google-apps.document"
    APPLICATION_VND_GOOGLE_APPS_SPREADSHEET = "application/vnd.google-apps.spreadsheet"
    APPLICATION_VND_GOOGLE_APPS_PRESENTATION = (
        "application/vnd.google-apps.presentation"
    )
    APPLICATION_VND_GOOGLE_APPS_DRAWING = "application/vnd.google-apps.drawing"
    TEXT_PLAIN = "text/plain"
    IMAGE_JPEG = "image/jpeg"
    IMAGE_PNG = "image/png"
    VIDEO_MP4 = "video/mp4"
    AUDIO_MPEG = "audio/mpeg"
    AUDIO_WAV = "audio/wav"
    AUDIO_OGG = "audio/ogg"
    AUDIO_MP3 = "audio/mp3"
    APPLICATION_ZIP = "application/zip"
    APPLICATION_OCTET_STREAM = "application/octet-stream"
