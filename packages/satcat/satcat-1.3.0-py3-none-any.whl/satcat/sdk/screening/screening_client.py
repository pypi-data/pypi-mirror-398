import json
import os
from io import StringIO
from pathlib import Path
from typing import (
    TYPE_CHECKING,
    Any,
    BinaryIO,
    Collection,
    Dict,
    List,
    Optional,
    TextIO,
    Union,
)
from urllib.parse import urljoin

from satcat.sdk.propagation import models as prop_models
from satcat.sdk.screening import models
from satcat.sdk.settings import settings
from satcat.sdk.utils import (
    PathLike,
    SortDirection,
    open_path_or_buf,
    poll_job_for_completion,
    poll_job_for_completion_percent_generator,
    remove_none_vals,
)

if TYPE_CHECKING:
    from satcat.sdk.client import Client

DEFAULT_SORT_DIRECTION = SortDirection.DESC
DEFAULT_SORT_FIELD = "created_at"
BEST_CATALOG_TYPE = "SP"


ScreenableType = Union[
    models.Screenable,
    models.Ephemeris,
    models.Catalog,
    prop_models.Propagation,
    models.ExternalCatalog,
]

ScreenableObject = Union[
    models.Ephemeris, models.Catalog, prop_models.Propagation, models.ExternalCatalog
]


class ScreeningClient:
    client: "Client"

    def __init__(self, client: "Client"):
        self.client = client

    def get_ephemeris(self, id: str) -> models.Ephemeris:
        """Get an Ephemeris by ID from the server.

        :param id: The ID of the resource to retrieve.
        :type id: str
        :return: The retrieved Ephemeris.
        :rtype: models.Ephemeris
        """
        path = urljoin(settings.satcat_rest_api_url, f"ephemerides/{id}")
        res = self.client.request_authenticated(path)
        data = res.json()
        data["client"] = self.client
        return models.Ephemeris.parse_obj(data)

    def download_ephemeris(self, id: str, file_format: str) -> TextIO:
        """Download the content of an ephemeris as a serialized ephemeris file.

        :param id: The ID of the resource to retrieve.
        :type id: str
        :param file_format: The file format to download the ephemeris in.

            **Note**: Only the formats ``"OEM"`` and ``"NASA"`` are currently supported. This field is case insensitive.

        :type file_format: str
        :return: A file-like object opened in text mode containing the contents of the formatted ephemeris file.
        :rtype: TextIO
        """
        path = urljoin(settings.satcat_rest_api_url, f"ephemerides/{id}/file")
        params = {"file_format": file_format.upper()}
        res = self.client.request_authenticated(path, params=params)
        outbuf = StringIO()
        outbuf.write(res.content.decode())
        outbuf.seek(0)
        return outbuf

    def get_screening(self, id: str) -> models.Screening:
        """Get a Screening by ID from the server.

        :param id: The ID of the resource to retrieve.
        :type id: str
        :return: The retrieved Screening.
        :rtype: models.Screening
        """
        path = urljoin(settings.satcat_rest_api_url, f"screenings/{id}")
        res = self.client.request_authenticated(path)
        data = res.json()
        data["client"] = self.client
        return models.Screening.parse_obj(data)

    def get_catalog(self, id: str) -> models.Catalog:
        """Get a Catalog by ID from the server.

        :param id: The ID of the resource to retrieve.
        :type id: str
        :return: The retrieved Catalog.
        :rtype: models.Catalog
        """
        path = urljoin(settings.satcat_rest_api_url, f"catalogs/{id}")
        res = self.client.request_authenticated(path)
        data = res.json()
        data["client"] = self.client
        return models.Catalog.parse_obj(data)

    def list_ephemerides(
        self,
        filters: Optional[List[Dict]] = None,
        count: Optional[int] = None,
        sort_field: str = DEFAULT_SORT_FIELD,
        sort_direction: "SortDirection" = DEFAULT_SORT_DIRECTION,
    ) -> Collection[models.Ephemeris]:
        """List the Ephemerides to which the authenticated user has access.

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
        :rtype: Collection[models.Ephemeris]
        """
        params = {
            "count": count,
            "sort_field": sort_field,
            "sort_direction": sort_direction,
        }
        path = urljoin(settings.satcat_rest_api_url, "ephemerides")
        items = self.client.request_list(
            path,
            filters=filters,
            params=params,
            count=count,
            sort_direction=sort_direction,
            sort_field=sort_field,
            fields=models.Ephemeris.__fields__.keys(),
        )
        results = [models.Ephemeris.parse_obj(item) for item in items]
        return results

    def list_screenings(
        self,
        filters: Optional[List[Dict]] = None,
        count: Optional[int] = None,
        sort_field: str = DEFAULT_SORT_FIELD,
        sort_direction: "SortDirection" = DEFAULT_SORT_DIRECTION,
        show_archived: bool = False,
    ) -> Collection[models.Screening]:
        """List the Screenings to which the authenticated user has access.

        :param filters: Filters to apply to the list of resources, defaults to None.
        :type filters: Optional[List[Dict]], optional
        :param count: Maximum number of results to return. If None, return the entire
            collection. Defaults to None.
        :type count: Optional[int], optional
        :param sort_field: The field on which to sort results, defaults to DEFAULT_SORT_FIELD.
        :type sort_field: str, optional
        :param sort_direction: The direction in which to sort results, defaults to "asc".
        :type sort_direction: str, optional
        :param show_archived: Whether to include archived screenings in the results.
        :type show_archived: bool, optional
        :return: The retrieved collection of resources.
        :rtype: Collection[models.Screening]
        """
        if not show_archived:
            if filters is None:
                filters = []
            filters.append({"field": "archived", "op": "ne", "value": True})
        path = urljoin(settings.satcat_rest_api_url, "screenings")
        items = self.client.request_list(
            path,
            filters=filters,
            count=count,
            sort_direction=sort_direction,
            sort_field=sort_field,
            fields=models.Screening.__fields__.keys(),
        )
        results = [models.Screening.parse_obj(item) for item in items]
        return results

    def list_catalogs(
        self,
        filters: Optional[List[Dict]] = None,
        count: Optional[int] = None,
        latest: bool = False,
        sort_field: str = DEFAULT_SORT_FIELD,
        sort_direction: "SortDirection" = DEFAULT_SORT_DIRECTION,
    ) -> Collection[models.Catalog]:
        """List the Catalogs to which the authenticated user has access.

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
        :rtype: Collection[models.Catalog]
        """
        params = {"latest": latest}
        path = urljoin(settings.satcat_rest_api_url, "catalogs")
        items = self.client.request_list(
            path,
            filters=filters,
            params=params,
            count=count,
            sort_direction=sort_direction,
            sort_field=sort_field,
        )
        results = [models.Catalog.parse_obj(item) for item in items]
        return results

    def list_catalog_ephemerides(
        self,
        id: str,
        filters: Optional[List[Dict]] = None,
        count: Optional[int] = None,
        sort_field: str = DEFAULT_SORT_FIELD,
        sort_direction: "SortDirection" = DEFAULT_SORT_DIRECTION,
    ) -> Collection[models.Ephemeris]:
        """List the Ephemerides which belong to a Catalog by the Catalog's ID.

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
        :rtype: Collection[models.Ephemeris]
        """
        path = urljoin(settings.satcat_rest_api_url, f"catalogs/{id}/ephemerides")
        items = self.client.request_list(
            path,
            filters=filters,
            count=count,
            sort_direction=sort_direction,
            sort_field=sort_field,
        )
        results = [models.Ephemeris.parse_obj(item) for item in items]
        return results

    def list_conjunctions(
        self,
        screening_id: str,
        filters: Optional[List[Dict]] = None,
        count: Optional[int] = None,
        sort_field: str = DEFAULT_SORT_FIELD,
        sort_direction: "SortDirection" = DEFAULT_SORT_DIRECTION,
    ) -> Collection[models.Conjunction]:
        """List the Conjunctions which were generated by a Screening.

        :param screening_id: The id of the screening.
        :type screening_id: str
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
        :rtype: Collection[models.Conjunction]
        """
        path = urljoin(
            settings.satcat_rest_api_url, f"screenings/{screening_id}/conjunctions"
        )
        items = self.client.request_list(
            path,
            filters=filters,
            count=count,
            sort_direction=sort_direction,
            sort_field=sort_field,
        )
        results = [models.Conjunction.parse_obj(item) for item in items]
        return results

    def list_screening_primaries(
        self,
        screening_id: str,
        filters: Optional[List[Dict]] = None,
        count: Optional[int] = None,
        sort_field: str = DEFAULT_SORT_FIELD,
        sort_direction: "SortDirection" = DEFAULT_SORT_DIRECTION,
    ) -> Collection[models.Screenable]:
        """List the primaries attached to a screening.

        :param screening_id: The id of the screening.
        :type screening_id: str
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
        :rtype: Collection[models.Screenable]
        """
        path = urljoin(
            settings.satcat_rest_api_url, f"screenings/{screening_id}/primaries"
        )
        items = self.client.request_list(
            path,
            filters=filters,
            count=count,
            sort_direction=sort_direction,
            sort_field=sort_field,
        )
        results = [models.Screenable.parse_obj(item) for item in items]
        return results

    def list_screening_secondaries(
        self,
        screening_id: str,
        filters: Optional[List[Dict]] = None,
        count: Optional[int] = None,
        sort_field: str = DEFAULT_SORT_FIELD,
        sort_direction: "SortDirection" = DEFAULT_SORT_DIRECTION,
    ) -> Collection[models.Screenable]:
        """List the secondaries attached to a screening.

        :param screening_id: The id of the screening.
        :type screening_id: str
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
        :rtype: Collection[models.Screenable]
        """
        path = urljoin(
            settings.satcat_rest_api_url, f"screenings/{screening_id}/secondaries"
        )
        items = self.client.request_list(
            path,
            filters=filters,
            count=count,
            sort_direction=sort_direction,
            sort_field=sort_field,
        )
        results = [models.Screenable.parse_obj(item) for item in items]
        return results

    def get_latest_catalog(
        self, catalog_type: str = BEST_CATALOG_TYPE
    ) -> models.Catalog:
        """Get the latest ready catalog for a given catalog type which is not archived.

        :param catalog_type: The catalog type to retrieve, defaults to BEST_CATALOG_TYPE.
        :type catalog_type: str, optional
        :return: The retrieved catalog.
        :rtype: models.Catalog
        """
        catalogs = self.list_catalogs(
            latest=True, filters=[{"field": "catalog_type", "value": catalog_type}]
        )
        if len(catalogs) > 0:
            return catalogs[0]
        else:
            raise ValueError(f"No latest catalog found for catalog type {catalog_type}")

    def add_screening_primary(
        self,
        screening: models.Screening,
        primary: Optional[ScreenableObject] = None,
        norad_id: Optional[int] = None,
        from_best_catalog=True,
    ) -> models.Screenable:
        """Add a primary to a screening.

        :param screening: The screening to modify.
        :type screening: models.Screening
        :param primary: The object to add to the screening.
        :type primary: ScreenableObject
        :param norad_id: Shortcut field to add an Ephemeris from a Catalog by its
            Norad Catalog ID. This field may only be used alongside `primary` if `primary`
            is a `Catalog` to add the ephemeris for a specific object from a Catalog by
            Norad ID to the screening. This is equivalent to explicitly adding the
            `Ephemeris` from the catalog to the screening directly.

            For example, if you wanted to add object 25544's ephemeris from a given catalog
            to a screening, you might use:

            .. code-block:: python

                client.screening.add_screening_primary(screening, catalog, norad_id=25544)

        :type norad_id: Optional[int], optional
        :return: The added Screenable.
        :rtype: models.Screenable
        """
        data = {}
        if isinstance(primary, models.Screening):
            data["ephemeris_id"] = primary.id
        elif isinstance(primary, models.Catalog):
            if norad_id is not None:
                data["norad_id"] = norad_id
                data["catalog_id"] = primary.id
            else:
                raise ValueError(
                    "norad_id must be supplied if primary is a Catalog to specify"
                    " a particular object."
                )
        elif isinstance(primary, models.Propagation):
            data["propagation_id"] = primary.id
        elif isinstance(primary, models.Ephemeris):
            data["ephemeris_id"] = primary.id
        elif norad_id and from_best_catalog:
            best_catalog = self.get_latest_catalog(BEST_CATALOG_TYPE)
            data["norad_id"] = norad_id
            data["catalog_id"] = best_catalog.id
        elif isinstance(primary, models.ExternalCatalog):
            raise ValueError(
                f"ExternalCatalogs are not supported as screening primaries."
            )
        else:
            raise ValueError(f"Unknown primary type {type(primary)}.")
        path = urljoin(
            settings.satcat_rest_api_url, f"screenings/{screening.id}/primaries"
        )
        res = self.client.request(path, method="POST", json=data)
        return models.Screenable.parse_obj(res.json())

    def add_screening_secondary(
        self,
        screening: models.Screening,
        secondary: ScreenableObject,
        norad_id: Optional[int] = None,
    ) -> models.Screenable:
        """Add a secondary to a screening.

        :param screening: The screening to modify.
        :type screening: models.Screening
        :param secondary: The object to add to the screening.
        :type secondary: ScreenableObject
        :param norad_id: Shortcut field to add an Ephemeris from a Catalog by its
            Norad Catalog ID. This field may only be used alongside `primary` if `primary`
            is a `Catalog` to add the ephemeris for a specific object from a Catalog by
            Norad ID to the screening. This is equivalent to explicitly adding the
            `Ephemeris` from the catalog to the screening directly.

            For example, if you wanted to add object 25544's ephemeris from a given catalog
            to a screening, you might use:

            .. code-block:: python

                client.screening.add_screening_primary(screening, catalog, norad_id=25544)

        :type norad_id: Optional[int], optional
        :return: The added Screenable.
        :rtype: models.Screenable
        """
        data = {}
        if isinstance(secondary, models.Screening):
            data["ephemeris_id"] = secondary.id
        elif isinstance(secondary, models.Catalog):
            data["catalog_id"] = secondary.id
            if norad_id is not None:
                data["norad_id"] = norad_id
        elif isinstance(secondary, models.Propagation):
            data["propagation_id"] = secondary.id
        elif isinstance(secondary, models.Ephemeris):
            data["ephemeris_id"] = secondary.id
        elif isinstance(secondary, models.ExternalCatalog):
            data["external_catalog"] = secondary.value
        else:
            raise ValueError(f"Unknown secondary type {type(secondary)}.")
        path = urljoin(
            settings.satcat_rest_api_url, f"screenings/{screening.id}/secondaries"
        )
        res = self.client.request(path, method="POST", json=data)
        return models.Screenable.parse_obj(res.json())

    def create_ephemeris(
        self,
        path_or_buf: Union[PathLike, BinaryIO],
        file_format: str = "AUTOMATIC",
        norad_id: Optional[int] = None,
        filename: Optional[str] = None,
        comments: Optional[str] = None,
        hbr_m: Optional[float] = None,
        context: Union[models.EphemerisContext, str, None] = None,
        designation: Union[models.EphemerisDesignation, str, None] = None,
    ) -> models.Ephemeris:
        """Upload an Ephemeris file to the server.
            .. note::
                Uploading an Ephemeris does not automatically trigger it to be screened.
                For this, you can use `create_screening`.

        :param path_or_buf: Path to an ephemeris file, or alternatively an open binary
            file-like object containing the contents of an ephemeris file.
            Note that the file should be opened in binary mode, even if the ephemeris
            file format is a common plaintext format.
        :type path_or_buf: Union[PathLike, BinaryIO]
        :param file_format: The file format. By default, the format will be automatically detected based on the file content.
        :type file_format: str
        :param norad_id: The NORAD Catalog ID of the object which the ephemeris
            file describes.

            .. note::
                Specifying the NORAD Catalog ID helps Kayhan ensure that the Ephemeris is not screened
                against other Ephemerides from the same object. While the NORAD Catalog ID field is
                optional to support Launch Screening and early-deployment screenings, we strongly
                recommend that you specify it for all on-orbit Ephemerides.

        :type norad_id: Optional[int]
        :param filename: The filename of the ephemeris file. If ``path_or_buf`` is
            a ``Path``, the filename will be automatically determined. Defaults to None
        :type filename: Optional[str], optional
        :param comments: Optional user-defined comments to attach to the file metadata.
            Defaults to None
        :type comments: Optional[str], optional
        :param hbr_m: The hard-body radius of the object in meters
        :type hbr_m: Optional[float]
        :param context: The Pathfinder context metadata for the ephemeris. For more information, see https://app.satcat.io/docs/pathfinder/operational-data/#ephemeris-metadata.
        :type context: Union[models.EphemerisContext, str, None]
        :param designation: The Pathfinder designation metadata for the ephemeris. For more information, see https://app.satcat.io/docs/pathfinder/operational-data/#ephemeris-metadata.
        :type designation: Union[models.EphemerisDesignation, str, None]
        :return: The created Ephemeris
        :rtype: models.Ephemeris
        """
        with open_path_or_buf(path_or_buf, mode="rb") as file:
            file_format = file_format.upper()
            if isinstance(path_or_buf, Path) and filename is None:
                filename = os.path.basename(path_or_buf.name)
            if isinstance(path_or_buf, str) and filename is None:
                filename = path_or_buf
            if filename is None:
                filename = "USER_UPLOADED_EPHEMERIS.txt"
                try:
                    filename = os.path.basename(file.name)
                except AttributeError:
                    pass  # use default name if buffer object has no name attr
            hbr_str = str(hbr_m) if hbr_m is not None else None
            context = (
                models.EphemerisContext(context)
                if isinstance(context, str)
                else context
            )
            designation = (
                models.EphemerisDesignation(designation)
                if isinstance(designation, str)
                else designation
            )
            data = [
                ("norad_id", (None, norad_id)),
                ("file_format", (None, file_format)),
                ("comments", (None, comments)),
                ("ephemeris_file", (filename, file)),
                ("hbr_m", (None, hbr_str)),
                ("context", (None, context.value if context is not None else None)),
                (
                    "designation",
                    (None, designation.value if designation is not None else None),
                ),
            ]
            path = urljoin(settings.satcat_rest_api_url, "ephemerides")
            res = self.client.request_authenticated(path, files=data, method="POST")
        return models.Ephemeris.parse_obj(res.json())

    def operationalize_ephemeris(self, ephemeris_id: str) -> models.Ephemeris:
        """Operationalize an ephemeris by ID.

        :param ephemeris_id: The ID of the resource to designate as 'OPERATIONAL'.
        :type ephemeris_id: str
        :return: The updated Ephemeris.
        :rtype: models.Ephemeris
        """

        path = urljoin(
            settings.satcat_rest_api_url,
            f"ephemerides/{ephemeris_id}/operationalize",
        )
        res = self.client.request_authenticated(path, json={}, method="PUT")
        ephemeris = models.Ephemeris.parse_obj(res.json())

        return ephemeris

    def resolve_to_screenable(self, input: ScreenableType) -> models.Screenable:
        if isinstance(input, models.Screenable):
            return input
        elif isinstance(input, models.Ephemeris):
            return models.Screenable(ephemeris_id=input.id)
        elif isinstance(input, models.Catalog):
            return models.Screenable(catalog_id=input.id)
        elif isinstance(input, prop_models.Propagation):
            return models.Screenable(propagation_id=input.id)
        elif isinstance(input, models.ExternalCatalog):
            return models.Screenable(external_catalog=input.value)
        else:
            raise TypeError(
                f"Cannot create Screenable from input of type {type(input)}"
            )

    def create_screening(
        self,
        config: Optional[models.ScreeningConfiguration] = None,
        primaries: Optional[List[ScreenableType]] = None,
        secondaries: Optional[List[ScreenableType]] = None,
        add_best_secondary_catalog: bool = False,
        add_operational_ephemeris_repository: bool = False,
        submit: bool = False,
    ) -> models.Screening:
        """Create a Screening on the server.

        :param config: The configuration with which to run the screening.
        :type config: models.ScreeningConfiguration
        :param primaries: The list of primaries which should be screened.
        :type primaries: Optional[List[models.Screenable]], optional
        :param secondaries: The list of secondaries which should be screened against.
        :type secondaries: Optional[List[models.Screenable]], optional
        :param add_best_secondary_catalog: Whether the secondary catalog determined by
            the application as "Best" (latest updated data and highest-fidelity
            available data source) should be automatically added to the screening.
        :type add_best_secondary_catalog: bool, optional
        :param add_operational_ephemeris_repository: Whether all ephemeris with a designation of
            ``OPERATIONAL`` and with a ``usable_time_end`` in the future should be automatically
            added to the screening.
        :type add_operational_ephemeris_repository: bool, optional
        :param submit: Whether to submit the screening instantly. If ``False``,
            the screening may be submitted later using
            ``client.screening.submit_screening(screening)``.
        :type submit: bool, optional
        :return: The created Screening.
        :rtype: models.Screening
        """
        if config is None:
            config = models.ScreeningConfiguration()
        data = remove_none_vals(json.loads(config.json()))

        if primaries is None:
            primaries = []
        if secondaries is None:
            secondaries = []

        if add_best_secondary_catalog:
            best_catalog = self.get_latest_catalog(BEST_CATALOG_TYPE)
            screenable = models.Screenable(catalog_id=best_catalog.id)
            secondaries = [s for s in secondaries]
            secondaries.append(screenable)

        if add_operational_ephemeris_repository:
            screenable = models.Screenable(
                ephemeris_group=models.EphemerisGroup.OPERATOR_REPOSITORY
            )
            secondaries.append(screenable)

        if primaries is not None:
            primaries = [self.resolve_to_screenable(p) for p in primaries]
            primaries_dicts = [remove_none_vals(p.dict()) for p in primaries]
            data["primaries"] = primaries_dicts
        if secondaries is not None:
            secondaries = [self.resolve_to_screenable(s) for s in secondaries]
            secondaries_dicts = [remove_none_vals(s.dict()) for s in secondaries]
            data["secondaries"] = secondaries_dicts
        params = {"submit": submit}
        path = urljoin(settings.satcat_rest_api_url, "screenings")
        res = self.client.request_authenticated(
            path, json=data, method="POST", params=params
        )
        screening = models.Screening.parse_obj(res.json())

        return screening

    def submit_screening(self, screening: models.Screening) -> models.Screening:
        """Submit the Screening for asynchronous processing on the server.
        Note that screenings may only be submitted if they have the ``"CREATED"``
        status.

        :param screening: The Screening to submit.
        :type screening: models.Screening
        :return: The submitted Screening.
        :rtype: models.Screening
        """
        path = urljoin(
            settings.satcat_rest_api_url, f"screenings/{screening.id}/submit"
        )
        res = self.client.request_authenticated(path, method="PUT")
        return models.Screening.parse_obj(res.json())

    def await_screening_completion(
        self, screening: models.Screening, poll_interval: int = 5, timeout: int = 3600
    ) -> models.Screening:
        """Synchronously await the completion of a screening.

        :param screening: The screening to await.
        :type screening: models.Screening
        :param poll_interval: Interval in seconds with which to poll for results.
            Defaults to 5.
        :type poll_interval: int, optional
        :param timeout: Length in seconds after which the request should time out.
            ``TimeoutError`` is raised if the timeout expires before the screening
            is completed. Defaults to 3600.
        :type timeout: int, optional
        :return: The completed Screening.
        :rtype: models.Screening
        """
        return poll_job_for_completion(
            lambda: self.get_screening(screening.id),
            poll_interval=poll_interval,
            timeout=timeout,
        )

    def await_screening_completion_percent_generator(
        self, screening: models.Screening, poll_interval: int = 5, timeout: int = 3600
    ) -> models.Screening:  # type: ignore
        gen = poll_job_for_completion_percent_generator(
            lambda: self.get_screening(screening.id),
            poll_interval=poll_interval,
            timeout=timeout,
        )
        while True:
            try:
                yield next(gen)
            except StopIteration as e:
                return e.value

    def get_api_spec(self) -> dict:
        """Retrieve the OpenAPI specification from the server."""
        path = urljoin(settings.satcat_rest_api_url, "openapi.json")
        res = self.client.request(path)
        return res.json()

    def list_ephemeris_formats(self) -> Collection[str]:
        """Retrieve the list of supported ephemeris file formats."""
        spec = self.get_api_spec()
        return spec["components"]["schemas"]["EphemerisReadFileFormat"]["enum"]

    def list_conjunctions_ccsds(
        self,
        screening_id: str,
        filters: Optional[List[Dict]] = None,
        count: Optional[int] = None,
        sort_field: str = DEFAULT_SORT_FIELD,
        sort_direction: "SortDirection" = DEFAULT_SORT_DIRECTION,
    ) -> List[Dict[str, Any]]:
        """List the Conjunctions in CCSDS format which belong to a Screening by the Screenings's ID.

        :param screening_id: ID of Screening job for conjunctions
        :type screening_id: str
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
        :rtype: List[Dict[str, Any]]
        """
        path = urljoin(
            settings.satcat_rest_api_url, f"screenings/{screening_id}/results/ccsds"
        )
        items = self.client.request_list(
            path,
            filters=filters,
            count=count,
            sort_direction=sort_direction,
            sort_field=sort_field,
        )
        sanitized_items = [
            {key: value for key, value in item.items() if key != "client"}
            for item in items
        ]
        return sanitized_items

    def get_conjunction_ccsds(
        self,
        screening_id: str,
        conjunction_id: str,
    ) -> Dict[str, Any]:
        """List single Conjunction in CCSDS format which belong to a Screening by the Screenings's ID.

        :param screening_id: ID of Screening job for conjunctions
        :type screening_id: str
        :param conjunction_id: ID of individual Conjunction
        :type conjunction_id: str
        :return: The Conjunction resource.
        :rtype: Dict[str, Any]
        """
        path = urljoin(
            settings.satcat_rest_api_url,
            f"screenings/{screening_id}/results/ccsds/{conjunction_id}",
        )
        res = self.client.request_authenticated(path)
        return res.json()
