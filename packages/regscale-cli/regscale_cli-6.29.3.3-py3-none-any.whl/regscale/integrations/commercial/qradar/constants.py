"""
Constants for QRadar integration.

This module contains configuration constants used throughout the QRadar integration,
including default control mappings, time windows, and configuration keys.
"""

# Default NIST 800-53 R5 controls for audit and logging assessments
DEFAULT_AUDIT_CONTROLS = ["AU-02", "AU-03", "AU-06", "AU-12"]

# Default time window for QRadar queries (in hours)
DEFAULT_TIME_WINDOW_HOURS = 8

# Configuration section key in init.yaml
CONFIG_SECTION = "qradar"

# Assessment types
ASSESSMENT_TYPE_CONTROL_TESTING = "Control Testing"

# Assessment results
ASSESSMENT_RESULT_PASS = "Pass"
ASSESSMENT_RESULT_FAIL = "Fail"

# POAM/Issue severity levels
SEVERITY_MODERATE = 5

# Control implementation statuses
STATUS_FULLY_IMPLEMENTED = "Fully Implemented"
STATUS_IN_REMEDIATION = "In Remediation"

# QRadar field names (commonly used)
FIELD_AWS_ACCOUNT_ID = "AWS Account ID"
FIELD_USERNAME = "username"
FIELD_SOURCE_IP = "sourceip"

# Control descriptions for audit controls
CONTROL_DESCRIPTIONS = {
    "AU-02": "Audit Events - Events are being generated",
    "AU-03": "Content of Audit Records - Audit records contain adequate information",
    "AU-06": "Audit Review, Analysis, and Reporting - Logs available for review",
    "AU-12": "Audit Generation - System capability to generate audit records",
}
