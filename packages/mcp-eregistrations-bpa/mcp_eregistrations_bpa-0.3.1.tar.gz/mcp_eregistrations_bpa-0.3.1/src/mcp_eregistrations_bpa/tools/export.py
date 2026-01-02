"""MCP tools for BPA service export operations.

This module provides tools for exporting complete BPA service definitions.

The export endpoint returns large JSON payloads (5-15MB) containing:
- Service metadata
- Registrations, determinants, roles, bots
- Form definitions (Form.io schemas)
- Translations, tutorials, catalogs

For large exports (>5MB), the data is saved to a file and a summary is returned.

API Endpoint used:
- POST /download_service/{service_id} - Export complete service definition
"""

from __future__ import annotations

import json
import tempfile
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from mcp.server.fastmcp import Context
from mcp.server.fastmcp.exceptions import ToolError

# Note: ServerSession moved out of TYPE_CHECKING for runtime type annotation evaluation
from mcp.server.session import ServerSession

from mcp_eregistrations_bpa.audit.context import (
    NotAuthenticatedError,
    get_current_user_email,
)
from mcp_eregistrations_bpa.audit.logger import AuditLogger
from mcp_eregistrations_bpa.bpa_client import BPAClient
from mcp_eregistrations_bpa.bpa_client.errors import (
    BPAClientError,
    BPANotFoundError,
    translate_error,
)
from mcp_eregistrations_bpa.tools.yaml_transformer import (
    TransformationError,
    YAMLTransformer,
)

__all__ = [
    "service_export_raw",
    "service_to_yaml",
    "service_copy",
    "register_export_tools",
]

# Threshold for saving to file instead of returning inline (5MB for JSON)
LARGE_EXPORT_THRESHOLD_BYTES = 5 * 1024 * 1024

# Threshold for YAML output (500KB)
LARGE_YAML_THRESHOLD_BYTES = 500 * 1024


def _generate_export_summary(
    data: dict[str, Any],
    size_bytes: int,
    *,
    include_forms: bool = True,
    include_translations: bool = True,
    include_catalogs: bool = True,
) -> dict[str, Any]:
    """Generate a summary of the exported service.

    Args:
        data: The complete export data.
        size_bytes: Size of the export in bytes.
        include_forms: Whether forms were included in export.
        include_translations: Whether translations were included in export.
        include_catalogs: Whether catalogs were included in export.

    Returns:
        dict: Summary statistics about the export.
    """
    # Count registrations
    registrations = data.get("registrations", [])
    registration_count = len(registrations) if isinstance(registrations, list) else 0

    # Count determinants
    determinants = data.get("determinants", [])
    determinant_count = len(determinants) if isinstance(determinants, list) else 0

    # Count roles
    roles = data.get("roles", [])
    role_count = len(roles) if isinstance(roles, list) else 0

    # Count bots
    bots = data.get("bots", [])
    bot_count = len(bots) if isinstance(bots, list) else 0

    # Count fields from forms
    field_count = 0
    for form_key in ["applicantForm", "guideForm", "sendFileForm", "paymentForm"]:
        form = data.get(form_key)
        if form and isinstance(form, dict):
            form_schema = form.get("formSchema")
            if form_schema and isinstance(form_schema, dict):
                components = form_schema.get("components", [])
                field_count += _count_form_components(components)

    # Build excluded sections list
    excluded_sections: list[str] = []
    if not include_forms:
        excluded_sections.append("forms")
    if not include_translations:
        excluded_sections.append("translations")
    if not include_catalogs:
        excluded_sections.append("catalogs")

    summary: dict[str, Any] = {
        "service_name": data.get("name", "Unknown"),
        "service_id": data.get("id"),
        "registration_count": registration_count,
        "determinant_count": determinant_count,
        "role_count": role_count,
        "bot_count": bot_count,
        "field_count": field_count,
        "size_bytes": size_bytes,
        "size_mb": round(size_bytes / (1024 * 1024), 2),
    }

    # Add selection info if any sections were excluded
    if excluded_sections:
        summary["excluded_sections"] = excluded_sections

    return summary


def _count_form_components(components: list[Any]) -> int:
    """Recursively count form components (fields).

    Args:
        components: List of Form.io components.

    Returns:
        int: Total count of form components.
    """
    count = 0
    for comp in components:
        if not isinstance(comp, dict):
            continue
        # Count this component if it has a key (it's a field)
        if comp.get("key"):
            count += 1
        # Recursively count nested components
        nested = comp.get("components", [])
        if isinstance(nested, list):
            count += _count_form_components(nested)
        # Handle columns layout
        columns = comp.get("columns", [])
        if isinstance(columns, list):
            for col in columns:
                if isinstance(col, dict):
                    col_comps = col.get("components", [])
                    if isinstance(col_comps, list):
                        count += _count_form_components(col_comps)
    return count


def _save_export_to_file(
    data: dict[str, Any],
    service_id: str,
) -> str:
    """Save export data to a temporary file.

    Args:
        data: The export data to save.
        service_id: The service ID for the filename.

    Returns:
        str: Path to the saved file.
    """
    timestamp = datetime.now(UTC).strftime("%Y%m%dT%H%M%S")
    filename = f"bpa_export_{service_id}_{timestamp}.json"

    # Use system temp directory
    temp_dir = Path(tempfile.gettempdir())
    file_path = temp_dir / filename

    with open(file_path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

    return str(file_path)


async def service_export_raw(
    service_id: str | int,
    include_all: bool = True,
    include_forms: bool = True,
    include_translations: bool = True,
    include_catalogs: bool = True,
    catalog_ids: list[str] | None = None,
    ctx: Context[ServerSession, None] | None = None,
) -> dict[str, Any]:
    """Export complete service definition as raw JSON.

    Exports the full service configuration from BPA including all components:
    forms, registrations, determinants, roles, bots, costs, and more.

    For large exports (>5MB), the data is saved to a file and the file path
    is returned along with a summary. This prevents memory issues and allows
    for efficient processing of large service definitions.

    For long-running exports, progress indication is provided via the MCP
    context if available.

    Args:
        service_id: BPA service UUID.
        include_all: Include all components (default True). When False,
            only core service metadata is exported. Granular options are
            ignored when include_all=False.
        include_forms: Include form schemas (guide, applicant, sendFile, payment).
            Default True. Only applies when include_all=True.
        include_translations: Include service translations. Default True.
            Only applies when include_all=True.
        include_catalogs: Include catalog definitions. Default True.
            Only applies when include_all=True.
        catalog_ids: Filter to specific catalog IDs. If None, all catalogs
            are included. Only applies when include_catalogs=True.
        ctx: Optional MCP context for progress reporting.

    Returns:
        dict: Export result containing:
            - export_data: Complete service JSON (if <5MB)
            - file_path: Path to saved file (if >=5MB)
            - summary: Quick stats (service name, counts, excluded sections)
            - metadata: Export timestamp, service_id
    """
    # Build export options
    options: dict[str, Any] | None = None

    if not include_all:
        # Minimal export: only core metadata (granular options ignored)
        options = {
            "serviceSelected": True,
            "registrationsSelected": True,
            "costsSelected": False,
            "requirementsSelected": False,
            "resultsSelected": False,
            "activityConditionsSelected": False,
            "registrationLawsSelected": False,
            "serviceLocationsSelected": False,
            "serviceTutorialsSelected": False,
            "serviceTranslationsSelected": False,
            "guideFormSelected": False,
            "applicantFormSelected": False,
            "sendFileFormSelected": False,
            "paymentFormSelected": False,
            "catalogsSelected": False,
            "rolesSelected": False,
            "determinantsSelected": False,
            "printDocumentsSelected": False,
            "botsSelected": False,
            "copyService": False,
        }
        # Force granular options to match include_all=False behavior for summary
        include_forms = False
        include_translations = False
        include_catalogs = False
    else:
        # Check if any granular options differ from defaults
        has_granular_options = (
            not include_forms
            or not include_translations
            or not include_catalogs
            or catalog_ids is not None
        )

        if has_granular_options:
            # Build selective options with granular control
            options = {
                "serviceSelected": True,
                "registrationsSelected": True,
                "costsSelected": True,
                "requirementsSelected": True,
                "resultsSelected": True,
                "activityConditionsSelected": True,
                "registrationLawsSelected": True,
                "serviceLocationsSelected": True,
                "serviceTutorialsSelected": True,
                "serviceTranslationsSelected": include_translations,
                "guideFormSelected": include_forms,
                "applicantFormSelected": include_forms,
                "sendFileFormSelected": include_forms,
                "paymentFormSelected": include_forms,
                "catalogsSelected": include_catalogs,
                "rolesSelected": True,
                "determinantsSelected": True,
                "printDocumentsSelected": True,
                "botsSelected": True,
                "copyService": False,
            }
            # Add catalog filter if specified
            if include_catalogs and catalog_ids is not None:
                options["catalogsToCopy"] = catalog_ids

    # Report progress: starting export
    if ctx:
        await ctx.report_progress(
            progress=0.1,
            total=1.0,
            message=f"Starting export for service {service_id}...",
        )

    try:
        async with BPAClient() as client:
            # Report progress: connected, requesting export
            if ctx:
                await ctx.report_progress(
                    progress=0.2,
                    total=1.0,
                    message="Connected to BPA. Requesting service export...",
                )

            try:
                export_data, size_bytes = await client.download_service(
                    str(service_id),
                    options=options,
                )
            except BPANotFoundError:
                raise ToolError(
                    f"[Service not found]: Service ID '{service_id}' does not exist. "
                    "[Verify the service ID using service_list]"
                )

            # Report progress: export received
            if ctx:
                size_mb = size_bytes / (1024 * 1024)
                await ctx.report_progress(
                    progress=0.8,
                    total=1.0,
                    message=f"Export received ({size_mb:.2f} MB). Processing...",
                )
    except ToolError:
        raise
    except BPAClientError as e:
        raise translate_error(e, resource_type="service", resource_id=service_id)

    # Generate summary with selection options
    summary = _generate_export_summary(
        export_data,
        size_bytes,
        include_forms=include_forms,
        include_translations=include_translations,
        include_catalogs=include_catalogs,
    )

    # Build metadata
    metadata = {
        "exported_at": datetime.now(UTC).isoformat(),
        "service_id": str(service_id),
        "include_all": include_all,
    }

    # Handle large exports
    if size_bytes >= LARGE_EXPORT_THRESHOLD_BYTES:
        file_path = _save_export_to_file(export_data, str(service_id))

        # Report progress: complete
        if ctx:
            await ctx.report_progress(
                progress=1.0,
                total=1.0,
                message=f"Export complete. Saved to {file_path}",
            )

        return {
            "file_path": file_path,
            "summary": summary,
            "metadata": metadata,
            "message": (
                f"Export saved to file ({summary['size_mb']} MB). "
                "Use the file_path to access the full data. "
                "Note: Temporary files should be cleaned up after use."
            ),
        }

    # Report progress: complete
    if ctx:
        await ctx.report_progress(
            progress=1.0,
            total=1.0,
            message="Export complete.",
        )

    # Return inline for smaller exports
    return {
        "export_data": export_data,
        "summary": summary,
        "metadata": metadata,
    }


def _save_yaml_to_file(
    content: str,
    service_id: str,
    extension: str = "yaml",
) -> str:
    """Save YAML/JSON content to a temporary file.

    Args:
        content: The YAML or JSON content to save.
        service_id: The service ID for the filename.
        extension: File extension to use (default "yaml").

    Returns:
        str: Path to the saved file.
    """
    timestamp = datetime.now(UTC).strftime("%Y%m%dT%H%M%S")
    filename = f"bpa_service_{service_id}_{timestamp}.{extension}"

    # Use system temp directory
    temp_dir = Path(tempfile.gettempdir())
    file_path = temp_dir / filename

    with open(file_path, "w", encoding="utf-8") as f:
        f.write(content)

    return str(file_path)


async def service_to_yaml(
    service_id: str | int,
    export_data: dict[str, Any] | None = None,
    include_metadata: bool = True,
    format: str = "yaml",
    ctx: Context[ServerSession, None] | None = None,
) -> dict[str, Any]:
    """Transform a BPA service export to clean, readable YAML or JSON format.

    Converts the raw JSON export from BPA into a human-readable
    representation optimized for review, version control, and AI analysis.

    The transformation includes:
    - Summary section at top with counts and statistics
    - camelCase to snake_case key conversion
    - Form.io schema parsing (extracts essential field properties)
    - Determinant condition parsing (readable format)
    - Metadata preservation for re-import capability

    For large outputs (>500KB), the data is saved to a file and
    the file path is returned with a summary.

    Args:
        service_id: BPA service UUID. Used to fetch export if export_data
            is not provided.
        export_data: Optional pre-fetched export data from service_export_raw.
            If None, the service will be exported automatically.
        include_metadata: Include _metadata section with IDs for re-import.
            Default True.
        format: Output format - "yaml" (default) or "json". Both use the
            same optimized schema, just different serialization.
        ctx: Optional MCP context for progress reporting.

    Returns:
        dict: Transformation result containing:
            - yaml_content/json_content: The content string (if <500KB)
            - file_path: Path to saved file (if >=500KB)
            - summary: Section counts and size info
            - metadata: Transformation timestamp, service_id

    Raises:
        ToolError: If service not found, export fails, transformation fails,
            or invalid format specified.
    """
    # Validate format parameter
    valid_formats = ("yaml", "json")
    if format.lower() not in valid_formats:
        raise ToolError(
            f"[Invalid format]: '{format}' is not valid. "
            f"[Use one of: {', '.join(valid_formats)}]"
        )
    # Report progress: starting
    if ctx:
        await ctx.report_progress(
            progress=0.1,
            total=1.0,
            message="Starting YAML transformation...",
        )

    # Get export data if not provided
    if export_data is None:
        if ctx:
            await ctx.report_progress(
                progress=0.2,
                total=1.0,
                message=f"Fetching export for service {service_id}...",
            )

        # Fetch raw export
        result = await service_export_raw(
            service_id=service_id,
            include_all=True,
            ctx=None,  # Don't double-report progress
        )

        # Handle file-based exports (large files)
        if "file_path" in result:
            # Read the export from file
            with open(result["file_path"], encoding="utf-8") as f:
                export_data = json.load(f)
        else:
            export_data = result.get("export_data", {})

    # Normalize format
    output_format = format.lower()

    if ctx:
        await ctx.report_progress(
            progress=0.5,
            total=1.0,
            message=f"Transforming to {output_format.upper()}...",
        )

    # Transform using the transformer
    transformer = YAMLTransformer(include_metadata=include_metadata)

    try:
        # Get the optimized data structure
        data_dict, transform_summary = transformer.transform_to_dict(export_data)

        # Serialize to requested format
        if output_format == "yaml":
            import yaml as yaml_module

            content = yaml_module.dump(
                data_dict,
                default_flow_style=False,
                allow_unicode=True,
                sort_keys=False,
                width=120,
            )
            content_key = "yaml_content"
            file_ext = "yaml"
        else:  # json
            content = json.dumps(data_dict, indent=2, ensure_ascii=False)
            content_key = "json_content"
            file_ext = "json"

    except TransformationError as e:
        # Save raw JSON for debugging
        raw_file_path = _save_export_to_file(export_data, str(service_id))
        raise ToolError(
            f"[Transformation failed]: {e}. [Raw JSON preserved at {raw_file_path}]"
        )

    # Calculate size
    content_size = len(content.encode("utf-8"))

    # Build result metadata
    result_metadata = {
        "transformed_at": datetime.now(UTC).isoformat(),
        "service_id": str(service_id),
        "schema_version": "1.0",
        "include_metadata": include_metadata,
        "format": output_format,
    }

    # Merge transformer summary with size info
    summary = {
        **transform_summary,
        "size_bytes": content_size,
        "size_kb": round(content_size / 1024, 2),
        "format": output_format,
    }

    # Handle large output
    if content_size >= LARGE_YAML_THRESHOLD_BYTES:
        file_path = _save_yaml_to_file(content, str(service_id), extension=file_ext)

        if ctx:
            await ctx.report_progress(
                progress=1.0,
                total=1.0,
                message=f"{output_format.upper()} saved to {file_path}",
            )

        return {
            "file_path": file_path,
            "summary": summary,
            "metadata": result_metadata,
            "message": (
                f"{output_format.upper()} saved to file ({summary['size_kb']} KB). "
                "Use the file_path to access the full content. "
                "Note: Temporary files should be cleaned up after use."
            ),
        }

    # Report completion
    if ctx:
        await ctx.report_progress(
            progress=1.0,
            total=1.0,
            message=f"{output_format.upper()} transformation complete.",
        )

    return {
        content_key: content,
        "summary": summary,
        "metadata": result_metadata,
    }


async def service_copy(
    source_service_id: str | int,
    new_name: str | None = None,
    include_forms: bool = True,
    include_roles: bool = True,
    include_determinants: bool = True,
    include_bots: bool = True,
    include_catalogs: bool = True,
    include_translations: bool = False,
    include_tutorials: bool = False,
    catalog_ids: list[str] | None = None,
    ctx: Context[ServerSession, None] | None = None,
) -> dict[str, Any]:
    """Create a copy of an existing BPA service with a new name.

    This operation follows the audit-before-write pattern:
    1. Validate parameters (pre-flight, no audit if validation fails)
    2. Fetch source service to verify it exists and get name
    3. Create PENDING audit record
    4. Execute POST /download_service API call with copyService=true
    5. Update audit record to SUCCESS or FAILED

    The copy operation uses the same export endpoint with special flags
    to create a duplicate of the service with a new name.

    Args:
        source_service_id: UUID of the service to copy.
        new_name: Name for the new service. If None, defaults to
            "{original_name} - copy".
        include_forms: Copy form schemas (guide, applicant, sendFile, payment).
            Default True.
        include_roles: Copy workflow roles. Default True.
        include_determinants: Copy determinant rules. Default True.
        include_bots: Copy bot configurations. Default True.
        include_catalogs: Copy catalog definitions. Default True.
        include_translations: Copy translations. Default False.
        include_tutorials: Copy tutorials. Default False.
        catalog_ids: Copy only specific catalogs by ID. If None, all catalogs
            are copied (when include_catalogs=True).
        ctx: Optional MCP context for progress reporting.

    Returns:
        dict: Copy result containing:
            - new_service_id: UUID of the created copy
            - new_service_name: Name of the new service
            - source_service_id: UUID of the original service
            - source_service_name: Name of the original service
            - components_copied: List of component types that were copied
            - components_excluded: List of component types that were excluded
            - warnings: List of potential issues (e.g., broken references)
            - audit_id: UUID of the audit record

    Raises:
        ToolError: If validation fails, source not found, permission denied,
            or API error.
    """
    # Pre-flight validation
    if not source_service_id or str(source_service_id).strip() == "":
        raise ToolError(
            "[Validation error]: source_service_id is required. "
            "[Use service_list to find available services]"
        )

    if new_name is not None and new_name.strip() == "":
        raise ToolError(
            "[Validation error]: new_name cannot be empty whitespace. "
            "[Provide a valid name or omit to use default naming]"
        )

    # Get authenticated user for audit
    try:
        user_email = get_current_user_email()
    except NotAuthenticatedError as e:
        raise ToolError(str(e))

    # Fetch source service to verify it exists and get original name
    if ctx:
        await ctx.report_progress(
            progress=0.1,
            total=1.0,
            message=f"Verifying source service {source_service_id}...",
        )

    try:
        async with BPAClient() as client:
            try:
                source_service = await client.get(
                    f"/service/{source_service_id}",
                    resource_type="service",
                )
            except BPANotFoundError:
                raise ToolError(
                    f"[Service not found]: Service ID '{source_service_id}' "
                    "does not exist. [Use service_list to see available services]"
                )

            source_name = source_service.get("name", "Unknown")

            # Determine new service name
            target_name = new_name.strip() if new_name else f"{source_name} - copy"

            # Build copy payload
            copy_options = _build_copy_payload(
                new_service_name=target_name,
                include_forms=include_forms,
                include_roles=include_roles,
                include_determinants=include_determinants,
                include_bots=include_bots,
                include_catalogs=include_catalogs,
                include_translations=include_translations,
                include_tutorials=include_tutorials,
                catalog_ids=catalog_ids,
            )

            # Track what will be copied/excluded
            components_copied = ["registrations"]  # Always copied
            components_excluded = []

            if include_forms:
                components_copied.append("forms")
            else:
                components_excluded.append("forms")

            if include_roles:
                components_copied.append("roles")
            else:
                components_excluded.append("roles")

            if include_determinants:
                components_copied.append("determinants")
            else:
                components_excluded.append("determinants")

            if include_bots:
                components_copied.append("bots")
            else:
                components_excluded.append("bots")

            if include_catalogs:
                components_copied.append("catalogs")
            else:
                components_excluded.append("catalogs")

            if include_translations:
                components_copied.append("translations")
            else:
                components_excluded.append("translations")

            if include_tutorials:
                components_copied.append("tutorials")
            else:
                components_excluded.append("tutorials")

            # Create audit record BEFORE API call (audit-before-write pattern)
            audit_logger = AuditLogger()
            audit_params = {
                "source_service_id": str(source_service_id),
                "source_service_name": source_name,
                "new_service_name": target_name,
                "include_forms": include_forms,
                "include_roles": include_roles,
                "include_determinants": include_determinants,
                "include_bots": include_bots,
                "include_catalogs": include_catalogs,
                "include_translations": include_translations,
                "include_tutorials": include_tutorials,
                "catalog_ids": catalog_ids,
            }
            audit_id = await audit_logger.record_pending(
                user_email=user_email,
                operation_type="copy",
                object_type="service",
                object_id=str(source_service_id),
                params=audit_params,
            )

            if ctx:
                await ctx.report_progress(
                    progress=0.3,
                    total=1.0,
                    message=f"Copying service to '{target_name}'...",
                )

            try:
                # Execute the copy operation
                copy_result, _size = await client.download_service(
                    str(source_service_id),
                    options=copy_options,
                )

                # Extract new service ID from response
                new_service_id = copy_result.get("id")
                new_service_name = copy_result.get("name", target_name)

                # Mark audit as success
                await audit_logger.mark_success(
                    audit_id,
                    result={
                        "new_service_id": new_service_id,
                        "new_service_name": new_service_name,
                        "source_service_id": str(source_service_id),
                    },
                )

            except BPAClientError as e:
                # Mark audit as failed
                await audit_logger.mark_failed(audit_id, str(e))
                raise

    except ToolError:
        raise
    except BPAClientError as e:
        raise translate_error(e, resource_type="service", resource_id=source_service_id)

    if ctx:
        await ctx.report_progress(
            progress=1.0,
            total=1.0,
            message="Service copy complete.",
        )

    # Generate warnings for potential broken references
    warnings = _generate_copy_warnings(
        include_forms=include_forms,
        include_catalogs=include_catalogs,
        include_determinants=include_determinants,
    )

    return {
        "new_service_id": new_service_id,
        "new_service_name": new_service_name,
        "source_service_id": str(source_service_id),
        "source_service_name": source_name,
        "components_copied": components_copied,
        "components_excluded": components_excluded,
        "warnings": warnings,
        "audit_id": audit_id,
    }


def _build_copy_payload(
    new_service_name: str,
    include_forms: bool,
    include_roles: bool,
    include_determinants: bool,
    include_bots: bool,
    include_catalogs: bool,
    include_translations: bool,
    include_tutorials: bool,
    catalog_ids: list[str] | None,
) -> dict[str, Any]:
    """Build the payload for the copy service API call.

    Args:
        new_service_name: Name for the new service.
        include_forms: Whether to copy forms.
        include_roles: Whether to copy roles.
        include_determinants: Whether to copy determinants.
        include_bots: Whether to copy bots.
        include_catalogs: Whether to copy catalogs.
        include_translations: Whether to copy translations.
        include_tutorials: Whether to copy tutorials.
        catalog_ids: Specific catalog IDs to copy, or None for all.

    Returns:
        dict: The payload for the download_service API call.
    """
    payload: dict[str, Any] = {
        "serviceSelected": True,
        "copyService": True,
        "newServiceName": new_service_name,
        # Core components always copied
        "costsSelected": True,
        "requirementsSelected": True,
        "resultsSelected": True,
        "activityConditionsSelected": True,
        "registrationLawsSelected": True,
        "serviceLocationsSelected": True,
        "registrationsSelected": True,
        "printDocumentsSelected": True,
        # Configurable components
        "guideFormSelected": include_forms,
        "applicantFormSelected": include_forms,
        "sendFileFormSelected": include_forms,
        "paymentFormSelected": include_forms,
        "rolesSelected": include_roles,
        "determinantsSelected": include_determinants,
        "botsSelected": include_bots,
        "catalogsSelected": include_catalogs,
        "serviceTranslationsSelected": include_translations,
        "serviceTutorialsSelected": include_tutorials,
    }

    # Add specific catalog IDs if provided
    if include_catalogs and catalog_ids is not None:
        payload["catalogsToCopy"] = catalog_ids

    return payload


def _generate_copy_warnings(
    include_forms: bool,
    include_catalogs: bool,
    include_determinants: bool,
) -> list[str]:
    """Generate warnings about potential broken references in the copy.

    Args:
        include_forms: Whether forms were copied.
        include_catalogs: Whether catalogs were copied.
        include_determinants: Whether determinants were copied.

    Returns:
        list: Warning messages about potential issues.
    """
    warnings: list[str] = []

    # Warn about catalog references in forms
    if include_forms and not include_catalogs:
        warnings.append(
            "Forms were copied but catalogs were excluded. "
            "Catalog references in forms may be broken."
        )

    # Warn about determinant references
    if include_forms and not include_determinants:
        warnings.append(
            "Forms were copied but determinants were excluded. "
            "Field visibility rules may not work correctly."
        )

    return warnings


def register_export_tools(mcp: Any) -> None:
    """Register export tools with the MCP server.

    Args:
        mcp: The FastMCP server instance.
    """
    mcp.tool()(service_export_raw)
    mcp.tool()(service_to_yaml)
    mcp.tool()(service_copy)
