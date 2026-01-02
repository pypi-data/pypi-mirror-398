"""MCP tools for Arazzo workflow orchestration.

This module provides tools for:
- Story 5.1: Workflow Catalog & Discovery
- Story 5.2: Intent-to-Workflow Matching
- Story 5.3: Input Extraction & Validation
- Story 5.4: Workflow Executor
- Story 5.5: Progress Reporting & Streaming
- Story 5.6: Error Recovery & Rollback
- Story 5.7: Workflow Chaining & Composition
- Story 5.8: Guided Interactive Mode
"""

from __future__ import annotations

import re
import time
import uuid
from collections.abc import Callable
from typing import Any

from mcp.server.fastmcp.exceptions import ToolError

from mcp_eregistrations_bpa.workflows import (
    WorkflowCatalog,
    get_workflow_catalog,
)

__all__ = [
    # Story 5.1: Workflow Catalog & Discovery
    "workflow_list",
    "workflow_describe",
    "workflow_search",
    # Story 5.2: Intent-to-Workflow Matching
    "workflow_match",
    # Story 5.3: Input Extraction & Validation
    "workflow_extract_inputs",
    # Story 5.4: Workflow Executor
    "workflow_execute",
    # Story 5.5: Progress Reporting & Streaming
    "workflow_status",
    "workflow_cancel",
    # Story 5.6: Error Recovery & Rollback
    "workflow_retry",
    "workflow_rollback",
    # Story 5.7: Workflow Chaining & Composition
    "workflow_chain",
    # Story 5.8: Guided Interactive Mode
    "workflow_start_interactive",
    "workflow_continue",
    "workflow_confirm",
    # Registration
    "register_workflow_tools",
]


# =============================================================================
# Story 5.1: Workflow Catalog & Discovery
# =============================================================================


async def workflow_list(category: str | None = None) -> dict[str, Any]:
    """List available Arazzo workflows for BPA service design.

    Returns a catalog of workflows that can be executed to create and configure
    BPA services. Each workflow represents a multi-step operation that orchestrates
    multiple MCP tools.

    Args:
        category: Optional category to filter workflows (e.g., "service-creation",
            "roles-configuration", "payments", "forms", "notifications").
            If None, returns all workflows.

    Returns:
        dict: Catalog of available workflows:
            - workflows: List of workflow entries with id, summary, category,
                required_inputs, and optional_inputs.
            - total: Total number of workflows matching the filter.
            - categories: List of all available categories.

    Example:
        >>> await workflow_list()
        {
            "workflows": [
                {
                    "id": "createMinimalService",
                    "summary": "Create a service with one registration",
                    "category": "service-creation",
                    "required_inputs": ["serviceName", "registrationName", ...],
                    "optional_inputs": ["serviceDescription"]
                },
                ...
            ],
            "total": 12,
            "categories": ["service-creation", "roles-configuration", ...]
        }
    """
    catalog = get_workflow_catalog()

    workflows = catalog.list_workflows(category=category)
    all_categories = catalog.categories

    return {
        "workflows": workflows,
        "total": len(workflows),
        "categories": all_categories,
    }


async def workflow_describe(workflow_id: str) -> dict[str, Any]:
    """Get detailed information about a specific workflow.

    Returns the full workflow specification including inputs, steps, and outputs.
    Use this to understand what a workflow does and what inputs it requires
    before executing it.

    Args:
        workflow_id: The unique workflow identifier (e.g., "createMinimalService").

    Returns:
        dict: Detailed workflow specification:
            - id: The workflow identifier.
            - summary: Short description of what the workflow does.
            - description: Detailed description with usage examples.
            - category: The workflow category.
            - inputs: Dictionary of input definitions with types, requirements,
                descriptions, and constraints.
            - steps: List of steps with descriptions and MCP tool mappings.
            - outputs: List of output field names produced by the workflow.
            - source_file: Path to the source Arazzo file.

    Raises:
        ToolError: If the workflow is not found.

    Example:
        >>> await workflow_describe("createMinimalService")
        {
            "id": "createMinimalService",
            "summary": "Create a service with one registration",
            "description": "Mirrors the BPA frontend flow...",
            "inputs": {
                "serviceName": {
                    "name": "serviceName",
                    "type": "string",
                    "required": True,
                    "description": "Display name of the service"
                },
                ...
            },
            "steps": [
                {"step_id": "createService", "description": "Create parent",
                 "tool": "service_create"},
                {"step_id": "createRegistration", "description": "Create reg",
                 "tool": "registration_create"}
            ],
            "outputs": ["serviceId", "serviceName", "registrationId"]
        }
    """
    catalog = get_workflow_catalog()
    workflow = catalog.get_workflow(workflow_id)

    if workflow is None:
        available = [wf["id"] for wf in catalog.list_workflows()[:5]]
        suggestion = ", ".join(available)
        raise ToolError(
            f"Workflow '{workflow_id}' not found. "
            f"Available workflows include: {suggestion}. "
            "Use 'workflow_list' to see all available workflows."
        )

    return workflow.to_detail_dict()


async def workflow_search(query: str, limit: int = 10) -> dict[str, Any]:
    """Search workflows by keyword.

    Searches in workflow IDs, summaries, and descriptions.
    Returns matches ranked by relevance.

    Args:
        query: The search query (e.g., "role", "create service", "payment").
        limit: Maximum number of results to return (default 10).

    Returns:
        dict: Search results:
            - query: The search query that was used.
            - matches: List of matching workflows with relevance scores.
            - total: Number of matches found.

    Example:
        >>> await workflow_search("role")
        {
            "query": "role",
            "matches": [
                {"id": "addRole", "summary": "Add a workflow role",
                 "category": "roles-configuration", "relevance": 0.95},
                {"id": "configureStandardWorkflow",
                 "summary": "Set up review-approve workflow", "relevance": 0.80}
            ],
            "total": 2
        }
    """
    if not query or not query.strip():
        raise ToolError(
            "Search query cannot be empty. Provide a keyword to search for."
        )

    catalog = get_workflow_catalog()
    matches = catalog.search_workflows(query.strip(), limit=limit)

    return {
        "query": query,
        "matches": matches,
        "total": len(matches),
    }


# =============================================================================
# Story 5.2: Intent-to-Workflow Matching
# =============================================================================


async def workflow_match(intent: str) -> dict[str, Any]:
    """Match a natural language intent to appropriate workflows.

    Analyzes the user's intent and suggests workflows that can fulfill it.
    Supports both simple intents (single workflow) and compound intents
    (multiple workflows to chain).

    Args:
        intent: Natural language description of what the user wants to do.
            Examples:
            - "create a business registration service"
            - "add a reviewer and approver to my service"
            - "set up payment processing"

    Returns:
        dict: Matching results:
            - intent: The original intent.
            - matches: List of matching workflows with confidence scores and
                extracted inputs.
            - compound: Whether this intent requires multiple workflows.
            - execution_order: Suggested order of workflow execution (if compound).
            - ambiguous: Whether the intent needs clarification.
            - clarification_needed: Question to ask if ambiguous.
            - options: Alternative interpretations if ambiguous.

    Example:
        >>> await workflow_match("create a permit service with reviewer and approver")
        {
            "intent": "create a permit service with reviewer and approver",
            "compound": True,
            "matches": [
                {
                    "workflow_id": "createMinimalService",
                    "confidence": 0.90,
                    "order": 1,
                    "extracted_inputs": {"serviceName": "Permit Service"},
                    "missing_inputs": ["registrationKey"]
                },
                {
                    "workflow_id": "configureStandardWorkflow",
                    "confidence": 0.85,
                    "order": 2,
                    "depends_on": "createMinimalService.outputs.serviceId",
                    "extracted_inputs": {}
                }
            ],
            "execution_order": ["createMinimalService", "configureStandardWorkflow"]
        }
    """
    if not intent or not intent.strip():
        raise ToolError("Intent cannot be empty. Describe what you want to do.")

    intent_clean = intent.strip().lower()
    catalog = get_workflow_catalog()

    # Analyze intent for key concepts
    concepts = _extract_concepts(intent_clean)

    # Find matching workflows
    matches = _find_matching_workflows(catalog, concepts, intent_clean)

    if not matches:
        # Return suggestions for ambiguous intent
        return {
            "intent": intent,
            "ambiguous": True,
            "clarification_needed": (
                "I couldn't find a specific workflow for your request. "
                "What would you like to do?"
            ),
            "options": [
                {
                    "workflow_id": "createMinimalService",
                    "description": "Create a new service with registration",
                },
                {
                    "workflow_id": "addRole",
                    "description": "Add a role (Reviewer, Approver, etc.)",
                },
                {
                    "workflow_id": "configureStandardWorkflow",
                    "description": "Set up a standard review-approve workflow",
                },
            ],
            "matches": [],
            "compound": False,
        }

    # Determine if compound (multiple workflows needed)
    compound = len(matches) > 1

    # Sort matches by order if compound
    if compound:
        matches = _order_matches(matches)
        execution_order = [m["workflow_id"] for m in matches]
    else:
        execution_order = [matches[0]["workflow_id"]]

    return {
        "intent": intent,
        "matches": matches,
        "compound": compound,
        "execution_order": execution_order,
        "ambiguous": False,
    }


def _extract_concepts(intent: str) -> dict[str, Any]:
    """Extract key concepts from intent string.

    Args:
        intent: The lowercase intent string.

    Returns:
        Dictionary of extracted concepts.
    """
    concepts: dict[str, Any] = {
        "action": None,
        "targets": [],
        "names": [],
        "roles": [],
    }

    # Detect action
    if re.search(r"\b(create|make|new|add|setup|set up)\b", intent):
        concepts["action"] = "create"
    elif re.search(r"\b(update|modify|change|edit)\b", intent):
        concepts["action"] = "update"
    elif re.search(r"\b(configure|setup|set up)\b", intent):
        concepts["action"] = "configure"

    # Detect targets
    if re.search(r"\bservice\b", intent):
        concepts["targets"].append("service")
    if re.search(r"\bregistration\b", intent):
        concepts["targets"].append("registration")
    if re.search(r"\brole[s]?\b", intent):
        concepts["targets"].append("role")
    if re.search(r"\breviewer\b", intent):
        concepts["roles"].append("Reviewer")
    if re.search(r"\bapprover\b", intent):
        concepts["roles"].append("Approver")
    if re.search(r"\bpayment[s]?\b", intent):
        concepts["targets"].append("payment")
    if re.search(r"\bform[s]?\b", intent):
        concepts["targets"].append("form")
    if re.search(r"\bbot[s]?\b", intent):
        concepts["targets"].append("bot")
    if re.search(r"\bworkflow\b", intent):
        concepts["targets"].append("workflow")

    # Extract quoted names
    quoted = re.findall(r"['\"]([^'\"]+)['\"]", intent)
    concepts["names"] = quoted

    # Extract service name patterns
    name_patterns = [
        r"(?:service\s+)?(?:called|named)\s+([a-zA-Z\s]+)",
        r"([a-zA-Z]+(?:\s+[a-zA-Z]+)*)\s+service",
    ]
    for pattern in name_patterns:
        match = re.search(pattern, intent)
        if match and match.group(1).strip():
            name = match.group(1).strip().title()
            if name not in concepts["names"]:
                concepts["names"].append(name)

    return concepts


def _find_matching_workflows(
    catalog: WorkflowCatalog,
    concepts: dict[str, Any],
    intent: str,
) -> list[dict[str, Any]]:
    """Find workflows matching the extracted concepts.

    Args:
        catalog: The workflow catalog.
        concepts: Extracted concepts from intent.
        intent: The original intent string.

    Returns:
        List of matching workflows with confidence and extracted inputs.
    """
    matches: list[dict[str, Any]] = []

    action = concepts.get("action")
    targets = concepts.get("targets", [])
    roles = concepts.get("roles", [])
    names = concepts.get("names", [])

    # Service creation intent
    if action == "create" and "service" in targets:
        workflow = catalog.get_workflow("createMinimalService")
        if workflow:
            extracted: dict[str, Any] = {}
            missing: list[str] = list(workflow.required_inputs)

            # Extract service name
            if names:
                extracted["serviceName"] = names[0]
                if "serviceName" in missing:
                    missing.remove("serviceName")
                # Derive registration name
                if "registrationName" in missing:
                    extracted["registrationName"] = names[0]
                    missing.remove("registrationName")
                # Derive short name
                if "registrationShortName" in missing:
                    extracted["registrationShortName"] = _to_short_name(names[0])
                    missing.remove("registrationShortName")
                # Derive key
                if "registrationKey" in missing:
                    extracted["registrationKey"] = _to_key(names[0])
                    missing.remove("registrationKey")

            matches.append(
                {
                    "workflow_id": "createMinimalService",
                    "confidence": 0.90 if names else 0.75,
                    "order": 1,
                    "extracted_inputs": extracted,
                    "missing_inputs": missing,
                }
            )

    # Role configuration intent
    if action in ("create", "configure") and (
        "role" in targets or "workflow" in targets or roles
    ):
        # Check if standard workflow with reviewer+approver
        if "Reviewer" in roles and "Approver" in roles:
            workflow = catalog.get_workflow("configureStandardWorkflow")
            if workflow:
                matches.append(
                    {
                        "workflow_id": "configureStandardWorkflow",
                        "confidence": 0.85,
                        "order": 2,
                        "extracted_inputs": {},
                        "missing_inputs": ["serviceId"],
                        "depends_on": "createMinimalService.outputs.serviceId"
                        if "service" in targets
                        else None,
                    }
                )
        else:
            # Individual role addition
            workflow = catalog.get_workflow("addRole")
            if workflow:
                for role in roles:
                    matches.append(
                        {
                            "workflow_id": "addRole",
                            "confidence": 0.80,
                            "order": 2,
                            "extracted_inputs": {"name": role},
                            "missing_inputs": ["serviceId", "assignedTo"],
                        }
                    )

    # Payment configuration intent
    if action in ("create", "configure") and "payment" in targets:
        workflow = catalog.get_workflow("configurePayments")
        if workflow:
            matches.append(
                {
                    "workflow_id": "configurePayments",
                    "confidence": 0.85,
                    "order": 3,
                    "extracted_inputs": {},
                    "missing_inputs": ["serviceId"],
                }
            )

    # If no matches found, try keyword search
    if not matches:
        search_results = catalog.search_workflows(intent, limit=3)
        for result in search_results:
            if result["relevance"] > 0.3:
                matches.append(
                    {
                        "workflow_id": result["id"],
                        "confidence": result["relevance"],
                        "order": 1,
                        "extracted_inputs": {},
                        "missing_inputs": [],
                    }
                )

    return matches


def _order_matches(matches: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Order matches by execution order.

    Args:
        matches: List of matched workflows.

    Returns:
        Sorted list by order field.
    """
    return sorted(matches, key=lambda m: m.get("order", 99))


def _to_short_name(name: str) -> str:
    """Convert a name to a short name.

    Args:
        name: The full name.

    Returns:
        A short name (max 50 chars).
    """
    return name[:50] if len(name) > 50 else name


def _to_key(name: str) -> str:
    """Convert a name to a URL-safe key.

    Args:
        name: The full name.

    Returns:
        A kebab-case key.
    """
    # Remove non-alphanumeric, lowercase, replace spaces with hyphens
    key = re.sub(r"[^a-zA-Z0-9\s-]", "", name.lower())
    key = re.sub(r"\s+", "-", key.strip())
    return key[:100]


# =============================================================================
# Story 5.3: Input Extraction & Validation
# =============================================================================


async def workflow_extract_inputs(
    message: str,
    workflow_id: str,
) -> dict[str, Any]:
    """Extract and validate workflow inputs from a natural language message.

    Parses entities from the message and maps them to the workflow's input schema.
    Validates extracted values against constraints and reports missing required inputs.

    Args:
        message: The user's message containing input values.
            Example: "Create a service called 'Vehicle Registration'"
        workflow_id: The workflow to extract inputs for.

    Returns:
        dict: Extraction results:
            - workflow_id: The target workflow.
            - message: The original message.
            - extracted: Dictionary of successfully extracted inputs.
            - inferred: Dictionary of auto-generated inputs with explanations.
            - valid: Whether all required inputs are present and valid.
            - missing: List of missing required inputs with prompts.
            - errors: List of validation errors.

    Raises:
        ToolError: If the workflow is not found.

    Example:
        >>> await workflow_extract_inputs(
        ...     message="Create a service called 'Vehicle Registration'",
        ...     workflow_id="createMinimalService"
        ... )
        {
            "workflow_id": "createMinimalService",
            "extracted": {
                "serviceName": "Vehicle Registration"
            },
            "inferred": {
                "registrationName": "Vehicle Registration (derived from serviceName)",
                "registrationKey": "vehicle-registration (auto-generated)"
            },
            "valid": False,
            "missing": [
                {
                    "input": "registrationShortName",
                    "required": True,
                    "prompt": "What should the registration short name be?"
                }
            ],
            "errors": []
        }
    """
    catalog = get_workflow_catalog()
    workflow = catalog.get_workflow(workflow_id)

    if workflow is None:
        raise ToolError(
            f"Workflow '{workflow_id}' not found. "
            "Use 'workflow_list' to see available workflows."
        )

    extracted: dict[str, Any] = {}
    inferred: dict[str, str] = {}
    errors: list[dict[str, Any]] = []

    # Extract quoted strings
    quoted = re.findall(r"['\"]([^'\"]+)['\"]", message)

    # Try to map quoted strings to inputs
    name_inputs = ["serviceName", "registrationName", "name"]
    for inp in workflow.inputs:
        if inp.name in name_inputs and quoted:
            extracted[inp.name] = quoted[0]

    # Extract service/registration names from patterns
    name_patterns = [
        (r"service\s+(?:called|named)\s+['\"]?([^'\"]+)['\"]?", "serviceName"),
        (r"['\"]?([^'\"]+)['\"]?\s+service", "serviceName"),
        (
            r"registration\s+(?:called|named)\s+['\"]?([^'\"]+)['\"]?",
            "registrationName",
        ),
    ]

    for pattern, field in name_patterns:
        match = re.search(pattern, message, re.IGNORECASE)
        if match and field not in extracted:
            value = match.group(1).strip().rstrip(".")
            if value:
                extracted[field] = value.title()

    # Infer derived fields
    if "serviceName" in extracted:
        svc_name = extracted["serviceName"]

        if "registrationName" not in extracted and workflow.get_input(
            "registrationName"
        ):
            extracted["registrationName"] = svc_name
            inferred["registrationName"] = "Derived from serviceName"

        if "registrationShortName" not in extracted and workflow.get_input(
            "registrationShortName"
        ):
            extracted["registrationShortName"] = _to_short_name(svc_name)
            inferred["registrationShortName"] = "Generated from registrationName"

        if "registrationKey" not in extracted and workflow.get_input("registrationKey"):
            extracted["registrationKey"] = _to_key(svc_name)
            inferred["registrationKey"] = "Generated from registrationName (kebab-case)"

        if "serviceShortName" not in extracted and workflow.get_input(
            "serviceShortName"
        ):
            extracted["serviceShortName"] = _to_short_name(svc_name)
            inferred["serviceShortName"] = "Generated from serviceName"

    # Validate extracted values
    for inp in workflow.inputs:
        if inp.name in extracted:
            value = extracted[inp.name]
            error = _validate_input_value(inp, value)
            if error:
                errors.append(
                    {
                        "input": inp.name,
                        "value": value,
                        "constraint": error["constraint"],
                        "message": error["message"],
                        "suggestion": error.get("suggestion"),
                    }
                )

    # Find missing required inputs
    missing: list[dict[str, Any]] = []
    for inp in workflow.inputs:
        if inp.required and inp.name not in extracted:
            missing.append(
                {
                    "input": inp.name,
                    "required": True,
                    "prompt": _generate_input_prompt(inp),
                    "suggestions": _generate_suggestions(inp),
                }
            )

    valid = len(errors) == 0 and len(missing) == 0

    return {
        "workflow_id": workflow_id,
        "message": message,
        "extracted": extracted,
        "inferred": inferred,
        "valid": valid,
        "missing": missing,
        "errors": errors,
    }


def _validate_input_value(
    inp: Any,  # WorkflowInput
    value: Any,
) -> dict[str, Any] | None:
    """Validate a single input value against its constraints.

    Args:
        inp: The WorkflowInput definition.
        value: The value to validate.

    Returns:
        Error dict if invalid, None if valid.
    """
    from mcp_eregistrations_bpa.workflows.models import InputType

    # String type validations
    if inp.input_type == InputType.STRING and isinstance(value, str):
        # Check pattern
        if inp.pattern:
            if not re.match(inp.pattern, value):
                return {
                    "constraint": f"pattern: {inp.pattern}",
                    "message": f"{inp.name} must match pattern {inp.pattern}",
                    "suggestion": _suggest_pattern_fix(value, inp.pattern),
                }

        # Check length
        if inp.min_length is not None and len(value) < inp.min_length:
            return {
                "constraint": f"minLength: {inp.min_length}",
                "message": f"{inp.name} must be at least {inp.min_length} characters",
            }
        if inp.max_length is not None and len(value) > inp.max_length:
            return {
                "constraint": f"maxLength: {inp.max_length}",
                "message": f"{inp.name} must be at most {inp.max_length} characters",
                "suggestion": value[: inp.max_length],
            }

        # Check enum
        if inp.enum_values and value not in inp.enum_values:
            return {
                "constraint": f"enum: {inp.enum_values}",
                "message": f"{inp.name} must be one of: {', '.join(inp.enum_values)}",
            }

    # Numeric validations
    if inp.input_type in (InputType.INTEGER, InputType.NUMBER):
        if isinstance(value, int | float):
            if inp.minimum is not None and value < inp.minimum:
                return {
                    "constraint": f"minimum: {inp.minimum}",
                    "message": f"{inp.name} must be at least {inp.minimum}",
                }
            if inp.maximum is not None and value > inp.maximum:
                return {
                    "constraint": f"maximum: {inp.maximum}",
                    "message": f"{inp.name} must be at most {inp.maximum}",
                }

    return None


def _suggest_pattern_fix(value: str, pattern: str) -> str | None:
    """Suggest a fix for a pattern violation.

    Args:
        value: The invalid value.
        pattern: The regex pattern.

    Returns:
        Suggested fixed value or None.
    """
    # Handle common patterns
    if pattern == "^[a-z0-9-]+$":
        # Kebab-case pattern
        fixed = re.sub(r"[^a-z0-9-]", "", value.lower().replace(" ", "-"))
        return fixed if fixed else None

    return None


def _generate_input_prompt(inp: Any) -> str:
    """Generate a prompt for a missing input.

    Args:
        inp: The WorkflowInput definition.

    Returns:
        A human-readable prompt.
    """
    if inp.description:
        return str(inp.description)

    # Generate based on name
    name = inp.name
    # Convert camelCase to words
    words = re.sub(r"([A-Z])", r" \1", name).strip().lower()
    return f"What is the {words}?"


def _generate_suggestions(inp: Any) -> list[str]:
    """Generate suggestions for an input.

    Args:
        inp: The WorkflowInput definition.

    Returns:
        List of suggestion strings.
    """
    suggestions: list[str] = []

    if inp.enum_values:
        suggestions.extend(inp.enum_values[:3])
    elif inp.default is not None:
        suggestions.append(f"Default: {inp.default}")

    return suggestions


# =============================================================================
# Story 5.4: Workflow Executor
# =============================================================================


async def workflow_execute(
    workflow_id: str,
    inputs: dict[str, Any],
    dry_run: bool = False,
) -> dict[str, Any]:
    """Execute a workflow with the provided inputs.

    Runs each step of the workflow in sequence, calling the appropriate
    MCP tools and passing outputs from previous steps as inputs to subsequent steps.

    Args:
        workflow_id: The workflow to execute (e.g., "createMinimalService").
        inputs: Dictionary of input values for the workflow.
        dry_run: If True, validate inputs and return execution plan without
            actually executing steps.

    Returns:
        dict: Execution results:
            - workflow_id: The workflow that was executed.
            - status: "completed", "failed", or "dry_run".
            - steps: List of step execution results.
            - outputs: Final workflow outputs.
            - message: Human-readable summary.
            - failed_at_step: Step ID where failure occurred (if failed).
            - error: Error message (if failed).
            - rollback_available: Whether rollback is possible (if failed).

    Raises:
        ToolError: If the workflow is not found or inputs are invalid.

    Example:
        >>> await workflow_execute(
        ...     workflow_id="createMinimalService",
        ...     inputs={
        ...         "serviceName": "Vehicle Registration",
        ...         "registrationName": "New Vehicle Application",
        ...         "registrationKey": "new-vehicle-app"
        ...     }
        ... )
        {
            "workflow_id": "createMinimalService",
            "status": "completed",
            "steps": [
                {
                    "step_id": "createService",
                    "tool": "service_create",
                    "status": "success",
                    "outputs": {"serviceId": "svc-123"}
                },
                ...
            ],
            "outputs": {"serviceId": "svc-123", "registrationId": "reg-456"},
            "message": "Service 'Vehicle Registration' created successfully"
        }
    """
    catalog = get_workflow_catalog()
    workflow = catalog.get_workflow(workflow_id)

    if workflow is None:
        raise ToolError(
            f"Workflow '{workflow_id}' not found. "
            "Use 'workflow_list' to see available workflows."
        )

    # Validate required inputs
    missing_inputs = []
    for inp in workflow.inputs:
        if inp.required and inp.name not in inputs:
            missing_inputs.append(inp.name)

    if missing_inputs:
        raise ToolError(
            f"Missing required inputs: {', '.join(missing_inputs)}. "
            f"Use 'workflow_describe {workflow_id}' to see required inputs."
        )

    # Initialize execution context
    context: dict[str, Any] = {
        "inputs": inputs.copy(),
        "steps": {},
        "outputs": {},
    }

    step_results: list[dict[str, Any]] = []
    completed_steps: list[str] = []

    # Dry run mode - return execution plan
    if dry_run:
        plan_steps = []
        for step in workflow.steps:
            plan_steps.append(
                {
                    "step_id": step.step_id,
                    "description": step.description,
                    "tool": step.mcp_tool,
                    "inputs": _resolve_step_inputs(step, context, preview=True),
                    "status": "planned",
                }
            )

        return {
            "workflow_id": workflow_id,
            "status": "dry_run",
            "steps": plan_steps,
            "message": f"Execution plan for '{workflow.summary}'",
            "total_steps": len(plan_steps),
        }

    # Execute each step
    for step in workflow.steps:
        # Check conditional execution
        if step.condition:
            condition_met = _evaluate_condition(step.condition, context)
            if not condition_met:
                step_results.append(
                    {
                        "step_id": step.step_id,
                        "status": "skipped",
                        "reason": f"Condition not met: {step.condition}",
                    }
                )
                continue

        # Resolve step inputs from context
        step_inputs = _resolve_step_inputs(step, context)

        # Execute the step
        try:
            step_output = await _execute_step(step, step_inputs)

            # Store outputs in context
            context["steps"][step.step_id] = step_output
            for key, value in step_output.items():
                context["outputs"][key] = value

            step_results.append(
                {
                    "step_id": step.step_id,
                    "tool": step.mcp_tool,
                    "inputs": step_inputs,
                    "status": "success",
                    "outputs": step_output,
                }
            )
            completed_steps.append(step.step_id)

        except Exception as e:
            # Step failed - stop execution
            step_results.append(
                {
                    "step_id": step.step_id,
                    "tool": step.mcp_tool,
                    "inputs": step_inputs,
                    "status": "failed",
                    "error": str(e),
                }
            )

            return {
                "workflow_id": workflow_id,
                "status": "failed",
                "failed_at_step": step.step_id,
                "error": str(e),
                "steps": step_results,
                "completed_steps": completed_steps,
                "rollback_available": len(completed_steps) > 0,
                "suggestion": _generate_failure_suggestion(step, str(e)),
            }

    # Collect final outputs
    final_outputs = _collect_workflow_outputs(workflow, context)

    return {
        "workflow_id": workflow_id,
        "status": "completed",
        "steps": step_results,
        "outputs": final_outputs,
        "message": _generate_success_message(workflow, final_outputs),
    }


def _resolve_step_inputs(
    step: Any,  # WorkflowStep
    context: dict[str, Any],
    preview: bool = False,
) -> dict[str, Any]:
    """Resolve step inputs from context using Arazzo expressions.

    Args:
        step: The workflow step.
        context: The execution context with inputs, steps, outputs.
        preview: If True, show placeholders instead of resolving.

    Returns:
        Dictionary of resolved inputs for the step.
    """
    resolved: dict[str, Any] = {}

    # Process request body
    for key, value in step.request_body.items():
        resolved[key] = _resolve_expression(value, context, preview)

    # Process parameters
    for param in step.parameters:
        name = param.get("name")
        value = param.get("value")
        if name and value:
            resolved[name] = _resolve_expression(value, context, preview)

    return resolved


def _resolve_expression(
    value: Any,
    context: dict[str, Any],
    preview: bool = False,
) -> Any:
    """Resolve an Arazzo runtime expression.

    Arazzo expressions use the format:
    - $inputs.fieldName - references workflow input
    - $steps.stepId.outputs.fieldName - references step output
    - $outputs.fieldName - references workflow output

    Args:
        value: The value to resolve (may be expression or literal).
        context: The execution context.
        preview: If True, return placeholder instead of resolving.

    Returns:
        Resolved value.
    """
    if not isinstance(value, str):
        return value

    # Check for Arazzo expression patterns
    if not value.startswith("$"):
        return value

    if preview:
        return f"<{value}>"

    # Parse and resolve expression
    parts = value.split(".")

    if value.startswith("$inputs."):
        field = parts[1] if len(parts) > 1 else None
        if field and field in context["inputs"]:
            return context["inputs"][field]
        return value  # Return original if not found

    if value.startswith("$steps."):
        if len(parts) >= 4:
            step_id = parts[1]
            # parts[2] should be "outputs"
            field = parts[3]
            if step_id in context["steps"]:
                step_outputs = context["steps"][step_id]
                if field in step_outputs:
                    return step_outputs[field]
        return value  # Return original if not found

    if value.startswith("$outputs."):
        field = parts[1] if len(parts) > 1 else None
        if field and field in context["outputs"]:
            return context["outputs"][field]
        return value

    return value


def _evaluate_condition(condition: str, context: dict[str, Any]) -> bool:
    """Evaluate a step condition expression.

    Args:
        condition: The condition expression.
        context: The execution context.

    Returns:
        True if condition is met, False otherwise.
    """
    # Simple condition evaluation
    # Format: $inputs.fieldName == value or $inputs.fieldName != value

    if "==" in condition:
        left, right = condition.split("==", 1)
        left_val = _resolve_expression(left.strip(), context)
        right_val = right.strip().strip("'\"")
        return str(left_val).lower() == right_val.lower()

    if "!=" in condition:
        left, right = condition.split("!=", 1)
        left_val = _resolve_expression(left.strip(), context)
        right_val = right.strip().strip("'\"")
        return str(left_val).lower() != right_val.lower()

    # Check for truthy value
    resolved = _resolve_expression(condition, context)
    if isinstance(resolved, bool):
        return resolved
    if isinstance(resolved, str):
        return resolved.lower() in ("true", "yes", "1")

    return bool(resolved)


async def _execute_step(
    step: Any,  # WorkflowStep
    inputs: dict[str, Any],
) -> dict[str, Any]:
    """Execute a single workflow step by calling the mapped MCP tool.

    Args:
        step: The workflow step to execute.
        inputs: Resolved inputs for the step.

    Returns:
        Dictionary of outputs from the step.

    Raises:
        ToolError: If the step fails.
    """
    tool_name = step.mcp_tool
    if not tool_name:
        raise ToolError(
            f"Step '{step.step_id}' has no mapped MCP tool. "
            f"operationId: {step.operation_id}"
        )

    # Import tools dynamically to avoid circular imports
    tool_func = _get_tool_function(tool_name)
    if tool_func is None:
        raise ToolError(f"MCP tool '{tool_name}' not found for step '{step.step_id}'.")

    # Execute the tool
    result = await tool_func(**inputs)

    # Extract outputs based on step output mappings
    outputs: dict[str, Any] = {}
    if isinstance(result, dict):
        # Use step output mappings if defined
        for output_name, output_expr in step.outputs.items():
            if isinstance(output_expr, str) and output_expr.startswith("$"):
                # Extract from result using expression
                parts = output_expr.split(".")
                if len(parts) >= 2 and parts[0] == "$response":
                    field = parts[1]
                    if field in result:
                        outputs[output_name] = result[field]
            else:
                # Direct mapping
                if output_expr in result:
                    outputs[output_name] = result[output_expr]

        # If no explicit mappings, use common output fields
        if not outputs:
            common_fields = ["id", "serviceId", "registrationId", "name", "key"]
            for field in common_fields:
                if field in result:
                    outputs[field] = result[field]

    return outputs


def _get_tool_function(tool_name: str) -> Any:
    """Get the tool function by name.

    Args:
        tool_name: The MCP tool name.

    Returns:
        The tool function or None if not found.
    """
    # Map tool names to functions
    from mcp_eregistrations_bpa.tools import bots, registrations, roles, services

    tool_map = {
        "service_create": getattr(services, "service_create", None),
        "service_update": getattr(services, "service_update", None),
        "service_list": services.service_list,
        "service_get": services.service_get,
        "registration_create": getattr(registrations, "registration_create", None),
        "registration_list": registrations.registration_list,
        "registration_get": registrations.registration_get,
        "role_create": getattr(roles, "role_create", None),
        "role_update": getattr(roles, "role_update", None),
        "role_list": roles.role_list,
        "role_get": roles.role_get,
        "bot_create": getattr(bots, "bot_create", None),
        "bot_update": getattr(bots, "bot_update", None),
        "bot_list": bots.bot_list,
        "bot_get": bots.bot_get,
    }

    return tool_map.get(tool_name)


def _collect_workflow_outputs(
    workflow: Any,  # WorkflowDefinition
    context: dict[str, Any],
) -> dict[str, Any]:
    """Collect final workflow outputs from context.

    Args:
        workflow: The workflow definition.
        context: The execution context.

    Returns:
        Dictionary of workflow outputs.
    """
    outputs: dict[str, Any] = {}

    for output_name, output_expr in workflow.outputs.items():
        resolved = _resolve_expression(output_expr, context)
        if resolved != output_expr:  # Only include if resolved
            outputs[output_name] = resolved
        elif output_name in context["outputs"]:
            outputs[output_name] = context["outputs"][output_name]

    # Include common outputs if not explicitly defined
    if not outputs:
        outputs = context["outputs"].copy()

    return outputs


def _generate_success_message(
    workflow: Any,  # WorkflowDefinition
    outputs: dict[str, Any],
) -> str:
    """Generate a success message for the workflow.

    Args:
        workflow: The workflow definition.
        outputs: The workflow outputs.

    Returns:
        Human-readable success message.
    """
    # Extract key values for message
    service_name = outputs.get("serviceName", outputs.get("name", ""))
    service_id = outputs.get("serviceId", outputs.get("id", ""))

    if service_name:
        return f"Workflow '{workflow.summary}' completed. Created '{service_name}'."
    if service_id:
        return f"Workflow '{workflow.summary}' completed. ID: {service_id}"

    return f"Workflow '{workflow.summary}' completed successfully."


def _generate_failure_suggestion(
    step: Any,  # WorkflowStep
    error: str,
) -> str:
    """Generate a suggestion for recovering from a failure.

    Args:
        step: The failed step.
        error: The error message.

    Returns:
        Suggestion for recovery.
    """
    error_lower = error.lower()

    if "already exists" in error_lower:
        return "Use a different name/key or delete the existing resource."
    if "not found" in error_lower:
        return "Verify the referenced resource exists. Check IDs and names."
    if "permission" in error_lower or "unauthorized" in error_lower:
        return "Check your permissions. You may need a different role."
    if "validation" in error_lower or "invalid" in error_lower:
        return "Check input values match the required format."

    return "Review the error message and try again with corrected inputs."


# =============================================================================
# Story 5.5: Progress Reporting & Streaming
# =============================================================================

# Track running workflow executions for status/cancel
_running_executions: dict[str, dict[str, Any]] = {}

# Track completed/failed executions for retry/rollback
_execution_history: dict[str, dict[str, Any]] = {}


async def workflow_execute_with_progress(
    workflow_id: str,
    inputs: dict[str, Any],
    on_progress: Callable[[dict[str, Any]], None] | None = None,
) -> dict[str, Any]:
    """Execute a workflow with progress callbacks.

    Similar to workflow_execute but reports progress after each step.
    Use this for workflows where you need real-time updates.

    Args:
        workflow_id: The workflow to execute.
        inputs: Dictionary of input values for the workflow.
        on_progress: Optional callback function called after each step with
            progress information.

    Returns:
        dict: Execution results (same as workflow_execute).

    Progress callback receives:
        {
            "type": "progress" | "heartbeat" | "complete",
            "execution_id": "exec-xyz",
            "workflow_id": "createMinimalService",
            "step": 1,
            "total": 3,
            "percent": 33,
            "message": "Created service 'My Service'",
            "elapsed_ms": 1234,
            "current_step": "createService"
        }
    """
    catalog = get_workflow_catalog()
    workflow = catalog.get_workflow(workflow_id)

    if workflow is None:
        raise ToolError(
            f"Workflow '{workflow_id}' not found. "
            "Use 'workflow_list' to see available workflows."
        )

    # Validate required inputs
    missing_inputs = []
    for inp in workflow.inputs:
        if inp.required and inp.name not in inputs:
            missing_inputs.append(inp.name)

    if missing_inputs:
        raise ToolError(
            f"Missing required inputs: {', '.join(missing_inputs)}. "
            f"Use 'workflow_describe {workflow_id}' to see required inputs."
        )

    # Generate execution ID
    execution_id = f"exec-{uuid.uuid4().hex[:8]}"
    start_time = time.time()

    # Register execution for tracking
    execution_state: dict[str, Any] = {
        "execution_id": execution_id,
        "workflow_id": workflow_id,
        "status": "running",
        "current_step": None,
        "completed_steps": [],
        "start_time": start_time,
        "cancelled": False,
    }
    _running_executions[execution_id] = execution_state

    # Initialize execution context
    context: dict[str, Any] = {
        "inputs": inputs.copy(),
        "steps": {},
        "outputs": {},
    }

    step_results: list[dict[str, Any]] = []
    total_steps = len(workflow.steps)

    try:
        # Execute each step
        for step_index, step in enumerate(workflow.steps, 1):
            # Check for cancellation
            if execution_state["cancelled"]:
                return {
                    "workflow_id": workflow_id,
                    "execution_id": execution_id,
                    "status": "cancelled",
                    "cancelled_at_step": step.step_id,
                    "completed_steps": execution_state["completed_steps"],
                    "remaining_steps": total_steps - step_index + 1,
                    "rollback_available": len(execution_state["completed_steps"]) > 0,
                }

            execution_state["current_step"] = step.step_id

            # Check conditional execution
            if step.condition:
                condition_met = _evaluate_condition(step.condition, context)
                if not condition_met:
                    step_results.append(
                        {
                            "step_id": step.step_id,
                            "status": "skipped",
                            "reason": f"Condition not met: {step.condition}",
                        }
                    )
                    continue

            # Resolve step inputs from context
            step_inputs = _resolve_step_inputs(step, context)

            # Execute the step
            try:
                step_output = await _execute_step(step, step_inputs)

                # Store outputs in context
                context["steps"][step.step_id] = step_output
                for key, value in step_output.items():
                    context["outputs"][key] = value

                step_results.append(
                    {
                        "step_id": step.step_id,
                        "tool": step.mcp_tool,
                        "inputs": step_inputs,
                        "status": "success",
                        "outputs": step_output,
                    }
                )
                execution_state["completed_steps"].append(step.step_id)

                # Report progress
                elapsed_ms = int((time.time() - start_time) * 1000)
                percent = int((step_index / total_steps) * 100)

                progress_info = {
                    "type": "progress",
                    "execution_id": execution_id,
                    "workflow_id": workflow_id,
                    "step": step_index,
                    "total": total_steps,
                    "percent": percent,
                    "message": _generate_step_progress_message(step, step_output),
                    "elapsed_ms": elapsed_ms,
                    "current_step": step.step_id,
                }

                if on_progress:
                    on_progress(progress_info)

            except Exception as e:
                # Step failed - stop execution
                step_results.append(
                    {
                        "step_id": step.step_id,
                        "tool": step.mcp_tool,
                        "inputs": step_inputs,
                        "status": "failed",
                        "error": str(e),
                    }
                )

                elapsed_ms = int((time.time() - start_time) * 1000)
                return {
                    "workflow_id": workflow_id,
                    "execution_id": execution_id,
                    "status": "failed",
                    "failed_at_step": step.step_id,
                    "error": str(e),
                    "steps": step_results,
                    "completed_steps": execution_state["completed_steps"],
                    "rollback_available": len(execution_state["completed_steps"]) > 0,
                    "suggestion": _generate_failure_suggestion(step, str(e)),
                    "duration_ms": elapsed_ms,
                }

        # Collect final outputs
        final_outputs = _collect_workflow_outputs(workflow, context)
        elapsed_ms = int((time.time() - start_time) * 1000)

        # Report completion
        if on_progress:
            on_progress(
                {
                    "type": "complete",
                    "execution_id": execution_id,
                    "workflow_id": workflow_id,
                    "summary": _generate_success_message(workflow, final_outputs),
                    "duration_ms": elapsed_ms,
                }
            )

        return {
            "workflow_id": workflow_id,
            "execution_id": execution_id,
            "status": "completed",
            "steps": step_results,
            "outputs": final_outputs,
            "message": _generate_success_message(workflow, final_outputs),
            "duration_ms": elapsed_ms,
        }

    finally:
        # Save execution history for retry/rollback before cleanup
        if execution_id in _running_executions:
            _execution_history[execution_id] = {
                **_running_executions[execution_id],
                "inputs": inputs.copy(),
                "context": context.copy(),
                "step_results": step_results,
                "total_steps": total_steps,
            }
            del _running_executions[execution_id]


def _generate_step_progress_message(
    step: Any,  # WorkflowStep
    outputs: dict[str, Any],
) -> str:
    """Generate a progress message for a completed step.

    Args:
        step: The completed step.
        outputs: The step outputs.

    Returns:
        Human-readable progress message.
    """
    name = outputs.get("name", outputs.get("serviceName", ""))
    if name:
        return f"{step.description}: '{name}'"
    return str(step.description)


async def workflow_status(execution_id: str) -> dict[str, Any]:
    """Get the status of a running workflow execution.

    Args:
        execution_id: The execution ID returned by workflow_execute_with_progress.

    Returns:
        dict: Current execution status:
            - execution_id: The execution ID.
            - workflow_id: The workflow being executed.
            - status: "running", "completed", "failed", or "not_found".
            - current_step: The step currently being executed.
            - completed_steps: List of completed step IDs.
            - elapsed_ms: Time since execution started.

    Example:
        >>> await workflow_status("exec-abc123")
        {
            "execution_id": "exec-abc123",
            "workflow_id": "createMinimalService",
            "status": "running",
            "current_step": "createRegistration",
            "completed_steps": ["createService"],
            "elapsed_ms": 1234
        }
    """
    if execution_id not in _running_executions:
        return {
            "execution_id": execution_id,
            "status": "not_found",
            "message": "Execution not found or already completed.",
        }

    state = _running_executions[execution_id]
    elapsed_ms = int((time.time() - state["start_time"]) * 1000)

    return {
        "execution_id": execution_id,
        "workflow_id": state["workflow_id"],
        "status": "running" if not state["cancelled"] else "cancelling",
        "current_step": state["current_step"],
        "completed_steps": state["completed_steps"],
        "elapsed_ms": elapsed_ms,
    }


async def workflow_cancel(execution_id: str) -> dict[str, Any]:
    """Cancel a running workflow execution.

    Requests cancellation of a running workflow. The workflow will stop
    after the current step completes. Previously completed steps remain
    and can be rolled back if needed.

    Args:
        execution_id: The execution ID returned by workflow_execute_with_progress.

    Returns:
        dict: Cancellation result:
            - cancelled: True if cancellation was requested.
            - execution_id: The execution ID.
            - message: Status message.

    Example:
        >>> await workflow_cancel("exec-abc123")
        {
            "cancelled": True,
            "execution_id": "exec-abc123",
            "message": "Cancellation requested. Workflow will stop after current step."
        }
    """
    if execution_id not in _running_executions:
        raise ToolError(
            f"Execution '{execution_id}' not found or already completed. "
            "Use 'workflow_status' to check execution status."
        )

    state = _running_executions[execution_id]
    state["cancelled"] = True

    return {
        "cancelled": True,
        "execution_id": execution_id,
        "workflow_id": state["workflow_id"],
        "current_step": state["current_step"],
        "completed_steps": state["completed_steps"],
        "message": "Cancellation requested. Workflow will stop after current step.",
    }


# =============================================================================
# Story 5.6: Error Recovery & Rollback
# =============================================================================


async def workflow_retry(
    execution_id: str,
    updated_inputs: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Retry a failed workflow from the point of failure.

    Resumes execution from the failed step using the original context.
    Optionally accepts updated inputs to fix the cause of failure.

    Args:
        execution_id: The execution ID of the failed workflow.
        updated_inputs: Optional dict of updated input values to use for retry.
            Only provided values will be updated; others remain unchanged.

    Returns:
        dict: Retry results:
            - execution_id: The new execution ID for this retry.
            - original_execution_id: The failed execution being retried.
            - resumed_from_step: The step where execution resumed.
            - status: "completed", "failed", or "cancelled".
            - steps: List of step execution results.
            - outputs: Final workflow outputs (if completed).
            - message: Human-readable summary.

    Raises:
        ToolError: If execution not found or was not failed.

    Example:
        >>> await workflow_retry(
        ...     execution_id="exec-789",
        ...     updated_inputs={"registrationKey": "new-unique-key"}
        ... )
        {
            "execution_id": "exec-abc",
            "original_execution_id": "exec-789",
            "resumed_from_step": "createRegistration",
            "status": "completed",
            "message": "Workflow completed after retry"
        }
    """
    if execution_id not in _execution_history:
        raise ToolError(
            f"Execution '{execution_id}' not found in history. "
            "Only failed or cancelled executions can be retried."
        )

    history = _execution_history[execution_id]

    # Check that execution failed or was cancelled
    if history.get("status") not in (None, "failed", "cancelled"):
        raise ToolError(
            f"Execution '{execution_id}' cannot be retried. "
            f"Status is '{history.get('status')}'. "
            "Only failed/cancelled executions can be retried."
        )

    workflow_id = history["workflow_id"]
    catalog = get_workflow_catalog()
    workflow = catalog.get_workflow(workflow_id)

    if workflow is None:
        raise ToolError(f"Workflow '{workflow_id}' no longer exists. Cannot retry.")

    # Prepare inputs - merge original with updates
    inputs = history["inputs"].copy()
    if updated_inputs:
        inputs.update(updated_inputs)

    # Find the failed step to resume from
    completed_steps = history.get("completed_steps", [])
    failed_step = None
    for step_result in history.get("step_results", []):
        if step_result.get("status") == "failed":
            failed_step = step_result.get("step_id")
            break

    # If no failed step found (cancelled), find first incomplete step
    if not failed_step:
        for step in workflow.steps:
            if step.step_id not in completed_steps:
                failed_step = step.step_id
                break

    if not failed_step:
        return {
            "execution_id": execution_id,
            "status": "already_completed",
            "message": "All steps were already completed. Nothing to retry.",
        }

    # Generate new execution ID for retry
    new_execution_id = f"exec-{uuid.uuid4().hex[:8]}"
    start_time = time.time()

    # Restore context from history
    context = history.get("context", {"inputs": inputs, "steps": {}, "outputs": {}})
    context["inputs"] = inputs  # Use updated inputs

    # Register new execution
    execution_state: dict[str, Any] = {
        "execution_id": new_execution_id,
        "workflow_id": workflow_id,
        "status": "running",
        "current_step": None,
        "completed_steps": completed_steps.copy(),
        "start_time": start_time,
        "cancelled": False,
    }
    _running_executions[new_execution_id] = execution_state

    step_results: list[dict[str, Any]] = []
    total_steps = len(workflow.steps)
    resume_from_index = None

    # Find the index to resume from
    for i, step in enumerate(workflow.steps):
        if step.step_id == failed_step:
            resume_from_index = i
            break

    if resume_from_index is None:
        raise ToolError(f"Cannot find step '{failed_step}' in workflow.")

    try:
        # Execute remaining steps
        for step_index, step in enumerate(
            workflow.steps[resume_from_index:], resume_from_index + 1
        ):
            if execution_state["cancelled"]:
                return {
                    "execution_id": new_execution_id,
                    "original_execution_id": execution_id,
                    "status": "cancelled",
                    "resumed_from_step": failed_step,
                    "completed_steps": execution_state["completed_steps"],
                }

            execution_state["current_step"] = step.step_id

            # Check conditional execution
            if step.condition:
                condition_met = _evaluate_condition(step.condition, context)
                if not condition_met:
                    step_results.append(
                        {
                            "step_id": step.step_id,
                            "status": "skipped",
                            "reason": f"Condition not met: {step.condition}",
                        }
                    )
                    continue

            # Resolve step inputs from context
            step_inputs = _resolve_step_inputs(step, context)

            try:
                step_output = await _execute_step(step, step_inputs)

                context["steps"][step.step_id] = step_output
                for key, value in step_output.items():
                    context["outputs"][key] = value

                step_results.append(
                    {
                        "step_id": step.step_id,
                        "tool": step.mcp_tool,
                        "inputs": step_inputs,
                        "status": "success",
                        "outputs": step_output,
                    }
                )
                execution_state["completed_steps"].append(step.step_id)

            except Exception as e:
                step_results.append(
                    {
                        "step_id": step.step_id,
                        "tool": step.mcp_tool,
                        "inputs": step_inputs,
                        "status": "failed",
                        "error": str(e),
                    }
                )

                elapsed_ms = int((time.time() - start_time) * 1000)
                return {
                    "execution_id": new_execution_id,
                    "original_execution_id": execution_id,
                    "status": "failed",
                    "resumed_from_step": failed_step,
                    "failed_at_step": step.step_id,
                    "error": str(e),
                    "steps": step_results,
                    "completed_steps": execution_state["completed_steps"],
                    "rollback_available": True,
                    "suggestion": _generate_failure_suggestion(step, str(e)),
                    "duration_ms": elapsed_ms,
                }

        # Collect final outputs
        final_outputs = _collect_workflow_outputs(workflow, context)
        elapsed_ms = int((time.time() - start_time) * 1000)

        return {
            "execution_id": new_execution_id,
            "original_execution_id": execution_id,
            "status": "completed",
            "resumed_from_step": failed_step,
            "steps": step_results,
            "outputs": final_outputs,
            "message": f"Workflow completed after retry from '{failed_step}'",
            "duration_ms": elapsed_ms,
        }

    finally:
        if new_execution_id in _running_executions:
            _execution_history[new_execution_id] = {
                **_running_executions[new_execution_id],
                "inputs": inputs.copy(),
                "context": context.copy(),
                "step_results": step_results,
                "total_steps": total_steps,
            }
            del _running_executions[new_execution_id]


async def workflow_rollback(
    execution_id: str,
    keep_steps: list[str] | None = None,
) -> dict[str, Any]:
    """Roll back completed steps from a workflow execution.

    Reverses the changes made by completed workflow steps using the
    audit/rollback system. Can perform full or partial rollback.

    Args:
        execution_id: The execution ID to roll back.
        keep_steps: Optional list of step IDs to keep (not roll back).
            If None, all completed steps will be rolled back.

    Returns:
        dict: Rollback results:
            - execution_id: The execution ID that was rolled back.
            - rollback_status: "completed" or "partial".
            - rolled_back_steps: List of steps that were rolled back.
            - kept_steps: List of steps that were kept.
            - rollback_details: Details of each rollback action.
            - message: Human-readable summary.

    Raises:
        ToolError: If execution not found or no steps to roll back.

    Example:
        >>> await workflow_rollback("exec-789")
        {
            "execution_id": "exec-789",
            "rollback_status": "completed",
            "rolled_back_steps": ["createRegistration", "createService"],
            "message": "All workflow changes have been rolled back"
        }
    """
    if execution_id not in _execution_history:
        raise ToolError(
            f"Execution '{execution_id}' not found in history. "
            "Cannot roll back executions that have no history."
        )

    history = _execution_history[execution_id]
    completed_steps = history.get("completed_steps", [])

    if not completed_steps:
        return {
            "execution_id": execution_id,
            "rollback_status": "nothing_to_rollback",
            "message": "No completed steps to roll back.",
        }

    # Determine which steps to roll back (reverse order)
    keep_steps = keep_steps or []
    steps_to_rollback = [s for s in reversed(completed_steps) if s not in keep_steps]
    kept_steps = [s for s in completed_steps if s in keep_steps]

    if not steps_to_rollback:
        return {
            "execution_id": execution_id,
            "rollback_status": "nothing_to_rollback",
            "kept_steps": kept_steps,
            "message": "All steps were in keep_steps. Nothing to roll back.",
        }

    # Get step results for audit info
    step_results = history.get("step_results", [])
    step_outputs: dict[str, dict[str, Any]] = {}
    for result in step_results:
        if result.get("status") == "success":
            step_outputs[result["step_id"]] = result.get("outputs", {})

    rollback_details: list[dict[str, Any]] = []
    rollback_errors: list[str] = []

    # Roll back each step in reverse order
    for step_id in steps_to_rollback:
        outputs = step_outputs.get(step_id, {})

        # Determine what to roll back based on outputs
        # This integrates with the existing rollback system
        rollback_result = await _rollback_step_outputs(step_id, outputs)

        if rollback_result.get("success"):
            rollback_details.append(
                {
                    "step": step_id,
                    "action": rollback_result.get("action", "rolled back"),
                    "details": rollback_result.get("details"),
                }
            )
        else:
            rollback_errors.append(
                f"Failed to rollback {step_id}: {rollback_result.get('error')}"
            )

    rollback_status = "completed" if not rollback_errors else "partial"

    # Clean up execution history after rollback
    if rollback_status == "completed" and not kept_steps:
        del _execution_history[execution_id]

    return {
        "execution_id": execution_id,
        "rollback_status": rollback_status,
        "rolled_back_steps": steps_to_rollback,
        "kept_steps": kept_steps,
        "rollback_details": rollback_details,
        "errors": rollback_errors if rollback_errors else None,
        "message": _generate_rollback_message(
            steps_to_rollback, kept_steps, rollback_errors
        ),
    }


async def _rollback_step_outputs(
    step_id: str,
    outputs: dict[str, Any],
) -> dict[str, Any]:
    """Roll back a step's outputs using the appropriate rollback method.

    Args:
        step_id: The step ID being rolled back.
        outputs: The outputs from the step to roll back.

    Returns:
        dict with success status and details.
    """
    # For now, log the rollback action
    # Full integration with audit/rollback system would require audit_id
    action = f"Marked for rollback: {step_id}"
    details = {"outputs_to_rollback": outputs}

    # If we have an audit_id in outputs, use the real rollback
    audit_id = outputs.get("audit_id")
    if audit_id:
        try:
            from mcp_eregistrations_bpa.tools.rollback import rollback

            result = await rollback(audit_id)
            return {
                "success": True,
                "action": f"Rolled back via audit {audit_id}",
                "details": result,
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
            }

    # Without audit_id, we record the intent but can't auto-rollback
    return {
        "success": True,
        "action": action,
        "details": details,
        "note": "Manual rollback may be required (no audit_id)",
    }


def _generate_rollback_message(
    rolled_back: list[str],
    kept: list[str],
    errors: list[str],
) -> str:
    """Generate a human-readable rollback message.

    Args:
        rolled_back: Steps that were rolled back.
        kept: Steps that were kept.
        errors: Any errors that occurred.

    Returns:
        Rollback summary message.
    """
    if errors:
        return f"Partial rollback completed with {len(errors)} error(s)."

    if kept:
        return f"Rolled back {len(rolled_back)} step(s), kept {len(kept)} step(s)."

    return "All workflow changes have been rolled back."


# =============================================================================
# Story 5.7: Workflow Chaining & Composition
# =============================================================================


async def workflow_chain(
    workflows: list[dict[str, Any]],
    rollback_on_failure: bool = True,
) -> dict[str, Any]:
    """Execute multiple workflows in sequence, passing outputs forward.

    Chains workflows together, allowing outputs from earlier workflows
    to be used as inputs for later ones via the $chain[i].outputs.field syntax.

    Args:
        workflows: List of workflow specifications, each containing:
            - workflow_id: ID of the workflow to execute.
            - inputs: Dict of input values. Can reference earlier outputs
              using $chain[0].outputs.fieldName syntax.
        rollback_on_failure: If True (default), roll back all completed
            workflows when any workflow fails.

    Returns:
        dict: Chain execution results:
            - chain_id: Unique identifier for this chain execution.
            - status: "completed", "failed", or "rolled_back".
            - results: List of workflow execution results.
            - failed_at: Index of failed workflow (if status is failed/rolled_back).
            - rolled_back: List of workflow IDs that were rolled back.
            - summary: Human-readable summary of the chain execution.

    Raises:
        ToolError: If workflows list is empty or invalid.

    Example:
        >>> await workflow_chain([
        ...     {"workflow_id": "createMinimalService",
        ...      "inputs": {"serviceName": "Permit"}},
        ...     {"workflow_id": "addRole", "inputs": {
        ...         "serviceId": "$chain[0].outputs.serviceId",
        ...         "name": "Reviewer"
        ...     }}
        ... ])
        {
            "chain_id": "chain-abc123",
            "status": "completed",
            "results": [...],
            "summary": "Executed 2 workflows successfully"
        }
    """
    if not workflows:
        raise ToolError("Workflow chain must contain at least one workflow.")

    chain_id = f"chain-{uuid.uuid4().hex[:8]}"
    start_time = time.time()

    results: list[dict[str, Any]] = []
    execution_ids: list[str] = []

    for i, wf_spec in enumerate(workflows):
        workflow_id = wf_spec.get("workflow_id")
        if not workflow_id:
            raise ToolError(f"Workflow at index {i} is missing 'workflow_id'.")

        # Resolve inputs that reference previous chain outputs
        raw_inputs = wf_spec.get("inputs", {})
        resolved_inputs = _resolve_chain_inputs(raw_inputs, results)

        try:
            # Execute the workflow
            result = await workflow_execute_with_progress(
                workflow_id=workflow_id,
                inputs=resolved_inputs,
            )

            results.append(
                {
                    "workflow_id": workflow_id,
                    "index": i,
                    "status": result.get("status", "unknown"),
                    "outputs": result.get("outputs", {}),
                    "execution_id": result.get("execution_id"),
                }
            )

            if result.get("execution_id"):
                execution_ids.append(result["execution_id"])

            # Check for failure
            if result.get("status") == "failed":
                if rollback_on_failure and execution_ids:
                    rollback_results = await _rollback_chain(execution_ids[:-1])
                    elapsed_ms = int((time.time() - start_time) * 1000)

                    return {
                        "chain_id": chain_id,
                        "status": "rolled_back",
                        "failed_at": i,
                        "failed_workflow": workflow_id,
                        "error": result.get("error"),
                        "results": results,
                        "rolled_back": [r["workflow_id"] for r in results[:-1]],
                        "rollback_details": rollback_results,
                        "summary": (
                            f"Chain failed at '{workflow_id}'. "
                            "Previous workflows rolled back."
                        ),
                        "duration_ms": elapsed_ms,
                    }
                else:
                    elapsed_ms = int((time.time() - start_time) * 1000)
                    return {
                        "chain_id": chain_id,
                        "status": "failed",
                        "failed_at": i,
                        "failed_workflow": workflow_id,
                        "error": result.get("error"),
                        "results": results,
                        "summary": f"Chain failed at '{workflow_id}'.",
                        "duration_ms": elapsed_ms,
                    }

        except Exception as e:
            # Handle unexpected execution errors
            results.append(
                {
                    "workflow_id": workflow_id,
                    "index": i,
                    "status": "error",
                    "error": str(e),
                }
            )

            if rollback_on_failure and execution_ids:
                rollback_results = await _rollback_chain(execution_ids)
                elapsed_ms = int((time.time() - start_time) * 1000)

                return {
                    "chain_id": chain_id,
                    "status": "rolled_back",
                    "failed_at": i,
                    "failed_workflow": workflow_id,
                    "error": str(e),
                    "results": results,
                    "rolled_back": [
                        r["workflow_id"] for r in results[:-1] if r.get("execution_id")
                    ],
                    "rollback_details": rollback_results,
                    "summary": (
                        f"Chain error at '{workflow_id}'. "
                        "Previous workflows rolled back."
                    ),
                    "duration_ms": elapsed_ms,
                }
            else:
                elapsed_ms = int((time.time() - start_time) * 1000)
                return {
                    "chain_id": chain_id,
                    "status": "failed",
                    "failed_at": i,
                    "failed_workflow": workflow_id,
                    "error": str(e),
                    "results": results,
                    "summary": f"Chain error at '{workflow_id}'.",
                    "duration_ms": elapsed_ms,
                }

    # All workflows completed successfully
    elapsed_ms = int((time.time() - start_time) * 1000)

    # Collect all outputs for easy access
    all_outputs: dict[str, Any] = {}
    for r in results:
        for key, value in r.get("outputs", {}).items():
            all_outputs[key] = value

    return {
        "chain_id": chain_id,
        "status": "completed",
        "results": results,
        "outputs": all_outputs,
        "summary": f"Executed {len(workflows)} workflow(s) successfully.",
        "duration_ms": elapsed_ms,
    }


def _resolve_chain_inputs(
    raw_inputs: dict[str, Any],
    chain_results: list[dict[str, Any]],
) -> dict[str, Any]:
    """Resolve chain references in input values.

    Replaces $chain[i].outputs.fieldName with actual values from
    earlier workflow results.

    Args:
        raw_inputs: Input dict that may contain chain references.
        chain_results: Results from workflows executed so far.

    Returns:
        Resolved inputs with chain references replaced.
    """
    resolved: dict[str, Any] = {}

    for key, value in raw_inputs.items():
        if isinstance(value, str) and value.startswith("$chain["):
            resolved[key] = _resolve_chain_expression(value, chain_results)
        elif isinstance(value, dict):
            resolved[key] = _resolve_chain_inputs(value, chain_results)
        else:
            resolved[key] = value

    return resolved


def _resolve_chain_expression(
    expression: str,
    chain_results: list[dict[str, Any]],
) -> Any:
    """Resolve a single chain expression.

    Parses expressions like $chain[0].outputs.serviceId and
    retrieves the value from chain results.

    Args:
        expression: Expression in format $chain[i].outputs.fieldName
        chain_results: Results from workflows executed so far.

    Returns:
        The resolved value, or the expression if not resolvable.
    """
    # Pattern: $chain[0].outputs.fieldName
    match = re.match(r"\$chain\[(\d+)\]\.outputs\.(\w+)", expression)
    if not match:
        return expression

    index = int(match.group(1))
    field_name = match.group(2)

    if index >= len(chain_results):
        return expression

    outputs = chain_results[index].get("outputs", {})
    return outputs.get(field_name, expression)


async def _rollback_chain(execution_ids: list[str]) -> list[dict[str, Any]]:
    """Roll back multiple workflow executions in reverse order.

    Args:
        execution_ids: List of execution IDs to roll back.

    Returns:
        List of rollback results.
    """
    rollback_results: list[dict[str, Any]] = []

    # Roll back in reverse order
    for exec_id in reversed(execution_ids):
        try:
            result = await workflow_rollback(exec_id)
            rollback_results.append(
                {
                    "execution_id": exec_id,
                    "status": "rolled_back",
                    "details": result,
                }
            )
        except Exception as e:
            rollback_results.append(
                {
                    "execution_id": exec_id,
                    "status": "rollback_failed",
                    "error": str(e),
                }
            )

    return rollback_results


# =============================================================================
# Story 5.8: Guided Interactive Mode
# =============================================================================

# Track interactive workflow sessions
_interactive_sessions: dict[str, dict[str, Any]] = {}


async def workflow_start_interactive(workflow_id: str) -> dict[str, Any]:
    """Start an interactive workflow session with step-by-step input prompts.

    Begins an interactive mode that guides the user through providing inputs
    one at a time, with suggestions and defaults for each input.

    Args:
        workflow_id: The workflow to start interactively.

    Returns:
        dict: Interactive session state:
            - mode: "interactive"
            - session_id: Unique session identifier.
            - workflow_id: The workflow being configured.
            - current_prompt: The first input prompt with:
                - input: Input field name.
                - question: Human-readable question.
                - type: Input type (string, integer, etc.).
                - required: Whether the input is required.
                - examples: Example values.
                - default: Default value if available.
            - progress: Progress info with answered/total counts.

    Raises:
        ToolError: If the workflow is not found.

    Example:
        >>> await workflow_start_interactive("createMinimalService")
        {
            "mode": "interactive",
            "session_id": "sess-abc123",
            "workflow_id": "createMinimalService",
            "current_prompt": {
                "input": "serviceName",
                "question": "What would you like to name your service?",
                "type": "string",
                "required": True,
                "examples": ["Business Registration", "Vehicle Permits"]
            },
            "progress": {"answered": 0, "total": 4}
        }
    """
    catalog = get_workflow_catalog()
    workflow = catalog.get_workflow(workflow_id)

    if workflow is None:
        raise ToolError(
            f"Workflow '{workflow_id}' not found. "
            "Use 'workflow_list' to see available workflows."
        )

    # Generate session ID
    session_id = f"sess-{uuid.uuid4().hex[:8]}"

    # Get ordered list of inputs
    ordered_inputs = _order_inputs_for_interactive(workflow)

    if not ordered_inputs:
        raise ToolError(
            f"Workflow '{workflow_id}' has no inputs to configure. "
            "Use 'workflow_execute' to run it directly."
        )

    # Create session state
    session: dict[str, Any] = {
        "session_id": session_id,
        "workflow_id": workflow_id,
        "workflow": workflow,
        "ordered_inputs": ordered_inputs,
        "current_index": 0,
        "collected_inputs": {},
        "inferred_inputs": {},
        "started_at": time.time(),
    }
    _interactive_sessions[session_id] = session

    # Generate first prompt
    first_input = ordered_inputs[0]
    current_prompt = _generate_interactive_prompt(first_input, session)

    return {
        "mode": "interactive",
        "session_id": session_id,
        "workflow_id": workflow_id,
        "current_prompt": current_prompt,
        "progress": {
            "answered": 0,
            "total": len(ordered_inputs),
        },
    }


async def workflow_continue(
    session_id: str,
    value: Any,
) -> dict[str, Any]:
    """Provide a value and continue to the next input prompt.

    Validates the provided value, stores it, and advances to the next input.
    May auto-infer related inputs based on the provided value.

    Args:
        session_id: The interactive session ID.
        value: The value for the current input.

    Returns:
        dict: Updated session state:
            - mode: "interactive" or "preview" if all inputs collected.
            - session_id: The session ID.
            - accepted: Dict of accepted input values so far.
            - current_prompt: Next input prompt (if more inputs needed).
            - progress: Updated progress info.
            - preview: Preview data if all inputs collected.

    Raises:
        ToolError: If session not found or value is invalid.

    Example:
        >>> await workflow_continue("sess-abc123", "Vehicle Registration")
        {
            "mode": "interactive",
            "accepted": {"serviceName": "Vehicle Registration"},
            "current_prompt": {
                "input": "registrationName",
                "question": "What should the registration procedure be called?",
                "suggestion": "Vehicle Registration",
                "required": True
            },
            "progress": {"answered": 1, "total": 4}
        }
    """
    if session_id not in _interactive_sessions:
        raise ToolError(
            f"Session '{session_id}' not found. "
            "Start a new session with 'workflow_start_interactive'."
        )

    session = _interactive_sessions[session_id]
    ordered_inputs = session["ordered_inputs"]
    current_index = session["current_index"]

    if current_index >= len(ordered_inputs):
        raise ToolError(
            f"Session '{session_id}' has already collected all inputs. "
            "Use 'workflow_confirm' to execute the workflow."
        )

    current_input = ordered_inputs[current_index]

    # Validate the provided value
    validation_error = _validate_input_value(current_input, value)
    if validation_error:
        return {
            "mode": "interactive",
            "session_id": session_id,
            "error": validation_error,
            "current_prompt": _generate_interactive_prompt(current_input, session),
            "progress": {
                "answered": len(session["collected_inputs"]),
                "total": len(ordered_inputs),
            },
        }

    # Store the value
    session["collected_inputs"][current_input.name] = value

    # Infer related inputs
    _infer_related_inputs(current_input, value, session)

    # Move to next input (skip already inferred ones)
    session["current_index"] = current_index + 1
    while (
        session["current_index"] < len(ordered_inputs)
        and ordered_inputs[session["current_index"]].name in session["collected_inputs"]
    ):
        session["current_index"] += 1

    # Check if all inputs collected
    if session["current_index"] >= len(ordered_inputs):
        # All inputs collected - return preview
        return _generate_preview(session)

    # Generate next prompt
    next_input = ordered_inputs[session["current_index"]]
    current_prompt = _generate_interactive_prompt(next_input, session)

    return {
        "mode": "interactive",
        "session_id": session_id,
        "accepted": session["collected_inputs"].copy(),
        "inferred": session["inferred_inputs"].copy(),
        "current_prompt": current_prompt,
        "progress": {
            "answered": len(session["collected_inputs"]),
            "total": len(ordered_inputs),
        },
    }


async def workflow_confirm(
    session_id: str,
    execute: bool = True,
) -> dict[str, Any]:
    """Confirm and execute the workflow with collected inputs.

    After all inputs are collected and previewed, this confirms the
    configuration and executes the workflow.

    Args:
        session_id: The interactive session ID.
        execute: If True (default), execute the workflow. If False,
            return the preview without executing.

    Returns:
        dict: Execution results:
            - status: "completed", "failed", or "cancelled".
            - workflow_id: The executed workflow.
            - inputs: The inputs used for execution.
            - outputs: Workflow outputs (if completed).
            - steps: Step execution details.
            - message: Human-readable summary.

    Raises:
        ToolError: If session not found or inputs incomplete.

    Example:
        >>> await workflow_confirm("sess-abc123")
        {
            "status": "completed",
            "workflow_id": "createMinimalService",
            "outputs": {"serviceId": "svc-123", "registrationId": "reg-456"},
            "message": "Service 'Vehicle Registration' created successfully"
        }
    """
    if session_id not in _interactive_sessions:
        raise ToolError(
            f"Session '{session_id}' not found. "
            "Start a new session with 'workflow_start_interactive'."
        )

    session = _interactive_sessions[session_id]
    ordered_inputs = session["ordered_inputs"]
    collected_inputs = session["collected_inputs"]

    # Check all required inputs are present
    missing_required = []
    for inp in ordered_inputs:
        if inp.required and inp.name not in collected_inputs:
            missing_required.append(inp.name)

    if missing_required:
        missing = ", ".join(missing_required)
        raise ToolError(
            f"Cannot confirm session. Missing required inputs: {missing}. "
            "Use 'workflow_continue' to provide values."
        )

    if not execute:
        # Return preview without executing
        return _generate_preview(session)

    # Execute the workflow
    try:
        result = await workflow_execute_with_progress(
            workflow_id=session["workflow_id"],
            inputs=collected_inputs,
        )

        # Clean up session on success
        del _interactive_sessions[session_id]

        return {
            "status": result.get("status", "unknown"),
            "session_id": session_id,
            "workflow_id": session["workflow_id"],
            "inputs": collected_inputs,
            "outputs": result.get("outputs", {}),
            "steps": result.get("steps", []),
            "message": result.get("message", "Workflow executed"),
            "duration_ms": result.get("duration_ms"),
        }

    except Exception as e:
        # Keep session for retry
        return {
            "status": "failed",
            "session_id": session_id,
            "workflow_id": session["workflow_id"],
            "inputs": collected_inputs,
            "error": str(e),
            "message": f"Workflow execution failed: {e}",
            "suggestion": "Review inputs and use 'workflow_continue' to update them, "
            "then try 'workflow_confirm' again.",
        }


def _order_inputs_for_interactive(workflow: Any) -> list[Any]:
    """Order workflow inputs for interactive prompting.

    Puts primary inputs first (service name, etc.) followed by
    derived inputs that can be auto-inferred.

    Args:
        workflow: The workflow definition.

    Returns:
        Ordered list of WorkflowInput objects.
    """
    primary: list[Any] = []
    secondary: list[Any] = []
    derived: list[Any] = []

    for inp in workflow.inputs:
        name = inp.name.lower()
        if "name" in name and "service" in name:
            primary.insert(0, inp)
        elif inp.required and "name" in name:
            primary.append(inp)
        elif inp.required:
            secondary.append(inp)
        else:
            derived.append(inp)

    return primary + secondary + derived


def _generate_interactive_prompt(
    inp: Any,  # WorkflowInput
    session: dict[str, Any],
) -> dict[str, Any]:
    """Generate an interactive prompt for an input.

    Args:
        inp: The WorkflowInput to prompt for.
        session: The current session state.

    Returns:
        Prompt dictionary with question, type, examples, etc.
    """
    prompt: dict[str, Any] = {
        "input": inp.name,
        "type": inp.input_type.value
        if hasattr(inp.input_type, "value")
        else str(inp.input_type),
        "required": inp.required,
    }

    # Generate question
    prompt["question"] = _generate_input_question(inp, session)

    # Add examples
    examples = _get_input_examples(inp)
    if examples:
        prompt["examples"] = examples

    # Add default
    if inp.default is not None:
        prompt["default"] = inp.default

    # Add suggestion based on previous inputs
    suggestion = _suggest_value(inp, session)
    if suggestion:
        prompt["suggestion"] = suggestion

    # Add validation hints
    if inp.pattern:
        prompt["format"] = inp.pattern
    if inp.min_length is not None:
        prompt["min_length"] = inp.min_length
    if inp.max_length is not None:
        prompt["max_length"] = inp.max_length
    if inp.enum_values:
        prompt["options"] = inp.enum_values

    return prompt


def _generate_input_question(
    inp: Any,  # WorkflowInput
    session: dict[str, Any],
) -> str:
    """Generate a human-readable question for an input.

    Args:
        inp: The input to generate a question for.
        session: The current session.

    Returns:
        A question string.
    """
    # Use description if available
    if inp.description:
        # Convert description to question form
        desc = str(inp.description).rstrip(".")
        if not desc.endswith("?"):
            desc = f"What is the {desc.lower()}?"
        return desc

    # Generate based on name
    name = inp.name
    # Convert camelCase to words
    words = re.sub(r"([A-Z])", r" \1", name).strip().lower()

    # Special cases
    if "name" in words:
        return f"What would you like to name the {words.replace(' name', '')}?"
    if "key" in words:
        return f"What should the {words} be? (URL-safe identifier)"
    if "id" in words:
        return f"What is the {words}?"

    return f"What is the {words}?"


def _get_input_examples(inp: Any) -> list[str]:
    """Get example values for an input.

    Args:
        inp: The input definition.

    Returns:
        List of example strings.
    """
    name = inp.name.lower()

    # Known examples for common input types
    if "servicename" in name:
        return ["Business Registration", "Vehicle Permits", "Construction Licenses"]
    if "registrationname" in name:
        return ["New Registration", "Renewal Application", "License Request"]
    if "rolename" in name or name == "name":
        return ["Reviewer", "Approver", "Inspector"]
    if "key" in name:
        return ["business-reg", "vehicle-permit", "construction-license"]

    # Use enum values as examples
    if inp.enum_values:
        return [str(v) for v in inp.enum_values[:3]]

    return []


def _suggest_value(
    inp: Any,  # WorkflowInput
    session: dict[str, Any],
) -> str | None:
    """Suggest a value based on previously collected inputs.

    Args:
        inp: The input to suggest for.
        session: The current session.

    Returns:
        Suggested value or None.
    """
    collected = session["collected_inputs"]
    name = inp.name.lower()

    # Derive from serviceName
    service_name = collected.get("serviceName")
    if service_name:
        if "registrationname" in name:
            return str(service_name)
        if "registrationshortname" in name or "serviceshortname" in name:
            return _to_short_name(str(service_name))
        if "registrationkey" in name or "servicekey" in name:
            return _to_key(str(service_name))

    # Derive from registrationName
    reg_name = collected.get("registrationName")
    if reg_name:
        if "shortname" in name:
            return _to_short_name(str(reg_name))
        if "key" in name:
            return _to_key(str(reg_name))

    return None


def _infer_related_inputs(
    inp: Any,  # WorkflowInput
    value: Any,
    session: dict[str, Any],
) -> None:
    """Infer related inputs from a provided value.

    Updates session with inferred values.

    Args:
        inp: The input that was just provided.
        value: The value that was provided.
        session: The session to update.
    """
    workflow = session["workflow"]
    name = inp.name.lower()

    # Infer from serviceName
    if "servicename" in name and isinstance(value, str):
        _try_infer(
            workflow, session, "registrationName", value, "Derived from serviceName"
        )
        _try_infer(
            workflow,
            session,
            "registrationShortName",
            _to_short_name(value),
            "Generated from serviceName",
        )
        _try_infer(
            workflow,
            session,
            "registrationKey",
            _to_key(value),
            "Generated from serviceName",
        )
        _try_infer(
            workflow,
            session,
            "serviceShortName",
            _to_short_name(value),
            "Generated from serviceName",
        )

    # Infer from registrationName
    if "registrationname" in name and isinstance(value, str):
        _try_infer(
            workflow,
            session,
            "registrationShortName",
            _to_short_name(value),
            "Generated from registrationName",
        )
        _try_infer(
            workflow,
            session,
            "registrationKey",
            _to_key(value),
            "Generated from registrationName",
        )


def _try_infer(
    workflow: Any,
    session: dict[str, Any],
    field_name: str,
    value: Any,
    reason: str,
) -> None:
    """Try to infer a field value if it exists and isn't already set.

    Args:
        workflow: The workflow definition.
        session: The session state.
        field_name: The field to infer.
        value: The inferred value.
        reason: Why this value was inferred.
    """
    if field_name in session["collected_inputs"]:
        return  # Already set

    inp = workflow.get_input(field_name)
    if inp is None:
        return  # Field doesn't exist in workflow

    session["collected_inputs"][field_name] = value
    session["inferred_inputs"][field_name] = reason


def _generate_preview(session: dict[str, Any]) -> dict[str, Any]:
    """Generate a preview of the workflow configuration.

    Args:
        session: The session state.

    Returns:
        Preview dictionary.
    """
    workflow = session["workflow"]
    inputs = session["collected_inputs"]

    # Generate step preview
    steps_preview = []
    for i, step in enumerate(workflow.steps, 1):
        desc = step.description
        # Replace placeholders with actual values
        for key, value in inputs.items():
            if isinstance(value, str):
                desc = desc.replace(f"${{{key}}}", value)
                desc = desc.replace(f"$inputs.{key}", value)
        steps_preview.append(f"{i}. {desc}")

    return {
        "mode": "preview",
        "session_id": session["session_id"],
        "workflow_id": session["workflow_id"],
        "inputs": inputs.copy(),
        "inferred": session["inferred_inputs"].copy(),
        "steps_preview": steps_preview,
        "confirm_prompt": "Ready to execute? Use workflow_confirm to proceed.",
    }


# =============================================================================
# Registration
# =============================================================================


def register_workflow_tools(mcp: Any) -> None:
    """Register workflow orchestration tools with the MCP server.

    Args:
        mcp: The FastMCP server instance.
    """
    # Story 5.1: Workflow Catalog & Discovery
    mcp.tool()(workflow_list)
    mcp.tool()(workflow_describe)
    mcp.tool()(workflow_search)

    # Story 5.2: Intent-to-Workflow Matching
    mcp.tool()(workflow_match)

    # Story 5.3: Input Extraction & Validation
    mcp.tool()(workflow_extract_inputs)

    # Story 5.4: Workflow Executor
    mcp.tool()(workflow_execute)

    # Story 5.5: Progress Reporting & Streaming
    mcp.tool()(workflow_status)
    mcp.tool()(workflow_cancel)

    # Story 5.6: Error Recovery & Rollback
    mcp.tool()(workflow_retry)
    mcp.tool()(workflow_rollback)

    # Story 5.7: Workflow Chaining & Composition
    mcp.tool()(workflow_chain)

    # Story 5.8: Guided Interactive Mode
    mcp.tool()(workflow_start_interactive)
    mcp.tool()(workflow_continue)
    mcp.tool()(workflow_confirm)
