import heapq
import os
from datetime import datetime
from io import StringIO
from pathlib import Path
from typing import TYPE_CHECKING, Any, Dict, List, Optional, TextIO, Union
from urllib.parse import urljoin

from satcat.sdk.settings import settings
from satcat.sdk.utils import PathLike, open_path_or_buf

if TYPE_CHECKING:
    from satcat.sdk.client import Client


class ODClient:
    client: "Client"

    def __init__(self, client: "Client"):
        self.client = client

    def list_assets(self) -> List[int]:
        """
        List assets for which the user has orbital determination data available.

        :return The list of object IDs.
        :rtype: Collection[int]
        """

        path = urljoin(settings.satcat_rest_api_url, "od/objects")
        items = self.client.request_authenticated(path)
        return items.json()["objects"]

    def list_object_files(
        self, object_id: int, today: bool = False, results: bool = False
    ) -> Dict[str, Any]:
        """
        List orbital determination files for a specific object.

        :param object_id: The NORAD ID or temporary ID of the object.
        :type object_id: int
        :param today: If True, only list files uploaded today.
        :type today: bool
        :param results: If True, only list result files.
        :type results: bool
        :return: The list of files for the specified object.
        :rtype: Collection[Dict[str, Any]]
        """

        path = urljoin(settings.satcat_rest_api_url, f"od/{object_id}")
        params = {"today": str(today).lower(), "results": str(results).lower()}
        items = self.client.request_authenticated(path, params=params)
        return items.json()["files"]

    def upload_file(
        self,
        object_id: int,
        path_or_buf: Union[PathLike, TextIO, StringIO],
        filename: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Upload an orbital determination (OD) file for a specific object.

        The file content can be provided either as a filesystem path or as an
        already-open file-like object. A filename must either be provided
        explicitly or derivable from ``path_or_buf``; otherwise this method
        will raise a ``ValueError``.

        :param object_id: The NORAD ID or temporary ID of the object that this
            OD file describes.
        :type object_id: int
        :param path_or_buf: Path to a file on disk, or an open text file-like
            object (e.g. ``io.StringIO``) containing the OD data to upload.
        :type path_or_buf: Union[PathLike, TextIO, StringIO]
        :param filename: Optional explicit filename to send to the API. If not provided,
            the filename will be derived from ``path_or_buf`` when possible (e.g. using
            ``os.path.basename``). The filename must follow one of these patterns::

              gnss_<object_id>_YYYY_MM_DD_HH_MM_SSZ.(json|csv|navsol)
              gnss_<object_id>_YYYY-MM-DDTHH:MM:SSZ.(json|csv|navsol)
              maneuver_<object_id>_YYYY_MM_DD_HH_MM_SSZ.(opm|txt)
              maneuver_<object_id>_YYYY-MM-DDTHH:MM:SSZ.(opm|txt)

            If no filename can be determined, a ``ValueError`` is raised.
        :type filename: Optional[str]
        :return: The JSON response from the OD upload endpoint.
        :rtype: Dict[str, Any]
        """

        with open_path_or_buf(path_or_buf, mode="rb") as file:
            resolved_filename = filename

            if resolved_filename is None:
                # Try to derive the filename from the original input
                if isinstance(path_or_buf, Path):
                    resolved_filename = os.path.basename(path_or_buf.name)
                elif isinstance(path_or_buf, str):
                    resolved_filename = os.path.basename(path_or_buf)
                else:
                    # Fall back to any name attribute on the underlying file object
                    file_name_attr = getattr(file, "name", None)
                    if isinstance(file_name_attr, str):
                        resolved_filename = os.path.basename(file_name_attr)

            if not resolved_filename:
                raise ValueError(
                    "A filename must be provided explicitly or derivable from path_or_buf."
                )

            path = urljoin(settings.satcat_rest_api_url, f"od/{object_id}/upload")
            files = {"file": (resolved_filename, file)}
            response = self.client.request_authenticated(
                path, method="POST", files=files
            )
        return response.json()

    def download_file(
        self, object_id: int, filename: str, output_path: Optional[PathLike]
    ) -> bytes:
        """
        Download an orbital determination (OD) file for a specific object.

        :param object_id: The NORAD ID or temporary ID of the object that this
            OD file describes.
        :type object_id: int
        :param filename: The name of the file to download.
        :type filename: str
        :param output_path: Optional path to save the downloaded file. If None, the file content is returned as bytes.
        :type output_path: Optional[PathLike]

        :return: The content of the downloaded file as bytes.
        :rtype: bytes
        """

        path = urljoin(settings.satcat_rest_api_url, f"od/{object_id}/file")
        response = self.client.request_authenticated(
            path, method="GET", json={"file_name": filename}
        )
        if output_path:
            expanded_path = os.path.abspath(os.path.expanduser(str(output_path)))
            os.makedirs(os.path.dirname(expanded_path), exist_ok=True)
            with open(expanded_path, "wb") as outf:
                outf.write(response.content)
        return response.content

    def download_recent_files(
        self,
        object_id: int,
        number: int = 1,
        report: bool = False,
        output_dir: Optional[PathLike] = None,
    ):
        """
        Download the most recent orbital determination (OD) files for a specific object.

        :param object_id: The NORAD ID or temporary ID of the object that this
            OD file describes.
        :type object_id: int
        :param number: The number of recent files to download.
        :type number: int
        :param report: If True, downloads the most recent pdf report file as well
        :type report: bool
        :param output_dir: Optional directory to save the downloaded files. If None, files are saved to the current working directory.
        :type output_dir: Optional[PathLike]
        :return: A tuple containing the count of definitive files, predictive files, and a boolean indicating if a PDF report was downloaded.
        :rtype: Tuple[int, int, bool]
        """

        files = self.list_object_files(object_id, results=True)

        file_heap = []

        definitive_count = 0
        predictive_count = 0
        pdf_downloaded = False

        for file_info in files:
            filename = file_info["filename"]
            if (
                "DEFINITIVE" in filename
                or "PREDICTIVE" in filename
                or filename.endswith(".pdf")
            ):
                heapq.heappush(
                    file_heap,
                    (
                        -datetime.fromisoformat(file_info["last_modified"]).timestamp(),
                        filename,
                    ),
                )

        # Create or set output directory
        if output_dir:
            expanded_dir = os.path.abspath(os.path.expanduser(str(output_dir)))
            os.makedirs(expanded_dir, exist_ok=True)
            path_base = expanded_dir
        else:
            path_base = os.getcwd()

        while file_heap:
            _, file_key = heapq.heappop(file_heap)
            file_name = os.path.basename(file_key)
            output_path = os.path.join(path_base, file_name)

            if (
                definitive_count == number
                and predictive_count == number
                and (pdf_downloaded or not report)
            ):
                break

            if file_name.endswith(".txt"):
                if "DEFINITIVE" in file_name and definitive_count < number:
                    self.download_file(object_id, file_key, output_path=output_path)
                    definitive_count += 1
                elif "PREDICTIVE" in file_name and predictive_count < number:
                    self.download_file(object_id, file_key, output_path=output_path)
                    predictive_count += 1
            elif report and file_name.endswith(".pdf") and not pdf_downloaded:
                self.download_file(object_id, file_key, output_path=output_path)
                pdf_downloaded = True

        return definitive_count, predictive_count, pdf_downloaded
