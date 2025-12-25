import sys
from scanner import scan_source_files
from analyzers.openapi import detect_openapi
from analyzers.rest_patterns import analyze_rest_patterns
from analyzers.auth import detect_authentication
from analyzers.headers import detect_json_usage
from report import generate_report

def run_api_openness_check(source_dir: str):
    files = scan_source_files(source_dir)

    openapi_result = detect_openapi(source_dir)
    rest_result = analyze_rest_patterns(files)
    auth_result = detect_authentication(files)
    json_result = detect_json_usage(files)

    results = {
        "API-OPEN-1": openapi_result,
        "API-OPEN-2": {
            "compliant": len(rest_result["methods_used"]) > 0,
            "evidence": rest_result["methods_used"]
        },
        "API-OPEN-3": {
            "compliant": rest_result["versioning"],
            "evidence": "Versioned endpoints detected" if rest_result["versioning"] else None
        },
        "API-OPEN-4": {
            "compliant": json_result,
            "evidence": "application/json headers detected" if json_result else None
        },
        "API-OPEN-5": {
            "compliant": auth_result,
            "evidence": "Authentication logic found" if auth_result else None
        }
    }
    report = generate_report(results, "api_openness_report.json")
    print("Check completed")
    print(report)


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Input server source code directory")
        sys.exit(1)
    run_api_openness_check(sys.argv[1])