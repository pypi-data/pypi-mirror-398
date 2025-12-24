import boto3
import os
import logging
import botocore.exceptions
from typing import Optional, Dict, Any

from sagemaker_jupyterlab_extension_common.jumpstart.constants import (
    PRIME_ACCESS_POINT_ACCOUNT,
    PRIME_ACCESS_POINT_LOCATION,
)

"""
Check out this quip for Nova Prime validation mechanism
https://quip-amazon.com/iarYAdjaXWpe/Nova-Prime-Validation-in-Studio-and-Maxdome
"""


def _check_s3_prime_access(
    session: boto3.Session, model_id: str, region: str, account_id: str, caller_arn: str
) -> bool:
    """
    Helper function to perform the actual S3 prime access check using a given boto3 session.
    """
    ACCESS_POINT_NAME = f"advanced-model-customization-recipes-{account_id}"
    access_point_arn = f"arn:aws:s3:{PRIME_ACCESS_POINT_LOCATION}:{PRIME_ACCESS_POINT_ACCOUNT}:accesspoint/{ACCESS_POINT_NAME}"
    object_key = f"{account_id}/advanced-access.json"

    logging.info(f"Attempting S3 GetObject for ARN: {caller_arn}")

    try:
        s3_client = session.client("s3", region_name=region)
        s3_client.get_object(Bucket=access_point_arn, Key=object_key)
        logging.info(
            f"Prime access VERIFIED for ARN: {caller_arn} in account {account_id}."
        )
        return True
    except botocore.exceptions.ClientError as e:
        error_code = e.response.get("Error", {}).get("Code", "Unknown")
        error_message = e.response.get("Error", {}).get("Message", str(e))

        logging.warning(
            f"Prime access check FAILED for ARN: {caller_arn} in account {account_id}. "
            f"Error Code: {error_code}, Message: {error_message}"
        )

        if error_code == "AccessDenied":
            logging.warning(
                "ACTION REQUIRED: The role used (or the policy on the Access Point) "
                "does not have 's3:GetObject' permissions on the S3 Access Point. "
                "Check the Access Point Policy and the IAM Policy of the accessing role."
            )
        elif error_code == "NoSuchKey":
            logging.warning(
                f"ACTION REQUIRED: The object '{object_key}' does NOT exist in the S3 bucket "
                f"behind access point '{ACCESS_POINT_NAME}'."
            )
        elif error_code == "NoSuchBucket":
            logging.warning(
                f"ACTION REQUIRED: The S3 Access Point '{ACCESS_POINT_NAME}' itself or its association "
                f"with the underlying bucket might be incorrect or missing in region {PRIME_ACCESS_POINT_LOCATION} for "
                f"account {PRIME_ACCESS_POINT_ACCOUNT}."
            )
        return False
    except Exception as e:
        logging.error(
            f"Unexpected error during S3 prime status check for ARN {caller_arn}: {e}"
        )
        return False


def _get_datazone_connection_details(
    domain: str, connection_id: str, region: str
) -> Optional[Dict[str, Any]]:
    """
    Fetches DataZone connection details.

    Returns:
        Optional[Dict[str, Any]]: The connection details if successful, None otherwise.
    """
    try:
        datazone_client = boto3.client("datazone", region_name=region)
        connection_details: Dict[str, Any] = datazone_client.get_connection(
            identifier=connection_id, domainIdentifier=domain, withSecret=True
        )
        logging.info(f"Successfully retrieved DataZone connection details.")

        if (
            "physicalEndpoints" not in connection_details
            or not connection_details["physicalEndpoints"]
        ):
            logging.warning(
                "No physicalEndpoints found for DataZone connection. Cannot determine target account/region for S3 access."
            )
            return None

        aws_location = connection_details["physicalEndpoints"][0].get("awsLocation")
        if not aws_location:
            logging.warning(
                "No awsLocation found in physicalEndpoints for DataZone connection. Cannot determine target account/region for S3 access."
            )
            return None

        return connection_details
    except botocore.exceptions.ClientError as e:
        logging.error(
            f"Failed to get DataZone connection details. Ensure the calling role has 'datazone:GetConnection' permissions. Error: {e}"
        )
        return None
    except Exception as e:
        logging.error(
            f"Unexpected error while fetching DataZone credentials or details: {e}"
        )
        return None


def _check_connection_role_prime_access(
    connection_details: Dict[str, Any], model_id: str, current_session_region: str
) -> bool:
    """
    Checks if the DataZone connection role has prime access.
    """
    connection_account_id = connection_details["physicalEndpoints"][0]["awsLocation"][
        "awsAccountId"
    ]
    connection_region = connection_details["physicalEndpoints"][0]["awsLocation"].get(
        "awsRegion", current_session_region
    )
    if "connectionCredentials" not in connection_details:
        logging.error("No 'connectionCredentials' found for DataZone connection role.")
        return False

    credentials = connection_details["connectionCredentials"]
    access_key_id = credentials.get("accessKeyId")
    secret_access_key = credentials.get("secretAccessKey")
    session_token = credentials.get("sessionToken")

    if not (access_key_id and secret_access_key and session_token):
        logging.error(
            "Missing credentials in DataZone connectionCredentials for connection role."
        )
        return False

    try:
        connection_session = boto3.Session(
            aws_access_key_id=access_key_id,
            aws_secret_access_key=secret_access_key,
            aws_session_token=session_token,
            region_name=connection_region,
        )
        sts_connection_client = connection_session.client(
            "sts", region_name=connection_region
        )
        connection_caller_identity = sts_connection_client.get_caller_identity()
        connection_role_arn = connection_caller_identity["Arn"]
        logging.debug(f"Identified DataZone Connection Role ARN: {connection_role_arn}")

        return _check_s3_prime_access(
            session=connection_session,
            model_id=model_id,
            region=connection_region,
            account_id=connection_account_id,
            caller_arn=connection_role_arn,
        )
    except botocore.exceptions.ClientError as e:
        logging.error(
            f"Failed to get caller identity or check prime access for DataZone connection role: {e}"
        )
        return False
    except Exception as e:
        logging.error(f"Unexpected error during connection role S3 check: {e}")
        return False


def _check_project_role_prime_access(
    connection_details: Dict[str, Any], model_id: str, current_session_region: str
) -> bool:
    """
    Checks if the project role (environmentUserRole) has prime access using the current session.
    """
    project_role_arn = connection_details.get("environmentUserRole")
    if not project_role_arn:
        logging.error(
            "Could not find 'environmentUserRole' (project role) in DataZone connection details. This role is required."
        )
        return False

    connection_account_id = connection_details["physicalEndpoints"][0]["awsLocation"][
        "awsAccountId"
    ]
    connection_region = connection_details["physicalEndpoints"][0]["awsLocation"].get(
        "awsRegion", current_session_region
    )

    logging.info(f"Checking prime access for the Project Role: {project_role_arn}.")
    try:
        current_session = boto3.Session(region_name=current_session_region)
        sts_current_client = current_session.client(
            "sts", region_name=current_session_region
        )
        current_caller_identity = sts_current_client.get_caller_identity()
        current_caller_arn = current_caller_identity["Arn"]

        return _check_s3_prime_access(
            session=current_session,
            model_id=model_id,
            region=connection_region,
            account_id=connection_account_id,
            caller_arn=current_caller_arn,
        )
    except botocore.exceptions.ClientError as e:
        logging.error(
            f"Failed to check prime access for the Project Role '{project_role_arn}' using current credentials: {e}"
        )
        return False
    except Exception as e:
        logging.error(f"Unexpected error during Project Role S3 check: {e}")
        return False


def _check_direct_prime_status(model_id: str, region: str) -> bool:
    """
    Checks prime status using the current environment/calling role's credentials.
    """
    logging.info(
        "No DataZone domain/connection ID provided. Checking prime status using current environment/calling role credentials."
    )
    try:
        current_session = boto3.Session(region_name=region)
        sts_client = current_session.client("sts", region_name=region)
        caller_identity = sts_client.get_caller_identity()
        account_id = caller_identity["Account"]
        caller_arn = caller_identity["Arn"]
        logging.debug(
            f"Current Calling Role ARN: {caller_arn} for account: {account_id}"
        )

        return _check_s3_prime_access(
            session=current_session,
            model_id=model_id,
            region=region,
            account_id=account_id,
            caller_arn=caller_arn,
        )
    except botocore.exceptions.ClientError as e:
        logging.error(
            f"Could not determine AWS Account ID/Caller ARN for inherited credentials. Error: {e}"
        )
        return False
    except Exception as e:
        logging.error(
            f"Unexpected error during prime status check with inherited credentials: {e}"
        )
        return False


def check_prime_status(
    model_id: str,
    region: str,
    domain: Optional[str] = None,
    connection_id: Optional[str] = None,
) -> bool:
    """
    Checks for prime status.

    If domain and connection_id are provided:
        1. Fetches temporary credentials for the DataZone connection role.
        2. Checks if this connection role has prime access.
        3. Identifies the project role (environmentUserRole) ARN.
        4. Since the script's calling role is the project role, it reuses its existing session
           to check the project role's prime access.
        5. Returns True only if *both* have prime access.
    Otherwise (if domain and connection_id are NOT provided):
        1. Uses the current environment/calling role's credentials.
        2. Checks if this calling role has prime access.
        3. Returns True if it has prime access.

    Args:
        model_id (str): The ID of the model to check access for.
        region (str): The AWS region to perform the check in.
        domain (Optional[str]): The AWS DataZone domain ID.
        connection_id (Optional[str]): The AWS DataZone connection ID.

    Returns:
        bool: True if the required roles have prime access, False otherwise.
    """
    if domain and connection_id:
        logging.info(
            f"Checking prime status using DataZone connection: {connection_id} in domain: {domain}"
        )

        connection_details = _get_datazone_connection_details(
            domain, connection_id, region
        )
        if not connection_details:
            return False

        # Extract connection_account_id and connection_region here to pass to subsequent functions
        aws_location = connection_details["physicalEndpoints"][0]["awsLocation"]
        connection_account_id = aws_location.get("awsAccountId")
        connection_region = aws_location.get("awsRegion", region)

        if not connection_account_id or not connection_region:
            logging.warning(
                "Failed to determine DataZone connection target account or region."
            )
            return False

        connection_role_has_prime_access = _check_connection_role_prime_access(
            connection_details, model_id, region
        )
        project_role_has_prime_access = _check_project_role_prime_access(
            connection_details, model_id, region
        )

        if connection_role_has_prime_access and project_role_has_prime_access:
            logging.info(
                "Both DataZone Connection Role AND Project Role have prime access."
            )
            return True
        else:
            logging.warning(
                f"One or both roles lack prime access: "
                f"Connection Role Access: {connection_role_has_prime_access}, "
                f"Project Role Access: {project_role_has_prime_access}."
            )
            return False
    else:
        return _check_direct_prime_status(model_id, region)
