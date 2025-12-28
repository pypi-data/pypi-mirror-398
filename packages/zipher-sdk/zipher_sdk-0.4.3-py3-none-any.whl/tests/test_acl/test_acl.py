import os
import time
import json
import base64
from uuid import uuid4
from copy import deepcopy
from unittest import TestCase

from databricks.sdk.service import iam
from databricks.sdk import WorkspaceClient
from databricks.sdk.service.sql import CreateWarehouseRequestWarehouseType, CreateQueryRequestQuery, \
    WarehouseAccessControlRequest, WarehousePermissionLevel
from databricks.sdk.service.workspace import ImportFormat
from databricks.sdk.service.settings import TokenAccessControlRequest, TokenPermissionLevel
from databricks.sdk.service.iam import ServicePrincipal, AccessControlRequest, PermissionLevel
from databricks.sdk.service.compute import ClusterSpec, AwsAttributes, InitScriptInfo, WorkspaceStorageInfo, \
    ClusterLogConf, DbfsStorageInfo
from databricks.sdk.service.jobs import JobPermissions, JobPermissionLevel, \
    JobCluster, RunLifeCycleState, RunResultState, Task, SparkPythonTask, SqlTask, SqlTaskQuery

from zipher.acl.zipher_installer import ZipherInstaller
from zipher.acl.models import InstallerConfig, InstallerUserConfig
from zipher.utils import get_workspace_client, create_oauth_secret_for_sp


class TestACL(TestCase):
    @classmethod
    def setUpClass(cls):
        cls.host = os.environ['DATABRICKS_HOST_TEST']
        cls.admin_dbx: WorkspaceClient = WorkspaceClient(host=cls.host, token=os.environ['DATABRICKS_TOKEN_TEST'])

        cls.test_uuid = uuid4()
        cls.dbfs_test_folder = 'zipher_acl_test'

        # Create a simple service principal that should reflect a non admin user in the client's workspace
        # that created a job which we want to be able to run / update etc...
        cls.sp = cls._create_user_sp()
        cls.job_id = str(cls._create_and_run_sample_job_using_sp(sp=cls.sp))

        cls.installer_config = InstallerConfig(
            zipher_group_name=f'zipher_{cls.test_uuid}',
            zipher_service_principal_name=f'zipher_sp_{cls.test_uuid}',
            zipher_workspace_dir_path=f'/zipher_script_{cls.test_uuid}',
            zipher_secret_scope_name=f'zipher_{cls.test_uuid}'
        )
        cls.installer = ZipherInstaller(host=cls.host, token=os.environ['DATABRICKS_TOKEN_TEST'], config=cls.installer_config)
        zipher_creds = cls.installer.setup(user_config=InstallerUserConfig(jobs_list=[cls.job_id]), skip_approval=True)

        cls.zipher_dbx = get_workspace_client(**zipher_creds)

    @classmethod
    def _create_user_sp(cls):
        print('Creating user-level service principal to run test job with.')
        entitlements = [iam.ComplexValue(value=ent) for ent in ['allow-cluster-create']]
        groups = [iam.ComplexValue(value=g.id) for g in cls.admin_dbx.groups.list() if g.display_name in ['users']]
        sp = cls.admin_dbx.service_principals.create(display_name=f"test_acl_user_sp_{cls.test_uuid}",
                                                     groups=groups,
                                                     entitlements=entitlements)

        permissions_to_grant = [TokenAccessControlRequest(service_principal_name=sp.application_id,
                                                          permission_level=TokenPermissionLevel.CAN_USE)]
        cls.admin_dbx.token_management.update_permissions(access_control_list=permissions_to_grant)
        print(f'Done creating user-level service principal with name "{sp.display_name}".')
        return sp

    @classmethod
    def _create_and_run_sample_job_using_sp(cls, sp: ServicePrincipal):
        print('Creating test job.')
        oauth_secret = create_oauth_secret_for_sp(dbx_client=cls.admin_dbx, sp=sp)
        user_dbx = WorkspaceClient(host=cls.host,
                                   client_id=sp.application_id,
                                   client_secret=oauth_secret['secret'])

        with open('sample_job.py') as sample_job:
            dbfs_job_script_path = f"dbfs:/{cls.dbfs_test_folder}/myspark_{cls.test_uuid}.py"
            contents = base64.b64encode(sample_job.read().encode("utf8"))
            contents = str(contents)[2:-1]
            user_dbx.dbfs.put(dbfs_job_script_path, contents=contents, overwrite=True)

        cls.policy = cls.admin_dbx.cluster_policies.create(
            name=f'acl_test_policy_{cls.test_uuid}',
            definition=json.dumps({
                "instance_pool_id": {
                    "type": "forbidden",
                    "hidden": True
                }
            })
        )
        cls.admin_dbx.permissions.update(
            request_object_type='cluster-policies',
            request_object_id=cls.policy.policy_id,
            access_control_list=[AccessControlRequest(
                service_principal_name=sp.application_id,
                permission_level=PermissionLevel.CAN_USE
            )]
        )

        cls.query = cls.admin_dbx.queries.create(
            query=CreateQueryRequestQuery(
                display_name=f'acl_test_query_{cls.test_uuid}',
                query_text='select 1'
            )
        )
        cls.admin_dbx.permissions.update(
            request_object_type='queries',
            request_object_id=cls.query.id,
            access_control_list=[AccessControlRequest(
                service_principal_name=sp.application_id,
                permission_level=PermissionLevel.CAN_RUN
            )]
        )

        cls.warehouse = cls.admin_dbx.warehouses.create(
            name=f'acl_test_warehouse_{cls.test_uuid}',
            cluster_size='2X-Small',
            enable_serverless_compute=True,
            max_num_clusters=1,
            auto_stop_mins=10,
            warehouse_type=CreateWarehouseRequestWarehouseType.PRO
        )
        cls.admin_dbx.warehouses.wait_get_warehouse_running(id=cls.warehouse.id)
        cls.admin_dbx.warehouses.update_permissions(warehouse_id=cls.warehouse.id,
                                                    access_control_list=[WarehouseAccessControlRequest(
                                                            service_principal_name=sp.application_id,
                                                            permission_level=WarehousePermissionLevel.CAN_USE
                                                        )])

        if 'azuredatabricks' in cls.admin_dbx.config.host:
            spec = ClusterSpec(num_workers=1, spark_version="14.3.x-scala2.12",
                               policy_id=cls.policy.policy_id, node_type_id="Standard_F4")
        else:
            spec = ClusterSpec(aws_attributes=AwsAttributes(ebs_volume_count=1, ebs_volume_size=32),
                               num_workers=1, spark_version="14.3.x-scala2.12", node_type_id="m6g.large",
                               policy_id=cls.policy.policy_id)
        job = user_dbx.jobs.create(
            name=f"test_acl_{cls.test_uuid}",
            job_clusters=[
                JobCluster(
                    job_cluster_key="test_cluster_1",
                    new_cluster=spec
                )
            ],
            tasks=[
                Task(
                    task_key="test_cluster_1",
                    job_cluster_key="test_cluster_1",
                    spark_python_task=SparkPythonTask(python_file=dbfs_job_script_path)
                ),
                Task(
                    task_key="test_sql",
                    sql_task=SqlTask(
                        query=SqlTaskQuery(query_id=cls.query.id),
                        warehouse_id=cls.warehouse.id
                    )
                )
            ]
        )

        print(f'Running job {job.job_id}')
        run_wait = user_dbx.jobs.run_now(job_id=int(job.job_id))
        print(f'Waiting for job {job.job_id} to finish...')
        run = run_wait.result()
        print('Done creating test job.')
        return job.job_id

    def _test_can_manage(self):
        permissions: JobPermissions = self.admin_dbx.jobs.get_permissions(job_id=self.job_id)
        for entity in permissions.access_control_list:
            if entity.group_name == self.installer_config.zipher_group_name:
                for perm in entity.all_permissions:
                    if perm.permission_level == JobPermissionLevel.CAN_MANAGE:
                        return
        assert False, f"Job ID {self.job_id} didn't grant CAN_MANAGE permissions to {self.installer_config.zipher_group_name}"

    def _test_fetch_historical_run(self):
        run = next(self.zipher_dbx.jobs.list_runs(job_id=int(self.job_id), expand_tasks=True))

        cluster_id = run.tasks[0].cluster_instance.cluster_id

        self.zipher_dbx.clusters.get(cluster_id=cluster_id)
        print(f"Successfully tested get historical cluster_id: {cluster_id}")

        self.zipher_dbx.clusters.events(cluster_id=cluster_id)
        print(f"Successfully tested get events historical cluster_id: {cluster_id}")

    def _test_update_job_settings(self):
        job = self.zipher_dbx.jobs.get(job_id=int(self.job_id))

        new_settings = deepcopy(job.settings)
        new_settings.job_clusters[0].new_cluster.num_workers = 2

        self.zipher_dbx.jobs.update(job_id=int(self.job_id), new_settings=new_settings)

        new_job = self.zipher_dbx.jobs.get(job_id=int(self.job_id))
        assert new_job.settings.job_clusters[0].new_cluster.num_workers == 2, 'Job was not updated with new settings'

        new_settings.job_clusters[0].new_cluster.num_workers = 1
        self.zipher_dbx.jobs.update(job_id=int(self.job_id), new_settings=new_settings)

    def _update_job_settings(self):
        job = self.zipher_dbx.jobs.get(job_id=int(self.job_id))
        new_settings = deepcopy(job.settings)

        # Upload zipher secret and put a path to it into job settings
        self.zipher_dbx.secrets.put_secret(scope=self.installer_config.zipher_secret_scope_name,
                                           key='zipher_api_key',
                                           string_value='test_key')
        new_settings.job_clusters[0].new_cluster.spark_env_vars = {
            'ZIPHER_API_KEY': f"{{{{secrets/{self.installer_config.zipher_secret_scope_name}/zipher_api_key}}}}"
        }

        # Upload init_script to workspace and put a path to it into job settings
        with open("init_script.sh", "rb") as init_script:
            self.zipher_dbx.workspace.upload(path=f'{self.installer_config.zipher_workspace_dir_path}/init_script.sh',
                                             content=init_script,
                                             overwrite=True, format=ImportFormat.AUTO)
        new_settings.job_clusters[0].new_cluster.init_scripts = [InitScriptInfo(
            workspace=WorkspaceStorageInfo(
                destination=f'{self.installer_config.zipher_workspace_dir_path}/init_script.sh'
            )
        )]

        # Update log path
        new_settings.job_clusters[0].new_cluster.cluster_log_conf = ClusterLogConf(
            dbfs=DbfsStorageInfo(destination=f'dbfs:/{self.dbfs_test_folder}')
        )

        self.zipher_dbx.jobs.update(job_id=int(self.job_id), new_settings=new_settings)
        print(f"Successfully updated secret and init_script to job_id {self.job_id}")

    def _wait_for_cluster_state_running(self, cluster_id):
        while True:
            cluster_info = self.zipher_dbx.clusters.get(cluster_id=cluster_id)
            state = cluster_info.state.value
            print(f"Cluster state: {state}")

            if state == 'RUNNING':
                print("Cluster is up and running!")
                break
            elif state == 'TERMINATED':
                raise RuntimeError("Cluster terminated unexpectedly.")
            elif state == 'ERROR':
                raise RuntimeError("Cluster failed to start.")

            time.sleep(10)

    def _resize_job(self, cluster_id):
        self.zipher_dbx.clusters.resize(cluster_id=cluster_id, num_workers=2)

        assert self.zipher_dbx.clusters.get(cluster_id=cluster_id).num_workers == 2, "Didn't manage to resize cluster"

    def _wait_for_run_success_end(self, run_id):
        while True:
            run_info = self.zipher_dbx.jobs.get_run(run_id=run_id)
            life_cycle_state = run_info.state.life_cycle_state
            result_state = run_info.state.result_state

            print(f"Job run state: {life_cycle_state}")

            # Check if the job has finished
            if life_cycle_state == RunLifeCycleState.TERMINATED:
                if result_state == RunResultState.SUCCESS:
                    print("Job completed successfully.")
                    return
                elif result_state == RunResultState.FAILED:
                    raise RuntimeError("Job failed with status: FAILED")
                elif result_state == RunResultState.TIMEDOUT:
                    raise RuntimeError("Job failed with status: TIMEDOUT")
                elif result_state == RunResultState.CANCELED:
                    raise RuntimeError("Job was canceled.")

            # Sleep before polling again
            time.sleep(10)

    def _test_init_script_log(self, cluster_id):
        init_script_stdout_files = [
            file
            for file in self.zipher_dbx.dbfs.list(path=f'dbfs:/{self.dbfs_test_folder}/{cluster_id}/init_scripts',
                                                  recursive=True)
            if file.path.endswith('stdout.log')
        ]

        assert init_script_stdout_files, 'No init script logs found'

        script_stdout_content = [
            base64.b64decode(self.zipher_dbx.dbfs.read(file.path).data).decode("utf-8")
            for file in init_script_stdout_files
        ]

        assert any([
            'Zipher init_script test succeeded!' in stdout
            for stdout in script_stdout_content
        ])

    def _test_run_output(self, run_id):
        task_run_id = self.zipher_dbx.jobs.get_run(run_id=run_id).tasks[0].run_id
        task_output = self.zipher_dbx.jobs.get_run_output(run_id=task_run_id).logs

        assert 'Successfully retrieved secret' in task_output

    def _test_new_job_run(self):
        self._update_job_settings()

        run = self.zipher_dbx.jobs.run_now(job_id=int(self.job_id))
        time.sleep(20)
        cluster_id = self.zipher_dbx.jobs.get_run(run.run_id).tasks[0].cluster_instance.cluster_id

        self._wait_for_cluster_state_running(cluster_id=cluster_id)
        self._resize_job(cluster_id=cluster_id)
        self._wait_for_run_success_end(run_id=run.run_id)

        time.sleep(20)
        self._test_init_script_log(cluster_id=cluster_id)
        self._test_run_output(run_id=run.run_id)

    def _test_can_read_policy(self):
        policy_id = self.zipher_dbx.jobs.get(job_id=int(self.job_id)).settings.job_clusters[0].new_cluster.policy_id
        policy = self.zipher_dbx.cluster_policies.get(policy_id=policy_id)

        assert policy

    def _test_cancel_run(self):
        run = self.zipher_dbx.jobs.run_now(job_id=int(self.job_id))
        time.sleep(20)
        cancel_response = self.zipher_dbx.jobs.cancel_run_and_wait(run_id=run.run_id)

        assert cancel_response.status.termination_details.message == "Run cancelled by user", f"Didn't manage to cancel run {run.run_id}"

    def _test_can_store_secret(self):
        self.zipher_dbx.secrets.put_secret(
            scope=self.installer_config.zipher_secret_scope_name,
            key='test_key',
            string_value='test_value'
        )

    def test(self):
        self._test_can_manage()
        self._test_can_read_policy()
        self._test_can_store_secret()
        self._test_fetch_historical_run()
        self._test_update_job_settings()
        self._test_new_job_run()
        self._test_cancel_run()

    @classmethod
    def tearDownClass(cls):
        cls.installer.clean_resources()
        cls.admin_dbx.cluster_policies.delete(policy_id=cls.policy.policy_id)
        cls.admin_dbx.service_principals.delete(id=cls.sp.id)
        cls.admin_dbx.jobs.delete(job_id=int(cls.job_id))
        cls.admin_dbx.dbfs.delete(path=f'dbfs:/{cls.dbfs_test_folder}', recursive=True)
        cls.admin_dbx.queries.delete(cls.query.id)
        cls.admin_dbx.warehouses.delete(cls.warehouse.id)


class TestExistingServicePrincipal(TestCase):
    """Separate test class for testing existing_service_principal_id without running expensive setUpClass."""
    
    @classmethod
    def setUpClass(cls):
        cls.host = os.environ['DATABRICKS_HOST_TEST']
        cls.admin_dbx: WorkspaceClient = WorkspaceClient(host=cls.host, token=os.environ['DATABRICKS_TOKEN_TEST'])
        
        cls.test_uuid = uuid4()
        entitlements = [iam.ComplexValue(value=ent) for ent in ['allow-cluster-create']]
        groups = [iam.ComplexValue(value=g.id) for g in cls.admin_dbx.groups.list() if g.display_name in ['users']]
        cls.sp = cls.admin_dbx.service_principals.create(display_name=f"test_existing_sp_{cls.test_uuid}",
                                                         groups=groups,
                                                         entitlements=entitlements)
        
        permissions_to_grant = [TokenAccessControlRequest(service_principal_name=cls.sp.application_id,
                                                          permission_level=TokenPermissionLevel.CAN_USE)]
        cls.admin_dbx.token_management.update_permissions(access_control_list=permissions_to_grant)
    
    def test_existing_service_principal(self):
        """Test that setup uses existing service principal when existing_service_principal_id is provided and doesn't create a new one."""
        test_uuid = uuid4()
        zipher_sp_name = f'zipher_sp_existing_{test_uuid}'
        
        installer_config = InstallerConfig(
            zipher_group_name=f'zipher_existing_sp_{test_uuid}',
            zipher_service_principal_name=zipher_sp_name,
            zipher_workspace_dir_path=f'/zipher_script_existing_{test_uuid}',
            zipher_secret_scope_name=f'zipher_existing_{test_uuid}'
        )
        installer = ZipherInstaller(host=self.host, token=os.environ['DATABRICKS_TOKEN_TEST'], config=installer_config)
        
        user_config = InstallerUserConfig(
            jobs_list=[],
            existing_service_principal_id=self.sp.application_id
        )
        zipher_creds = installer.setup(user_config=user_config, skip_approval=True)
        
        assert zipher_creds is not None, "Setup should return credentials"
        zipher_sps = [sp for sp in self.admin_dbx.service_principals.list() if sp.display_name == zipher_sp_name]
        assert len(zipher_sps) == 0, "Should not create new SP when using existing_service_principal_id"
        
        # Verify existing SP is in the zipher group
        group = [g for g in self.admin_dbx.groups.list() if g.display_name == installer_config.zipher_group_name][0]
        group_details = self.admin_dbx.groups.get(id=group.id)
        sp_in_group = any(member.value == self.sp.id for member in (group_details.members or []))
        assert sp_in_group, f"Existing SP {self.sp.id} should be in group {installer_config.zipher_group_name}"
        
        # Verify existing SP has token permissions
        token_perms = self.admin_dbx.token_management.get_permissions()
        sp_has_token_perms = any(
            hasattr(perm, 'service_principal_name') and perm.service_principal_name == self.sp.application_id
            for perm in token_perms.access_control_list
        )
        assert sp_has_token_perms, f"Existing SP {self.sp.application_id} should have token permissions"
        
        installer.clean_resources()
    
    @classmethod
    def tearDownClass(cls):
        cls.admin_dbx.service_principals.delete(id=cls.sp.id)
