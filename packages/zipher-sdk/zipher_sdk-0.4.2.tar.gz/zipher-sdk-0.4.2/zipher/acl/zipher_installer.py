import time
from typing import Optional
from multiprocessing.pool import ThreadPool
from datetime import datetime, timedelta

import requests
import databricks
from databricks.sdk.service import iam
from databricks.sdk.errors.platform import ResourceConflict
from databricks.sdk.service.workspace import AclPermission, ObjectInfo
from databricks.sdk.service.jobs import JobAccessControlRequest, JobPermissionLevel
from databricks.sdk.service.catalog import SecurableType, PermissionsChange, Privilege
from databricks.sdk.service.sql import WarehousePermissionLevel, WarehouseAccessControlRequest
from databricks.sdk.service.iam import ServicePrincipal, AccessControlRequest, PermissionLevel, Group
from databricks.sdk.service.compute import ClusterPolicyAccessControlRequest, ClusterPolicyPermissionLevel
from databricks.sdk.service.settings import TokenAccessControlRequest, TokenPermissionLevel, CreateOboTokenResponse

from zipher.exceptions import CredentialsError
from zipher.utils import get_workspace_client, get_warehouses_from_job, get_policies_from_job, \
    create_oauth_secret_for_sp
from zipher.acl.models import InstallerConfig, InstallerUserConfig, JobPermissions, ServicePrincipalTokenType


JOB_PERMISSIONS_MAP = {
    JobPermissions.CAN_VIEW: JobPermissionLevel.CAN_VIEW,
    JobPermissions.CAN_MANAGE: JobPermissionLevel.CAN_MANAGE
}


class ZipherInstaller:
    def __init__(self,
                 host: Optional[str] = None,
                 token: Optional[str] = None,
                 client_id: Optional[str] = None,
                 client_secret: Optional[str] = None,
                 profile: Optional[str] = None,
                 config: Optional[InstallerConfig] = None):

        self.config = config or InstallerConfig()
        self.dbx_client = get_workspace_client(host=host, client_id=client_id, client_secret=client_secret,
                                               token=token, profile=profile)

    def _validate_workspace_client(self):
        try:
            user = self.dbx_client.current_user.me()
            workspace_id = self.dbx_client.get_workspace_id()

            print(f"User '{user.display_name}' authenticated against workspace '{workspace_id}'")

            user_input_continue = input("Do you wish to proceed with Zipher installation? (y/n): ")
            if user_input_continue != 'y':
                exit()

            if user.groups and not any([group.display == 'admins' for group in user.groups]):
                user_input_admin = input(("This user is not a member of 'Admins' group and might not have "
                                          "enough permissions to install Zipher. Do you wish to continue? (y/n): "))
                if user_input_admin != 'y':
                    exit()

        except Exception:
            raise

    def _create_zipher_group(self, group_name: str) -> Group:
        print(f"Creating group '{group_name}'")
        try:
            group_entitlements = [iam.ComplexValue(value=ent) for ent in self.config.zipher_group_entitlements]
            zipher_group = self.dbx_client.groups.create(display_name=group_name, entitlements=group_entitlements)
            print(f"Successfully created group '{group_name}'")

            permissions_to_grant = [TokenAccessControlRequest(group_name=group_name,
                                                              permission_level=TokenPermissionLevel.CAN_USE)]
            self.dbx_client.token_management.update_permissions(access_control_list=permissions_to_grant)
            print(f"Successfully enabled group {group_name} to use tokens")

            return zipher_group
        except ResourceConflict:
            print(f"Group '{group_name}' already exists")
            return [group for group in self.dbx_client.groups.list(filter=f'displayName eq "{group_name}"')][0]
        except databricks.sdk.errors.platform.PermissionDenied:
            raise CredentialsError('Not enough permissions to create new group.')
        except Exception:
            raise

    def _create_zipher_workspace_dir(self, path: str, zipher_group_name: str) -> ObjectInfo:
        print(f"\nCreating workspace directory '{path}'")
        self.dbx_client.workspace.mkdirs(path=path)
        zipher_directory = self.dbx_client.workspace.get_status(path=path)

        self.dbx_client.permissions.set(
            request_object_type="directories",
            request_object_id=str(zipher_directory.object_id),
            access_control_list=[
                AccessControlRequest(group_name="users", permission_level=PermissionLevel.CAN_READ),
                AccessControlRequest(group_name=zipher_group_name, permission_level=PermissionLevel.CAN_MANAGE)
            ]
        )
        print(f"Successfully created workspace directory '{path}'\n")

        return zipher_directory

    def _create_secrets(self, secret_scope_name: str, zipher_group_name: str):
        print(f"Creating secrets scope '{secret_scope_name}'")
        try:
            self.dbx_client.secrets.create_scope(scope=secret_scope_name)
            print(f"Successfully created secrets scope '{secret_scope_name}'\n")
        except databricks.sdk.errors.platform.ResourceAlreadyExists as e:
            print(f"Scope {secret_scope_name} already exists\n")

        self.dbx_client.secrets.put_acl(scope=secret_scope_name, principal="users", permission=AclPermission.READ)

        for _ in range(12):
            self.dbx_client.secrets.put_acl(scope=secret_scope_name, principal=zipher_group_name, permission=AclPermission.MANAGE)
            acls = list(self.dbx_client.secrets.list_acls(secret_scope_name))
            if any([item.principal == zipher_group_name for item in acls]):
                return
            time.sleep(10)

        print('WARNING. Was not able to grant MANAGE permissions to Zipher secrets scope. Skipping...')

    def _get_relevant_job_ids(self, days_back, max_runs, max_jobs):
        print(f"Fetching relevant jobs (might take a few minutes)...")
        start_date = datetime.now() - timedelta(days=days_back)
        start_date_ms_int = int(start_date.timestamp() * 1000)

        jobs = self.dbx_client.jobs.list()
        runs = self.dbx_client.jobs.list_runs(limit=0, start_time_from=start_date_ms_int)

        all_job_ids = set()
        for idx, job in enumerate(jobs):
            if len(all_job_ids) >= max_jobs:
                break
            all_job_ids.add(job.job_id)
        for idx, run in enumerate(runs):
            if idx >= max_runs or len(all_job_ids) >= max_jobs:
                break
            all_job_ids.add(run.job_id)
        return set(list(all_job_ids.copy()))

    def _grant_group_permissions_to_job(self, job_id, group_name, job_permission: JobPermissionLevel):
        try:
            job = self.dbx_client.jobs.get(job_id=int(job_id))

            job_permissions_to_grant = [JobAccessControlRequest(group_name=group_name, permission_level=job_permission)]

            self.dbx_client.jobs.update_permissions(job_id=job_id, access_control_list=job_permissions_to_grant)

            return get_policies_from_job(job), get_warehouses_from_job(job)
        except Exception as e:
            print(f"Failed to provide group {group_name} with '{job_permission.value}' on job_id {job_id} with error: {e}")

            return set(), set()

    def _grant_group_permissions_to_policy(self, policy_id, group_name):
        policy_permissions_to_grant = [ClusterPolicyAccessControlRequest(group_name=group_name,
                                                                         permission_level=ClusterPolicyPermissionLevel.CAN_USE)]
        try:
            self.dbx_client.cluster_policies.update_permissions(cluster_policy_id=policy_id,
                                                                access_control_list=policy_permissions_to_grant)
        except Exception as e:
            print(f"Failed to provide group {group_name} with '{ClusterPolicyPermissionLevel.CAN_USE}' on policy_id {policy_id} with error: {e}")

    def _grant_group_permissions_to_warehouse(self, warehouse_id, group_name):
        warehouse_permissions_to_grant = [WarehouseAccessControlRequest(group_name=group_name,
                                                                        permission_level=WarehousePermissionLevel.CAN_MANAGE)]
        try:
            self.dbx_client.warehouses.update_permissions(warehouse_id=warehouse_id,
                                                          access_control_list=warehouse_permissions_to_grant)
        except Exception as e:
            print(f"Failed to provide group {group_name} with '{WarehousePermissionLevel.CAN_MANAGE.value}' on warehouse_id {warehouse_id} with error: {e}")

    def _enable_job_permissions(self, user_config: InstallerUserConfig):
        if user_config.jobs_list is not None:
            relevant_job_ids = user_config.jobs_list

            if not user_config.jobs_list:
                return
        else:
            relevant_job_ids= self._get_relevant_job_ids(days_back=user_config.days_back,
                                                         max_jobs=user_config.max_jobs,
                                                         max_runs=user_config.max_runs)

        print(f"About to grant Zipher {user_config.jobs_permission} permissions to {len(relevant_job_ids)} jobs")
        with ThreadPool(processes=20) as pool:
            args = [(job_id, self.config.zipher_group_name, JOB_PERMISSIONS_MAP[user_config.jobs_permission]) for job_id in relevant_job_ids]
            results = pool.starmap(self._grant_group_permissions_to_job, args)

        policies = set.union(*[result[0] for result in results])
        if policies and user_config.jobs_permission == JobPermissions.CAN_MANAGE:
            print(f"\nAbout to grant Zipher permissions to {len(policies)} policies...")
            with ThreadPool(processes=10) as pool:
                args = [(policy_id, self.config.zipher_group_name) for policy_id in policies]
                pool.starmap(self._grant_group_permissions_to_policy, args)

        warehouses = set.union(*[result[1] for result in results])
        if warehouses and user_config.jobs_permission == JobPermissions.CAN_MANAGE:
            print(f"\nAbout to grant Zipher permissions to {len(warehouses)} warehouses...")
            with ThreadPool(processes=10) as pool:
                args = [(warehouse_id, self.config.zipher_group_name) for warehouse_id in warehouses]
                pool.starmap(self._grant_group_permissions_to_warehouse, args)

    def _create_service_principal(self, name: str, zipher_group: Group):
        matching_sp = [sp for sp in self.dbx_client.service_principals.list() if sp.display_name == name]
        if matching_sp:
            service_principal = matching_sp[0]
            print(f"\nService principal named {service_principal.display_name} already exists. id={service_principal.id}, application-id={service_principal.application_id}")
            return service_principal

        service_principal = self.dbx_client.service_principals.create(
            display_name=name,
            groups=[iam.ComplexValue(value=zipher_group.id)]
        )
        print(f"\nCreated service principal named {service_principal.display_name} with id={service_principal.id}, application-id={service_principal.application_id}")

        permissions_to_grant = [TokenAccessControlRequest(service_principal_name=service_principal.application_id,
                                                          permission_level=TokenPermissionLevel.CAN_USE)]

        self.dbx_client.token_management.update_permissions(access_control_list=permissions_to_grant)
        print(f"Granted token permissions to service principal named {service_principal.display_name}\n")

        return service_principal

    def _use_existing_service_principal(self, sp_id: str, zipher_group: Group) -> ServicePrincipal:
        """Use an existing service principal and add it to the zipher group with token permissions."""
        sp = self.dbx_client.service_principals.get(id=sp_id)
        print(f"\nUsing existing service principal: {sp.display_name} (id={sp.id})")
        
        # Add existing SP to the zipher group (same as in _create_service_principal)
        existing_groups = [g.value for g in sp.groups] if sp.groups else []
        if zipher_group.id not in existing_groups:
            updated_groups = existing_groups + [zipher_group.id]
            self.dbx_client.service_principals.update(
                id=sp.id,
                display_name=sp.display_name,
                groups=[iam.ComplexValue(value=gid) for gid in updated_groups]
            )
        
        # Grant token permissions (same logic as _create_service_principal lines 214-218)
        permissions_to_grant = [TokenAccessControlRequest(service_principal_name=sp.application_id,
                                                          permission_level=TokenPermissionLevel.CAN_USE)]
        self.dbx_client.token_management.update_permissions(access_control_list=permissions_to_grant)
        print(f"Granted token permissions to existing service principal\n")
        
        return sp

    def _create_oauth_secret_for_sp(self, sp: ServicePrincipal):
        token = self.dbx_client.config.token or self.dbx_client.config.oauth_token().access_token

        url = f'{self.dbx_client.config.host}/api/2.0/accounts/servicePrincipals/{sp.id}/credentials/secrets'
        headers = {
            'Authorization': f'Bearer {token}',
            'Content-Type': 'application/json'
        }
        result = requests.post(url=url, headers=headers).json()

        if 'secret' not in result:
            raise ValueError(repr(result))

        return result

    def _create_token_for_sp(self, sp: ServicePrincipal) -> CreateOboTokenResponse:
        try:
            token = self.dbx_client.token_management.create_obo_token(sp.application_id)
            print(f"Successfully generated token: {token.token_value} for service principal: {sp.display_name}")
            return token
        except databricks.sdk.errors.platform.PermissionDenied:
            print(f"""Permission denied while trying to generate token on behalf of service principal {sp.display_name}.
    Check Account Console and make sure this workspace is enabled on tokens generation for service principals""")
            raise

    def _create_creds_for_sp(self, sp: ServicePrincipal, sp_token_type: ServicePrincipalTokenType):
        if sp_token_type == ServicePrincipalTokenType.OAUTH:
            try:
                # Apparently you can only create OAUTH creds using user-level credentials and not another service principal
                # So we fall back to PAT if this user permissions level is not enough
                oauth_secret = create_oauth_secret_for_sp(dbx_client=self.dbx_client, sp=sp)
                return {
                    'host': self.dbx_client.config.host,
                    'client_id': sp.application_id,
                    'client_secret': oauth_secret['secret']
                }
            except Exception as e:
                print(f'Was not able to generate OAUTH creds with following result: {e}')
                print(f'Falling back to Personal Access Token creation')

        zipher_token = self._create_token_for_sp(sp=sp)
        return {
            'host': self.dbx_client.config.host,
            'token': zipher_token.token_value
        }

    def _add_unity_catalog_permissions(self, sp: ServicePrincipal):
        try:
            self.dbx_client.metastores.current()
        except Exception as e:
            print('This workspace is not Unity Catalog enabled. Skipping...')
            return

        try:
            for schema_name in self.config.unity_catalog_schemas:
                try:
                    self.dbx_client.grants.update(
                        securable_type=SecurableType.SCHEMA,
                        full_name=schema_name,
                        changes=[PermissionsChange(
                            add=[Privilege.USE_SCHEMA],
                            principal=sp.application_id
                        )]
                    )
                except databricks.sdk.errors.platform.NotFound:
                    print(f"Schema {schema_name} does not exist.")
                    continue
            for table_name in self.config.unity_catalog_tables:
                try:
                    self.dbx_client.grants.update(
                        securable_type=SecurableType.TABLE,
                        full_name=table_name,
                        changes=[PermissionsChange(
                            add=[Privilege.SELECT],
                            principal=sp.application_id
                        )]
                    )
                except databricks.sdk.errors.platform.NotFound:
                    print(f"Table {table_name} does not exist.")
                    continue
        except databricks.sdk.errors.platform.PermissionDenied:
            print('This user is not authorized to grant SELECT permissions on Unity Catalog tables. '
                  'This action might require account-level admin credentials.')
            return

    def setup(self, user_config: InstallerUserConfig, skip_approval=False):
        if not skip_approval:
            self._validate_workspace_client()

        print("\nStarting Zipher ACL Setup\n")

        group = self._create_zipher_group(group_name=self.config.zipher_group_name)

        directory = self._create_zipher_workspace_dir(path=self.config.zipher_workspace_dir_path,
                                                      zipher_group_name=self.config.zipher_group_name)

        self._enable_job_permissions(user_config=user_config)

        if user_config.existing_service_principal_id:
            sp = self._use_existing_service_principal(user_config.existing_service_principal_id, group)
        else:
            sp = self._create_service_principal(name=self.config.zipher_service_principal_name,
                                                zipher_group=group)

        self._add_unity_catalog_permissions(sp)

        self._create_secrets(secret_scope_name=self.config.zipher_secret_scope_name,
                             zipher_group_name=self.config.zipher_group_name)

        creds = self._create_creds_for_sp(sp, user_config.service_principal_token_type)

        print("\nFinished Zipher ACL Setup\n")

        return creds

    def clean_resources(self):
        print("Start cleanup...")
        self._delete_group()
        self._delete_sp()
        self._delete_secrets_scope()
        self._delete_workspace_dir()
        print("Finished cleanup")

    def _delete_group(self):
        groups = self.dbx_client.groups.list(filter=f'displayName eq "{self.config.zipher_group_name}"')
        for group in groups:
            print(f">>>>> Deleting group {group.display_name}")
            try:
                self.dbx_client.groups.delete(group.id)
                print(f"<<<<< Successfully deleted group\n")
            except Exception as e:
                print(f"Error while deleting group: {e}")

    def _delete_sp(self):
        sps = self.dbx_client.service_principals.list(filter=f'displayName eq "{self.config.zipher_service_principal_name}"')
        for sp in sps:
            print(f">>>>> Deleting service principal {sp.display_name}")
            try:
                self.dbx_client.service_principals.delete(sp.id)
                print(f"<<<<< Successfully deleted service principal\n")
            except Exception as e:
                print(f"Error while deleting service principal: {e}")

    def _delete_workspace_dir(self):
        print(f">>>>> Deleting workspace directory {self.config.zipher_workspace_dir_path}")
        try:
            self.dbx_client.workspace.delete(path=self.config.zipher_workspace_dir_path, recursive=True)
            print(f"<<<<< Successfully deleted workspace directory\n")
        except Exception as e:
            print(f"Error while deleting workspace dir: {e}")

    def _delete_secrets_scope(self):
        print(f">>>>> Deleting secrets scope {self.config.zipher_secret_scope_name}")
        try:
            self.dbx_client.secrets.delete_scope(self.config.zipher_secret_scope_name)
            print(f"<<<<< Successfully deleted secrets scope\n")
        except Exception as e:
            print(f"Error while deleting secrets scope: {e}")
