import logging
import json
from .default_sagemaker_client import get_sagemaker_client


logging.basicConfig(format="%(levelname)s: %(message)s", level=logging.INFO)


def get_is_dual_stack_enabled() -> bool:
    try:
        with open("/opt/ml/metadata/resource-metadata.json", "r") as f:
            data = json.load(f)
            sm_domain_id = data["DomainId"]
            sm_client = get_sagemaker_client()
            domain_details = sm_client.describe_domain(sm_domain_id)
    except Exception as e:
        logging.error(f"Cannot detect dual stack: {e}")
        return False

    if not isinstance(domain_details, dict) or domain_details is None:
        return False

    ip_address_type = domain_details.get("DomainSettings", {}).get("IpAddressType")
    if not isinstance(ip_address_type, str):
        return False

    return ip_address_type.lower() == "dualstack"


def is_dual_stack_enabled() -> bool:
    return get_is_dual_stack_enabled()
