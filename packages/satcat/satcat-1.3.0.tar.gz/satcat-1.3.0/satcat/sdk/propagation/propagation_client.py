import json
import time
from pathlib import Path
from typing import (
    TYPE_CHECKING,
    BinaryIO,
    Collection,
    Dict,
    List,
    Optional,
    TextIO,
    Union,
)
from urllib.parse import urljoin

from satcat.sdk.propagation import models
from satcat.sdk.settings import settings
from satcat.sdk.utils import (
    PathLike,
    SortDirection,
    open_path_or_buf,
    poll_job_for_completion,
    remove_none_vals,
)

if TYPE_CHECKING:
    from satcat.sdk.client import Client

DEFAULT_SORT_DIRECTION = SortDirection.DESC
DEFAULT_SORT_FIELD = "created_at"
BEST_CATALOG_TYPE = "SP"


class PropagationClient:
    client: "Client"

    def __init__(self, client: "Client"):
        self.client = client

    def create_propagation(
        self,
        config: Optional[models.PropagationConfiguration] = None,
        opm_file: Optional[Union[PathLike, BinaryIO]] = None,
        submit: bool = False,
    ) -> models.Propagation:
        """Create a propagation on the server.

        :param config: The configuration with which to run the propagation.
        :type config: Optional[models.PropagationConfiguration], optional
        :param opm_file: The content of a CCSDS OPM (Orbit Parameter Message)
            file to use in configuring the propagation.
        :type opm_file: Optional[TextIO], optional
        :param submit: Whether to submit the propagation instantly. If ``False``,
            the propagation may be submitted later using
            ``client.propagation.submit_propagation(propagation)``.
        :type submit: bool, optional
        :return: _description_
        :rtype: models.Propagation
        """
        if config is None:
            config = models.PropagationConfiguration()
        data = json.loads(config.json()) 
        data = remove_none_vals(data)
        path = urljoin(settings.satcat_rest_api_url, "propagations")
        params = {"submit": submit}
        res = self.client.request_authenticated(
            path, json=data, method="POST", params=params
        )
        propagation = models.Propagation.parse_obj(res.json())

        if opm_file is not None:
            propagation = self.add_opm_to_propagation(propagation, opm_file)

        if submit:
            propagation = self.submit_propagation(propagation)

        return propagation

    def get_propagation(self, id: str) -> models.Propagation:
        """Get a propagation by ID from the server.

        :param id: The ID of the resource to retrieve.
        :type id: str
        :return: The retrieved propagation.
        :rtype: models.Propagation
        """
        path = urljoin(settings.satcat_rest_api_url, f"propagations/{id}")
        res = self.client.request_authenticated(path)
        data = res.json()
        data["client"] = self.client
        return models.Propagation.parse_obj(data)

    def add_opm_to_propagation(
        self, propagation: models.Propagation, opm_file: Union[PathLike, BinaryIO]
    ) -> models.Propagation:
        """Configure a propagation using a CCSDS OPM (Orbit Parameter Message).

            Configures the initial state and maneuvers of the propagation using the data
            provided in the OPM.

            If the propagation is configured to use a ``target_duration_s`` instead of
            an explicit ``end_time`` , the propagation's ``start_time`` will be updated
            to match the epoch of the state vector in the OPM.

        :param propagation: The ``Propagation`` to update.
        :type propagation: models.Propagation
        :param opm_file: _description_
        :type opm_file: TextIO
        """
        propagation_id = propagation.id
        with open_path_or_buf(opm_file) as opm_buf:
            filename = None
            if isinstance(opm_file, Path):
                filename = opm_file.name
            if isinstance(opm_file, str):
                filename = opm_file
            if filename is None:
                filename = "USER_UPLOADED_OPM.txt"
                try:
                    filename = opm_buf.name
                except AttributeError:
                    pass  # use default name if buffer object has no name attr
            req_data = {"opm_file": (filename, opm_buf)}
            path = path = urljoin(
                settings.satcat_rest_api_url, f"propagations/{propagation_id}/opm"
            )
            res = self.client.request_authenticated(path, files=req_data, method="POST")
        return models.Propagation.parse_obj(res.json())

    def submit_propagation(self, propagation: models.Propagation) -> models.Propagation:
        """Submit the Propagation for asynchronous processing on the server.
            Note that propagations may only be submitted if they have the ``"CREATED"``
            status.

        :param propagation: The Propagation to submit.
        :type propagation: models.Propagation
        :return: The submitted Propagation.
        :rtype: models.Propagation
        """

        propagation_id = propagation.id
        path = path = urljoin(
            settings.satcat_rest_api_url, f"propagations/{propagation_id}/submit"
        )
        res = self.client.request_authenticated(path, method="PUT")
        return models.Propagation.parse_obj(res.json())

    def await_propagation_completion(
        self,
        propagation: models.Propagation,
        poll_interval: int = 5,
        timeout: int = 3600,
    ) -> models.Propagation:
        """Synchronously await the completion of a propagation.

        :param propagation: The propagation to await.
        :type propagation: models.Propagation
        :param poll_interval: Interval in seconds with which to poll for results.
            Defaults to 5.
        :type poll_interval: int, optional
        :param timeout: Length in seconds after which the request should time out.
            ``TimeoutError`` is raised if the timeout expires before the propagation
            is completed. Defaults to 3600.
        :type timeout: int, optional
        :return: The completed Propagation.
        :rtype: models.Propagation
        """
        return poll_job_for_completion(
            lambda: self.get_propagation(propagation.id),
            poll_interval=poll_interval,
            timeout=timeout,
        )
