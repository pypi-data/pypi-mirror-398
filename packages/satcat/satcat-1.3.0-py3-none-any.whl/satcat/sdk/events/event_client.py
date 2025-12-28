from io import StringIO
from typing import TYPE_CHECKING, Any, Dict, List, Optional, TextIO, Union
from urllib.parse import urljoin

from satcat.sdk.events import models
from satcat.sdk.settings import settings
from satcat.sdk.utils import SortDirection

DEFAULT_SORT_DIRECTION = SortDirection.DESC
DEFAULT_SORT_FIELD = "created_at"


if TYPE_CHECKING:
    from satcat.sdk.client import Client


class EventClient:
    client: "Client"

    def __init__(self, client: "Client"):
        self.client = client

    def list_events(
        self,
        filters: Optional[List[Dict]] = None,
        count: Optional[int] = None,
        sort_field: str = DEFAULT_SORT_FIELD,
        sort_direction: "SortDirection" = DEFAULT_SORT_DIRECTION,
    ):
        """
        List available events

        :param filters: Filters to apply to the list of resources, defaults to None.
        :type filters: Optional[List[Dict]], optional
        :param count: Maximum number of results to return. If None, return the entire
            collection. Defaults to None.
        :type count: Optional[int], optional
        :param sort_field: The field on which to sort results, defaults to DEFAULT_SORT_FIELD.
        :type sort_field: str, optional
        :param sort_direction: The direction in which to sort results, defaults to "asc".
        :type sort_direction: str, optional
        :return: The retrieved collection of resources.
        :rtype: Collection[models.Event]
        """
        params = {
            "count": count,
            "sort_field": sort_field,
            "sort_direction": sort_direction,
        }
        path = urljoin(settings.satcat_rest_api_url, "events")
        items = self.client.request_list(
            path,
            filters=filters,
            params=params,
            count=count,
            sort_direction=sort_direction,
            sort_field=sort_field,
            fields=models.Event.__fields__.keys(),
        )
        return [models.Event.parse_obj(item) for item in items]

    def list_event_conjunctions(
        self,
        event_key: str,
        filters: Optional[List[Dict]] = None,
        count: Optional[int] = None,
        sort_field: str = DEFAULT_SORT_FIELD,
        sort_direction: "SortDirection" = DEFAULT_SORT_DIRECTION,
    ):
        """
        List available conjunctions for a specific event

        :param event_key: The key of the event to filter by.
        :type event_key: str
        :param filters: Filters to apply to the list of resources, defaults to None.
        :type filters: Optional[List[Dict]], optional
        :param count: Maximum number of results to return. If None, return the entire
            collection. Defaults to None.
        :type count: Optional[int], optional
        :param sort_field: The field on which to sort results, defaults to DEFAULT_SORT_FIELD.
        :type sort_field: str, optional
        :param sort_direction: The direction in which to sort results, defaults to "asc".
        :type sort_direction: str, optional
        :return: The retrieved collection of resources.
        :rtype: Collection[models.ConjunctionMinimal]
        """
        params = {
            "count": count,
            "sort_field": sort_field,
            "sort_direction": sort_direction,
        }

        path = urljoin(settings.satcat_rest_api_url, f"events/{event_key}/cdms")

        items = self.client.request_list(
            path,
            filters=filters,
            params=params,
            count=count,
            sort_direction=sort_direction,
            sort_field=sort_field,
        )

        return [models.ConjunctionMinimal.parse_obj(item) for item in items]

    def list_conjunctions(
        self,
        filters: Optional[List[Dict]] = None,
        count: Optional[int] = None,
        sort_field: str = DEFAULT_SORT_FIELD,
        sort_direction: "SortDirection" = DEFAULT_SORT_DIRECTION,
    ):
        """
        List available conjunctions

        :param filters: Filters to apply to the list of resources, defaults to None.
        :type filters: Optional[List[Dict]], optional
        :param count: Maximum number of results to return. If None, return the entire
            collection. Defaults to None.
        :type count: Optional[int], optional
        :param sort_field: The field on which to sort results, defaults to DEFAULT_SORT_FIELD.
        :type sort_field: str, optional
        :param sort_direction: The direction in which to sort results, defaults to "asc".
        :type sort_direction: str, optional
        :return: The retrieved collection of resources.
        :rtype: Collection[models.ConjunctionMinimal]
        """
        params = {
            "count": count,
            "sort_field": sort_field,
            "sort_direction": sort_direction,
        }
        path = urljoin(settings.satcat_rest_api_url, "conjunction_messages")
        items = self.client.request_list(
            path,
            filters=filters,
            params=params,
            count=count,
            sort_direction=sort_direction,
            sort_field=sort_field,
            fields=models.ConjunctionMinimal.__fields__.keys(),
        )
        return [models.ConjunctionMinimal.parse_obj(item) for item in items]

    def list_conjunctions_ccsds(
        self,
        filters: Optional[List[Dict]] = None,
        count: Optional[int] = None,
        sort_field: str = DEFAULT_SORT_FIELD,
        sort_direction: "SortDirection" = DEFAULT_SORT_DIRECTION,
    ):
        """
        List available conjunctions in CCSDS format

        :param filters: Filters to apply to the list of resources, defaults to None.
        :type filters: Optional[List[Dict]], optional
        :param count: Maximum number of results to return. If None, return the entire
            collection. Defaults to None.
        :type count: Optional[int], optional
        :param sort_field: The field on which to sort results, defaults to DEFAULT_SORT_FIELD.
        :type sort_field: str, optional
        :param sort_direction: The direction in which to sort results, defaults to "asc".
        :type sort_direction: str, optional
        :return: The retrieved collection of resources.
        :rtype: Collection[dict]
        """
        params = {
            "count": count,
            "sort_field": sort_field,
            "sort_direction": sort_direction,
        }
        path = urljoin(settings.satcat_rest_api_url, "conjunction_messages/ccsds")
        items = self.client.request_list(
            path,
            filters=filters,
            params=params,
            count=count,
            sort_direction=sort_direction,
            sort_field=sort_field,
        )
        sanitized_items = [
            {key: value for key, value in item.items() if key != "client"}
            for item in items
        ]
        return sanitized_items

    def get_conjunction(self, cdm_id: str):
        """
        Get a specific conjunction by its cdm_id or key. Note that this returns a more details Conjunction description than the screening conjunction endpoint.

        :param cdm_id: the cdm_id or cdm key of the conjunction to retrieve.
        :type cdm_id: str
        :return: The retrieved conjunction.
        :rtype: models.ConjunctionDetailed
        """
        path = f"conjunction_messages/{cdm_id}"
        res = self.client.request_authenticated(path)
        data = res.json()
        data["client"] = self.client
        return models.ConjunctionDetailed.parse_obj(data)

    def get_conjunction_ccsds(self, cdm_id: str):
        """
        Get a specific conjunction by its cdm_id or key in CCSDS format. Note that this returns a more details Conjunction description than the screening conjunction endpoint.

        :param cdm_id: the cdm_id or cdm key of the conjunction to retrieve.
        :type cdm_id: str
        :return: The retrieved conjunction.
        :rtype: dict
        """
        path = f"conjunction_messages/{cdm_id}/ccsds"
        res = self.client.request_authenticated(path)
        return res.json()

    def download_conjunction(
        self,
        cdm_id: str,
        file_format: Optional[str] = "json",
        satcat_updated: bool = True,
    ) -> TextIO:
        """
        Downloads a specific conjunction message file by its CDM ID or key.

        :param cdm_id: The CDM ID or key of the conjunction to retrieve.
        :param file_format: The desired file format for the conjunction file (e.g., "json"). Defaults to "json".
        :param satcat_updated: Flag indicating whether to retrieve the Satcat-updated version of the conjunction file.
            This updated version would contain the remediated collision probability value computed by Satcat as well as the
            updated exclusion volume radius (HBR) values used to compute them. Defaults to True.
        :type file_format: Optional[str]
        :return: The content of the retrieved conjunction file.
        :rtype: bytes
        """
        path = (
            f"conjunction_messages/{cdm_id}/file?updated={str(satcat_updated).lower()}"
        )
        params = {"file_format": file_format.upper()}
        res = self.client.request_authenticated(path, params=params)
        outbuf = StringIO()
        outbuf.write(res.content.decode())
        outbuf.seek(0)
        return outbuf

    def request_cdm_pc_method(
        self,
        cdm: Union[models.ConjunctionDetailed, str],
        method: models.PCRemediationMethod,
    ) -> Dict[str, Any]:
        """
        Requests a specific collision probability method for a conjunction message by its CDM ID or key.

        :param cdm: The Conjunction object to request the collision probability method for, or a string representing the CDM ID or key (e.g. "CDM-S123456").
        :param method: The PC method to request.
        :type method: models.PCRemediationMethod
        :return: The content of the CDM in CCSDS JSON format with the requested PC method populated in the standard `COLLISION_PROBABILITY` field.
        :rtype: Dict
        """
        if isinstance(cdm, models.ConjunctionDetailed):

            cdm_id = cdm.key
        elif isinstance(cdm, str):
            cdm_id = cdm
        else:
            raise ValueError(
                "cdm must be a ConjunctionDetailed instance or a string representing the CDM ID or key."
            )
        path = f"conjunction_messages/{cdm_id}/pc_remediation?method={method.value}"
        res = self.client.request_authenticated(path, method="POST")
        return res.json()
