import os
import json
from typing import Dict, Optional

import requests
from databricks.sdk.service.compute import ClusterSpec
from zipher.models import ConfFetcherRequest, GetOptimizedTasksRequest, Config
from zipher.exceptions import MissingAPIKeyError

class Client:
    def __init__(self, customer_id: str, zipher_api_key: str = '', config: Optional[Config] = None):
        self.config = config or Config()
        self.zipher_api_key = zipher_api_key or os.getenv(self.config.zipher_api_key_env_var)
        if not self.zipher_api_key:
            raise MissingAPIKeyError(f"Zipher API Key should be provided (either as '{self.config.zipher_api_key_env_var}' env"
                                     f" var or as zipher_api_key param to client constructor).")

        self.customer_id = customer_id

    def _call_conf_fetcher_api(self, params: ConfFetcherRequest):
        headers = {
            'x-api-key': self.zipher_api_key
        }
        response = requests.get(
            url=self.config.zipher_config_fetcher_api_endpoint,
            headers=headers,
            params=params.model_dump()
        )
        if response.ok:
            return response.json()
        else:
            response.raise_for_status()

    def _call_get_optimized_tasks_api(self, params: GetOptimizedTasksRequest):
        headers = {
            'x-api-key': self.zipher_api_key
        }
        response = requests.get(
            url=self.config.zipher_get_optimized_tasks_api_endpoint,
            headers=headers,
            params=params.model_dump()
        )
        if response.ok:
            return response.json()
        else:
            response.raise_for_status()

    def get_optimized_tasks(self, job_id: str, tasks: list[dict]) -> list[dict]:
        params = GetOptimizedTasksRequest(customer_id=self.customer_id, job_id=job_id, tasks=json.dumps(tasks))
        return self._call_get_optimized_tasks_api(params)
    
    def get_optimized_config(self, job_id: str, task_key: Optional[str] = None) -> Dict:
        params = ConfFetcherRequest(customer_id=self.customer_id, job_id=job_id, task_key=task_key)
        return self._call_conf_fetcher_api(params)

    def get_optimized_config_as_dbx_cluster_spec(self, job_id: str) -> ClusterSpec:
        return ClusterSpec.from_dict(self.get_optimized_config(job_id))

    def update_existing_conf(self, job_id: str, existing_conf: Dict, task_key: Optional[str] = None) -> Dict:
        if 'new_cluster' in existing_conf:
            existing_conf = existing_conf['new_cluster']
        params = ConfFetcherRequest(customer_id=self.customer_id, job_id=job_id, merge_with=json.dumps(existing_conf), task_key=task_key)
        try:
            return self._call_conf_fetcher_api(params)
        except:
            return existing_conf
