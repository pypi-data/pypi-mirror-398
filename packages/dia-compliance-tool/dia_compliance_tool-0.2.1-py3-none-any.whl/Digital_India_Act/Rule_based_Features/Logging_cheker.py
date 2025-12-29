# This checker if the backend code uses logging libraries to log the things mentioned above
# The languagues to which we are checking the compliance are currently Python, Node, Java

import os
import re

class LoggingChecker:
    name = "Logging/Audit Trail check"
    description = "This checker will look for the logging based on static inspection of the backend code"

    # --- Defining some language specific patterns to look -------

    PYTHON_LOGGING = [
        r"import logging",
        r"logging\.getLogger",
        r"logger\.(info|warning|error|critical)"
    ]

    NODE_LOGGING = [
        r"require\(['\"](winston|pino|bunyan)['\"]",
        r"new (Logger|Pino)",
        r"(logger|log)\.(info|warn|error)"
    ]

    JAVA_LOGGING = [
        r"LoggerFactory\.getLogger",
        r"LogManager\.getLogger",
        r"log\.(info|warn|error|debug)"
    ]

    GO_LOGGING = [
        r"log\.(Print|Printf|Fatal|Fatalf)",
        r"zap\.New",
        r"logrus\.(Info|Warn|Error)"
    ]

    DOTNET_LOGGING = [
        r"ILogger<",
        r"_logger\.(LogInformation|LogWarning|LogError)",
        r"Serilog\.Log\."
    ]

    RUBY_LOGGING = [
        r"Rails\.logger\.(info|warn|error|debug)",
        r"Logger\.new"
    ]


    SENSITIVE_PATTERNS = [
        r"password\s*=",
        r"token\s*=",
        r"secret\s*=",
        r"api[_-]?key\s*="
    ]

    AUDIT_EVENTS = [
        r"login",
        r"logout",
        r"delete",
        r"update",
        r"create",
        r"access"
    ]

    SENSITIVE_OPS = [
        r"delete",
        r"remove",
        r"revoke",
        r"export",
        r"consent",
        r"deactivate"
    ]
    BAD_LOGGING = [
        r"print\(",
        r"console\.log",
        r"System\.out\.println",
        r"fmt\.Println"    
    ]

    # -------- File extensions -------- #

    EXTENSIONS = {
        "python": [".py"],
        "node": [".js", ".ts"],
        "java": [".java"],
        "go": [".go"],
        "dotnet": [".cs"],
        "ruby": [".rb"]
    }

    # ----- Run function ------

    def run(self,repo_path):
        results = []
        files_scanned = 0
        not_scanned = []
        scanned = []

        for root, _, files in os.walk(repo_path):
            for file in files:
                lang = self.detect_language(file)
                if not lang:
                    not_scanned.append(file)
                    continue

                path = os.path.join(root,file)
                files_scanned += 1
                scanned.append(file)

                with open(path, "r",errors="ignore") as f:
                    code = f.read()

                result = self.analyze_file(path,code,lang)
                if result["issues"]:
                    results.append(result)

        
        return {
            "files_scanned_count": files_scanned,
            "files_scanned": scanned,
            "files_not_scanned": not_scanned,
            "violations": len(results),
            "details": results
        }
    
    def detect_language(self,filename):
        for lang,exts in self.EXTENSIONS.items():
            if any(filename.endswith(ext) for ext in exts):
                return lang
        return None
    
    def analyze_file(self, path, code, lang):
        issues = []

        has_logging = self.has_logging(code, lang)

        # 1. No logging framework
        if not has_logging:
            issues.append("No logging framework detected")

        # 2. Sensitive data logged
        if self.logs_sensitive_data(code):
            issues.append("Sensitive data may be logged")

        # 3. Non-persistent logging
        if self.uses_bad_logging(code):
            issues.append("Console-based/teminal-based logging detected (non-persistent)")

        # 4. Sensitive operations without logging
        if self.has_sensitive_ops(code) and not has_logging:
            issues.append("Sensitive operations without audit logging")

        # 5. Audit event without audit log
        if self.has_audit_event(code) and not self.has_audit_log(code):
            issues.append("Audit-relevant event without corresponding log")

        severity = self.get_severity(issues)

        return {
            "file": path,
            "language": lang,
            "severity": severity,
            "issues": issues,
            "recommendation": self.recommendation(issues, lang)
        }

    
    # --- Rule check functions ---- #

    def has_logging(self,code, lang):
        patterns = {
            "python": self.PYTHON_LOGGING,
            "node": self.NODE_LOGGING,
            "java": self.JAVA_LOGGING,
            "go": self.GO_LOGGING,
            "dotnet": self.DOTNET_LOGGING,
            "ruby": self.RUBY_LOGGING
        }
        return any(re.search(p,code) for p in patterns.get(lang,[]))
    
    def logs_sensitive_data(self, code):
        sensitive = any(re.search(s, code, re.IGNORECASE) for s in self.SENSITIVE_PATTERNS)
        logging_used = self.uses_bad_logging(code) or re.search(
            r"(logger\.|log\.|LogInformation|Rails\.logger|zap\.|logrus\.)",
            code,
            re.IGNORECASE
        )
        return sensitive and logging_used


    
    def uses_bad_logging(self,code):
        return any(re.search(p,code) for p in self.BAD_LOGGING)
    
    def has_sensitive_ops(self, code):
        return any(re.search(s, code, re.IGNORECASE) for s in self.SENSITIVE_OPS)


    def has_audit_event(self, code):
        return any(re.search(e, code, re.IGNORECASE) for e in self.AUDIT_EVENTS)

    def has_audit_log(self, code):
        return re.search(r"(audit|access|action|logger\.info|logger\.warn|logger\.error|log\.)", code, re.IGNORECASE)

    

    # ----- Output Helpers --------- #

    def get_severity(self,issues):
        if not issues:
            return "low"
        if "Sensitive data may be logged" in issues:
            return "high"
        return "medium"
    
    def recommendation(self, issues, lang):
        rec = []

        if "No logging framework detected" in issues:
            rec.append(f"Introduce a standard logging framework in {lang}")

        if "Sensitive data may be logged" in issues:
            rec.append(
                "Do not log passwords, tokens, secrets, or API keys. "
                "Mask or remove sensitive fields before logging."
            )

        if "Sensitive operations without audit logging" in issues:
            rec.append("Add audit logs for sensitive operations such as delete, revoke, or consent changes")

        if "Audit-relevant event without corresponding log" in issues:
            rec.append("Log access, update, and delete events for auditability")

        if "Console-based logging detected (non-persistent)" in issues:
            rec.append(
                "Replace console logging with persistent structured logs using standard logging libraries"
            )

        return " ".join(rec)



