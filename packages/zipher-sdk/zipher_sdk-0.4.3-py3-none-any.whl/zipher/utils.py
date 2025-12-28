from typing import Union, Optional

import requests
from databricks.sdk import WorkspaceClient
from databricks.sdk.service.jobs import Job, BaseJob
from databricks.sdk.service.iam import ServicePrincipal

from zipher.exceptions import CredentialsError
from zipher.models import WorkspaceClientAuthType


def get_workspace_client(host, client_id: Optional[str] = None, client_secret: Optional[str] = None,
                         token: Optional[str] = None, profile: Optional[str] = None) -> WorkspaceClient:
    try:
        if host and client_id and client_secret:
            client = WorkspaceClient(host=host, client_id=client_id, client_secret=client_secret,
                                     auth_type=WorkspaceClientAuthType.oauth.value)
        elif host and token:
            client = WorkspaceClient(host=host, token=token, auth_type=WorkspaceClientAuthType.pat.value)
        else:
            client = WorkspaceClient(profile=profile)

        client.get_workspace_id()

        return client
    except Exception as e:
        raise CredentialsError('Not able to authenticate with provided credentials.')


def create_oauth_secret_for_sp(dbx_client: WorkspaceClient, sp: ServicePrincipal):
    token = dbx_client.config.token or dbx_client.config.oauth_token().access_token

    url = f'{dbx_client.config.host}/api/2.0/accounts/servicePrincipals/{sp.id}/credentials/secrets'
    headers = {
        'Authorization': f'Bearer {token}',
        'Content-Type': 'application/json'
    }
    result = requests.post(url=url, headers=headers).json()

    if 'secret' not in result:
        raise ValueError(repr(result))

    return result


def get_policies_from_job(job: Union[Job, BaseJob]):
    policies = set()
    if job.settings.job_clusters:
        for cluster in job.settings.job_clusters:
            if cluster.new_cluster.policy_id:
                policies.add(cluster.new_cluster.policy_id)

    for task in job.settings.tasks:
        if task.new_cluster and task.new_cluster.policy_id:
            policies.add(task.new_cluster.policy_id)

    return policies


def get_warehouses_from_job(job: Union[Job, BaseJob]):
    warehouses = set()

    for task in job.settings.tasks:
        if task.sql_task:
            warehouses.add(task.sql_task.warehouse_id)

    return warehouses
