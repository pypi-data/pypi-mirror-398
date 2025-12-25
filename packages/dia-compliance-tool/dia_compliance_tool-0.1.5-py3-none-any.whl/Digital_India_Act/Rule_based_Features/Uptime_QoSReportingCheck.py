import os
import re
from typing import Dict, List, Any

class UptimeQoSReportingChecker:
    name = "Uptime & QoS Reporting Check"
    description = "Rule based detection of uptime, health, metrics, and QoS monitoring mechanisms"

    # defining patterns

    HEALTH_PATTERNS = [
        r"/health[z]?",
        r"/status",
        r"/healthcheck",
        r"actuator/health",
        r"/readiness",
        r"/liveness",
        r"/live",
        r"/ready"
    ]

    METRICS_PATTERNS = [
        r"/metrics",
        r"prometheus",
        r"opentelemetry",
        r"micrometer",
        r"statsd",
        r"grafana",
        r"newrelic",
        r"datadog",
        r"elastic(apm)?",
        r"cloudwatch",
        r"appmetrics"
    ]

    LOGGING_PATTERNS = [
        r"logger\.",
        r"logging\.",
        r"winston",
        r"log4j",
        r"slf4j",
        r"pino",
        r"bunyan",
        r"structlog",
        r"logrus",
        r"zap"
    ]

    ALERTING_PATTERNS = [
        r"pagerduty",
        r"opsgenie",
        r"alertmanager",
        r"cloudwatch.*alarm",
        r"sns",
        r"slack.*(alert|incident|ops)",
        r"webhook.*(alert|incident)",
        r"send(alert|notification)",
        r"incident",
        r"on[-_]?call"
    ]

    QOS_PATTERNS = [
        r"timeout",
        r"retry",
        r"circuit",
        r"rate[_\-]?limit",
        r"bulkhead",
        r"resilience4j",
        r"hystrix",
        r"backoff",
        r"throttle",
        r"latency",
        r"throughput",
        r"error[_\-]?rate",
        r"deadline"
    ]

    QOS_NEEDED_PATTERNS = [
        r"requests\.",
        r"axios\.",
        r"fetch\(",
        r"http\.client",
        r"urllib",
        r"grpc",
        r"socket",
        r"select\s+",
        r"insert\s+",
        r"update\s+",
        r"delete\s+",
        r"find\(",
        r"save\(",
        r"query\(",
        r"@app\.route",
        r"router\.",
        r"@GetMapping",
        r"@PostMapping",
        r"express\(",
        r"fastapi",
        r"flask"
    ]


    SUPPORTED_EXTENSIONS = (".js", ".ts", ".py", ".java", ".go")

    def collect_backend_files(self,base_path:str) -> Dict[str,str]:
        files = {}
        for root,_,fs in os.walk(base_path):
            for f in fs:
                if f.endswith(self.SUPPORTED_EXTENSIONS):
                    path = os.path.join(root,f)
                    try:
                        with open(path,"r",errors="ignore") as fp:
                            files[path] = fp.read()
                    except:
                        pass
        return files
    
    def pattern_found(self,patterns: List[str],text: str)-> bool:
        return any(re.search(p,text,re.IGNORECASE) for p in patterns)
    
    def ask_human_questions(self) -> Dict[str, str]:
        print("\n=== Human Verification: Uptime & QoS Operations ===")
        print("Please answer the following questions (yes/no):\n")

        questions = {
            "ping_monitoring": "Do you actively monitor uptime using ping/HTTP checks?",
            "sla_tracking": "Do you track uptime or latency against defined SLAs?",
            "incident_alerts": "Are alerts triggered automatically during downtime or latency breaches?",
            "qos_review": "Do you periodically review latency, error rates, and throughput?",
            "incident_logs": "Are incident logs retained and auditable?"
        }

        answers = {}
        for key, question in questions.items():
            while True:
                ans = input(f"{question} (yes/no): ").strip().lower()
                if ans in ("yes", "no"):
                    answers[key] = ans
                    break
                else:
                    print("Please answer only 'yes' or 'no'.")

        return answers

    def run(self, backend_path: str, is_human_in_loop: bool = True) -> Dict[str, Any]:
        backend_files = self.collect_backend_files(backend_path)

        if not backend_files:
            return {
                "status": "NOT_CHECKED",
                "reason": "No backend source code found",
                "uptime_reporting": None,
                "qos_monitoring": None,
                "severity": "undetermined",
                "files_analyzed": [],
                "recommendation": (
                    "Backend server source code is required to assess uptime and QoS reporting compliance under Digital India Act"
                )
            }
        
        health_files=[]
        metrics_files =[]
        logging_files = []
        alerting_files=[]
        qos_files=[]
        
        uptime_qos_needed_files=[]
        uptime_qos_missing = {}

        for path, content in backend_files.items():
            has_health = self.pattern_found(self.HEALTH_PATTERNS, content)
            has_metrics = self.pattern_found(self.METRICS_PATTERNS, content)
            has_logging = self.pattern_found(self.LOGGING_PATTERNS, content)
            has_alerting = self.pattern_found(self.ALERTING_PATTERNS, content)
            has_qos = self.pattern_found(self.QOS_PATTERNS, content)

            if has_health:
                health_files.append(path)
            if has_metrics:
                metrics_files.append(path)
            if has_logging:
                logging_files.append(path)
            if has_alerting:
                alerting_files.append(path)
            if has_qos:
                qos_files.append(path)

            needs_uptime_qos = self.pattern_found(self.QOS_NEEDED_PATTERNS, content)

            if needs_uptime_qos:
                uptime_qos_needed_files.append(path)
                missing = []

                if not has_health:
                    missing.append("health_endpoint")
                if not has_metrics:
                    missing.append("metrics")
                if not has_logging:
                    missing.append("logging")
                if not has_alerting:
                    missing.append("alerting")
                if not has_qos:
                    missing.append("qos_controls")

                if missing:
                    uptime_qos_missing[path] = missing

        uptime_reporting = bool(health_files or metrics_files)
        qos_monitoring = bool(qos_files)


        if uptime_qos_missing:
            severity = "high"
        elif not uptime_reporting:
            severity = "medium"
        else:
            severity = "low"
        
        human_answers = self.ask_human_questions() if is_human_in_loop else {}

        positive_answers = sum(
            1 for v in human_answers.values()
            if v == "yes"
        )

        operational_support = positive_answers >= 3

        # Adjust severity using human inputs
        if severity == "high" and operational_support:
            final_severity = "medium"
        elif severity == "medium" and operational_support:
            final_severity = "low"
        else:
            final_severity = severity
        
        recommendation = []
        if not health_files:
            recommendation.append("Add a health/status endpoint (e.g., /health or /status).")
        if not metrics_files:
            recommendation.append("Expose service metrics using Prometheus or OpenTelemetry.")
        if not logging_files:
            recommendation.append("Add structured logging for errors and latency.")
        if not qos_files:
            recommendation.append("Implement QoS controls such as timeouts, retries, or circuit breakers.")
        if not alerting_files:
            recommendation.append("Integrate alerting mechanisms for downtime or degradation.")

        return {
            "uptime_reporting": uptime_reporting,
            "qos_monitoring": qos_monitoring,
            "severity": final_severity,
            "files_analyzed": list(backend_files.keys()),
            "human_verfication_answers":human_answers,
            "evidence": {
                "health_endpoints": health_files,
                "metrics": metrics_files,
                "logging": logging_files,
                "alerting": alerting_files,
                "qos_controls": qos_files
            },
            "uptime_and_qos_reporting_file_wise":{
                "files_where_needed": uptime_qos_needed_files,
                "files_missing_controls":uptime_qos_missing
            },
            "recommendation": (
                " ".join(recommendation)
                if recommendation
                else "Uptime and QoS reporting mechanisms are adequately implemented."
            )
        }