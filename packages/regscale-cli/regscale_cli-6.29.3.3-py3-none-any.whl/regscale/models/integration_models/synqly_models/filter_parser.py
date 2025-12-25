"""
Centralized parser for extracting filter definitions from Synqly capabilities.
Used by both code generation and query builder.
"""

import json
import re
from typing import Dict, List, Optional, Set, Tuple
import importlib.resources as pkg_resources

from regscale.models.integration_models.synqly_models.connector_types import ConnectorType


class FilterParser:
    """Parser for Synqly filter definitions from capabilities.json"""

    # Define which connectors support filtering
    FILTERABLE_CONNECTORS: Set[str] = {ConnectorType.Assets.value, ConnectorType.Vulnerabilities.value}

    def __init__(self, capabilities_data: Optional[List[dict]] = None):
        """
        Initialize the filter parser with provided or loaded capabilities.

        :param Optional[List[dict]] capabilities_data: Pre-loaded capabilities data.
            If None, will load from package resources.
        """
        if capabilities_data is None:
            self.capabilities_data = self._load_capabilities()
        else:
            self.capabilities_data = capabilities_data
        self.filter_mapping = self._build_filter_mapping()

    def _load_capabilities(self) -> List[dict]:
        """
        Load capabilities.json from package resources.

        :return: List of capability definitions
        :rtype: List[dict]
        """
        try:
            files = pkg_resources.files("regscale.models.integration_models.synqly_models")
            capabilities_file = files / "capabilities.json"
            with capabilities_file.open("r") as file:
                data = json.load(file)
                return data.get("result", [])
        except Exception as e:
            print(f"Error loading capabilities.json: {e}")
            return []

    def _build_filter_mapping(self) -> Dict[str, Dict[str, List[dict]]]:
        """
        Build comprehensive filter mapping for all providers.

        Structure:
        {
            'assets_armis_centrix': {
                'query_devices': [
                    {
                        'name': 'device.ip',
                        'type': 'string',
                        'operators': ['eq', 'ne', 'in', 'not_in'],
                        'values': []  # For enum types
                    },
                    ...
                ]
            },
            'vulnerabilities_qualys': {
                'query_findings': [...],
                'query_assets': [...]
            },
            ...
        }

        :return: Mapping of provider IDs to their operations and filters
        :rtype: Dict[str, Dict[str, List[dict]]]
        """
        filter_mapping = {}

        for provider in self.capabilities_data:
            provider_id = provider.get("id", "")
            connector_type = provider.get("connector", "")

            # Only process filterable connector types
            if connector_type not in self.FILTERABLE_CONNECTORS:
                continue

            # Skip mock providers if desired (they end with _mock)
            # if provider_id.endswith('_mock'):
            #     continue

            operations = provider.get("operations", [])
            for operation in operations:
                # Only process supported operations with filters
                if not operation.get("supported", False):
                    continue

                filters = operation.get("filters", [])
                if filters:
                    if provider_id not in filter_mapping:
                        filter_mapping[provider_id] = {}

                    operation_name = operation.get("name", "")
                    filter_mapping[provider_id][operation_name] = filters

        return filter_mapping

    def get_filters_for_provider(self, provider_id: str, operation: Optional[str] = None) -> List[dict]:
        """
        Get filters for a specific provider and optionally a specific operation.

        :param str provider_id: Provider ID (e.g., 'assets_armis_centrix')
        :param Optional[str] operation: Operation name (e.g., 'query_devices')
        :return: List of filter definitions
        :rtype: List[dict]
        """
        provider_filters = self.filter_mapping.get(provider_id, {})

        if operation:
            return provider_filters.get(operation, [])

        # Return all filters for all operations if no specific operation
        all_filters = []
        seen_fields = set()  # Avoid duplicates

        for op_filters in provider_filters.values():
            for filter_def in op_filters:
                field_name = filter_def.get("name", "")
                if field_name not in seen_fields:
                    all_filters.append(filter_def)
                    seen_fields.add(field_name)

        return all_filters

    def get_providers_with_filters(self, connector_type: str) -> List[str]:
        """
        Get list of providers that support filtering for a connector type.

        :param str connector_type: Connector type (e.g., 'assets', 'vulnerabilities')
        :return: List of provider IDs that have filters
        :rtype: List[str]
        """
        providers = []

        for provider_id, operations in self.filter_mapping.items():
            # Check if provider matches connector type and has filters
            if provider_id.startswith(f"{connector_type}_") and operations:
                providers.append(provider_id)

        # Sort for consistent ordering
        return sorted(providers)

    def has_filters(self, provider_id: str) -> bool:
        """
        Check if a provider has any filters defined.

        :param str provider_id: Provider ID to check
        :return: True if provider has filters
        :rtype: bool
        """
        return provider_id in self.filter_mapping and bool(self.filter_mapping[provider_id])

    @staticmethod
    def format_filter_string(field: str, operator: str, value: str) -> str:
        """
        Convert user input to Synqly filter format.

        :param str field: Field name (e.g., 'device.ip')
        :param str operator: Operator (e.g., 'eq', 'gte')
        :param str value: Filter value
        :return: Formatted filter string
        :rtype: str

        Example:
            format_filter_string('device.ip', 'eq', '192.168.1.1')
            Returns: 'device.ip[eq]192.168.1.1'
        """
        return f"{field}[{operator}]{value}"

    @staticmethod
    def parse_filter_string(filter_string: str) -> Optional[Tuple[str, str, str]]:
        """
        Parse a filter string into its components.

        :param str filter_string: Filter in format 'field[operator]value'
        :return: Tuple of (field, operator, value) or None if invalid
        :rtype: Optional[Tuple[str, str, str]]
        """
        match = re.match(r"^([a-z._]+)\[([a-z_]+)\](.+)$", filter_string, re.IGNORECASE)
        if match:
            return match.groups()
        return None

    def validate_filter(self, provider_id: str, filter_string: str) -> Tuple[bool, str]:
        """
        Validate a filter string against provider capabilities.

        :param str provider_id: Provider ID (e.g., 'assets_armis_centrix')
        :param str filter_string: Filter in format 'field[operator]value'
        :return: Tuple of (is_valid, error_message)
        :rtype: Tuple[bool, str]
        """
        # Parse the filter string
        parsed = self.parse_filter_string(filter_string)
        if not parsed:
            return False, f"Invalid filter format: {filter_string}. Expected format: field[operator]value"

        field, operator, value = parsed

        # Get all filters for this provider
        provider_filters = self.get_filters_for_provider(provider_id)

        if not provider_filters:
            return False, f"Provider '{provider_id}' does not support filtering"

        # Check if field exists
        field_filter = None
        for f in provider_filters:
            if f.get("name") == field:
                field_filter = f
                break

        if not field_filter:
            available_fields = [f.get("name", "") for f in provider_filters]
            return (
                False,
                f"Field '{field}' not supported by {provider_id}. Available fields: {', '.join(available_fields)}",
            )

        # Check if operator is valid for this field
        valid_operators = field_filter.get("operators", [])
        if operator not in valid_operators:
            return (
                False,
                f"Operator '{operator}' not valid for field '{field}'. Valid operators: {', '.join(valid_operators)}",
            )

        # Optionally validate value type and format
        field_type = field_filter.get("type", "string")

        # Handle comma-separated values for 'in' and 'not_in' operators
        if operator in ["in", "not_in"]:
            values_to_check = [v.strip() for v in value.split(",")]
        else:
            values_to_check = [value]

        for val in values_to_check:
            if field_type == "number":
                try:
                    float(val)
                except ValueError:
                    return False, f"Value '{val}' is not a valid number for field '{field}'"
            elif field_type == "enum":
                valid_values = field_filter.get("values", [])
                if valid_values and val not in valid_values:
                    return (
                        False,
                        f"Value '{val}' not valid for field '{field}'. Valid values: {', '.join(valid_values)}",
                    )

        return True, ""

    def get_operator_display_name(self, operator: str) -> str:
        """
        Get human-friendly display name for an operator.

        :param str operator: Operator code
        :return: Display name
        :rtype: str
        """
        operator_map = {
            "eq": "equals",
            "ne": "not equals",
            "in": "in list",
            "not_in": "not in list",
            "like": "matches pattern",
            "not_like": "does not match pattern",
            "gt": "greater than",
            "gte": "greater than or equal to",
            "lt": "less than",
            "lte": "less than or equal to",
        }
        return operator_map.get(operator, operator)

    def get_field_display_name(self, field: str) -> str:
        """
        Convert field name to human-friendly display name.

        :param str field: Field name (e.g., 'device.hw_info.serial_number')
        :return: Display name (e.g., 'Device Hardware Info Serial Number')
        :rtype: str
        """
        # Replace dots and underscores with spaces, then title case
        display = field.replace(".", " ").replace("_", " ").title()
        return display

    def get_connector_operations(self, connector_type: str) -> Dict[str, List[str]]:
        """
        Get all operations that support filtering for a connector type.

        :param str connector_type: Connector type (e.g., 'assets')
        :return: Dict mapping provider IDs to their filterable operations
        :rtype: Dict[str, List[str]]
        """
        operations_map = {}

        for provider_id, operations in self.filter_mapping.items():
            if provider_id.startswith(f"{connector_type}_"):
                operations_map[provider_id] = list(operations.keys())

        return operations_map

    def get_stats(self) -> dict:
        """
        Get statistics about loaded filters.

        :return: Dictionary with filter statistics
        :rtype: dict
        """
        stats = {
            "total_providers": len(self.capabilities_data),
            "providers_with_filters": len(self.filter_mapping),
            "total_filters": 0,
            "by_connector": {},
        }

        for connector in self.FILTERABLE_CONNECTORS:
            providers = self.get_providers_with_filters(connector)
            filter_count = sum(len(self.get_filters_for_provider(p)) for p in providers)
            stats["by_connector"][connector] = {"providers": len(providers), "filters": filter_count}
            stats["total_filters"] += filter_count

        return stats
