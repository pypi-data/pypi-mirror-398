"""
Functions for working with HEA's OpenAPI spec file, found on gitlab.com in the
https://gitlab.com/huntsman-cancer-institute/risr/hea/hea-openapi-specs project.
"""
import os
from contextlib import contextmanager
from tempfile import NamedTemporaryFile
from typing import Optional, Generator
from urllib.request import urlopen



@contextmanager
def download_openapi_spec(branch_or_tag: Optional[str] = 'master') -> Generator[str, None, None]:
    """
    A context manager for use in with statements. It downloads HEA's OpenAPI spec file into a temporary file, yielding
    the path of the file. It automatically deletes the file upon exiting the with statement.

    :param branch_or_tag: the branch or tag to get. Defaults to the master branch.
    :raises OSError: if an error occurred downloading and writing the spec to a temporary file.
    """
    with NamedTemporaryFile(delete=False) as tmpfile:
        with urlopen(open_api_spec_url(branch_or_tag)) as url:
            tmpfile.write(url.read())
        filename = tmpfile.name
    yield filename
    os.remove(filename)


def open_api_spec_url(branch_or_tag: Optional[str] = 'master') -> str:
    """
    Gets the URL for HEA's OpenAPI spec document.

    :param branch_or_tag: the branch or tag to get. Defaults to the master branch.
    :return: a URL string.
    """
    if branch_or_tag is None:
        branch_or_tag = 'master'
    return f'https://gitlab.com/huntsman-cancer-institute/risr/hea/hea-openapi-specs/-/raw/{branch_or_tag}/openapi.yaml'
