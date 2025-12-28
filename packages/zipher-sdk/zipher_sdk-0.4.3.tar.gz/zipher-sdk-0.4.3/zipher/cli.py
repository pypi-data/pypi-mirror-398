import os
import argparse
import traceback

import databricks.sdk.errors.platform

from zipher.acl.models import InstallerUserConfig, JobPermissions, ServicePrincipalTokenType
from zipher.acl.zipher_installer import ZipherInstaller


def comma_separated_list(value):
    return [job_id.strip() for job_id in value.split(',')]


def main():
    parent_parser = argparse.ArgumentParser(add_help=False)
    parent_parser.add_argument(
        "--workspace-host",
        type=str,
        default=None,
        help="Databricks workspace host URL."
    )

    parent_parser.add_argument(
        "--access-token",
        type=str,
        default=None,
        help="Databricks workspace access token."
    )

    parent_parser.add_argument(
        "--client-id",
        type=str,
        default=None,
        help="Databricks workspace OAuth client id."
    )

    parent_parser.add_argument(
        "--client-secret",
        type=str,
        default=None,
        help="Databricks workspace OAuth client secret."
    )

    parent_parser.add_argument(
        "--profile",
        type=str,
        default=None,
        help="Profile name from .databrickscfg."
    )

    parent_parser.add_argument(
        "--verbose",
        action='store_true',
        help="Print full error message on fail."
    )

    parser = argparse.ArgumentParser(prog="zipher", description="Zipher CLI", parents=[parent_parser], add_help=False)
    subparsers = parser.add_subparsers(dest="command", required=True)
    setup_parser = subparsers.add_parser("setup", help="Perform a full Zipher installation.", parents=[parent_parser])

    setup_parser.add_argument(
        "--jobs-list",
        type=comma_separated_list,
        default=None,
        help="Comma-separated list of jobs ids to provide access to."
    )

    setup_parser.add_argument(
        "--max-jobs",
        type=int,
        default=2000,
        help="Maximum number of jobs to consider when iterating over jobs to grant permissions (default: 2000)."
    )

    setup_parser.add_argument(
        "--max-runs",
        type=int,
        default=2000,
        help="Maximum number of runs to consider when iterating over runs to grant permissions to relative jobs (default: 2000)."
    )

    setup_parser.add_argument(
        "--days-back",
        type=int,
        default=7,
        help="How many days back to fetch relevant job runs for permission updates (default: 7)."
    )

    setup_parser.add_argument(
        "--readonly",
        action='store_true',
        help=("Provide Zipher with only CAN_VIEW permissions on listed jobs. "
              "When not provided will default to CAN_MANAGE permissions.")
    )

    setup_parser.add_argument(
        "--pat",
        action='store_true',
        help="Generate Personal Access Token for Zipher instead of default OAuth client creds."
    )

    setup_parser.add_argument(
        "--skip-approval",
        action='store_true',
        help="Skip user input approval."
    )

    setup_parser.add_argument(
        "--existing-sp-id",
        type=str,
        default=None,
        help="Use existing service principal by Application ID (UUID) instead of creating a new one."
    )

    remove_parser = subparsers.add_parser("remove", help="Remove Zipher resources from the workspace.", parents=[parent_parser])

    args = parser.parse_args()

    host = args.workspace_host or os.environ.get("ZIPHER_DATABRICKS_HOST")
    token = args.access_token or os.environ.get("ZIPHER_DATABRICKS_TOKEN")
    client_id = args.client_id or os.environ.get('ZIPHER_DATABRICKS_CLIENT_ID')
    client_secret = args.client_secret or os.environ.get('ZIPHER_DATABRICKS_CLIENT_SECRET')
    profile = args.profile

    try:
        zipher_acl = ZipherInstaller(host=host, token=token, client_id=client_id,
                                     client_secret=client_secret, profile=profile)

        if args.command == "setup":
            config = InstallerUserConfig(
                days_back=args.days_back,
                max_jobs=args.max_jobs,
                max_runs=args.max_runs,
                jobs_list=args.jobs_list,
                jobs_permission=JobPermissions.CAN_VIEW if args.readonly else JobPermissions.CAN_MANAGE,
                service_principal_token_type=ServicePrincipalTokenType.PERSONAL_ACCESS_TOKEN if args.pat else ServicePrincipalTokenType.OAUTH,
                existing_service_principal_id=args.existing_sp_id
            )

            zipher_token = zipher_acl.setup(user_config=config, skip_approval=args.skip_approval)
            if zipher_token:
                print(f"\nZipher setup complete. Credentials for Zipher service principal:\n{zipher_token}")
            else:
                print("Something went wrong. Credentials for Zipher were not generated.")
        elif args.command == "remove":
            zipher_acl.clean_resources()
    except databricks.sdk.errors.platform.PermissionDenied:
        print('Unexpected error: Not enough permissions to install Zipher.')

        if args.verbose:
            traceback.print_exc()
    except Exception as e:
        print(f"Unexpected error: {e}")

        if args.verbose:
            traceback.print_exc()


if __name__ == "__main__":
    main()