"""YAML transformation engine for BPA service exports.

Transforms raw JSON exports from BPA into clean, human-readable YAML
suitable for AI consumption, version control, and documentation.

Key transformations:
- Parse stringified JSON (formSchema, jsonDeterminants)
- Convert camelCase to snake_case
- Extract essential Form.io properties
- Preserve metadata for re-import
"""

from __future__ import annotations

import json
import re
from datetime import UTC, datetime
from typing import Any

import yaml

__all__ = [
    "YAMLTransformer",
    "TransformationError",
]

# Schema version for the YAML output
SCHEMA_VERSION = "1.0"

# Form.io properties to extract (essential for understanding the form)
ESSENTIAL_FORMIO_PROPS = {
    "key",
    "type",
    "label",
    "validate",
    "data",
    "determinantIds",
    "hidden",
    "disabled",
    "defaultValue",
    "multiple",
    "conditional",
}

# Form.io properties to skip (internal/noise)
SKIP_FORMIO_PROPS = {
    "tableView",
    "input",
    "version",
    "persistent",
    "customDefaultValue",
    "calculateValue",
    "calculateServer",
    "widget",
    "attributes",
    "overlay",
    "allowCalculateOverride",
    "encrypted",
    "showCharCount",
    "showWordCount",
    "spellcheck",
    "redrawOn",
    "clearOnHide",
    "modalEdit",
    "refreshOn",
    "dataGridLabel",
    "allowMultipleMasks",
    "addons",
    "mask",
    "inputType",
    "inputFormat",
    "inputMask",
    "displayMask",
    "tabindex",
    "autocomplete",
    "dbIndex",
    "customClass",
    "id",
    "placeholder",
    "prefix",
    "suffix",
    "tooltip",
    "description",
    "errorLabel",
    "hideLabel",
    "autofocus",
    "kickbox",
    "minLength",
    "maxLength",
    "delimiter",
    "requireDecimal",
    "case",
    "truncateMultipleSpaces",
}


class TransformationError(Exception):
    """Raised when YAML transformation fails."""

    pass


def camel_to_snake(name: str) -> str:
    """Convert camelCase to snake_case.

    Args:
        name: The camelCase string to convert.

    Returns:
        The snake_case equivalent.

    Examples:
        >>> camel_to_snake("shortName")
        'short_name'
        >>> camel_to_snake("applicantFormSelected")
        'applicant_form_selected'
    """
    # Insert underscore before uppercase letters and convert to lowercase
    s1 = re.sub(r"(.)([A-Z][a-z]+)", r"\1_\2", name)
    return re.sub(r"([a-z0-9])([A-Z])", r"\1_\2", s1).lower()


def transform_keys(obj: Any, skip_keys: set[str] | None = None) -> Any:
    """Recursively transform dictionary keys from camelCase to snake_case.

    Args:
        obj: The object to transform (dict, list, or primitive).
        skip_keys: Set of keys to skip transformation for.

    Returns:
        The transformed object with snake_case keys.
    """
    skip_keys = skip_keys or set()

    if isinstance(obj, dict):
        return {
            (camel_to_snake(k) if k not in skip_keys else k): transform_keys(
                v, skip_keys
            )
            for k, v in obj.items()
        }
    elif isinstance(obj, list):
        return [transform_keys(item, skip_keys) for item in obj]
    else:
        return obj


class YAMLTransformer:
    """Transforms BPA JSON exports to clean YAML format."""

    def __init__(self, include_metadata: bool = True) -> None:
        """Initialize the transformer.

        Args:
            include_metadata: Whether to include _metadata section with IDs
                for re-import capability. Default True.
        """
        self._include_metadata = include_metadata
        self._metadata: dict[str, Any] = {}

    def transform_to_dict(
        self, export_data: dict[str, Any]
    ) -> tuple[dict[str, Any], dict[str, Any]]:
        """Transform raw JSON export to optimized dictionary structure.

        This method builds the clean, optimized data structure without
        serializing it. Use this when you need the data as a Python dict
        (e.g., for JSON serialization).

        Args:
            export_data: Raw JSON export from service_export_raw.

        Returns:
            Tuple of (data_dict, summary).

        Raises:
            TransformationError: If transformation fails.
        """
        try:
            # Build the optimized structure
            data_dict = self._build_yaml_structure(export_data)

            # Generate summary (extract from data since it's now in the structure)
            summary = data_dict.get("summary", {}).copy()
            if not summary:
                summary = self._generate_summary(data_dict)

            return data_dict, summary

        except Exception as e:
            raise TransformationError(f"Failed to transform export: {e}") from e

    def transform(self, export_data: dict[str, Any]) -> tuple[str, dict[str, Any]]:
        """Transform raw JSON export to YAML.

        Args:
            export_data: Raw JSON export from service_export_raw.

        Returns:
            Tuple of (yaml_content, summary).

        Raises:
            TransformationError: If transformation fails.
        """
        try:
            # Build the optimized structure
            yaml_data, summary = self.transform_to_dict(export_data)

            # Convert to YAML string
            yaml_content = yaml.dump(
                yaml_data,
                default_flow_style=False,
                allow_unicode=True,
                sort_keys=False,
                width=120,
            )

            return yaml_content, summary

        except Exception as e:
            raise TransformationError(f"Failed to transform export: {e}") from e

    def _build_yaml_structure(self, data: dict[str, Any]) -> dict[str, Any]:
        """Build the complete YAML structure.

        Args:
            data: Raw export data.

        Returns:
            Structured dictionary for YAML output.
        """
        # Reset metadata for this transformation
        self._metadata = {
            "service_id": data.get("id"),
            "service_old_id": data.get("oldId"),
            "registration_ids": {},
            "determinant_ids": {},
            "role_ids": {},
            "bot_ids": {},
        }

        result: dict[str, Any] = {
            "version": SCHEMA_VERSION,
            "exported_at": datetime.now(UTC).isoformat(),
        }

        # Add BPA version if available
        if "bpaVersion" in data:
            result["bpa_version"] = data["bpaVersion"]

        # Build all sections first to calculate summary
        service_section = self._build_service_section(data)
        registrations = data.get("registrations", [])
        registrations_section = (
            self._build_registrations_section(registrations) if registrations else []
        )
        determinants = data.get("determinants", [])
        determinants_section = (
            self._build_determinants_section(determinants) if determinants else {}
        )
        forms_section = self._build_forms_section(data)
        roles = data.get("roles", [])
        workflow_section = self._build_workflow_section(roles) if roles else {}
        bots = data.get("bots", [])
        bots_section = self._build_bots_section(bots) if bots else {}
        print_docs = data.get("printDocuments", [])
        print_docs_section = (
            self._build_print_documents_section(print_docs) if print_docs else []
        )

        # Add summary section at the top (after version/exported_at)
        result["summary"] = self._build_summary_section(
            service_section,
            registrations_section,
            determinants_section,
            forms_section,
            workflow_section,
            bots_section,
        )

        # Build service section
        result["service"] = service_section

        # Add pre-built sections (only if they have content)
        if registrations_section:
            result["registrations"] = registrations_section

        if determinants_section:
            result["determinants"] = determinants_section

        if forms_section:
            result["forms"] = forms_section

        if workflow_section and workflow_section.get("roles"):
            result["workflow"] = workflow_section

        if bots_section:
            result["bots"] = bots_section

        if print_docs_section:
            result["print_documents"] = print_docs_section

        # Add metadata section if requested
        if self._include_metadata:
            result["_metadata"] = self._metadata

        return result

    def _build_summary_section(
        self,
        service_section: dict[str, Any],
        registrations_section: list[dict[str, Any]],
        determinants_section: dict[str, Any],
        forms_section: dict[str, Any],
        workflow_section: dict[str, Any],
        bots_section: dict[str, Any],
    ) -> dict[str, Any]:
        """Build the summary section for quick scanning.

        Args:
            service_section: Built service section.
            registrations_section: Built registrations list.
            determinants_section: Built determinants dictionary.
            forms_section: Built forms dictionary.
            workflow_section: Built workflow dictionary.
            bots_section: Built bots dictionary.

        Returns:
            Summary dictionary with counts.
        """
        summary: dict[str, Any] = {
            "service_name": service_section.get("name", "Unknown"),
        }

        # Count registrations
        summary["registration_count"] = len(registrations_section)

        # Count determinants
        det_count = 0
        for category in determinants_section.values():
            if isinstance(category, list):
                det_count += len(category)
        summary["determinant_count"] = det_count

        # Count form fields
        field_count = 0
        for form in forms_section.values():
            if isinstance(form, dict):
                components = form.get("components", [])
                field_count += self._count_components(components)
        summary["field_count"] = field_count

        # Count roles
        roles = workflow_section.get("roles", [])
        summary["role_count"] = len(roles)

        # Count bots
        bot_count = 0
        for category in bots_section.values():
            if isinstance(category, list):
                bot_count += len(category)
        summary["bot_count"] = bot_count

        return summary

    def _build_service_section(self, data: dict[str, Any]) -> dict[str, Any]:
        """Build the service section.

        Args:
            data: Raw export data.

        Returns:
            Service section dictionary.
        """
        service: dict[str, Any] = {
            "name": data.get("name", "Unknown"),
            "short_name": data.get("shortName", ""),
            "active": data.get("active", True),
        }

        # Extract service properties from serviceJsonProperties
        json_props = data.get("serviceJsonProperties")
        if json_props:
            if isinstance(json_props, str):
                try:
                    json_props = json.loads(json_props)
                except json.JSONDecodeError:
                    json_props = {}

            if isinstance(json_props, dict):
                service["properties"] = transform_keys(json_props)

        return service

    def _build_registrations_section(
        self, registrations: list[dict[str, Any]]
    ) -> list[dict[str, Any]]:
        """Build the registrations section.

        Args:
            registrations: List of registration objects.

        Returns:
            Transformed registrations list.
        """
        result = []

        for reg in registrations:
            name = reg.get("name", "Unknown")

            # Store ID mapping
            if reg.get("id"):
                self._metadata["registration_ids"][name] = reg["id"]

            transformed = {
                "name": name,
                "short_name": reg.get("shortName", ""),
                "active": reg.get("active", True),
            }

            # Add costs if present
            costs = reg.get("costs", [])
            if costs:
                transformed["costs"] = self._transform_costs(costs)

            # Add document requirements if present
            doc_reqs = reg.get("documentRequirements", [])
            if doc_reqs:
                transformed["document_requirements"] = [
                    {"name": dr.get("name", ""), "required": dr.get("required", True)}
                    for dr in doc_reqs
                ]

            # Add document results if present
            doc_results = reg.get("documentResults", [])
            if doc_results:
                transformed["document_results"] = [
                    {
                        "name": dr.get("name", ""),
                        "is_digital": dr.get("isDigital", False),
                    }
                    for dr in doc_results
                ]

            result.append(transformed)

        return result

    def _transform_costs(self, costs: list[dict[str, Any]]) -> list[dict[str, Any]]:
        """Transform cost objects.

        Args:
            costs: List of cost objects.

        Returns:
            Transformed costs list.
        """
        result = []

        for cost in costs:
            transformed: dict[str, Any] = {
                "name": cost.get("name", ""),
            }

            # Determine cost type
            cost_type = cost.get("costType", "").lower()
            if cost_type == "fix":
                transformed["type"] = "fixed"
                transformed["amount"] = cost.get("fixValue", 0)
            elif cost_type == "formula":
                transformed["type"] = "formula"
                transformed["formula"] = cost.get("formula", "")
            else:
                transformed["type"] = cost_type or "unknown"

            # Add currency if present
            currency = cost.get("currency") or cost.get("currencyId")
            if currency:
                transformed["currency"] = currency

            result.append(transformed)

        return result

    def _build_determinants_section(
        self, determinants: list[dict[str, Any]]
    ) -> dict[str, Any]:
        """Build the determinants section.

        Args:
            determinants: List of determinant objects.

        Returns:
            Categorized determinants dictionary.
        """
        form_field_based = []
        registration_based = []
        other = []

        for det in determinants:
            name = det.get("name", "Unknown")

            # Store ID mapping
            if det.get("id"):
                self._metadata["determinant_ids"][name] = det["id"]

            det_type = det.get("type", "").lower()

            transformed: dict[str, Any] = {
                "name": name,
            }

            if det_type in ("textdeterminant", "text"):
                transformed["field"] = det.get("targetFormFieldKey", "")
                transformed["operator"] = det.get("operator", "equals")
                # Parse condition value from jsonCondition if available
                json_cond = det.get("jsonCondition")
                if json_cond:
                    transformed["value"] = self._parse_condition_value(json_cond)
                form_field_based.append(transformed)

            elif det_type in ("selectdeterminant", "select"):
                transformed["field"] = det.get("targetFormFieldKey", "")
                transformed["operator"] = det.get("operator", "equals")
                transformed["value"] = det.get("selectValue", "")
                form_field_based.append(transformed)

            elif det_type in ("registrationdeterminant", "registration"):
                transformed["registration"] = det.get("registrationName", "")
                transformed["selected"] = det.get("selected", True)
                registration_based.append(transformed)

            else:
                transformed["type"] = det_type
                other.append(transformed)

        result: dict[str, Any] = {}

        if form_field_based:
            result["form_field_based"] = form_field_based

        if registration_based:
            result["registration_based"] = registration_based

        if other:
            result["other"] = other

        return result

    def _parse_condition_value(self, json_condition: str | dict[str, Any]) -> Any:
        """Parse condition value from jsonCondition.

        Args:
            json_condition: JSON condition string or dict.

        Returns:
            Extracted condition value.
        """
        if isinstance(json_condition, str):
            try:
                json_condition = json.loads(json_condition)
            except json.JSONDecodeError:
                return json_condition

        if isinstance(json_condition, dict):
            # Extract value from common patterns
            return json_condition.get("value", json_condition)

        return json_condition

    def _build_forms_section(self, data: dict[str, Any]) -> dict[str, Any]:
        """Build the forms section.

        Args:
            data: Raw export data.

        Returns:
            Forms section dictionary.
        """
        forms: dict[str, Any] = {}

        form_keys = [
            ("guideForm", "guide"),
            ("applicantForm", "applicant"),
            ("sendFileForm", "send_file"),
            ("paymentForm", "payment"),
        ]

        for json_key, yaml_key in form_keys:
            form_data = data.get(json_key)
            if form_data:
                parsed = self._parse_form(form_data)
                if parsed:
                    forms[yaml_key] = parsed

        return forms

    def _parse_form(self, form_data: dict[str, Any]) -> dict[str, Any] | None:
        """Parse a form object.

        Args:
            form_data: Form data from export.

        Returns:
            Parsed form dictionary or None.
        """
        if not form_data:
            return None

        result: dict[str, Any] = {
            "active": form_data.get("active", True),
        }

        # Parse form schema
        form_schema = form_data.get("formSchema")
        if form_schema:
            components = self._parse_form_schema(form_schema)
            if components:
                result["components"] = components

        return result

    def _parse_form_schema(
        self, schema: str | dict[str, Any]
    ) -> list[dict[str, Any]] | None:
        """Parse Form.io schema (may be stringified JSON).

        Args:
            schema: Form schema (string or dict).

        Returns:
            List of parsed components.
        """
        if isinstance(schema, str):
            try:
                schema = json.loads(schema)
            except json.JSONDecodeError:
                return None

        if not isinstance(schema, dict):
            return None

        components = schema.get("components", [])
        if not components:
            return None

        return self._extract_components(components)

    def _extract_components(
        self, components: list[dict[str, Any]]
    ) -> list[dict[str, Any]]:
        """Extract essential properties from Form.io components.

        Args:
            components: List of Form.io components.

        Returns:
            Simplified component list.
        """
        result = []

        for comp in components:
            if not isinstance(comp, dict):
                continue

            # Skip components without a key
            key = comp.get("key")
            if not key:
                continue

            extracted: dict[str, Any] = {
                "key": key,
                "type": comp.get("type", "unknown"),
            }

            # Add label if present
            label = comp.get("label")
            if label:
                extracted["label"] = label

            # Add required if true
            validate = comp.get("validate", {})
            if isinstance(validate, dict) and validate.get("required"):
                extracted["required"] = True

            # Add data source info for selects
            data = comp.get("data", {})
            if isinstance(data, dict):
                if data.get("dataSrc"):
                    extracted["data_source"] = data["dataSrc"]
                if data.get("catalog"):
                    extracted["catalog"] = data["catalog"]

            # Add determinant IDs if present
            det_ids = comp.get("determinantIds")
            if det_ids:
                extracted["determinant_ids"] = det_ids

            # Add hidden/disabled if true
            if comp.get("hidden"):
                extracted["hidden"] = True
            if comp.get("disabled"):
                extracted["disabled"] = True

            # Handle nested components (panels, columns, etc.)
            nested = comp.get("components", [])
            if nested:
                nested_extracted = self._extract_components(nested)
                if nested_extracted:
                    extracted["components"] = nested_extracted

            # Handle columns
            columns = comp.get("columns", [])
            if columns:
                col_components = []
                for col in columns:
                    if isinstance(col, dict):
                        col_nested = col.get("components", [])
                        if col_nested:
                            col_components.extend(self._extract_components(col_nested))
                if col_components:
                    extracted["components"] = col_components

            # Handle tabs
            tabs = comp.get("tabs", [])
            if tabs:
                extracted["tabs"] = [
                    {"label": t.get("label", ""), "key": t.get("key", "")}
                    for t in tabs
                    if isinstance(t, dict)
                ]

            result.append(extracted)

        return result

    def _build_workflow_section(self, roles: list[dict[str, Any]]) -> dict[str, Any]:
        """Build the workflow section from roles.

        Args:
            roles: List of role objects.

        Returns:
            Workflow section dictionary.
        """
        result: dict[str, Any] = {"roles": []}

        for role in roles:
            name = role.get("name", "Unknown")

            # Store ID mapping
            if role.get("id"):
                self._metadata["role_ids"][name] = role["id"]

            transformed: dict[str, Any] = {
                "name": name,
                "short_name": role.get("shortName", ""),
            }

            # Add role type
            role_type = role.get("type", "")
            if role_type:
                transformed["type"] = role_type

            # Add start role flag
            if role.get("startRole"):
                transformed["start_role"] = True

            # Add visible to applicant
            if role.get("visibleToApplicant"):
                transformed["visible_to_applicant"] = True

            # Add statuses/destinations if present
            statuses = role.get("statuses", [])
            if statuses:
                transformed["statuses"] = [
                    {
                        "name": s.get("name", ""),
                        "type": s.get("type", "status"),
                    }
                    for s in statuses
                    if isinstance(s, dict)
                ]

            result["roles"].append(transformed)

        return result

    def _build_bots_section(self, bots: list[dict[str, Any]]) -> dict[str, Any]:
        """Build the bots section.

        Args:
            bots: List of bot objects.

        Returns:
            Categorized bots dictionary.
        """
        documents = []
        data_bots = []
        other = []

        for bot in bots:
            name = bot.get("name", "Unknown")

            # Store ID mapping
            if bot.get("id"):
                self._metadata["bot_ids"][name] = bot["id"]

            transformed: dict[str, Any] = {
                "name": name,
                "short_name": bot.get("shortName", ""),
            }

            # Add enabled status
            if not bot.get("enabled", True):
                transformed["enabled"] = False

            bot_type = bot.get("botType", "").lower()

            if "document" in bot_type or "upload" in bot_type:
                transformed["category"] = "document"
                documents.append(transformed)
            elif "data" in bot_type or "fetch" in bot_type:
                transformed["category"] = "data"
                data_bots.append(transformed)
            else:
                transformed["category"] = bot_type or "other"
                other.append(transformed)

        result: dict[str, Any] = {}

        if documents:
            result["documents"] = documents
        if data_bots:
            result["data"] = data_bots
        if other:
            result["other"] = other

        return result

    def _build_print_documents_section(
        self, print_docs: list[dict[str, Any]]
    ) -> list[dict[str, Any]]:
        """Build the print documents section.

        Args:
            print_docs: List of print document objects.

        Returns:
            Transformed print documents list.
        """
        return [
            {
                "name": doc.get("name", ""),
                "short_name": doc.get("shortName", ""),
                "active": doc.get("active", True),
            }
            for doc in print_docs
        ]

    def _generate_summary(self, yaml_data: dict[str, Any]) -> dict[str, Any]:
        """Generate summary statistics for the transformation.

        Args:
            yaml_data: The transformed YAML data.

        Returns:
            Summary dictionary.
        """
        summary: dict[str, Any] = {
            "service_name": yaml_data.get("service", {}).get("name", "Unknown"),
            "version": yaml_data.get("version", SCHEMA_VERSION),
        }

        # Count registrations
        registrations = yaml_data.get("registrations", [])
        summary["registration_count"] = len(registrations)

        # Count determinants
        determinants = yaml_data.get("determinants", {})
        det_count = 0
        for category in determinants.values():
            if isinstance(category, list):
                det_count += len(category)
        summary["determinant_count"] = det_count

        # Count form fields
        forms = yaml_data.get("forms", {})
        field_count = 0
        for form in forms.values():
            if isinstance(form, dict):
                components = form.get("components", [])
                field_count += self._count_components(components)
        summary["field_count"] = field_count

        # Count roles
        workflow = yaml_data.get("workflow", {})
        roles = workflow.get("roles", [])
        summary["role_count"] = len(roles)

        # Count bots
        bots = yaml_data.get("bots", {})
        bot_count = 0
        for category in bots.values():
            if isinstance(category, list):
                bot_count += len(category)
        summary["bot_count"] = bot_count

        return summary

    def _count_components(self, components: list[dict[str, Any]]) -> int:
        """Recursively count form components.

        Args:
            components: List of components.

        Returns:
            Total component count.
        """
        count = 0
        for comp in components:
            if isinstance(comp, dict):
                count += 1
                nested = comp.get("components", [])
                if nested:
                    count += self._count_components(nested)
        return count
