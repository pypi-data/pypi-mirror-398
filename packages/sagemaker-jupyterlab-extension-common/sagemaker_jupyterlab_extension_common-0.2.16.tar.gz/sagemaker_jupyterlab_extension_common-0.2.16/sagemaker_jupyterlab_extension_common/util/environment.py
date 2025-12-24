import json
from enum import Enum
import logging

from sagemaker_jupyterlab_extension_common.clients import get_sagemaker_client

logging.basicConfig(format="%(levelname)s: %(message)s", level=logging.INFO)


class Environment(Enum):
    STUDIO_SSO = "STUDIO_SSO"
    STUDIO_IAM = "STUDIO_IAM"
    MD = "MD"
    MD_IDC = "MD_IDC"
    MD_IAM = "MD_IAM"
    MD_SAML = "MD_SAML"
    UNKNOWN = "UNKNOWN"


class EnvironmentDetector:
    _cached_env = None

    @classmethod
    async def get_environment(cls):
        """
        Detects the environment in which the code is running. This is done by checking for the presence of
        certain files and environment variables. The result is cached for subsequent calls.
        :return: Environment - The environment in which the code is running.
        :rtype: Environment
        """

        if cls._cached_env is None:
            detected_env = await cls._detect_environment()
            if detected_env != Environment.UNKNOWN:
                cls._cached_env = detected_env
        else:
            detected_env = cls._cached_env

        logging.info(f"Environment is {detected_env}")
        return detected_env

    @classmethod
    def clear_env_cache(cls):
        logging.info("Clearing cached environment")
        cls._cached_env = None

    @classmethod
    async def _detect_environment(cls):
        try:
            with open("/opt/ml/metadata/resource-metadata.json", "r") as f:
                data = json.load(f)
                if (
                    "AdditionalMetadata" in data
                    and "DataZoneScopeName" in data["AdditionalMetadata"]
                ):
                    try:
                        with open(
                            "/home/sagemaker-user/.aws/amazon_q/settings.json"
                        ) as g:
                            settings = json.load(g)
                            logging.info("MD auth_mode: " + settings.get("auth_mode"))
                            auth_mode = settings.get("auth_mode")
                            if auth_mode == "IAM":
                                return Environment.MD_IAM
                            elif auth_mode == "IDC":
                                return Environment.MD_IDC
                            elif auth_mode == "SAML":
                                return Environment.MD_SAML
                            else:
                                return Environment.MD_IAM
                    except Exception:
                        # return MD_IAM by default if settings file cannot be read
                        return Environment.MD_IAM
                elif "ResourceArn" in data:
                    sm_domain_id = data["DomainId"]
                    logging.info(f"DomainId - {sm_domain_id}")
                    sm_client = get_sagemaker_client()
                    domain_details = await sm_client.describe_domain(sm_domain_id)
                    logging.debug(f"Studio domain level details: {domain_details}")
                    is_q_enabled = cls.is_q_enabled_studio_domain(domain_details)
                    logging.info(f"is_q_enabled: {is_q_enabled}")
                    if is_q_enabled and domain_details.get("AuthMode") == "SSO":
                        return Environment.STUDIO_SSO
                    # always return free tier even if it is SSO mode
                    # admins can control the usage through IAM policy
                    # This should not affect MD as they are already detected and returned
                    return Environment.STUDIO_IAM
        except Exception as e:
            logging.error(f"Error detecting environment: {e}")
        return Environment.UNKNOWN

    @classmethod
    def is_md_environment(cls):
        if cls._cached_env is None:
            try:
                with open("/opt/ml/metadata/resource-metadata.json", "r") as f:
                    data = json.load(f)
                    if (
                        "AdditionalMetadata" in data
                        and "DataZoneScopeName" in data["AdditionalMetadata"]
                    ):
                        return True
                    return False
            except Exception as e:
                logging.error(f"Error detecting if MD environment: {e}")
            return False
        return cls._cached_env in [
            Environment.MD_IAM,
            Environment.MD_IDC,
            Environment.MD_SAML,
        ]

    @classmethod
    def is_smai_environment(cls):
        """Check if the environment is a SageMaker AI environment"""
        if cls._cached_env is None:
            try:
                with open("/opt/ml/metadata/resource-metadata.json", "r") as f:
                    data = json.load(f)
                    if "ResourceArn" in data and "AdditionalMetadata" not in data:
                        return True
                    elif (
                        "AdditionalMetadata" in data
                        and "DataZoneScopeName" in data["AdditionalMetadata"]
                    ):
                        return False
                    return False
            except Exception as e:
                logging.error(f"Error detecting if SMAI environment: {e}")
            return False
        return cls._cached_env in [
            Environment.STUDIO_IAM,
            Environment.STUDIO_SSO,
        ]

    @classmethod
    def is_q_enabled_studio_domain(cls, domain_details):
        return (
            domain_details.get("DomainSettings") is not None
            and domain_details.get("DomainSettings").get("AmazonQSettings") is not None
            and domain_details.get("DomainSettings")
            .get("AmazonQSettings")
            .get("Status")
            == "ENABLED"
        )
