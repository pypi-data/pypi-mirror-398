from enum import Enum
from typing import Optional

from pydantic import BaseModel


class WorkspaceClientAuthType(Enum):
    pat = 'pat'
    oauth = 'oauth-m2m'


class ConfFetcherRequest(BaseModel):
    job_id: str
    customer_id: str
    task_key: Optional[str] = None
    merge_with: Optional[str] = None


class Config(BaseModel, extra='forbid', use_enum_values=True):
    zipher_api_key_env_var: str = 'ZIPHER_API_KEY'

    databricks_host_env_var: str = 'DATABRICKS_HOST'
    databricks_token_env_var: str = 'DATABRICKS_TOKEN'
    databricks_client_id_env_var: str = 'DATABRICKS_CLIENT_ID'
    databricks_client_secret_env_var: str = 'DATABRICKS_CLIENT_SECRET'

    zipher_config_fetcher_api_endpoint: str = 'https://api.zipher.cloud/default/get_clusterspec'
    zipher_get_optimized_tasks_api_endpoint: str = 'https://api.zipher.cloud/default/get_optimized_tasks'

class GetOptimizedTasksRequest(BaseModel):
    customer_id: str
    job_id: str
    tasks: Optional[str] = None
