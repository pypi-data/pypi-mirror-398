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
    Type
)
from urllib.parse import urljoin

from satcat.sdk.propagation import models as prop_models
from satcat.sdk.maneuvers import models
from satcat.sdk.settings import settings
from satcat.sdk.utils import (
    PathLike,
    SortDirection,
    open_path_or_buf,
    poll_job_for_completion,
    poll_job_for_completion_percent_generator,
    remove_none_vals,
    NotFoundError
)

if TYPE_CHECKING:
    from satcat.sdk.client import Client

DEFAULT_SORT_DIRECTION = SortDirection.DESC
DEFAULT_SORT_FIELD = "created_at"



class ColaManeuverClient:
    client: "Client"

    def __init__(self, client: "Client"):
        self.client = client

    def create_project(self) -> models.ManeuverProject:
        """Create a Satcat Maneuver Designer Project on the server.

        :return: The created Maneuver Project.
        :rtype: models.ManeuverProject
        """
        path = urljoin(settings.satcat_rest_api_url, "maneuver_projects")
        res = self.client.request_authenticated(
            path, method="POST"
        )
        project = models.ManeuverProject.parse_obj(res.json())
        return project

    def create_variant_for_project(self, project_id: str, config: Optional[models.ColaManeuverVariantConfiguration] = None) -> models.ColaManeuverVariant:
        """Create a COLA Maneuver Variant for a given Project.

        Variants are asynchronous jobs that are automatically triggered when created. The status of a variant can be polled using ``get_variant`` or
        the variant's completion can be awaited synchronously using ``await_variant_completion``.

        :param project_id: The ID of the project under which to create the variant.
        :type project_id: str
        :param config: The configuration of the variant to run, defaults to None
        :type config: Optional[models.ColaManeuverVariantConfiguration], optional
        :return: The created Variant.
        :rtype: models.ColaManeuverVariant
        """
        if config is None:
            config = models.ColaManeuverVariantConfiguration()
        data = remove_none_vals(json.loads(config.json()))

        path = urljoin(settings.satcat_rest_api_url, f"maneuver_projects/simple/{str(project_id)}/variants")
        res = self.client.request_authenticated(
            path, json=data, method="POST"
        )
        variant = models.ColaManeuverVariant.parse_obj(res.json())
        return variant
 

    def get_variant(self, variant_id: str) -> models.ColaManeuverVariantWithTradespace:
        """Retrieve an existing COLA maneuver variant by ID.

        :param variant_id: The ID of the variant to retrieve.
        :type variant_id: str
        :raises NotFoundError: If the variant is not found, an exception is raised.
        :return: The retrieved Variant, including the generated tradespace data if the variant completed successfully.
        :rtype: models.ColaManeuverVariantWithTradespace
        """
        filters=[dict(field='id', value=str(variant_id))]
        variants = self.list_variants(filters=filters, count=1, model=models.ColaManeuverVariantWithTradespace)
        if len(variants) == 0:
            raise NotFoundError()

        return variants[0]


    def await_variant_completion(self, variant: models.ColaManeuverVariant, poll_interval: int = 5, timeout: int = 3600) -> models.ColaManeuverVariant:
        """Synchronously await the completion of a variant.

        :param variant: The variant to await.
        :type variant: models.ColaManeuverVariant
        :param poll_interval: Interval in seconds with which to poll for results.
            Defaults to 5.
        :type poll_interval: int, optional
        :param timeout: Length in seconds after which the request should time out.
            ``TimeoutError`` is raised if the timeout expires before the screening
            is completed. Defaults to 3600.
        :type timeout: int, optional
        :return: The completed variant.
        :rtype: models.ColaManeuverVariant
        """
        return poll_job_for_completion(
            lambda: self.get_variant(variant.id),
            poll_interval=poll_interval,
            timeout=timeout,
        )


    def list_projects(
        self, 
        filters: Optional[List[Dict]] = None,
        count: Optional[int] = None,
        sort_field: str = DEFAULT_SORT_FIELD,
        sort_direction: "SortDirection" = DEFAULT_SORT_DIRECTION,    
    ) -> List[models.ManeuverProject]:
        """List the Maneuver Designer Projects to which the authenticated user has access.

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
        :rtype: List[models.ManeuverProject]
        """
        path = urljoin(settings.satcat_rest_api_url, "maneuver_projects")
        items = self.client.request_list(
            path,
            filters=filters,
            count=count,
            sort_direction=sort_direction,
            sort_field=sort_field,
            fields=models.ManeuverProject.__fields__.keys(),
        )
        results = [models.ManeuverProject.parse_obj(item) for item in items]
        return results

    def list_variants(
        self, 
        filters: Optional[List[Dict]] = None,
        count: Optional[int] = None,
        sort_field: str = DEFAULT_SORT_FIELD,
        sort_direction: "SortDirection" = DEFAULT_SORT_DIRECTION,
        model: Type[models.ColaManeuverVariantConfiguration] = models.ColaManeuverVariant
    ) -> List[models.ColaManeuverVariant]:
        """List the Maneuver Designer COLA Variants to which the authenticated user has access.

        :param filters: Filters to apply to the list of resources, defaults to None.
        :type filters: Optional[List[Dict]], optional
        :param count: Maximum number of results to return. If None, return the entire
            collection. Defaults to None.
        :type count: Optional[int], optional
        :param sort_field: The field on which to sort results, defaults to DEFAULT_SORT_FIELD.
        :type sort_field: str, optional
        :param sort_direction: The direction in which to sort results, defaults to "asc".
        :type sort_direction: str, optional
        :param model: The data model to retrieve from the server. The `ColaManeuverVariantWithTradespace` model can be used to include the generated tradespace data in the contents of each listed variant.
        :type model: Type[models.ColaManeuverVariantConfiguration]
        :return: The retrieved collection of resources.
        :rtype: List[models.ManeuverProject]
        """
        path = urljoin(settings.satcat_rest_api_url, "cola_maneuver_variants")
        items = self.client.request_list(
            path,
            filters=filters,
            count=count,
            sort_direction=sort_direction,
            sort_field=sort_field,
            fields=model.__fields__.keys(),
        )
        results = [model.parse_obj(item) for item in items]
        return results

    def get_latest_variant_for_cdm(
        self, 
        cdm_key: str
    ) -> Optional[models.ColaManeuverVariant]:
        """Find the most recently run COLA maneuver variant generated from a given CDM.

        .. note::
            CDM key is Satcat's unique identifier for CDMs, and is of the form "CDM-S12345".

        :param cdm_key: The key of the CDM for which to search
        :type cdm_key: str
        :return: The latest maneuver variant for the desired CDM. If no variants are available, returns None.
        :rtype: Optional[models.ColaManeuverVariant]
        """
        variants = self.list_variants(
            filters=[
                dict(field="original_conjunction.cdm_key", value=cdm_key)
            ],
            sort_field='created_at',
            sort_direction=SortDirection.DESC,
            count=1,
            model=models.ColaManeuverVariantWithTradespace
        )

        if len(variants) == 0:
            return None

        return variants[0]
    
    def create_hifi_plan(self, project_id: str, variant_id: str, config: models.TimestampedSimpleManeuverPlanParameters) -> models.ColaManeuverHifiPlan:
        """Create a high-fidelity maneuver plan for a COLA maneuver variant. Hifi plans are asynchronous jobs that are automatically triggered when created. The status of a plan can be polled using ``get_hifi_plan`` or
        the plan's completion can be awaited synchronously using ``await_hifi_plan_completion``.

        Note that the maneuver plan does not need to be one of the points reported in the original tradespace; this allows for fine-grain
        refinement of maneuver plan times and delta-V values.

        :param project_id: _description_
        :type project_id: str
        :param variant_id: _description_
        :type variant_id: str
        :param config: _description_
        :type config: models.TimestampedSimpleManeuverPlanParameters
        :return: _description_
        :rtype: models.ColaManeuverHifiPlan
        """
        data = remove_none_vals(json.loads(config.json()))

        params={"variant_id": variant_id}
        path = urljoin(settings.satcat_rest_api_url, f"maneuver_projects/simple/{project_id}/maneuver_plans")
        res = self.client.request_authenticated(
            path, json=data, method="POST", params=params
        )
        plan = models.ColaManeuverHifiPlan.parse_obj(res.json())
        return plan
    
    def list_hifi_plans(
        self,
        filters: Optional[List[Dict]] = None,
        count: Optional[int] = None,
        sort_field: str = DEFAULT_SORT_FIELD,
        sort_direction: "SortDirection" = DEFAULT_SORT_DIRECTION,
        model: Type[models.ColaManeuverHifiPlan] = models.ColaManeuverHifiPlan
    ) -> List[models.ColaManeuverHifiPlan]:
        """List the Maneuver Designer COLA Hifi plans to which the authenticated user has access.

        :param filters: Filters to apply to the list of resources, defaults to None.
        :type filters: Optional[List[Dict]], optional
        :param count: Maximum number of results to return. If None, return the entire
            collection. Defaults to None.
        :type count: Optional[int], optional
        :param sort_field: The field on which to sort results, defaults to DEFAULT_SORT_FIELD.
        :type sort_field: str, optional
        :param sort_direction: The direction in which to sort results, defaults to "asc".
        :type sort_direction: str, optional
        :param model: The data model to retrieve from the server. The `ColaManeuverVariantWithTradespace` model can be used to include the generated tradespace data in the contents of each listed variant.
        :type model: Type[models.ColaManeuverVariantConfiguration]
        :return: The retrieved collection of resources.
        :rtype: List[models.ManeuverProject]
        """
        path = urljoin(settings.satcat_rest_api_url, "cola_maneuver_plans")
        items = self.client.request_list(
            path,
            filters=filters,
            count=count,
            sort_direction=sort_direction,
            sort_field=sort_field,
            fields=model.__fields__.keys(),
        )
        results = [model.parse_obj(item) for item in items]
        return results
    
    def get_hifi_plan(self, plan_id: str) -> models.ColaManeuverHifiPlan:
        """Retrieve an existing COLA maneuver Hifi plan by ID.

        :param plan_id: The ID of the maneuver plan to retrieve.
        :type plan_id: str
        :raises NotFoundError: If the plan is not found, an exception is raised.
        :return: The retrieved maneuver plan data
        :rtype: models.ColaManeuverHifiPlan
        """
        filters=[dict(field='id', value=str(plan_id))]
        variants = self.list_hifi_plans(filters=filters, count=1, model=models.ColaManeuverHifiPlan)
        if len(variants) == 0:
            raise NotFoundError()

        return variants[0]

    def await_hifi_plan_completion(self, plan: models.ColaManeuverHifiPlan, poll_interval: int = 5, timeout: int = 3600) -> models.ColaManeuverHifiPlan:
        """Synchronously await the completion of a hifi plan.

        :param plan: The hifi plan to await.
        :type plan: models.ColaManeuverHifiPlan
        :param poll_interval: Interval in seconds with which to poll for results.
            Defaults to 5.
        :type poll_interval: int, optional
        :param timeout: Length in seconds after which the request should time out.
            ``TimeoutError`` is raised if the timeout expires before the screening
            is completed. Defaults to 3600.
        :type timeout: int, optional
        :return: The completed plan.
        :rtype: models.ColaManeuverHifiPlan
        """
        return poll_job_for_completion(
            lambda: self.get_hifi_plan(plan.id),
            poll_interval=poll_interval,
            timeout=timeout,
        )