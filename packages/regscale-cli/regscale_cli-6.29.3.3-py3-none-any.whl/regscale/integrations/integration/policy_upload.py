"""
Policy Upload Integration Module

This module provides centralized functionality for uploading policies to RegScale
from various integration sources. It handles policy creation with proper error handling
and field validation.

Usage:
    from regscale.integrations.integration.policy_upload import PolicyUploader, PolicyUploadRequest

    # Create upload request
    request = PolicyUploadRequest(
        policy_number="AWS-IAM-001",
        title="My Policy",
        description="Policy description",
        policy_type="AWS IAM",
        status="Active",
        parent_module="securityplans",
        parent_id=123
    )

    # Upload policy
    uploader = PolicyUploader()
    created_policy = uploader.upload_policy(request)
    print(f"Created policy ID: {created_policy['id']}")
"""

import json
import logging
from datetime import datetime
from typing import Optional, Dict, Any

from pydantic import BaseModel, Field, field_validator

from regscale.core.app.utils.api_handler import APIHandler
from regscale.models.regscale_models.regscale_model import RegScaleModel

logger = logging.getLogger("regscale")

# Date format constants
REGSCALE_DATE_FORMAT = "%Y-%m-%dT%H:%M:%S"  # ISO 8601 format required by RegScale API


class PolicyUploadError(Exception):
    """Exception raised when policy upload fails."""

    pass


class PolicyUploadRequest(BaseModel):
    """
    Request model for uploading a policy to RegScale.

    This model defines the required and optional fields for creating a policy
    in RegScale, with proper validation and default values.
    """

    policy_number: str = Field(..., description="Unique policy number/identifier", min_length=1, max_length=255)

    title: str = Field(..., description="Policy title", min_length=1, max_length=500)

    description: str = Field(..., description="Policy description (can include formatted text, JSON, etc.)")

    policy_type: str = Field(default="Custom", description="Type of policy (e.g., AWS IAM, CIS, NIST, Custom)")

    status: str = Field(default="Active", description="Policy status")

    parent_module: str = Field(..., description="Parent module type (securityplans or components)")

    parent_id: int = Field(..., description="ID of the parent Security Plan or Component", gt=0)

    date_approved: Optional[str] = Field(
        default=None, description="Date policy was approved (format: 'MMM DD, YYYY'). If None, uses current date."
    )

    expiration_date: Optional[str] = Field(
        default=None, description="Policy expiration date (format: 'MMM DD, YYYY'). If None, uses current date."
    )

    policy_owner_id: Optional[str] = Field(
        default=None, description="UUID of policy owner. If None, uses current user from auth token."
    )

    is_public: bool = Field(default=True, description="Whether policy is public")

    practice_level: Optional[str] = Field(default="", description="Practice level")

    process_level: Optional[str] = Field(default="", description="Process level")

    policy_template: Optional[str] = Field(default="", description="Policy template")

    policy_template_id: Optional[str] = Field(default="", description="Policy template ID")

    org_id: Optional[int] = Field(default=0, description="Organization ID")

    facility_id: Optional[int] = Field(default=None, description="Facility ID")

    @field_validator("status")
    @classmethod
    def validate_status(cls, v: str) -> str:
        """Validate policy status."""
        valid_statuses = ["Active", "Draft", "Archived", "Inactive"]
        if v not in valid_statuses:
            raise ValueError(f"Status must be one of: {', '.join(valid_statuses)}")
        return v

    @field_validator("parent_module")
    @classmethod
    def validate_parent_module(cls, v: str) -> str:
        """Validate parent module type."""
        valid_modules = ["securityplans", "components"]
        if v not in valid_modules:
            raise ValueError(f"Parent module must be one of: {', '.join(valid_modules)}")
        return v

    @field_validator("date_approved", "expiration_date")
    @classmethod
    def validate_date_format(cls, v: Optional[str]) -> Optional[str]:
        """Validate date format if provided."""
        if v is None:
            return v

        # Try to parse the date to ensure it's in correct ISO 8601 format
        # RegScale requires: YYYY-MM-DDTHH:MM:SS (e.g., "2025-12-16T11:28:33")
        try:
            datetime.strptime(v, REGSCALE_DATE_FORMAT)
            return v
        except ValueError:
            raise ValueError(
                f"Date must be in ISO 8601 format 'YYYY-MM-DDTHH:MM:SS' (e.g., '2025-12-16T11:28:33'), got: {v}"
            )

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "policy_number": "AWS-IAM-20251216-001",
                    "title": "AWS IAM Policy for Cloud Security",
                    "description": "IAM policy granting required permissions",
                    "policy_type": "AWS IAM",
                    "status": "Active",
                    "parent_module": "securityplans",
                    "parent_id": 123,
                }
            ]
        }
    }


class PolicyUploadResponse(BaseModel):
    """Response model for policy upload operations."""

    id: int = Field(..., description="RegScale policy ID")
    uuid: Optional[str] = Field(None, description="Policy UUID")
    policy_number: str = Field(..., description="Policy number")
    title: str = Field(..., description="Policy title")
    status: str = Field(..., description="Policy status")
    parent_id: int = Field(..., description="Parent ID")
    parent_module: str = Field(..., description="Parent module")
    date_created: Optional[str] = Field(None, description="Creation date")

    model_config = {"extra": "allow"}  # Allow additional fields from API response


class PolicyUploader:
    """
    Policy uploader service for creating policies in RegScale.

    This class handles the API communication and error handling for policy uploads,
    working around RegScale's field configuration requirements.
    """

    def __init__(self, api_handler: Optional[APIHandler] = None):
        """
        Initialize the policy uploader.

        Args:
            api_handler: Optional APIHandler instance. If None, creates a new one.
        """
        self.api_handler = api_handler or APIHandler()

    def _build_policy_payload(self, request: PolicyUploadRequest, policy_owner_id: str) -> Dict[str, Any]:
        """
        Build API payload for policy creation.

        Args:
            request: PolicyUploadRequest with policy details
            policy_owner_id: UUID of policy owner

        Returns:
            Dict containing the policy payload for RegScale API
        """
        payload = {
            "policyNumber": request.policy_number,
            "title": request.title,
            "description": request.description,
            "policyType": request.policy_type,
            "status": request.status,
            "parentModule": request.parent_module,
            "parentId": request.parent_id,
            "policyOwnerId": policy_owner_id,
            "isPublic": request.is_public,
        }

        # Only include date fields for Active policies
        # Draft policies should NOT have dates (tested with policies 13, 27)
        if request.status == "Active":
            now = datetime.now()
            current_date = now.strftime(REGSCALE_DATE_FORMAT)

            # Set expiration date to one year from now
            from dateutil.relativedelta import relativedelta

            expiration_datetime = now + relativedelta(years=1)
            default_expiration_date = expiration_datetime.strftime(REGSCALE_DATE_FORMAT)

            payload["dateApproved"] = request.date_approved or current_date
            payload["expirationDate"] = request.expiration_date or default_expiration_date

        return payload

    def _handle_api_response(self, response, payload: Dict[str, Any]) -> Dict[str, Any]:
        """
        Handle API response and extract created policy or raise error.

        Args:
            response: Response object from API call
            payload: The payload that was sent (for error logging)

        Returns:
            Dict containing the created policy data

        Raises:
            PolicyUploadError: If policy creation fails
        """
        if response is not None and response.status_code == 200:
            created_policy = response.json()
            logger.info("Successfully created policy ID %s: %s", created_policy.get("id"), created_policy.get("title"))
            return created_policy

        # Build detailed error message
        if response is not None:
            try:
                if hasattr(response, "text"):
                    error_text = response.text
                elif hasattr(response, "content"):
                    error_text = response.content.decode("utf-8")
                else:
                    error_text = str(response)
            except Exception as e:
                error_text = f"Could not read response: {e}"
            error_msg = f"Failed to create policy: {response.status_code} - {error_text}"
        else:
            error_msg = "Failed to create policy: No response from API"

        logger.error(error_msg)
        logger.error("Policy payload was: %s", json.dumps(payload, indent=2))
        raise PolicyUploadError(error_msg)

    def upload_policy(self, request: PolicyUploadRequest) -> Dict[str, Any]:
        """
        Upload a policy to RegScale.

        This method handles the creation of a policy in RegScale, managing field
        requirements and RegScale-specific configuration quirks.

        Args:
            request: PolicyUploadRequest with policy details

        Returns:
            Dict containing the created policy data from RegScale API

        Raises:
            ValueError: If request validation fails
            PolicyUploadError: If API request fails

        Example:
            >>> request = PolicyUploadRequest(
            ...     policy_number="POLICY-001",
            ...     title="My Policy",
            ...     description="Description",
            ...     parent_module="securityplans",
            ...     parent_id=123
            ... )
            >>> uploader = PolicyUploader()
            >>> result = uploader.upload_policy(request)
            >>> print(f"Created policy ID: {result['id']}")
        """
        # Get current user ID if not provided
        policy_owner_id = request.policy_owner_id or RegScaleModel.get_user_id()

        # Build payload for RegScale API
        payload = self._build_policy_payload(request, policy_owner_id)

        logger.info("Creating policy: %s", request.title)
        logger.debug("Policy payload: %s", json.dumps(payload, indent=2))

        # Create policy via API
        response = self.api_handler.post(endpoint="/api/policies", data=payload)

        # Handle response (returns created policy or raises PolicyUploadError)
        return self._handle_api_response(response, payload)

    def upload_policy_from_json(
        self,
        policy_json: Dict[str, Any],
        parent_module: str,
        parent_id: int,
        policy_number: Optional[str] = None,
        title: Optional[str] = None,
        policy_type: str = "Custom",
        status: str = "Active",
    ) -> Dict[str, Any]:
        """
        Create a policy from a JSON document (e.g., IAM policy, config file).

        This is a convenience method for creating policies where the policy content
        is a structured JSON document that should be embedded in the description.

        Args:
            policy_json: The policy JSON content (will be embedded in description)
            parent_module: "securityplans" or "components"
            parent_id: ID of parent Security Plan or Component
            policy_number: Optional custom policy number (auto-generated if None)
            title: Optional custom title (uses policy_type if None)
            policy_type: Type of policy (default: "Custom")
            status: Policy status (default: "Active")

        Returns:
            Dict containing the created policy data from RegScale API

        Example:
            >>> iam_policy = {
            ...     "Version": "2012-10-17",
            ...     "Statement": [{"Effect": "Allow", "Action": "*", "Resource": "*"}]
            ... }
            >>> uploader = PolicyUploader()
            >>> result = uploader.upload_policy_from_json(
            ...     policy_json=iam_policy,
            ...     parent_module="securityplans",
            ...     parent_id=123,
            ...     policy_type="AWS IAM"
            ... )
        """
        # Generate policy number if not provided
        if policy_number is None:
            timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
            policy_number = f"{policy_type.upper().replace(' ', '-')}-{timestamp}"

        # Generate title if not provided
        if title is None:
            title = f"{policy_type} Policy"

        # Format JSON for description
        policy_json_str = json.dumps(policy_json, indent=2)

        # Build description with embedded JSON
        description = f"""{policy_type} Policy Document

**Policy Content**:
```json
{policy_json_str}
```
"""

        # Create upload request
        request = PolicyUploadRequest(
            policy_number=policy_number,
            title=title,
            description=description,
            policy_type=policy_type,
            status=status,
            parent_module=parent_module,
            parent_id=parent_id,
        )

        return self.upload_policy(request)
