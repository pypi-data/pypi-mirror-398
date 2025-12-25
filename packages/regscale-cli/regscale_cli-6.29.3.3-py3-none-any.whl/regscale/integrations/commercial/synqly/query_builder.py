"""Interactive query builder for Synqly connector filters"""

import click
from typing import List, Optional
from regscale.models.integration_models.synqly_models.filter_parser import FilterParser

# Constants
INVALID_CHOICE_MSG = "Invalid choice"


def handle_build_query(connector: str, provider: Optional[str], validate: Optional[str], list_fields: bool):
    """
    Build and validate filter queries for Synqly connectors.

    Examples:
        # Build a filter (interactive by default)
        regscale assets build-query

        # List all fields for a specific provider
        regscale assets build-query --provider assets_armis_centrix --list-fields

        # Validate a filter string
        regscale assets build-query --provider assets_armis_centrix --validate "device.ip[eq]192.168.1.1"
    """
    parser = FilterParser()

    # Check for modes that require provider first
    if validate or list_fields:
        if not provider:
            click.echo("Error: --provider is required when using --validate or --list-fields options.", err=True)
            click.echo("\nAvailable providers with filters:")
            _list_providers(parser, connector)
            return

    # Handle provider-specific modes
    if provider:
        # Validate provider exists and has filters
        if not parser.has_filters(provider):
            click.echo(f"Error: Provider '{provider}' either doesn't exist or doesn't support filtering.", err=True)
            click.echo("\nAvailable providers with filters:")
            _list_providers(parser, connector)
            return

        # Handle specific modes
        if validate:
            _validate_filter(parser, provider, validate)
        elif list_fields:
            _list_fields(parser, provider)
        else:
            # Show provider info
            _show_provider_info(parser, provider)
    else:
        # Default behavior: interactive mode
        _interactive_mode_full(parser, connector)


def _list_providers(parser: FilterParser, connector: str):
    """List all providers that support filtering for a connector type"""
    providers = parser.get_providers_with_filters(connector)

    # Filter out mock providers
    filtered_providers = [p for p in providers if not p.endswith("_mock")]

    if not filtered_providers:
        click.echo(f"No providers found with filter support for {connector} connector.")
        return

    click.echo(f"\nProviders with filter support for {connector}:")
    click.echo("=" * 60)

    for provider_id in filtered_providers:
        filters = parser.get_filters_for_provider(provider_id)
        operations = parser.get_connector_operations(connector).get(provider_id, [])

        # Extract provider name from ID
        provider_name = provider_id.replace(f"{connector}_", "").replace("_", " ").title()

        click.echo(f"\n{provider_name}")
        click.echo(f"  Provider ID: {provider_id}")
        click.echo(f"  Supported operations: {', '.join(operations)}")
        click.echo(f"  Available filters: {len(filters)}")

        # Show first 3 filters as examples
        if filters:
            click.echo("  Example fields:")
            for i, f in enumerate(filters[:3], 1):
                ops = ", ".join(f.get("operators", []))
                click.echo(f"    - {f['name']} ({f['type']}) [{ops}]")
            if len(filters) > 3:
                click.echo(f"    ... and {len(filters) - 3} more")


def _list_fields(parser: FilterParser, provider: str):
    """List all available fields for a provider"""
    filters = parser.get_filters_for_provider(provider)

    if not filters:
        click.echo(f"No filters available for provider '{provider}'")
        return

    provider_name = provider.replace(provider.split("_")[0] + "_", "").replace("_", " ").title()
    click.echo(f"\nAvailable filters for {provider_name}:")
    click.echo("=" * 80)

    # Group by field prefix for better organization
    grouped = {}
    for f in filters:
        field_name = f["name"]
        prefix = field_name.split(".")[0] if "." in field_name else "root"
        if prefix not in grouped:
            grouped[prefix] = []
        grouped[prefix].append(f)

    for prefix, fields in sorted(grouped.items()):
        click.echo(f"\n{prefix.upper()} fields:")
        for f in sorted(fields, key=lambda x: x["name"]):
            field_display = parser.get_field_display_name(f["name"])
            operators = [parser.get_operator_display_name(op) for op in f.get("operators", [])]

            click.echo(f"  {f['name']}")
            click.echo(f"    Display: {field_display}")
            click.echo(f"    Type: {f['type']}")
            click.echo(f"    Operators: {', '.join(operators)}")

            # Show enum values if present
            if f.get("values"):
                click.echo(f"    Allowed values: {', '.join(f['values'])}")


def _validate_filter(parser: FilterParser, provider: str, filter_string: str):
    """Validate a filter string against provider capabilities"""
    # Check if it's a semicolon-separated list of filters
    if ";" in filter_string:
        filters = filter_string.split(";")
        click.echo(f"Validating {len(filters)} filters...")
        all_valid = True

        for i, single_filter in enumerate(filters, 1):
            single_filter = single_filter.strip()
            is_valid, error = parser.validate_filter(provider, single_filter)

            if is_valid:
                click.echo(f"  Filter {i} is valid: {single_filter}")
                # Parse and show the components
                field, operator, value = parser.parse_filter_string(single_filter)
                click.echo(f"    Field: {field}, Operator: {operator}, Value: {value}")
            else:
                click.echo(f"  Filter {i} is invalid: {single_filter}", err=True)
                click.echo(f"    Error: {error}", err=True)
                all_valid = False

        if all_valid:
            click.echo(f'\nAll filters are valid. Complete filter string: "{filter_string}"')
        else:
            click.echo("\nSome filters are invalid. Please fix the errors above.", err=True)
    else:
        # Single filter validation (original behavior)
        is_valid, error = parser.validate_filter(provider, filter_string)

        if is_valid:
            click.echo(f"Filter is valid: {filter_string}")

            # Parse and show the components
            field, operator, value = parser.parse_filter_string(filter_string)
            click.echo("\nParsed components:")
            click.echo(f"  Field: {field}")
            click.echo(f"  Operator: {operator} ({parser.get_operator_display_name(operator)})")
            click.echo(f"  Value: {value}")
        else:
            click.echo(f"Filter is invalid: {error}", err=True)


def _interactive_mode_full(
    parser: FilterParser,
    connector: str,
    provider: Optional[str] = None,
    accumulated_filters: Optional[List[str]] = None,
):
    """Full interactive mode to build filters step by step"""
    # Initialize accumulated filters on first call
    if accumulated_filters is None:
        accumulated_filters = []

    # If no provider specified, let user choose
    if not provider:
        provider = _choose_provider_interactive(parser, connector)
        if not provider:
            return

    # Get operation
    selected_operation = _select_operation(parser, provider)
    if not selected_operation:
        return

    # Get field
    selected_field = _select_field(parser, provider, selected_operation)
    if not selected_field:
        return

    # Get operator
    selected_operator = _select_operator(parser, selected_field)
    if not selected_operator:
        return

    # Get value
    value = _get_filter_value(selected_field)
    if value is None:
        return

    # Build and validate filter
    filter_str = _build_and_validate_filter(parser, provider, selected_field["name"], selected_operator, value)
    if not filter_str:
        return

    # Add to accumulated filters
    accumulated_filters.append(filter_str)

    # Show results with all accumulated filters
    _display_filter_result(provider, accumulated_filters)

    # Ask if they want to add more filters
    click.echo("\nWould you like to add another filter?")
    add_more = click.confirm("Add another filter", default=False)

    if add_more:
        _interactive_mode_full(
            parser, provider.split("_")[0], provider, accumulated_filters
        )  # Recursive call with accumulated filters


def _select_operation(parser: FilterParser, provider: str) -> Optional[str]:
    """Select an operation for the provider"""
    operations = parser.get_connector_operations(provider.split("_")[0]).get(provider, [])
    if not operations:
        click.echo(f"No operations available for {provider}")
        return None

    click.echo("\nInteractive Query Builder")
    click.echo("=" * 60)
    click.echo(f"Provider: {provider}")

    click.echo("\nStep 1: Choose operation")
    click.echo("-" * 30)
    for i, op in enumerate(operations, 1):
        click.echo(f"  {i}. {op}")

    operation_choice = click.prompt("\nSelect operation (number)", type=int)
    if operation_choice < 1 or operation_choice > len(operations):
        click.echo(INVALID_CHOICE_MSG)
        return None

    selected = operations[operation_choice - 1]
    click.echo(f"Selected: {selected}")
    return selected


def _select_field(parser: FilterParser, provider: str, operation: str) -> Optional[dict]:
    """Select a field to filter on"""
    filters = parser.get_filters_for_provider(provider, operation)
    if not filters:
        click.echo(f"No filters available for operation '{operation}'")
        return None

    click.echo("\nStep 2: Choose field to filter")
    click.echo("-" * 30)
    for i, f in enumerate(filters, 1):
        click.echo(f"  {i}. {f['name']} ({f['type']})")

    field_choice = click.prompt("\nSelect field (number)", type=int)
    if field_choice < 1 or field_choice > len(filters):
        click.echo(INVALID_CHOICE_MSG)
        return None

    selected = filters[field_choice - 1]
    click.echo(f"Selected: {selected['name']}")
    return selected


def _select_operator(parser: FilterParser, field: dict) -> Optional[str]:
    """Select an operator for the field"""
    operators = field.get("operators", [])

    click.echo("\nStep 3: Choose operator")
    click.echo("-" * 30)
    for i, op in enumerate(operators, 1):
        display = parser.get_operator_display_name(op)
        click.echo(f"  {i}. {op} ({display})")

    operator_choice = click.prompt("\nSelect operator (number)", type=int)
    if operator_choice < 1 or operator_choice > len(operators):
        click.echo(INVALID_CHOICE_MSG)
        return None

    selected = operators[operator_choice - 1]
    click.echo(f"Selected: {selected}")
    return selected


def _get_filter_value(field: dict) -> Optional[str]:
    """Get the value for the filter"""
    click.echo("\nStep 4: Enter value")
    click.echo("-" * 30)

    if field.get("values"):
        # Enum field - show choices
        click.echo("Allowed values:")
        for i, v in enumerate(field["values"], 1):
            click.echo(f"  {i}. {v}")

        value_choice = click.prompt("\nSelect value (number)", type=int)
        if value_choice < 1 or value_choice > len(field["values"]):
            click.echo(INVALID_CHOICE_MSG)
            return None
        return field["values"][value_choice - 1]

    # Free text/number
    if field.get("type") == "number":
        value = click.prompt("Enter numeric value", type=str)
        try:
            float(value)
            return value
        except ValueError:
            click.echo("Invalid number value", err=True)
            return None

    return click.prompt("Enter value", type=str)


def _build_and_validate_filter(
    parser: FilterParser, provider: str, field_name: str, operator: str, value: str
) -> Optional[str]:
    """Build and validate the filter string"""
    filter_str = parser.format_filter_string(field_name, operator, value)

    is_valid, error = parser.validate_filter(provider, filter_str)
    if not is_valid:
        click.echo(f"\nFilter validation failed: {error}", err=True)
        return None

    return filter_str


def _display_filter_result(provider: str, filters: List[str]):
    """Display the created filters and command"""
    click.echo("\n" + "=" * 60)
    if len(filters) == 1:
        click.echo("Filter created successfully.")
    else:
        click.echo(f"{len(filters)} filters created successfully.")
    click.echo("=" * 60)

    click.echo("\nFilter(s):")
    for i, filter_str in enumerate(filters, 1):
        click.echo(f"  {i}. {filter_str}")

    connector = provider.split("_")[0]
    filter_flag = "asset_filter" if connector == "vulnerabilities" else "filter"

    click.echo("\nComplete command:")
    provider_name = provider.replace(provider.split("_")[0] + "_", "")

    # Build command with semicolon-separated filters
    if filters:
        filter_string = ";".join(filters)
        filter_option = f'--{filter_flag} "{filter_string}"'
    else:
        filter_option = ""

    example_cmd = f"regscale {provider.split('_')[0]} sync_{provider_name} --regscale_ssp_id <SSP_ID> {filter_option}"
    click.echo(f"  {example_cmd}")


def _choose_provider_interactive(parser: FilterParser, connector: str) -> Optional[str]:
    """Let user choose a provider interactively"""
    providers = parser.get_providers_with_filters(connector)

    # Filter out mock providers and those without click commands
    # Mock providers end with '_mock', and we only want providers that have actual integrations
    filtered_providers = []
    for provider_id in providers:
        # Skip mock providers
        if provider_id.endswith("_mock"):
            continue
        # Only include providers that would have generated click commands
        # These are the ones with actual integration configurations
        filtered_providers.append(provider_id)

    if not filtered_providers:
        click.echo(f"No providers found with filter support for {connector}")
        return None

    click.echo(f"\nAvailable {connector} providers with filter support:")
    click.echo("-" * 40)

    for i, provider_id in enumerate(filtered_providers, 1):
        provider_name = provider_id.replace(f"{connector}_", "").replace("_", " ").title()
        filter_count = len(parser.get_filters_for_provider(provider_id))
        click.echo(f"  {i}. {provider_name} ({filter_count} filters)")

    choice = click.prompt("\nSelect provider (number)", type=int)

    if choice < 1 or choice > len(filtered_providers):
        click.echo(INVALID_CHOICE_MSG)
        return None

    return filtered_providers[choice - 1]


def _build_filter_interactive(
    parser: FilterParser, provider: str, filters: List[dict], field_input: str
) -> Optional[str]:
    """Build a single filter interactively"""
    # Find matching field
    matching_field = _find_matching_field(filters, field_input)
    if not matching_field:
        click.echo(f"Field '{field_input}' not found. Use 'list' to see available fields.", err=True)
        return None

    field_name = matching_field["name"]
    field_type = matching_field["type"]
    operators = matching_field.get("operators", [])

    click.echo(f"\nField: {field_name} (type: {field_type})")

    # Show and get operator
    operator = _prompt_for_operator(parser, operators)
    if not operator:
        return None

    # Get value
    value = _prompt_for_value(matching_field)
    if value is None:
        return None

    # Build and validate filter
    return _create_validated_filter(parser, provider, field_name, operator, value)


def _find_matching_field(filters: List[dict], field_input: str) -> Optional[dict]:
    """Find a field matching the user input"""
    field_lower = field_input.lower()
    for f in filters:
        if f["name"].lower() == field_lower or f["name"].lower().endswith(f".{field_lower}"):
            return f
    return None


def _prompt_for_operator(parser: FilterParser, operators: List[str]) -> Optional[str]:
    """Prompt user to select an operator"""
    click.echo("Available operators:")
    for op in operators:
        display = parser.get_operator_display_name(op)
        click.echo(f"  - {op} ({display})")

    return click.prompt("Operator", type=click.Choice(operators))


def _prompt_for_value(field: dict) -> Optional[str]:
    """Prompt user for a value based on field type"""
    if field.get("values"):
        # Enum field
        click.echo(f"Allowed values: {', '.join(field['values'])}")
        return click.prompt("Value", type=click.Choice(field["values"]))

    # Free text/number
    if field.get("type") == "number":
        value = click.prompt("Value", type=str)
        try:
            float(value)
            return value
        except ValueError:
            click.echo("Invalid number value", err=True)
            return None

    return click.prompt("Value", type=str)


def _create_validated_filter(
    parser: FilterParser, provider: str, field_name: str, operator: str, value: str
) -> Optional[str]:
    """Create and validate a filter string"""
    filter_str = parser.format_filter_string(field_name, operator, value)
    is_valid, error = parser.validate_filter(provider, filter_str)

    if is_valid:
        click.echo(f"Filter created: {filter_str}")
        return filter_str

    click.echo(f"Filter validation failed: {error}", err=True)
    return None


def _show_field_list(filters: List[dict]):
    """Show a compact list of available fields"""
    click.echo("\nAvailable fields:")
    for f in sorted(filters, key=lambda x: x["name"]):
        ops = ", ".join(f.get("operators", []))
        click.echo(f"  - {f['name']} ({f['type']}) [{ops}]")


def _show_interactive_help():
    """Show help for interactive mode"""
    click.echo("\nInteractive Mode Commands:")
    click.echo("  <field_name>  - Start building a filter for this field")
    click.echo("  list          - Show all available fields")
    click.echo("  clear         - Clear all filters")
    click.echo("  done          - Finish and show the final query")
    click.echo("  help          - Show this help message")


def _show_provider_info(parser: FilterParser, provider: str):
    """Show general information about a provider's filtering capabilities"""
    filters = parser.get_filters_for_provider(provider)
    operations = list(parser.filter_mapping.get(provider, {}).keys())

    provider_name = provider.replace(provider.split("_")[0] + "_", "").replace("_", " ").title()

    click.echo(f"\nProvider: {provider_name}")
    click.echo(f"Provider ID: {provider}")
    click.echo(f"Supported operations: {', '.join(operations)}")
    click.echo(f"Total available filters: {len(filters)}")

    click.echo("\nExample filters:")
    # Show a few example filters
    for f in filters[:3]:
        example_value = "value"
        if f["type"] == "number":
            example_value = "100"
        elif f.get("values"):
            example_value = f["values"][0]

        example = parser.format_filter_string(f["name"], f["operators"][0], example_value)
        click.echo(f"  {example}")

    click.echo("\nUse --list-fields to see all available fields")
    click.echo("Use --validate '<filter>' to validate a filter string")
