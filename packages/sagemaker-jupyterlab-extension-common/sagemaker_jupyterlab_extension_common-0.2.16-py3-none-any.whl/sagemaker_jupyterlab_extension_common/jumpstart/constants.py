from enum import Enum
import os
from sagemaker_jupyterlab_extension_common.constants import DEFAULT_HOME_DIRECTORY
from sagemaker_jupyterlab_extension_common.jumpstart.notebook_types import (
    JumpStartModelNotebookAlterationType,
    JumpStartResourceType,
)

NOTEBOOK_TRANSFORMATION_TYPE = frozenset(
    [
        JumpStartResourceType.inferNotebook,
        JumpStartResourceType.modelSdkNotebook,
        JumpStartResourceType.hyperpodNotebook,
        JumpStartResourceType.novaNotebook,
        JumpStartResourceType.openSourceNotebook,
    ]
)
# Supported serverless model customization techniques
SUPPORTED_CUSTOMIZATION_TECHNIQUES = frozenset(
    [
        "SFT",  # Supervised Fine-Tuning
        "DPO",  # Direct Preference Optimization
        "RLVR",  # Reinforcement Learning from Verifiable Rewards
        "RLAIF",  # Reinforcement Learning from AI Feedback
        "PPO",  # Proximal Policy Optimization
        "CPT",  # Continued Pre-Training
        "DIST",  # Distillation
    ]
)
REMOVAL_OPERATIONS = frozenset(
    [
        JumpStartModelNotebookAlterationType.dropModelSelection,
        JumpStartModelNotebookAlterationType.dropForDeploy,
        JumpStartModelNotebookAlterationType.dropForTraining,
    ]
)

HOME_PATH = os.environ.get("HOME", DEFAULT_HOME_DIRECTORY)
NOTEBOOK_FOLDER = "DemoNotebooks"
NOTEBOOK_PATH = f"{HOME_PATH}/{NOTEBOOK_FOLDER}/"
MD_PATH = "src"
MD_NOTEBOOK_PATH = f"{HOME_PATH}/{MD_PATH}/{NOTEBOOK_FOLDER}/"
MD_UNIFIED_STORAGE_PATH = "shared"
MD_UNIFIED_STORAGE_NOTEBOOK_PATH = (
    f"{HOME_PATH}/{MD_UNIFIED_STORAGE_PATH}/{NOTEBOOK_FOLDER}/"
)


JUMPSTART_ALTERATIONS = "jumpStartAlterations"

CODE_COMMIT_ACCOUNT = "630353334627"

PRIME_ACCESS_POINT_ACCOUNT = "334772094012"
PRIME_ACCESS_POINT_LOCATION = "us-west-2"

FETCH_CODE_COMMIT_CREDENTIALS = """import boto3
import os
import subprocess

# Assume role and get temporary credentials
sts_client = boto3.client("sts")
caller_identity = sts_client.get_caller_identity()
my_account_id = caller_identity['Account']
region_name = boto3.Session().region_name
assumed_role = sts_client.assume_role(
    RoleArn=f"arn:aws:iam::630353334627:role/{my_account_id}_cc-read-only-role",
    RoleSessionName="SageMakerCloneSession"
)
credentials = assumed_role['Credentials']

env = os.environ.copy()
env.update({
    'AWS_ACCESS_KEY_ID': credentials['AccessKeyId'],
    'AWS_SECRET_ACCESS_KEY': credentials['SecretAccessKey'],
    'AWS_SESSION_TOKEN': credentials['SessionToken'],
    'AWS_DEFAULT_REGION': region_name
})
"""

CODE_COMMIT_CLONE_TEMPLATE = """if os.path.exists("Nova-Forge"):
    print("Nova-Forge already exists")
else:
    clone_url = f'https://git-codecommit.{region_name}.amazonaws.com/v1/repos/Nova-Forge'
    subprocess.run([
        'git',
        '-c', 'credential.helper=!aws codecommit credential-helper $@',
        '-c', 'credential.UseHttpPath=true',
        'clone',
        '--recurse-submodules',
        clone_url
    ], env=env)
os.chdir('Nova-Forge')
subprocess.run(['pip', 'install', '-e', '.'])
"""

PUBLIC_REPO_CLONE_TEMPLATE = """import subprocess

if os.path.exists("sagemaker-hyperpod-cli"):
    print("hyperpod cli already installed")
else:
    subprocess.run(['git', 'clone', '--branch', 'release_v2', '--recurse-submodules', 'https://github.com/aws/sagemaker-hyperpod-cli.git'])
 
os.chdir('sagemaker-hyperpod-cli')
subprocess.run(['pip', 'install', '-e', '.'])
"""

# Setup notebook max size based on:
# https://docs.anaconda.com/anaconda-repository/user-guide/tasks/work-with-notebooks/#:~:text=Uploading%20a%20notebook,MAX_IPYNB_SIZE%20variable%20in%20the%20config.
NOTEBOOK_SIZE_LIMIT_IN_BYTES = 26214400  # 25MB
NOTEBOOK_SIZE_LIMIT_IN_MB = NOTEBOOK_SIZE_LIMIT_IN_BYTES / 1048576

CLIENT_REQUEST_ID_HEADER = "X-Client-Req-Id"
SERVER_REQUEST_ID_HEADER = "X-Server-Req-Id"

MISSING_CLIENT_REQUEST_ID = "MISSING_CLIENT_REQUEST_ID"
MISSING_SERVER_REQUEST_ID = "MISSING_SERVER_REQUEST_ID"

# TODO: support RIP.
JUMPSTART_GA_REGIONS = frozenset(
    [
        "eu-north-1",
        "me-south-1",
        "ap-south-1",
        "eu-west-3",
        "us-east-2",
        "af-south-1",
        "eu-west-1",
        "eu-central-1",
        "sa-east-1",
        "ap-east-1",
        "us-east-1",
        "ap-northeast-2",
        "eu-west-2",
        "eu-south-1",
        "ap-northeast-1",
        "us-west-2",
        "us-west-1",
        "ap-southeast-1",
        "ap-southeast-2",
        "ca-central-1",
        "ap-northeast-3",
        "il-central-1",
        "ap-southeast-3",
        "me-central-1",
        "eu-central-2",
        "ap-southeast-5",
        "ap-south-2",
        "ap-southeast-4",
        "ap-southeast-7",
        "ca-west-1",
        "eu-south-2",
        "mx-central-1",
        "us-gov-west-1",
        "us-gov-east-1",
        "cn-north-1",
        "cn-northwest-1",
    ]
)


class ErrorCode(str, Enum):
    NOTEBOOK_NOT_AVAILABLE = "NOTEBOOK_NOT_AVAILABLE"
    NOTEBOOK_SIZE_TOO_LARGE = "NOTEBOOK_SIZE_TOO_LARGE"
    INVALID_REQUEST = "INVALID_REQUEST"
    INTERNAL_SERVER_ERROR = "INTERNAL_SERVER_ERROR"
    DOWNLOAD_DIRECTORY_NOT_FOUND = "DOWNLOAD_DIRECTORY_NOT_FOUND"
    SAGEMAKER_UNIFIED_STUDIO_PROJECT_DIRECTORY_NOT_SET = (
        "SAGEMAKER_UNIFIED_STUDIO_PROJECT_DIRECTORY_NOT_SET"
    )
    SAGEMAKER_UNIFIED_STUDIO_PROJECT_DIRECTORY_INVALID = (
        "SAGEMAKER_UNIFIED_STUDIO_PROJECT_DIRECTORY_INVALID"
    )
    SAGEMAKER_UNIFIED_STUDIO_STORAGE_METADATA_FILE_NOT_FOUND = (
        "SAGEMAKER_UNIFIED_STUDIO_STORAGE_METADATA_FILE_NOT_FOUND"
    )
    PROJECT_STORAGE_METADATA_JSON_DECODE_ERROR = (
        "PROJECT_STORAGE_METADATA_JSON_DECODE_ERROR"
    )


DEFAULT_PYTHON3_KERNEL_SPEC = {
    "display_name": "Python 3 (ipykernel)",
    "language": "python",
    "name": "python3",
}
