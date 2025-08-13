import os

# -----------------------------
# Config (ENV)
# -----------------------------
EPO_HOST = os.environ.get("EPO_HOST", "https://localhost:8443").rstrip("/")
EPO_USERNAME = os.environ.get("EPO_USERNAME", "")
EPO_PASSWORD = os.environ.get("EPO_PASSWORD", "")
IGNORE_SSL = os.environ.get("EPO_IGNORE_SSL", "false").lower() in ("true", "1", "yes")
TIMEOUT = int(os.environ.get("EPO_TIMEOUT", "30"))
EXPORTER_PORT = int(os.environ.get("EPO_EXPORTER_PORT", "9898"))
LOG_LEVEL = os.environ.get("EPO_LOG_LEVEL", "INFO").upper()

# Saved Query IDs
Q_EVENTS_BY_PRODUCT = os.environ.get("EPO_Q_EVENTS_BY_PRODUCT")
Q_INSTALLED_BY_PRODUCT = os.environ.get("EPO_Q_INSTALLED_BY_PRODUCT")
Q_REPORTING_ENDPOINTS_BY_PRODUCT = os.environ.get("EPO_Q_REPORTING_ENDPOINTS_BY_PRODUCT")
Q_POLICY_ASSIGNMENTS = os.environ.get("EPO_Q_POLICY_ASSIGNMENTS")
Q_MANAGED_COMM = os.environ.get("EPO_Q_MANAGED_SYSTEMS_COMM")
Q_POLICY_NOT_APPLIED = os.environ.get("EPO_Q_POLICY_NOT_APPLIED")
Q_DAT_OUTDATED = os.environ.get("EPO_Q_DAT_OUTDATED")
Q_TIE_REP = os.environ.get("EPO_Q_TIE_REP")
Q_TIE_REP_BY_SOURCE = os.environ.get("EPO_Q_TIE_REP_BY_SOURCE")
Q_TIE_UNKNOWN_PREVALENT = os.environ.get("EPO_Q_TIE_UNKNOWN_PREVALENT")
Q_ATP_RULES = os.environ.get("EPO_Q_ATP_RULES")
Q_ATP_DAC = os.environ.get("EPO_Q_ATP_DAC")
Q_AGENT_VERSION_DIST = os.environ.get("EPO_Q_AGENT_VERSION_DIST")
Q_PRODUCT_VERSION_DIST = os.environ.get("EPO_Q_PRODUCT_VERSION_DIST")
Q_TAG_USAGE = os.environ.get("EPO_Q_TAG_USAGE")
Q_CLIENT_TASK_FAILED = os.environ.get("EPO_Q_CLIENT_TASK_FAILED")
Q_REPOSITORY_STATUS = os.environ.get("EPO_Q_REPOSITORY_STATUS")
Q_EVENTS_BY_PRODUCT_SEVERITY = os.environ.get("EPO_Q_EVENTS_BY_PRODUCT_SEVERITY")
Q_QUARANTINE_ITEMS = os.environ.get("EPO_Q_QUARANTINE_ITEMS")
Q_DAT_INFO = os.environ.get("EPO_Q_DAT_INFO")
Q_POLICY_LAST_MODIFIED = os.environ.get("EPO_Q_POLICY_LAST_MODIFIED")

# Agent-Server Communication Interval (minutes)
ASCI_MINUTES = int(os.environ.get("EPO_ASCI_MINUTES", "60"))
ASCI_OVERDUE_MULTIPLIER = float(os.environ.get("EPO_ASCI_OVERDUE_MULTIPLIER", "2.0"))

import os
# expose env in one place
EPO_HOST = os.environ.get("EPO_HOST", "https://localhost:8443")
# ... add your env bindings ...
