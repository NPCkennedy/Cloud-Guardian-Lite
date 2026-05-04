import logging
from azure.identity import DefaultAzureCredential
from azure.mgmt.resource import ResourceManagementClient
from . import report
from . import notifier

# Configuration - update these values for your environment
SUBSCRIPTION_ID = "0cb2ebf6-d6c2-4b63-9f38-ba16ebe4feb1"
RESOURCE_GROUP = "cloud-guardian-rg"
REQUIRED_TAGS = ["Owner", "Environment", "CostCenter"]

# Set up logging
logging.basicConfig(level=logging.INFO)
logging.getLogger("azure").setLevel(logging.WARNING)
logging.getLogger("azure.core.pipeline.policies.http_logging_policy").setLevel(logging.WARNING)
logger = logging.getLogger(__name__)

# Function to retrieve all resources in the specified resource group
def get_resources(credential: DefaultAzureCredential) -> list:
    """Connect to Azure and return all resources in the resource group."""

    client = ResourceManagementClient(credential, SUBSCRIPTION_ID) #create a resource management client using the provided credentials and subscription ID
    logger.info(f"scanning resource group: {RESOURCE_GROUP}") #log the resource group being scanned

    resources = list(client.resources.list_by_resource_group(RESOURCE_GROUP))
    logger.info(f"Found {len(resources)} resources")
    
    return resources

# Function to check each resource for missing required tags
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

    # Log the completion of the scan
    logger.info(f"scan complete. {len(violations)} violations found.")
    return violations


if __name__ == "__main__":
    #authenticate with azure using default credentials (az login)
    try:
        credential = DefaultAzureCredential()
        logger.info("Successfully authenticated with Azure")
    except Exception as e:
        logger.error(f"Failed to authenticate with Azure: {e}")
        logger.error("run 'az login' to authenticate and try again")
        exit(1)

    #get resources
    try:
        resources = get_resources(credential)
    except Exception as e:
        logger.error(f"Failed to retrieve resources: {e}")
        exit(1)

    #check for tag violations
    try:
        violations = check_tags(resources)
    except Exception as e:
        logger.error(f"Failed to check tags: {e}")
        exit(1)

    #write report
    if violations:
        try:
            report.write_report(violations)
            notifier.notify(violations)
            logger.warning(f"Scan complete. {len(violations)} violations found. Review violations.json")
            exit(1)
        except Exception as e:
            logger.error(f"Failed to write report or send alert: {e}")
            exit(1)
    else:
        logger.info("Scan complete. All resources compliant.")
        exit(0)
