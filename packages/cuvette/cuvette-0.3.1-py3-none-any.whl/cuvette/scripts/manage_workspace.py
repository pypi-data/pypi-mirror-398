import argparse
import os
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor

from beaker import Beaker
from beaker.exceptions import BeakerPermissionsError

from cuvette.constants.secrets import GENERAL_ENV_SECRETS, GENERAL_FILE_SECRETS, SECRETS_ROOT, USER_ENV_SECRETS, USER_FILE_SECRETS


def create_workspace(name, description=None, public=True):
    beaker = Beaker.from_env()
    
    workspace = beaker.workspace.create(
        name,
        description=description
    )
    
    return workspace


def create():
    parser = argparse.ArgumentParser(
        description="Create a workspace."
    )
    parser.add_argument(
        "-w", "--workspace", type=str, help="Name of the workspace to create."
    )
    args = parser.parse_args()

    workspace = create_workspace(args.workspace)
    
    workspace_suffix = args.workspace.split('/')[-1] # ai2/davidh -> davidh

    print(f"Created: https://beaker.allen.ai/orgs/ai2/workspaces/{workspace_suffix}")


def _sync_secret(bk, workspace_name, entry):
    secret_name = entry['name']
    type = entry['type']
    env = entry.get('env', None)
    path = entry.get('path', None)

    if type == 'env':
        # Read from environment variable
        value = os.environ.get(env)
        if value is None:
            print(f"Warning: Environment variable {env} not found")
            return
    elif type == "file":
        full_path = SECRETS_ROOT / Path(path)

        # Read from file
        try:
            with open(full_path, 'r') as f:
                value = f.read()
        except FileNotFoundError:
            print(f"Warning: File {path} not found")
            return
    else:
        print(f"Warning: Invalid source for secret {secret_name}")
        return

    # remove leading / trailing spaces or newlines
    value = value.strip()
    
    # Write secret to workspace
    try:
        bk.secret.write(
            secret_name,
            value,
            workspace=workspace_name
        )
        print(f"Added: {secret_name}")
    except BeakerPermissionsError as e:
        print(f"\033[31mFailed: {secret_name} ({e})\033[0m")


def sync_secrets(workspace_name, secrets_config):
    beaker = Beaker.from_env()
    
    with ThreadPoolExecutor(max_workers=8) as executor:
        futures = []
        for entry in secrets_config:
            future = executor.submit(_sync_secret, beaker, workspace_name, entry)
            futures.append(future)
        
        # Wait for all tasks to complete
        for future in futures:
            future.result()


def sync():
    parser = argparse.ArgumentParser(
        description="Sync secrets to a Beaker workspace."
    )
    parser.add_argument(
        "--workspace", "-w", type=str, required=True, help="The name of the workspace."
    )
    parser.add_argument(
        "--all", "-a", action="store_true", help="Sync both general and user secrets."
    )
    args = parser.parse_args()
    
    if args.all:
        sync_secrets(args.workspace, GENERAL_FILE_SECRETS + GENERAL_ENV_SECRETS + USER_FILE_SECRETS + USER_ENV_SECRETS)
    else:
        sync_secrets(args.workspace, USER_FILE_SECRETS + USER_ENV_SECRETS)


def list_secrets():
    parser = argparse.ArgumentParser(
        description="List secrets in a Beaker workspace."
    )
    parser.add_argument(
        "--workspace", "-w", type=str, required=True, help="The name of the workspace."
    )
    parser.add_argument(
        "--show_values", "-v", action="store_true", help="Show all values."
    )
    args = parser.parse_args()

    workspace_name = args.workspace

    beaker = Beaker.from_env()
    # Get workspace object first
    workspace = beaker.workspace.get(workspace_name)
    secrets = beaker.secret.list(workspace=workspace)

    for secret in secrets:
        print(secret.name)

        if args.show_values:
            value = beaker.secret.read(secret, workspace=workspace)
            print(value)


def copy_secret():
    parser = argparse.ArgumentParser(
        description="Copy a secret from one Beaker workspace to another."
    )
    parser.add_argument(
        "--from-workspace", "-f", type=str, required=True, help="The source workspace."
    )
    parser.add_argument(
        "--to-workspace", "-t", type=str, required=True, help="The destination workspace."
    )
    parser.add_argument(
        "--secret", "-s", type=str, required=True, help="The name of the secret to copy."
    )
    parser.add_argument(
        "--new-name", "-n", type=str, help="New name for the secret in destination workspace (optional)."
    )
    args = parser.parse_args()

    beaker = Beaker.from_env()
    
    try:
        # Get workspace objects
        from_workspace = beaker.workspace.get(args.from_workspace)
        to_workspace = beaker.workspace.get(args.to_workspace)
        
        # Get the secret object from the source workspace
        secret = beaker.secret.get(args.secret, workspace=from_workspace)
        
        # Read the secret value
        secret_value = beaker.secret.read(secret, workspace=from_workspace)
        
        # Determine the name for the secret in the destination workspace
        destination_name = args.new_name if args.new_name else args.secret
        
        # Write the secret to the destination workspace
        beaker.secret.write(destination_name, secret_value, workspace=to_workspace)
        
        print(f"Copied '{args.secret}': '{args.from_workspace}' -> '{args.to_workspace}' ('{destination_name}')")
        
    except Exception as e:
        print(f"Error copying secret: {e}")
