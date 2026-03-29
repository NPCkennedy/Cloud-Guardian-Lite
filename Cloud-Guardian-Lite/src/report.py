import json
import loggin
from datetime import datetime, timezone

logger = logging.getLogger(__name__)

def write_report(violations: list) -> str:
    """Write violations to a JSON report file. Returns the filename."""
    
    timestamp = datetime.now(timezone.utc).isoformat()
    
    report = {
        "scan_timestamp": timestamp,
        "total_violations": len(violations),
        "violations": violations
    }

    filename = "violations.json"

    with open(filename, "w") as f:
        json.dump(report, f, indent=2)

    logger.info(f"Report written to {filename}")
    return filename 
