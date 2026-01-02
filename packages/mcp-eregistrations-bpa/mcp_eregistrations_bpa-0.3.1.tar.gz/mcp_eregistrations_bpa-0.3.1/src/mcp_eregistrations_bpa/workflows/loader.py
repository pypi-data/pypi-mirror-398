"""Arazzo workflow loader and catalog manager.

Loads Arazzo YAML workflow specifications and provides a catalog
for workflow discovery and execution.
"""

from __future__ import annotations

import re
from pathlib import Path
from typing import Any

import yaml

from mcp_eregistrations_bpa.workflows.models import (
    OPERATION_TO_TOOL_MAP,
    InputType,
    WorkflowDefinition,
    WorkflowInput,
    WorkflowStep,
    derive_category,
)

# Default workflow directory (relative to project root)
DEFAULT_WORKFLOW_DIR = "_bmad-output/arazzo-workflows"


class WorkflowCatalog:
    """Catalog of available Arazzo workflows.

    Loads and indexes workflows from Arazzo YAML files for discovery
    and execution by the workflow orchestration tools.
    """

    def __init__(self) -> None:
        """Initialize an empty workflow catalog."""
        self._workflows: dict[str, WorkflowDefinition] = {}
        self._loaded = False
        self._workflow_dir: Path | None = None

    @property
    def workflow_count(self) -> int:
        """Get the number of loaded workflows."""
        return len(self._workflows)

    @property
    def categories(self) -> list[str]:
        """Get unique categories from all workflows."""
        cats = set()
        for wf in self._workflows.values():
            cats.add(wf.category)
        return sorted(cats)

    def load_from_directory(self, workflow_dir: str | Path | None = None) -> None:
        """Load all Arazzo workflows from a directory.

        Args:
            workflow_dir: Path to the workflow directory.
                If None, searches for the default location.

        Raises:
            FileNotFoundError: If the workflow directory doesn't exist.
        """
        if workflow_dir is None:
            workflow_dir = self._find_workflow_directory()

        self._workflow_dir = Path(workflow_dir)
        if not self._workflow_dir.exists():
            raise FileNotFoundError(
                f"Workflow directory not found: {self._workflow_dir}"
            )

        # Load all .arazzo.yaml files
        for yaml_file in self._workflow_dir.glob("*.arazzo.yaml"):
            self._load_arazzo_file(yaml_file)

        self._loaded = True

    def _find_workflow_directory(self) -> Path:
        """Find the workflow directory by searching from current directory upward.

        Returns:
            Path to the workflow directory.

        Raises:
            FileNotFoundError: If the workflow directory is not found.
        """
        # Start from current working directory
        current = Path.cwd()

        # Search upward for the workflow directory
        for _ in range(10):  # Limit search depth
            candidate = current / DEFAULT_WORKFLOW_DIR
            if candidate.exists():
                return candidate

            parent = current.parent
            if parent == current:
                break
            current = parent

        # Try relative to this module's location
        module_dir = Path(__file__).parent.parent.parent.parent
        candidate = module_dir / DEFAULT_WORKFLOW_DIR
        if candidate.exists():
            return candidate

        raise FileNotFoundError(
            f"Workflow directory '{DEFAULT_WORKFLOW_DIR}' not found. "
            "Ensure you're running from the project root."
        )

    def _load_arazzo_file(self, yaml_file: Path) -> None:
        """Load workflows from a single Arazzo YAML file.

        Args:
            yaml_file: Path to the Arazzo YAML file.
        """
        with open(yaml_file, encoding="utf-8") as f:
            data = yaml.safe_load(f)

        if not data or "workflows" not in data:
            return

        assert self._workflow_dir is not None  # Set by load_from_directory before call
        source_file = str(yaml_file.relative_to(self._workflow_dir.parent.parent))

        for workflow_data in data.get("workflows", []):
            workflow = self._parse_workflow(workflow_data, source_file)
            if workflow:
                self._workflows[workflow.workflow_id] = workflow

    def _parse_workflow(
        self, data: dict[str, Any], source_file: str
    ) -> WorkflowDefinition | None:
        """Parse a single workflow definition from Arazzo data.

        Args:
            data: The workflow dictionary from the YAML.
            source_file: Path to the source file.

        Returns:
            Parsed WorkflowDefinition or None if invalid.
        """
        workflow_id = data.get("workflowId")
        if not workflow_id:
            return None

        summary = data.get("summary", "")
        description = data.get("description", "")
        category = derive_category(workflow_id, summary, description)

        # Parse inputs
        inputs = self._parse_inputs(data.get("inputs", {}))

        # Parse steps
        steps = self._parse_steps(data.get("steps", []))

        # Parse outputs
        outputs = data.get("outputs", {})
        if isinstance(outputs, list):
            # Convert list to dict with same key/value
            outputs = {o: o for o in outputs}

        return WorkflowDefinition(
            workflow_id=workflow_id,
            summary=summary,
            description=description,
            category=category,
            inputs=inputs,
            steps=steps,
            outputs=outputs,
            failure_actions=data.get("failureActions", []),
            source_file=source_file,
        )

    def _parse_inputs(self, inputs_data: dict[str, Any]) -> list[WorkflowInput]:
        """Parse workflow input definitions.

        Args:
            inputs_data: The inputs section from the workflow.

        Returns:
            List of WorkflowInput objects.
        """
        result: list[WorkflowInput] = []

        if not isinstance(inputs_data, dict):
            return result

        properties = inputs_data.get("properties", {})
        required = inputs_data.get("required", [])

        for name, prop_data in properties.items():
            input_type = self._parse_input_type(prop_data.get("type", "string"))
            result.append(
                WorkflowInput(
                    name=name,
                    input_type=input_type,
                    required=name in required,
                    description=prop_data.get("description", ""),
                    default=prop_data.get("default"),
                    enum_values=prop_data.get("enum"),
                    pattern=prop_data.get("pattern"),
                    min_length=prop_data.get("minLength"),
                    max_length=prop_data.get("maxLength"),
                    minimum=prop_data.get("minimum"),
                    maximum=prop_data.get("maximum"),
                )
            )

        return result

    def _parse_input_type(self, type_str: str) -> InputType:
        """Parse input type string to InputType enum.

        Args:
            type_str: The type string from YAML.

        Returns:
            The corresponding InputType.
        """
        type_map = {
            "string": InputType.STRING,
            "integer": InputType.INTEGER,
            "number": InputType.NUMBER,
            "boolean": InputType.BOOLEAN,
            "array": InputType.ARRAY,
            "object": InputType.OBJECT,
        }
        return type_map.get(type_str.lower(), InputType.STRING)

    def _parse_steps(self, steps_data: list[dict[str, Any]]) -> list[WorkflowStep]:
        """Parse workflow step definitions.

        Args:
            steps_data: The steps list from the workflow.

        Returns:
            List of WorkflowStep objects.
        """
        result: list[WorkflowStep] = []

        for step_data in steps_data:
            step_id = step_data.get("stepId")
            if not step_id:
                continue

            operation_id = step_data.get("operationId")
            mcp_tool = OPERATION_TO_TOOL_MAP.get(operation_id) if operation_id else None

            # Parse request body
            request_body = {}
            if "requestBody" in step_data:
                rb = step_data["requestBody"]
                if isinstance(rb, dict) and "payload" in rb:
                    request_body = rb["payload"]

            result.append(
                WorkflowStep(
                    step_id=step_id,
                    description=step_data.get("description", ""),
                    operation_id=operation_id,
                    mcp_tool=mcp_tool,
                    request_body=request_body,
                    parameters=step_data.get("parameters", []),
                    success_criteria=step_data.get("successCriteria", []),
                    on_success=step_data.get("onSuccess", []),
                    on_failure=step_data.get("onFailure", []),
                    outputs=step_data.get("outputs", {}),
                    condition=step_data.get("condition"),
                )
            )

        return result

    def get_workflow(self, workflow_id: str) -> WorkflowDefinition | None:
        """Get a workflow by ID.

        Args:
            workflow_id: The workflow ID to look up.

        Returns:
            The workflow definition or None if not found.
        """
        self._ensure_loaded()
        return self._workflows.get(workflow_id)

    def list_workflows(self, category: str | None = None) -> list[dict[str, Any]]:
        """List all workflows, optionally filtered by category.

        Args:
            category: Optional category to filter by.

        Returns:
            List of workflow catalog entries.
        """
        self._ensure_loaded()

        result = []
        for wf in self._workflows.values():
            if category is None or wf.category == category:
                result.append(wf.to_catalog_entry())

        return result

    def search_workflows(self, query: str, limit: int = 10) -> list[dict[str, Any]]:
        """Search workflows by keyword.

        Searches in workflow ID, summary, and description.
        Returns matches with relevance scores.

        Args:
            query: The search query.
            limit: Maximum number of results.

        Returns:
            List of matches with relevance scores.
        """
        self._ensure_loaded()

        query_lower = query.lower()
        query_words = set(re.split(r"\W+", query_lower))

        matches: list[tuple[float, WorkflowDefinition]] = []

        for wf in self._workflows.values():
            score = self._calculate_relevance(wf, query_lower, query_words)
            if score > 0:
                matches.append((score, wf))

        # Sort by relevance (descending)
        matches.sort(key=lambda x: x[0], reverse=True)

        return [
            {
                "id": wf.workflow_id,
                "summary": wf.summary,
                "category": wf.category,
                "relevance": round(score, 2),
            }
            for score, wf in matches[:limit]
        ]

    def _calculate_relevance(
        self,
        workflow: WorkflowDefinition,
        query_lower: str,
        query_words: set[str],
    ) -> float:
        """Calculate relevance score for a workflow against a query.

        Args:
            workflow: The workflow to score.
            query_lower: The lowercase query string.
            query_words: Set of query words.

        Returns:
            Relevance score (0-1).
        """
        score = 0.0

        # Exact ID match
        if query_lower in workflow.workflow_id.lower():
            score += 0.5

        # ID word match
        id_words = set(re.split(r"(?=[A-Z])|_|-", workflow.workflow_id.lower()))
        id_matches = len(query_words & id_words)
        if id_matches > 0:
            score += 0.3 * (id_matches / len(query_words))

        # Summary match
        summary_lower = workflow.summary.lower()
        if query_lower in summary_lower:
            score += 0.3
        else:
            summary_words = set(re.split(r"\W+", summary_lower))
            summary_matches = len(query_words & summary_words)
            if summary_matches > 0:
                score += 0.2 * (summary_matches / len(query_words))

        # Description match
        desc_lower = workflow.description.lower()
        if query_lower in desc_lower:
            score += 0.1
        else:
            desc_words = set(re.split(r"\W+", desc_lower))
            desc_matches = len(query_words & desc_words)
            if desc_matches > 0:
                score += 0.05 * (desc_matches / len(query_words))

        # Category match
        if query_lower in workflow.category.lower():
            score += 0.1

        return min(score, 1.0)

    def _ensure_loaded(self) -> None:
        """Ensure workflows are loaded, loading if necessary."""
        if not self._loaded:
            self.load_from_directory()


# Global catalog instance
_catalog: WorkflowCatalog | None = None


def get_workflow_catalog() -> WorkflowCatalog:
    """Get the global workflow catalog instance.

    Loads workflows on first access.

    Returns:
        The global WorkflowCatalog instance.
    """
    global _catalog
    if _catalog is None:
        _catalog = WorkflowCatalog()
        try:
            _catalog.load_from_directory()
        except FileNotFoundError:
            # Catalog will be empty but usable
            pass
    return _catalog


def reload_workflow_catalog(workflow_dir: str | Path | None = None) -> WorkflowCatalog:
    """Reload the workflow catalog from disk.

    Args:
        workflow_dir: Optional path to the workflow directory.

    Returns:
        The reloaded WorkflowCatalog instance.
    """
    global _catalog
    _catalog = WorkflowCatalog()
    _catalog.load_from_directory(workflow_dir)
    return _catalog
