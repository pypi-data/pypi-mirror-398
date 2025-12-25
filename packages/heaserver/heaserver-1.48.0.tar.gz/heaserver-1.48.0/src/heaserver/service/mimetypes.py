"""
Utility functions for handling the mime types of heaobject.data.Data objects.
"""
import mimetypes

from heaobject.data import DataFile


def guess_mime_type(url: str) -> str:
    """
    Returns the mime type for the given URL, file name, or path, based on the file extension.

    :param url: the file path or URL (required).
    :returns: the mime type.
    """
    result = mimetypes.guess_type(url, False)[0]
    if result is not None:
        return result
    else:
        return DataFile.DEFAULT_MIME_TYPE
