import logging
from azure.identity import DefaultAzureCredential
from azure.mgmt.resource import ResourceManagementClient
from . import report

SUBSCRIPTION_ID = "***REMOVED***"
RESOURCE_GROUP = "cloud-guardian-rg"
REQUIRED_TAGS = ["Owner", "Environment", "CostCenter"]

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def get_resources(credential: DefaultAzureCredential) -> list:
    """Connect to Azure and return all resources in the resource group."""

    client = ResourceManagementClient(credential, SUBSCRIPTION_ID)
    logger.info(f"scanning resource group: {RESOURCE_GROUP}")

    resources = list(client.resources.list_by_resource_group(RESOURCE_GROUP))
    logger.info(f"Found {len(resources)} resources")
    
    return resources

def check_tags(resources: list) -> list:
    """check each resource for missing required tags. returns list of violations"""

    violations = []

    for resource in resources:
        missing_tags = []
        tags = resource.tags

        if tags is None:
            missing_tags = REQUIRED_TAGS.copy()
        else:
            for tag in REQUIRED_TAGS:
                if tag not in tags:
                    missing_tags.append(tag)

        if missing_tags:
            violation = {
                "resource_name": resource.name,
                "resource_type": resource.type,
                "missing_tags": missing_tags
            }
            logger.warning(f"Violation: {resource.name} missing {missing_tags}")
            violations.append(violation)

    logger.info(f"scan complete. {len(violations)} violations found.")
    return violations

if __name__ == "__main__":
    credential = DefaultAzureCredential()
    resources = get_resources(credential)
    violations = check_tags(resources)

    if violations:
        logger.info(f"Writing report with {len(violations)} violations")
        report.write_report(violations)
    else:
        logger.info(f"All resources compliant. No violations found.")
