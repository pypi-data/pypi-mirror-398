"""
Module to store constants for Microsoft Defender for Cloud
"""

import os

DATE_FORMAT = "%Y-%m-%dT%H:%M:%S"
IDENTIFICATION_TYPE = "Vulnerability Assessment"
CLOUD_RECS = "Microsoft Defender for Cloud Recommendation"
APP_JSON = "application/json"
AFD_ENDPOINTS = "microsoft.cdn/profiles/afdendpoints"
DATA_TYPE = "@odata.type"
ENTRA_SAVE_DIR = os.path.join("artifacts", "defender", "entra")

# Azure Entra (Azure AD) Microsoft Graph API endpoints
GRAPH_BASE_URL = "https://graph.microsoft.com/v1.0"
GRAPH_BETA_URL = "https://graph.microsoft.com/beta"

# Azure Entra API endpoints for FedRAMP evidence collection
ENTRA_ENDPOINTS = {
    "users": "/users?$select=id,displayName,userPrincipalName,accountEnabled,userType,createdDateTime&$top=999",
    "users_delta": "/users/delta?$select=id,displayName,userPrincipalName,accountEnabled,userType,createdDateTime",
    "guest_users": "/users?$filter=userType eq 'Guest'&$select=id,displayName,userPrincipalName,accountEnabled",
    "security_groups": "/groups?$filter=securityEnabled eq true&$select=id,displayName,securityEnabled",
    "groups_and_members": "/groups?$expand=members($select=id,displayName,userPrincipalName)",
    # "groups": "/groups",
    # "group_members": "/groups/{group-id}/members?$select=id,displayName,userPrincipalName",
    "role_assignments": "/roleManagement/directory/roleAssignments?$expand=roleDefinition",
    "role_definitions": "/roleManagement/directory/roleDefinitions?$select=id,displayName,description",
    "pim_assignments": "/roleManagement/directory/roleAssignmentScheduleInstances?$expand=activatedUsing,principal,roleDefinition",
    "pim_eligibility": "/roleManagement/directory/roleEligibilityScheduleInstances?$expand=roleDefinition",
    "conditional_access": "/identity/conditionalAccess/policies",
    "auth_methods_policy": "/policies/authenticationMethodsPolicy",
    "user_mfa_registration": "/reports/authenticationMethods/userRegistrationDetails?$top=999",
    "mfa_registered_users": "/reports/authenticationMethods/userRegistrationDetails?$filter=isMfaRegistered eq true",
    "sign_in_logs": "/auditLogs/signIns?$filter=createdDateTime ge {start_date}&$top=1000",
    "directory_audits": "/auditLogs/directoryAudits?$filter=activityDateTime ge {start_date}&$top=1000",
    "provisioning_logs": "/auditLogs/provisioning?$filter=activityDateTime ge {start_date}&$top=1000",
    "access_review_definitions": "/identityGovernance/accessReviews/definitions",
    "access_review_instances": "/identityGovernance/accessReviews/definitions/{def_id}/instances",
    "access_review_decisions": "/identityGovernance/accessReviews/definitions/{def_id}/instances/{instance_id}/decisions?$top=100",
}

# Evidence categories for FedRAMP controls
EVIDENCE_CATEGORIES = {
    "users_groups": "Users & Groups Management",
    "rbac_pim": "Role-Based Access Control & Privileged Identity Management",
    "conditional_access": "Conditional Access Policies",
    "authentication": "Authentication Methods & Multi-Factor Authentication",
    "audit_logs": "Audit & Sign-in Logs",
    "access_reviews": "Access Reviews & Governance",
}

AC_1 = "AC-1"
AC_2 = "AC-2"
AC_2_1 = "AC-2(1)"
AC_2_3 = "AC-2(3)"
AC_2_5 = "AC-2(5)"
AC_2_7 = "AC-2(7)"
AC_2_12 = "AC-2(12)"
AC_365 = ["AC-3", "AC-6", "AC-5"]
AU_2 = "AU-2"
AU_3 = "AU-3"
AU_6 = "AU-6"
AU_12 = "AU-12"
IA_2 = "IA-2"
IA_2_1 = "IA-2(1)"
IA_2_2 = "IA-2(2)"
IA_2_3 = "IA-2(3)"
IA_2_4 = "IA-2(4)"
IA_2_5 = "IA-2(5)"
IA_2_6 = "IA-2(6)"
IA_2_7 = "IA-2(7)"
IA_2_8 = "IA-2(8)"
IA_2_9 = "IA-2(9)"
IA_2_10 = "IA-2(10)"
IA_2_11 = "IA-2(11)"
IA_2_12 = "IA-2(12)"
IA_4 = "IA-4"
IA_5 = "IA-5"

# Mapping between Azure Entra evidence types and FedRAMP control identifiers
# Based on Azure_Entra_FedRAMP_High_Evidence.docx mapping table
EVIDENCE_TO_CONTROLS_MAPPING = {
    # Users & Groups evidence maps to Account Management controls
    "users": [AC_1, AC_2, AC_2_1, AC_2_3, AC_2_5, AC_2_7, AC_2_12],
    "users_delta": [AC_1, AC_2, AC_2_1, AC_2_3, AC_2_5, AC_2_7, AC_2_12],
    "guest_users": [AC_1, AC_2, AC_2_1, AC_2_3, AC_2_5, AC_2_7, AC_2_12, "IA-8", "IA-8(1)"],
    "security_groups": [AC_1, AC_2, AC_2_1, AC_2_3, AC_2_5, AC_2_7, AC_2_12],
    "groups_and_members": [AC_1, AC_2, AC_2_1, AC_2_3, AC_2_5, AC_2_7, AC_2_12],
    # RBAC & PIM evidence maps to Access Control and Privilege Management controls
    "role_assignments": AC_365,
    "role_definitions": AC_365,
    "pim_assignments": AC_365,
    "pim_eligibility": AC_365,
    # Conditional Access maps to Access Enforcement controls
    "conditional_access": ["AC-17", "AC-19"],
    # Authentication methods map to Identification & Authentication controls
    "auth_methods_policy": [
        IA_2,
        IA_2_1,
        IA_2_2,
        IA_2_3,
        IA_2_4,
        IA_2_5,
        IA_2_6,
        IA_2_7,
        IA_2_8,
        IA_2_9,
        IA_2_10,
        IA_2_11,
        IA_2_12,
        IA_4,
        IA_5,
    ],
    "user_mfa_registration": [
        IA_2,
        IA_2_1,
        IA_2_2,
        IA_2_3,
        IA_2_4,
        IA_2_5,
        IA_2_6,
        IA_2_7,
        IA_2_8,
        IA_2_9,
        IA_2_10,
        IA_2_11,
        IA_2_12,
        IA_4,
        IA_5,
    ],
    "mfa_registered_users": [
        IA_2,
        IA_2_1,
        IA_2_2,
        IA_2_3,
        IA_2_4,
        IA_2_5,
        IA_2_6,
        IA_2_7,
        IA_2_8,
        IA_2_9,
        IA_2_10,
        IA_2_11,
        IA_2_12,
        IA_4,
        IA_5,
    ],
    # Sign-in logs map to Unsuccessful Logon controls and Audit controls
    "sign_in_logs": ["AC-7", AU_2, AU_3, AU_6, AU_12],
    # Directory audits map to Audit controls and Account Management
    "directory_audits": [AU_2, AU_3, AU_6, AU_12, IA_4, IA_5],
    # Provisioning logs map to Audit controls
    "provisioning_logs": [AU_2, AU_3, AU_6, AU_12],
    # Access reviews map to Account Management and Privilege controls
    "access_review_definitions": ["AC-3", "AC-6", "AC-5", "IA-8", "IA-8(1)"],
}

# Reverse mapping for easy lookup of which evidence types are needed for a control
CONTROLS_TO_EVIDENCE_MAPPING = {}
for evidence_type, controls in EVIDENCE_TO_CONTROLS_MAPPING.items():
    for control in controls:
        if control not in CONTROLS_TO_EVIDENCE_MAPPING:
            CONTROLS_TO_EVIDENCE_MAPPING[control] = []
        CONTROLS_TO_EVIDENCE_MAPPING[control].append(evidence_type)


RESOURCES_QUERY = """
resources
| where subscriptionId == "{SUBSCRIPTION_ID}"
| extend resourceName = name,
        resourceType = type,
        resourceLocation = location,
        resourceGroup = resourceGroup,
        resourceId = id,
        propertiesJson = parse_json(properties)
| extend ipAddress =
   case(
       resourceType =~ "microsoft.network/networkinterfaces", tostring(propertiesJson.ipConfigurations[0].properties.privateIPAddress),
       resourceType =~ "microsoft.network/publicipaddresses", tostring(propertiesJson.ipAddress),
       resourceType =~ "microsoft.compute/virtualmachines", tostring(propertiesJson.networkProfile.networkInterfaces[0].id),
       ""
   )
| project resourceName, resourceType, resourceLocation, resourceGroup, resourceId, ipAddress, properties
"""

CONTAINER_SCAN_QUERY = """
securityresources
| where type == 'microsoft.security/assessments'
| summarize by assessmentKey=name
| join kind=inner (
    securityresources
    | where type == 'microsoft.security/assessments/subassessments'
    | extend assessmentKey = extract('.*assessments/(.+?)/.*', 1, id)
    | where resourceGroup == '{RESOURCE_GROUP}'
) on assessmentKey
| project assessmentKey, subassessmentKey=name, id, parse_json(properties), resourceGroup, subscriptionId, tenantId
| extend description = properties.description,
    displayName = properties.displayName,
    resourceId = properties.resourceDetails.id,
    tag = properties.additionalData.artifactDetails.tags,
    resourceSource = properties.resourceDetails.source,
    category = properties.category,
    severity = properties.status.severity,
    code = properties.status.code,
    timeGenerated = properties.timeGenerated,
    remediation = properties.remediation,
    impact = properties.impact,
    vulnId = properties.id,
    additionalData = properties.additionalData
    | where resourceId startswith "/subscriptions"
| order by ['id'] asc
"""

DB_SCAN_QUERY = """
securityresources
| where type =~ "microsoft.security/assessments/subassessments"
| extend assessmentKey=extract(@"(?i)providers/Microsoft.Security/assessments/([^/]*)", 1, id), subAssessmentId=tostring(properties.id), parentResourceId= extract("(.+)/providers/Microsoft.Security", 1, id)
| extend resourceIdTemp = iff(properties.resourceDetails.id != "", properties.resourceDetails.id, extract("(.+)/providers/Microsoft.Security", 1, id))
| extend resourceId = iff(properties.resourceDetails.source =~ "OnPremiseSql", strcat(resourceIdTemp, "/servers/", properties.resourceDetails.serverName, "/databases/" , properties.resourceDetails.databaseName), resourceIdTemp)
| where assessmentKey =~ "{ASSESSMENT_KEY}"
| where subscriptionId == "{SUBSCRIPTION_ID}"
| project assessmentKey,
    subAssessmentId,
    resourceId,
    name=properties.displayName,
    description=properties.description,
    severity=properties.status.severity,
    status=properties.status.code,
    cause=properties.status.cause,
    category=properties.category,
    impact=properties.impact,
    remediation=properties.remediation,
    benchmarks=properties.additionalData.benchmarks
| where status == "Unhealthy"
"""
