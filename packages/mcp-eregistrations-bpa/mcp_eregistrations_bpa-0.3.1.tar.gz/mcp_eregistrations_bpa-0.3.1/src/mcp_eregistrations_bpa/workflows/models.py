"""Data models for Arazzo workflow definitions.

These models represent the parsed structure of Arazzo workflow specifications,
optimized for MCP tool consumption and workflow execution.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any


class InputType(Enum):
    """Supported input types for workflow parameters."""

    STRING = "string"
    INTEGER = "integer"
    NUMBER = "number"
    BOOLEAN = "boolean"
    ARRAY = "array"
    OBJECT = "object"


@dataclass
class WorkflowInput:
    """Definition of a workflow input parameter.

    Attributes:
        name: The input parameter name.
        input_type: The type of the input (string, integer, boolean, etc.).
        required: Whether this input is required.
        description: Human-readable description of the input.
        default: Default value if not provided.
        enum_values: List of allowed values for enum inputs.
        pattern: Regex pattern for string validation.
        min_length: Minimum length for string inputs.
        max_length: Maximum length for string inputs.
        minimum: Minimum value for numeric inputs.
        maximum: Maximum value for numeric inputs.
    """

    name: str
    input_type: InputType = InputType.STRING
    required: bool = False
    description: str = ""
    default: Any = None
    enum_values: list[str] | None = None
    pattern: str | None = None
    min_length: int | None = None
    max_length: int | None = None
    minimum: float | None = None
    maximum: float | None = None

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for API response."""
        result: dict[str, Any] = {
            "name": self.name,
            "type": self.input_type.value,
            "required": self.required,
        }
        if self.description:
            result["description"] = self.description
        if self.default is not None:
            result["default"] = self.default
        if self.enum_values:
            result["enum"] = self.enum_values
        if self.pattern:
            result["pattern"] = self.pattern
        if self.min_length is not None:
            result["minLength"] = self.min_length
        if self.max_length is not None:
            result["maxLength"] = self.max_length
        if self.minimum is not None:
            result["minimum"] = self.minimum
        if self.maximum is not None:
            result["maximum"] = self.maximum
        return result


@dataclass
class WorkflowStep:
    """Definition of a single step in a workflow.

    Attributes:
        step_id: Unique identifier for this step within the workflow.
        description: Human-readable description of what this step does.
        operation_id: The BPA API operation ID (optional).
        mcp_tool: The MCP tool to invoke for this step (derived from operationId).
        request_body: The request body template with input references.
        parameters: Path/query parameters for the API call.
        success_criteria: Conditions for step success.
        on_success: Actions to take on success (goto next step, end).
        on_failure: Actions to take on failure.
        outputs: Output mappings from response to step outputs.
        condition: Optional condition for conditional step execution.
    """

    step_id: str
    description: str = ""
    operation_id: str | None = None
    mcp_tool: str | None = None
    request_body: dict[str, Any] = field(default_factory=dict)
    parameters: list[dict[str, Any]] = field(default_factory=list)
    success_criteria: list[dict[str, Any]] = field(default_factory=list)
    on_success: list[dict[str, Any]] = field(default_factory=list)
    on_failure: list[dict[str, Any]] = field(default_factory=list)
    outputs: dict[str, str] = field(default_factory=dict)
    condition: str | None = None

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for API response."""
        result: dict[str, Any] = {
            "step_id": self.step_id,
            "description": self.description,
        }
        if self.mcp_tool:
            result["tool"] = self.mcp_tool
        if self.outputs:
            result["outputs"] = list(self.outputs.keys())
        if self.condition:
            result["condition"] = self.condition
        return result


@dataclass
class WorkflowDefinition:
    """Complete definition of an Arazzo workflow.

    Attributes:
        workflow_id: Unique identifier for the workflow.
        summary: Short summary of what the workflow does.
        description: Detailed description with usage examples.
        category: Category for grouping related workflows.
        inputs: List of input parameter definitions.
        steps: List of workflow steps to execute.
        outputs: Output mappings from step outputs to workflow outputs.
        failure_actions: Actions to take on workflow failure.
        source_file: Path to the source Arazzo file.
    """

    workflow_id: str
    summary: str = ""
    description: str = ""
    category: str = "general"
    inputs: list[WorkflowInput] = field(default_factory=list)
    steps: list[WorkflowStep] = field(default_factory=list)
    outputs: dict[str, str] = field(default_factory=dict)
    failure_actions: list[dict[str, Any]] = field(default_factory=list)
    source_file: str = ""

    @property
    def required_inputs(self) -> list[str]:
        """Get list of required input names."""
        return [inp.name for inp in self.inputs if inp.required]

    @property
    def optional_inputs(self) -> list[str]:
        """Get list of optional input names."""
        return [inp.name for inp in self.inputs if not inp.required]

    def get_input(self, name: str) -> WorkflowInput | None:
        """Get input definition by name."""
        for inp in self.inputs:
            if inp.name == name:
                return inp
        return None

    def to_catalog_entry(self) -> dict[str, Any]:
        """Convert to catalog entry format (summary view)."""
        return {
            "id": self.workflow_id,
            "summary": self.summary,
            "category": self.category,
            "required_inputs": self.required_inputs,
            "optional_inputs": self.optional_inputs,
        }

    def to_detail_dict(self) -> dict[str, Any]:
        """Convert to detailed format for workflow_describe."""
        return {
            "id": self.workflow_id,
            "summary": self.summary,
            "description": self.description,
            "category": self.category,
            "inputs": {inp.name: inp.to_dict() for inp in self.inputs},
            "steps": [step.to_dict() for step in self.steps],
            "outputs": list(self.outputs.keys()),
            "source_file": self.source_file,
        }


# Mapping from Arazzo operationId to MCP tool names
OPERATION_TO_TOOL_MAP: dict[str, str] = {
    # Service operations
    "createService": "service_create",
    "updateService": "service_update",
    "getService": "service_get",
    "listServices": "service_list",
    # Registration operations
    "createRegistration": "registration_create",
    "updateRegistration": "registration_update",
    "getRegistration": "registration_get",
    "listRegistrations": "registration_list",
    # Role operations
    "createRole": "role_create",
    "updateRole": "role_update",
    "deleteRole": "role_delete",
    "getRole": "role_get",
    "listRoles": "role_list",
    # Bot operations
    "createBot": "bot_create",
    "updateBot": "bot_update",
    "getBot": "bot_get",
    "listBots": "bot_list",
    # Determinant operations
    "createTextDeterminant": "textdeterminant_create",
    "updateTextDeterminant": "textdeterminant_update",
    "createSelectDeterminant": "selectdeterminant_create",
    "getDeterminant": "determinant_get",
    "listDeterminants": "determinant_list",
    # Document requirement operations
    "createDocumentRequirement": "documentrequirement_create",
    "updateDocumentRequirement": "documentrequirement_update",
    "deleteDocumentRequirement": "documentrequirement_delete",
    "listDocumentRequirements": "documentrequirement_list",
    # Cost operations
    "createFixedCost": "cost_create_fixed",
    "createFormulaCost": "cost_create_formula",
    "updateCost": "cost_update",
    "deleteCost": "cost_delete",
    # Field operations
    "getField": "field_get",
    "listFields": "field_list",
}


def derive_category(workflow_id: str, summary: str, description: str) -> str:
    """Derive workflow category from its ID and content.

    Args:
        workflow_id: The workflow ID.
        summary: The workflow summary.
        description: The workflow description.

    Returns:
        A category string for grouping.
    """
    workflow_lower = workflow_id.lower()
    combined = f"{summary} {description}".lower()

    # Service creation
    if "createservice" in workflow_lower or "create a service" in combined:
        return "service-creation"

    # Role configuration
    if "role" in workflow_lower or "role" in combined:
        return "roles-configuration"

    # Bot configuration
    if "bot" in workflow_lower or "automation" in combined:
        return "automation"

    # Form configuration
    if "form" in workflow_lower or "field" in workflow_lower:
        return "forms"

    # Payment configuration
    if "payment" in workflow_lower or "cost" in workflow_lower:
        return "payments"

    # Determinant configuration
    if "determinant" in workflow_lower:
        return "determinants"

    # Document configuration
    if "document" in workflow_lower:
        return "documents"

    # Notification configuration
    if "notification" in workflow_lower:
        return "notifications"

    # Classification configuration
    if "classification" in workflow_lower:
        return "classifications"

    # Institution configuration
    if "institution" in workflow_lower:
        return "institutions"

    # Workflow configuration
    if "workflow" in workflow_lower:
        return "workflow"

    # Publishing
    if "publish" in workflow_lower:
        return "publishing"

    return "general"
