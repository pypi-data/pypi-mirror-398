import json
from datetime import datetime

def generate_report(results: dict, output_path: str):
    report = {
        "module": "API Openness & Standard Format",
        "timestamp": datetime.utcnow().isoformat(),
        "results": results,
        "summary": {
            "total_rules": len(results),
            "passed": sum(1 for r in results.values() if r["compliant"]),
            "failed": sum(1 for r in results.values() if not r["compliant"])
        }
    }

    with open(output_path, "w") as f:
        json.dump(report, f, indent=4)

    return report