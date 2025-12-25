from Digital_India_Act import UptimeQoSReportingChecker
import json
def main():
    checker = UptimeQoSReportingChecker()

    path = "./test_backend_uqos1"
    

    result = checker.run(path,is_human_in_loop=False)
    print(json.dumps(result, indent=2))

    path1 = "./test_backend_uqos2"
    result1 = checker.run(path1,is_human_in_loop=True)

    print(json.dumps(result1, indent=2))

if __name__ == "__main__":
    main()

"""
Result for path:

{
  "uptime_reporting": false,
  "qos_monitoring": false,
  "severity": "high",
  "files_analyzed": [
    "./test_backend_uqos1\\app.py",
    "./test_backend_uqos1\\db.py",
    "./test_backend_uqos1\\service.py"
  ],
  "human_verfication_answers": {},
  "evidence": {
    "health_endpoints": [],
    "metrics": [],
    "logging": [],
    "alerting": [],
    "qos_controls": []
  },
  "uptime_and_qos_reporting_file_wise": {
    "files_where_needed": [
      "./test_backend_uqos1\\app.py",
      "./test_backend_uqos1\\db.py",
      "./test_backend_uqos1\\service.py"
    ],
    "files_missing_controls": {
      "./test_backend_uqos1\\app.py": [
        "health_endpoint",
        "metrics",
        "logging",
        "alerting",
        "qos_controls"
      ],
      "./test_backend_uqos1\\db.py": [
        "health_endpoint",
        "metrics",
        "logging",
        "alerting",
        "qos_controls"
      ],
      "./test_backend_uqos1\\service.py": [
        "health_endpoint",
        "metrics",
        "logging",
        "alerting",
        "qos_controls"
      ]
    }
  },
  "recommendation": "Add a health/status endpoint (e.g., /health or /status). Expose service metrics using Prometheus or OpenTelemetry. Add structured logging for errors and latency. Implement QoS controls such as timeouts, retries, or circuit breakers. Integrate alerting mechanisms for downtime or degradation."
}


Results for path1 with human verification:

=== Human Verification: Uptime & QoS Operations ===
Please answer the following questions (yes/no):

Do you actively monitor uptime using ping/HTTP checks? (yes/no): yes
Do you track uptime or latency against defined SLAs? (yes/no): no
Are alerts triggered automatically during downtime or latency breaches? (yes/no): yes
Do you periodically review latency, error rates, and throughput? (yes/no): yes
Are incident logs retained and auditable? (yes/no): no
{
  "uptime_reporting": true,
  "qos_monitoring": true,
  "severity": "medium",
  "files_analyzed": [
    "./test_backend_uqos2\\health.py",
    "./test_backend_uqos2\\main.py",
    "./test_backend_uqos2\\metrics.py",
    "./test_backend_uqos2\\service.py"
  ],
  "human_verfication_answers": {
    "ping_monitoring": "yes",
    "sla_tracking": "no",
    "incident_alerts": "yes",
    "qos_review": "yes",
    "incident_logs": "no"
  },
  "evidence": {
    "health_endpoints": [
      "./test_backend_uqos2\\health.py"
    ],
    "metrics": [
      "./test_backend_uqos2\\metrics.py"
    ],
    "logging": [
      "./test_backend_uqos2\\main.py",
      "./test_backend_uqos2\\service.py"
    ],
    "alerting": [],
    "qos_controls": [
      "./test_backend_uqos2\\service.py"
    ]
  },
  "uptime_and_qos_reporting_file_wise": {
    "files_where_needed": [
      "./test_backend_uqos2\\health.py",
      "./test_backend_uqos2\\service.py"
    ],
    "files_missing_controls": {
      "./test_backend_uqos2\\health.py": [
        "metrics",
        "logging",
        "alerting",
        "qos_controls"
      ],
      "./test_backend_uqos2\\service.py": [
        "health_endpoint",
        "metrics",
        "alerting"
      ]
    }
  },
  "recommendation": "Integrate alerting mechanisms for downtime or degradation."
}
"""