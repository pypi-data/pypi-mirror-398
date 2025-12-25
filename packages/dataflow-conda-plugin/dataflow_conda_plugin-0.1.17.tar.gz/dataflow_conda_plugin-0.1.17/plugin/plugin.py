import subprocess, sys, pkg_resources, os, requests, re, sys
from conda import plugins
from conda.base.context import context
from dataflow.utils.logger import CustomLogger
from dataflow.configuration import ConfigurationManager

logger = CustomLogger().get_logger(__name__)
dataflow_config = ConfigurationManager('/dataflow/app/auth_config/dataflow_auth.cfg')

env_api = dataflow_config.get_config_value('auth', 'env_api')

def is_local_environment(target_prefix):
    """Check if the environment is a local user environment."""
    return (
        os.environ.get('HOSTNAME') is not None and 
        target_prefix and 
        target_prefix.startswith('/home/jovyan')
    )

def save_environment(env_name: str, status: str):
    """Save environment information via API."""
    try:
        response = requests.post(
            env_api,
            params={
                "env_name": env_name,
                "status": status
            },
            timeout=30
        )
        
        if response.status_code in [200, 201]:
            logger.info(f"Environment '{env_name}' saved successfully")
        else:
            logger.error(f"Error saving environment: {response.status_code} - {response.text}")
            print("Error saving environment! Please try again after deleting the environment")
            
    except requests.exceptions.RequestException as e:
        logger.error(f"Network error saving environment: {str(e)}")
        print("Error saving environment! Please check your connection and try again")
    except Exception as e:
        logger.error(f"Unexpected error saving environment: {str(e)}")
        print("Error saving environment! Please try again after deleting the environment")

def install_deps(command: str):
    """Install dataflow dependencies."""
    target_prefix = context.target_prefix
    args = context._argparse_args
    python_version = args.get("python") 
    print(f"Installing Dataflow dependencies in the environment with Python version: {python_version}")
    env_name = os.path.basename(target_prefix) if target_prefix else None

    should_save_to_db = is_local_environment(target_prefix) and env_name

    try:
        if (args.get('clone') is not None):
            if should_save_to_db:
                save_environment(env_name, "Success")
            return
        
        if env_name and should_save_to_db:
            save_environment(env_name, "Success")
        
        install_dataflow_deps = pkg_resources.resource_filename('plugin', 'scripts/install_dataflow_deps.sh')
        process = subprocess.Popen(
            ["bash", install_dataflow_deps, target_prefix],
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            bufsize=1
        )
        
        for line in iter(process.stdout.readline, ''):
            print(line, end='')
            sys.stdout.flush()
        
        return_code = process.wait()
        if return_code != 0:
            print(f"Error in creating environment!!")
            if should_save_to_db and env_name:
                save_environment(env_name, "Failed")
            raise RuntimeError(f"Dataflow dependency installation failed! Please make sure compatible python version is used")
        else:
            if env_name and should_save_to_db:
                save_environment(env_name, "Success")

    except Exception as e:
        print(f"An unexpected error occurred: {str(e)}\nPlease delete the environment and try again.")
        logger.error(f"Error installing dependencies: {str(e)}")
        if should_save_to_db and env_name:
            save_environment(env_name, "Failed")
        raise e

def remove_environment(env_name: str):
    """Remove environment information via API."""
    try:
        response = requests.delete(
            env_api,
            params={"env_name": env_name},
            timeout=30
        )
        
        if response.status_code == 200:
            logger.info(f"Environment '{env_name}' removed successfully")
        elif response.status_code == 404:
            logger.warning(f"Environment '{env_name}' not found")
        else:
            logger.error(f"Error removing environment: {response.status_code} - {response.text}")
            print("Error removing environment! Please delete from the dataflow environment page")
            
    except requests.exceptions.RequestException as e:
        logger.error(f"Network error removing environment: {str(e)}")
        print("Error removing environment! Please delete from the dataflow environment page")
    except Exception as e:
        logger.error(f"Unexpected error removing environment: {str(e)}")
        print("Error removing environment! Please delete from the dataflow environment page")

def mark_environment_for_refresh(env_name: str):
    """Mark environment for refresh via API."""
    try:
        response = requests.put(
            env_api,
            params={"env_name": env_name},
            json={"need_refresh": True},
            timeout=30
        )
        
        if response.status_code == 200:
            logger.info(f"Environment '{env_name}' marked for refresh")
        else:
            logger.error(f"Error marking environment for refresh: {response.status_code} - {response.text}")

    except requests.exceptions.RequestException as e:
        logger.error(f"Network error marking environment for refresh: {str(e)}")
    except Exception as e:
        logger.error(f"Unexpected error marking environment for refresh: {str(e)}")

def package_operations(command: str):
    """Track conda install/remove/update commands for packages and update libraries in database."""
    target_prefix = context.target_prefix
    env_name = os.path.basename(target_prefix) if target_prefix else None

    # to catch env removal
    if not os.path.exists(target_prefix):
        if is_local_environment(target_prefix) and env_name:
            remove_environment(env_name)
        return

    should_update_db = is_local_environment(target_prefix) and env_name

    if should_update_db:
        mark_environment_for_refresh(env_name)

def set_pip_constraint(command: str):
    """Set PIP_CONSTRAINT environment variable based on Python version."""
    if "NO_CONDA_PLUGIN_PIP_CONSTRAINT" in os.environ:
        return
    for arg in sys.argv:
        if arg.startswith("python"):
            # Match python=3.10, python=3.10.1, python=3.11, python=3.11.5, etc.
            match = re.fullmatch(r"python=(3\.10(\.\d+)?|3\.11(\.\d+)?|3\.12(\.\d+)?)", arg)
            if not match:
                raise ValueError(f"Invalid argument: {arg}! Only Python 3.10, 3.11, and 3.12 are supported.")
            version = match.group(1)
            major_minor = ".".join(version.split(".")[:2])
            break
    else:
        major_minor = "3.12"
    # Set PIP_CONSTRAINT environment variable to the appropriate constraint file
    os.environ["PIP_CONSTRAINT"] = f"/dataflow/tmp/pip_constraints/py{major_minor}-constraints.txt"


@plugins.hookimpl
def conda_post_commands():
    yield plugins.CondaPostCommand(
        name=f"install_deps_post_command",
        action=install_deps,
        run_for={"create", "env_create"},
    )
    yield plugins.CondaPostCommand(
        name=f"package_operations_post_command",
        action=package_operations,
        run_for={"install", "remove", "update"},
    )

@plugins.hookimpl
def conda_pre_commands():
    yield plugins.CondaPreCommand(
        name="set_pip_constraint",
        action=set_pip_constraint,
        run_for={"create"},
    )