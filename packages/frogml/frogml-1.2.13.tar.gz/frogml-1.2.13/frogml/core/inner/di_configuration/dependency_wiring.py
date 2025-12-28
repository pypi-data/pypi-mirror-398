import os
from pathlib import Path
from typing import Optional

from frogml.core.inner.const import FrogMLConstants
from frogml.core.inner.di_configuration import FrogmlContainer
from frogml.core.inner.tool.grpc.grpc_tools import validate_grpc_address
from frogml.core.tools.logger import get_frogml_logger

logger = get_frogml_logger()

__DEFAULT_CONFIG_FILE_PATH: Path = Path(__file__).parent / "config.yml"


def wire_dependencies() -> FrogmlContainer:
    container = FrogmlContainer()

    container.config.from_yaml(__DEFAULT_CONFIG_FILE_PATH)
    control_plane_grpc_address_override: Optional[str] = os.getenv(
        FrogMLConstants.CONTROL_PLANE_GRPC_ADDRESS_ENVAR_NAME
    )

    if control_plane_grpc_address_override:
        validate_grpc_address(control_plane_grpc_address_override)
        __override_control_plane_grpc_address(
            container, control_plane_grpc_address_override
        )

    from frogml.core.clients import (
        kube_deployment_captain,
        model_version_manager,
        analytics,
        system_secret,
        autoscaling,
        build_orchestrator,
        batch_job_management,
        instance_template,
        feature_store,
        deployment,
        user_application_instance,
        jfrog_gateway,
        alert_management,
        integration_management,
        model_management,
        audience,
        data_versioning,
        logging_client,
        automation_management,
        file_versioning,
        alerts_registry,
        administration,
        model_group_management,
    )

    container.wire(
        packages=[
            administration,
            alert_management,
            audience,
            automation_management,
            autoscaling,
            analytics,
            batch_job_management,
            build_orchestrator,
            data_versioning,
            deployment,
            file_versioning,
            instance_template,
            kube_deployment_captain,
            logging_client,
            model_management,
            feature_store,
            user_application_instance,
            alerts_registry,
            integration_management,
            system_secret,
            model_version_manager,
            jfrog_gateway,
            model_group_management,
        ]
    )

    return container


def __override_control_plane_grpc_address(
    container: "FrogmlContainer", control_plane_grpc_address_override: str
):
    logger.debug(
        "Overriding control plane gRPC address from environment variable to %s.",
        control_plane_grpc_address_override,
    )
    container.config.grpc.core.address.from_value(
        control_plane_grpc_address_override.strip()
    )
