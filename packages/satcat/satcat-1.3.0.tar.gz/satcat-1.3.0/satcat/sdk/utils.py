import re
import time
from datetime import datetime, timezone
from enum import Enum
from pathlib import Path
from typing import IO, Callable, Dict, Union


class SortDirection(Enum):
    ASC = "asc"
    DESC = "desc"


PathLike = Union[str, Path]

# Limit for polling for a job to return CREATED. After this, polling will raise an error if the job is still in created because it is likely the job was never started
DEFAULT_CREATED_TIMEOUT = 30

class open_path_or_buf:
    path_or_buf: Union[Path, IO]
    buf: IO
    need_to_close_buf: bool = False

    def __init__(self, path_or_buf: Union[PathLike, IO], mode: str = "r") -> IO:
        self.path_or_buf = path_or_buf
        self.mode = mode

    def __enter__(self):
        """[summary]

        :param path_or_buf: An open file or buffer or path to a file to open.
            If a buffer is passed, it must have been opened with the correct
            mode.
        :type path_or_buf: Union[Path, IO]
        :param mode: The mode with which to open the file, defaults to "r"
        :type mode: str
        :return: [description]
        :rtype: IO
        """
        if isinstance(self.path_or_buf, Path) or isinstance(self.path_or_buf, str):
            self.buf = open(self.path_or_buf, self.mode)
            self.need_to_close_buf = True
        else:
            self.buf = self.path_or_buf
            self.need_to_close_buf = False

        return self.buf

    def __exit__(self, type, value, traceback):
        if self.need_to_close_buf:
            self.buf.close()


def remove_none_vals(d: Dict) -> Dict:
    return {k: v for k, v in d.items() if v is not None}


def poll_job_for_completion(
    get_job_fn: Callable, poll_interval: int = 5, timeout: int = 3600, created_timeout: int = DEFAULT_CREATED_TIMEOUT
):
    tst = time.time()

    elapsed = 0
    job = get_job_fn()
    while job.status in ["RUNNING", "PENDING", "CREATED"] and elapsed < timeout:
        if job.status == "CREATED" and elapsed > created_timeout:
            raise TimeoutError(f"Job is still in the CREATED state. Please confirm the job was started.")
        job = get_job_fn()
        time.sleep(poll_interval)
        elapsed = time.time() - tst

    if elapsed > timeout and job.status == "RUNNING":
        raise TimeoutError()

    return job


def poll_job_for_completion_percent_generator(
    get_job_fn: Callable, poll_interval: int = 5, timeout: int = 3600
):
    tst = time.time()

    elapsed = 0
    job = get_job_fn()
    while job.status in ["RUNNING", "PENDING", "CREATED"] and elapsed < timeout:
        job = get_job_fn()
        elapsed = time.time() - tst
        time.sleep(poll_interval)
        try:
            yield job.percent_complete
        except AttributeError:
            yield 0

    if elapsed > timeout and job.status == "RUNNING":
        raise TimeoutError()

    return job


def utc(timestamp: str) -> datetime:
    """Create a datetime object from an ISO8601 timestamp string.
    The timestamp string must include the "Z" suffix indicating that
    the timestamp is expressed in the UTC time system.

    It is recommended that you use this function to pass any `datetime`
    parameters to Satcat SDK functions to ensure that your `datetime`
    is created with the correct timezone information.

    :param timestamp: The timestamp string to convert
    :type timestamp: str
    :return: The created datetime object
    :rtype: datetime
    """
    if not timestamp.endswith("Z"):
        raise ValueError("UTC Timestamps must use the 'Z' UTC indicator.")
    return datetime.fromisoformat(timestamp[:-1]).replace(tzinfo=timezone.utc)


def kebab_case(text: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", text.lower()).strip("-")

class NotFoundError(Exception):
    ...