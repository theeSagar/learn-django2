import mimetypes
from pathlib import Path
from urllib.parse import unquote

from django.conf import settings
from django.http import FileResponse, Http404


def download_media_file(request, file_path):
    # Decode URL-encoded paths (e.g., spaces)
    file_path = unquote(file_path)
    
    full_path = Path(settings.MEDIA_ROOT) / file_path
    try:
        full_path.resolve().relative_to(Path(settings.MEDIA_ROOT).resolve())
    except ValueError:
        raise Http404("Invalid file path")

    if full_path.exists() and full_path.is_file():
        mime_type, _ = mimetypes.guess_type(str(full_path))
        return FileResponse(open(full_path, 'rb'), content_type=mime_type or 'application/octet-stream')
    else:
        raise Http404("File not found.")