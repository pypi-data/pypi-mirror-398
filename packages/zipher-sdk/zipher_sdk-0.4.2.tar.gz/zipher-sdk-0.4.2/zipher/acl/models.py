from enum import Enum
from typing import Optional, List

from pydantic import BaseModel


class InstallerConfig(BaseModel, extra='forbid', use_enum_values=True):
    zipher_group_name: str = 'zipher'
    zipher_group_entitlements: List[str] = [
        'workspace-access',
        'allow-cluster-create',
        'databricks-sql-access'
    ]

    zipher_service_principal_name: str = 'zipher_sp'

    zipher_workspace_dir_path: str = '/zipher_script'
    zipher_secret_scope_name: str = 'zipher'

    unity_catalog_schemas: List[str] = [
        'system.billing',
        'system.compute'
    ]
    unity_catalog_tables: List[str] = [
        'system.billing.usage',
        'system.billing.list_prices',
        'system.billing.cloud_infra_cost',
        'system.compute.clusters',
        'system.compute.node_timeline'
    ]


class JobPermissions(str, Enum):
    CAN_VIEW = 'CAN_VIEW'
    CAN_MANAGE = 'CAN_MANAGE'


class ServicePrincipalTokenType(str, Enum):
    PERSONAL_ACCESS_TOKEN = 'PERSONAL_ACCESS_TOKEN'
    OAUTH = 'OAUTH'


class InstallerUserConfig(BaseModel, extra='forbid', use_enum_values=True):
    days_back: Optional[int] = None
    max_jobs: Optional[int] = None
    max_runs: Optional[int] = None
    jobs_list : Optional[List[str]] = None
    jobs_permission: JobPermissions = JobPermissions.CAN_MANAGE
    service_principal_token_type: ServicePrincipalTokenType = ServicePrincipalTokenType.OAUTH
    existing_service_principal_id: Optional[str] = None
