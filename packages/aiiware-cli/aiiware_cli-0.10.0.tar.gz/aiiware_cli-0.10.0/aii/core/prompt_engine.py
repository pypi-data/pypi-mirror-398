# Copyright 2025-present AiiWare.com. All Rights Reserved.
#
# This source code is proprietary and confidential to AiiWare.com.
# Unauthorized copying, modification, distribution, or use is strictly
# prohibited without prior written permission.

"""Prompt engine for loading, validating, and managing prompt templates.

This module provides the core prompt management functionality for v0.6.1 Prompt Library:
- Prompt discovery (list, search, filter)
- Prompt loading (user > builtin priority)
- Variable substitution (Handlebars-style)
- Prompt validation (schema, syntax, metadata)

Note: Internal class names use "Template" for backward compatibility,
but the public API uses "Prompt" terminology (e.g., "aii prompt use").
"""


from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Dict, Any, List, Optional
import re
import yaml


class PromptInputType(str, Enum):
    """Input type for prompts - how users provide input.

    NATURAL_LANGUAGE: User provides free-form text, system prompt guides behavior (95% of use cases)
    TEMPLATE: User provides --flag value pairs, template substitutes variables (5% structured output)
    """
    NATURAL_LANGUAGE = "natural_language"
    TEMPLATE = "template"


class TemplateCategory(str, Enum):
    """Prompt categories for organization."""
    BUSINESS = "business"
    CONTENT = "content"
    DEVELOPMENT = "development"
    SOCIAL = "social"
    MARKETING = "marketing"
    PRODUCTIVITY = "productivity"
    GENERAL = "general"


@dataclass(frozen=True)
class TemplateVariable:
    """Prompt variable specification (for variable substitution in prompts).

    Attributes:
        name: Variable name (kebab-case recommended)
        description: Help text explaining what this variable is
        required: Whether this variable must be provided
        type: Data type (string, number, boolean, array)
        default: Default value if not provided
        example: Example value for documentation
        validation: Optional regex pattern for validation
    """
    name: str
    description: str
    required: bool = False
    type: str = "string"
    default: Any = None
    example: Optional[str] = None
    validation: Optional[str] = None


@dataclass(frozen=True)
class TemplateExample:
    """Prompt usage example.

    Attributes:
        description: What this example demonstrates
        command: Full command to run
        output: Expected output (optional)
    """
    description: str
    command: str
    output: Optional[str] = None


@dataclass(frozen=True)
class Template:
    """Prompt template data structure.

    Supports two input modes:
    1. NATURAL_LANGUAGE (default): User provides free-form text, system_prompt guides behavior
    2. TEMPLATE: User provides --flag value pairs, template substitutes variables

    Attributes:
        name: Unique identifier (kebab-case)
        description: Short description (1 line)
        category: Template category
        input_type: How users provide input (natural_language or template)
        system_prompt: System prompt for natural_language mode (guides LLM behavior)
        template: The actual prompt text (with variables for template mode)
        variables: List of variable specifications (for template mode)
        author: Template author (optional)
        version: Template version (optional)
        tags: Searchable tags (optional)
        examples: Usage examples (optional)
        path: File path where template was loaded from
    """
    name: str
    description: str
    category: str
    template: str
    input_type: PromptInputType = PromptInputType.NATURAL_LANGUAGE
    system_prompt: Optional[str] = None
    variables: List[TemplateVariable] = field(default_factory=list)
    author: Optional[str] = None
    version: Optional[str] = None
    tags: List[str] = field(default_factory=list)
    examples: List[TemplateExample] = field(default_factory=list)
    path: Optional[Path] = None

    def validate(self) -> 'ValidationResult':
        """Validate prompt configuration based on input_type.

        Returns:
            ValidationResult with errors, warnings, suggestions
        """
        errors = []
        warnings = []
        suggestions = []

        # Required fields (common to both modes)
        if not self.name:
            errors.append("Missing required field: name")
        if not self.description:
            errors.append("Missing required field: description")

        # Mode-specific validation
        if self.input_type == PromptInputType.NATURAL_LANGUAGE:
            # Natural language mode requires system_prompt
            if not self.system_prompt:
                errors.append("Natural language mode requires 'system_prompt' field")
            if self.variables:
                warnings.append("Natural language mode doesn't use 'variables' field (will be ignored)")

        elif self.input_type == PromptInputType.TEMPLATE:
            # Template mode requires template with variables
            if not self.template:
                errors.append("Template mode requires 'template' field")
            if not self.variables:
                warnings.append("Template mode should define 'variables' for user input")

        # Both modes can optionally have template for context/structure
        # (natural_language can use template for output formatting)

        # Optional metadata warnings
        if not self.author:
            warnings.append("No 'author' field provided (recommended)")
        if not self.tags:
            warnings.append("No 'tags' field provided (helps with discovery)")
        if not self.version:
            warnings.append("No 'version' field provided (recommended for tracking)")

        # Suggestions
        if not self.examples:
            suggestions.append("Add example usage in 'examples' field")
        if not self.category or self.category == "general":
            suggestions.append("Consider specifying a category (business, content, development, etc.)")

        is_valid = len(errors) == 0

        return ValidationResult(
            is_valid=is_valid,
            errors=errors,
            warnings=warnings,
            suggestions=suggestions,
        )


@dataclass
class ValidationError:
    """Detailed validation error with context and suggestions (v0.6.2).

    Attributes:
        message: Error message
        line_number: Line number where error occurred (optional)
        column_number: Column number where error occurred (optional)
        error_type: Type of error (syntax_error, missing_field, invalid_value, etc.)
        field_name: Field that has the error (optional)
        context_lines: Lines of context around the error (optional)
        fix_suggestion: Actionable suggestion to fix the error (optional)
        example: Example of correct syntax (optional)
    """
    message: str
    error_type: str = "unknown"
    line_number: Optional[int] = None
    column_number: Optional[int] = None
    field_name: Optional[str] = None
    context_lines: List[str] = field(default_factory=list)
    fix_suggestion: Optional[str] = None
    example: Optional[str] = None

    def format(self) -> str:
        """Format error message with context for display."""
        output = []

        # Error header
        if self.line_number:
            output.append(f"Line {self.line_number}: {self.message}")
        else:
            output.append(self.message)

        # Context
        if self.context_lines:
            output.append("")
            for i, line in enumerate(self.context_lines):
                # Calculate actual line number (context is ±2 lines)
                if self.line_number:
                    line_num = self.line_number - 2 + i
                else:
                    line_num = i + 1
                marker = "  ← " if i == 2 else "    "  # Mark error line (middle of 5 lines)
                output.append(f"  {line_num:3d}: {line}{marker if i == 2 else ''}")

        # Fix suggestion
        if self.fix_suggestion:
            output.append("")
            output.append(f"  ✓ Fix: {self.fix_suggestion}")

        # Example
        if self.example:
            output.append("")
            output.append("  ✓ Example:")
            for line in self.example.split("\n"):
                output.append(f"    {line}")

        return "\n".join(output)


@dataclass
class ValidationResult:
    """Prompt validation result (enhanced in v0.6.2).

    Attributes:
        is_valid: Whether template is valid
        errors: List of detailed validation errors (v0.6.2: now ValidationError objects)
        warnings: List of warnings (non-blocking suggestions)
        suggestions: List of improvement suggestions
    """
    is_valid: bool
    errors: List[ValidationError] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    suggestions: List[str] = field(default_factory=list)

    def format_errors(self) -> str:
        """Format all errors for display (v0.6.2)."""
        if self.is_valid:
            return "✅ Validation passed"

        output = ["❌ Validation failed:\n"]

        for i, error in enumerate(self.errors, 1):
            output.append(error.format())
            if i < len(self.errors):
                output.append("")  # Blank line between errors

        output.append("")
        output.append("─" * 60)
        output.append(f"Found {len(self.errors)} error(s). Fix these issues and run validate again.")

        return "\n".join(output)


class TemplateNotFoundError(Exception):
    """Raised when a prompt template cannot be found."""
    pass


class MissingVariableError(Exception):
    """Raised when required variables are not provided."""

    def __init__(self, missing_vars: List[str], template_name: str):
        self.missing_vars = missing_vars
        self.template_name = template_name
        super().__init__(f"Missing required variables: {', '.join(missing_vars)}")


class TemplateEngine:
    """Prompt engine for loading, validating, and managing prompt templates.

    This engine handles:
    - Prompt discovery (scanning builtin and user directories)
    - Prompt loading (with user > builtin priority)
    - Prompt validation (schema, syntax, metadata)
    - Variable substitution (Handlebars-style)

    Prompt resolution order:
    1. User prompts (~/.aii/prompts/) - Highest priority
    2. Legacy user templates (~/.aii/templates/) - Compatibility
    3. Built-in prompts (package data/prompts/) - Fallback

    Note: Class name is "TemplateEngine" for backward compatibility,
    but it manages "prompts" in the product terminology.
    """

    def __init__(self, builtin_path: Optional[Path] = None, user_path: Optional[Path] = None):
        """Initialize prompt engine.

        Args:
            builtin_path: Path to built-in prompts (defaults to package data/prompts/)
            user_path: Path to user prompts (defaults to ~/.aii/prompts/)
        """
        # Built-in prompts path
        if builtin_path:
            self.builtin_path = builtin_path
        else:
            # Default: aii/data/prompts/ in package (or data/templates/ for compatibility)
            prompts_path = Path(__file__).parent.parent / "data" / "prompts"
            templates_path = Path(__file__).parent.parent / "data" / "templates"
            self.builtin_path = prompts_path if prompts_path.exists() else templates_path

        # User prompts path
        if user_path:
            self.user_path = user_path
        else:
            # Default: ~/.aii/prompts/ (or ~/.aii/templates/ for backward compatibility)
            self.user_path = Path.home() / ".aii" / "prompts"
            self.legacy_user_path = Path.home() / ".aii" / "templates"

        self.categories = [
            TemplateCategory.BUSINESS,
            TemplateCategory.CONTENT,
            TemplateCategory.DEVELOPMENT,
            TemplateCategory.SOCIAL,
            TemplateCategory.MARKETING,
            TemplateCategory.PRODUCTIVITY,
        ]

    def list_templates(
        self,
        category: Optional[str] = None,
        tag: Optional[str] = None,
        user_only: bool = False,
        builtin_only: bool = False,
    ) -> List[Template]:
        """List all available templates with optional filtering.

        Args:
            category: Filter by category (business, content, dev, etc.)
            tag: Filter by tag
            user_only: Only show user templates
            builtin_only: Only show built-in templates

        Returns:
            List of Template objects (metadata only, not full template text)
        """
        templates = []
        template_names = set()

        # Discover built-in templates
        if not user_only:
            builtin_templates = self._discover_builtin_templates()
            for template in builtin_templates:
                templates.append(template)
                template_names.add(template.name)

        # Discover user templates (override built-in with same name)
        if not builtin_only:
            user_templates = self._discover_user_templates()
            for template in user_templates:
                # Remove built-in if exists (user override)
                if template.name in template_names:
                    templates = [t for t in templates if t.name != template.name]

                templates.append(template)
                template_names.add(template.name)

        # Apply filters
        if category:
            templates = [t for t in templates if t.category == category]

        if tag:
            templates = [t for t in templates if tag in t.tags]

        # Sort by category, then name
        templates.sort(key=lambda t: (t.category, t.name))

        return templates

    def load_template(self, name: str) -> Template:
        """Load prompt template by name (user > builtin priority).

        Args:
            name: Prompt name (without .yaml extension)

        Returns:
            Template object

        Raises:
            TemplateNotFoundError: If prompt doesn't exist
        """
        # Resolution order:
        # 1. User prompts (flat) - ~/.aii/prompts/{name}.yaml
        user_flat = self.user_path / f"{name}.yaml"
        if user_flat.exists():
            return self._parse_template(user_flat)

        # 2. User prompts (by category) - ~/.aii/prompts/{category}/{name}.yaml
        for category in self.categories:
            user_cat = self.user_path / category.value / f"{name}.yaml"
            if user_cat.exists():
                return self._parse_template(user_cat)

        # 3. Legacy user templates (flat) - ~/.aii/templates/{name}.yaml
        if hasattr(self, 'legacy_user_path'):
            legacy_flat = self.legacy_user_path / f"{name}.yaml"
            if legacy_flat.exists():
                return self._parse_template(legacy_flat)

        # 4. Legacy user templates (by category) - ~/.aii/templates/{category}/{name}.yaml
        if hasattr(self, 'legacy_user_path'):
            for category in self.categories:
                legacy_cat = self.legacy_user_path / category.value / f"{name}.yaml"
                if legacy_cat.exists():
                    return self._parse_template(legacy_cat)

        # 5. Built-in prompts (flat, legacy) - data/prompts/{name}.yaml or data/templates/{name}.yaml
        builtin_flat = self.builtin_path / f"{name}.yaml"
        if builtin_flat.exists():
            return self._parse_template(builtin_flat)

        # 6. Built-in prompts (by category) - data/prompts/{category}/{name}.yaml
        for category in self.categories:
            builtin_cat = self.builtin_path / category.value / f"{name}.yaml"
            if builtin_cat.exists():
                return self._parse_template(builtin_cat)

        # Not found
        raise TemplateNotFoundError(f"Prompt not found: {name}")

    def validate_template(self, template: Template) -> ValidationResult:
        """Validate template syntax and metadata.

        Args:
            template: Template to validate

        Returns:
            ValidationResult with errors, warnings, suggestions
        """
        errors = []
        warnings = []
        suggestions = []

        # Required fields
        if not template.name:
            errors.append("Missing required field: name")
        if not template.description:
            errors.append("Missing required field: description")
        if not template.template:
            errors.append("Missing required field: template")

        # Validate Handlebars syntax
        handlebars_errors = self._validate_handlebars(template.template)
        errors.extend(handlebars_errors)

        # Validate variable references
        var_errors = self._validate_variable_references(template)
        errors.extend(var_errors)

        # Warnings for missing optional metadata
        if not template.author:
            warnings.append("No 'author' field provided (recommended)")
        if not template.tags:
            warnings.append("No 'tags' field provided (helps with discovery)")
        if not template.version:
            warnings.append("No 'version' field provided (recommended for tracking)")

        # Suggestions
        if not template.examples:
            suggestions.append("Add example usage in 'examples' field")
        if not template.category or template.category == "general":
            suggestions.append("Consider specifying a category (business, content, development, etc.)")

        is_valid = len(errors) == 0

        return ValidationResult(
            is_valid=is_valid,
            errors=errors,
            warnings=warnings,
            suggestions=suggestions,
        )

    def validate_prompt_file(self, file_path: Path) -> ValidationResult:
        """Validate prompt YAML file with detailed error reporting (v0.6.2).

        This method provides enhanced validation with:
        - Line numbers for errors
        - Context lines around errors
        - Actionable fix suggestions
        - Examples of correct syntax

        Args:
            file_path: Path to prompt YAML file

        Returns:
            ValidationResult with detailed ValidationError objects
        """
        errors = []

        # Step 1: Check file exists
        if not file_path.exists():
            errors.append(ValidationError(
                message=f"Prompt file not found: {file_path}",
                error_type="file_not_found",
                fix_suggestion=f"Check the file path. Expected location: ~/.aii/prompts/<category>/<name>.yaml"
            ))
            return ValidationResult(is_valid=False, errors=errors)

        # Step 2: Load and parse YAML
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
                data = yaml.safe_load(content)
        except yaml.YAMLError as e:
            # Extract error details
            line_num = getattr(e, 'problem_mark', None)
            line_number = line_num.line + 1 if line_num else None

            # Get context lines
            lines = content.split("\n")
            context = self._extract_context(lines, line_number, radius=2)

            # Determine error type and suggestion
            error_msg = str(e)
            error_type = self._detect_yaml_error_type(error_msg)
            suggestion = self._generate_yaml_fix_suggestion(error_msg)

            errors.append(ValidationError(
                message=error_type,
                error_type="syntax_error",
                line_number=line_number,
                context_lines=context,
                fix_suggestion=suggestion
            ))
            return ValidationResult(is_valid=False, errors=errors)
        except Exception as e:
            errors.append(ValidationError(
                message=f"Failed to read file: {e}",
                error_type="file_error"
            ))
            return ValidationResult(is_valid=False, errors=errors)

        # Step 3: Validate schema
        errors.extend(self._validate_required_fields(data))
        errors.extend(self._validate_field_types(data))
        errors.extend(self._validate_input_type_consistency(data))

        return ValidationResult(
            is_valid=len(errors) == 0,
            errors=errors
        )

    def _extract_context(self, lines: List[str], line_number: Optional[int], radius: int = 2) -> List[str]:
        """Extract context lines around error line.

        Args:
            lines: All lines from file
            line_number: Line number where error occurred (1-indexed)
            radius: Number of lines before/after to include

        Returns:
            List of context lines (up to 2*radius+1 lines)
        """
        if not line_number or line_number <= 0:
            return []

        start = max(0, line_number - radius - 1)
        end = min(len(lines), line_number + radius)

        return lines[start:end]

    def _detect_yaml_error_type(self, error_msg: str) -> str:
        """Detect specific YAML error type from error message.

        Args:
            error_msg: YAML error message

        Returns:
            Human-readable error type
        """
        error_msg_lower = error_msg.lower()

        if "indentation" in error_msg_lower:
            return "Indentation error"
        elif "could not find expected" in error_msg_lower:
            return "YAML structure error"
        elif "found character" in error_msg_lower or "unexpected" in error_msg_lower:
            return "Invalid character"
        elif "mapping" in error_msg_lower:
            return "Invalid key-value structure"
        else:
            return "YAML syntax error"

    def _generate_yaml_fix_suggestion(self, error_msg: str) -> str:
        """Generate actionable fix suggestion based on error.

        Args:
            error_msg: YAML error message

        Returns:
            Actionable fix suggestion
        """
        error_msg_lower = error_msg.lower()

        suggestions = {
            "indentation": "Use 2 spaces for indentation (not tabs, not 4 spaces)",
            "structure": "Check YAML structure. Keys should be followed by colon and space",
            "character": "Remove or escape special characters",
            "mapping": "Ensure proper key: value format",
        }

        for keyword, suggestion in suggestions.items():
            if keyword in error_msg_lower:
                return suggestion

        return "Check YAML syntax. See: https://yaml.org/spec/"

    def _validate_required_fields(self, data: Dict[str, Any]) -> List[ValidationError]:
        """Validate required fields are present.

        Args:
            data: Parsed YAML data

        Returns:
            List of ValidationError objects for missing fields
        """
        errors = []
        required = ["name", "description", "category", "input_type"]

        for field in required:
            if field not in data:
                errors.append(ValidationError(
                    message=f"Missing required field: '{field}'",
                    error_type="missing_field",
                    field_name=field,
                    fix_suggestion=f"Add '{field}' to your YAML file",
                    example=self._get_field_example(field)
                ))

        return errors

    def _validate_field_types(self, data: Dict[str, Any]) -> List[ValidationError]:
        """Validate field types and enums.

        Args:
            data: Parsed YAML data

        Returns:
            List of ValidationError objects for invalid types
        """
        errors = []

        # Category validation (v0.6.2: Allow custom categories)
        if "category" in data:
            # Accept any kebab-case category (predefined or custom)
            category = data["category"]

            # Validate format: kebab-case (lowercase, hyphens only)
            if not re.match(r'^[a-z0-9]+(-[a-z0-9]+)*$', category):
                errors.append(ValidationError(
                    message=f"Invalid category format: '{category}'",
                    error_type="invalid_value",
                    field_name="category",
                    fix_suggestion="Use kebab-case format (lowercase, hyphens only)",
                    example="category: data-analysis"
                ))

            # Warn if not a standard category (informational, not an error)
            standard_categories = ["business", "content", "development", "social", "marketing", "productivity"]
            if category not in standard_categories:
                # Custom category - valid, but log for awareness
                pass  # Accept custom categories without warning

        # Input type enum validation
        if "input_type" in data:
            valid_types = ["natural_language", "template"]
            if data["input_type"] not in valid_types:
                errors.append(ValidationError(
                    message=f"Invalid input_type: '{data['input_type']}'",
                    error_type="invalid_value",
                    field_name="input_type",
                    fix_suggestion=f"Use one of: {', '.join(valid_types)}",
                    example="input_type: natural_language"
                ))

        return errors

    def _validate_input_type_consistency(self, data: Dict[str, Any]) -> List[ValidationError]:
        """Validate input_type consistency with required fields.

        Args:
            data: Parsed YAML data

        Returns:
            List of ValidationError objects for consistency issues
        """
        errors = []
        input_type = data.get("input_type")

        if input_type == "natural_language":
            if "system_prompt" not in data:
                errors.append(ValidationError(
                    message="Field 'system_prompt' is required for input_type: natural_language",
                    error_type="missing_field",
                    field_name="system_prompt",
                    fix_suggestion="Add system_prompt field",
                    example="system_prompt: |\n  Your behavior instructions here"
                ))

        elif input_type == "template":
            if "template" not in data:
                errors.append(ValidationError(
                    message="Field 'template' is required for input_type: template",
                    error_type="missing_field",
                    field_name="template",
                    fix_suggestion="Add template field",
                    example="template: |\n  Your template with {{variables}} here"
                ))

        return errors

    def _get_field_example(self, field: str) -> str:
        """Get example value for a field.

        Args:
            field: Field name

        Returns:
            Example YAML for that field
        """
        examples = {
            "name": "name: my-prompt",
            "description": "description: Brief description of what this prompt does",
            "category": "category: development",
            "input_type": "input_type: natural_language",
            "system_prompt": "system_prompt: |\n  You are a helpful assistant.",
            "template": "template: |\n  Your template with {{variable}} here",
        }
        return examples.get(field, f"{field}: value")

    def validate_variables(
        self,
        template: Template,
        variables: Dict[str, str]
    ) -> List[str]:
        """Check for missing required variables.

        Args:
            template: Template object
            variables: User-provided variables

        Returns:
            List of missing required variable names
        """
        missing = []
        for var in template.variables:
            if var.required and var.name not in variables:
                missing.append(var.name)
        return missing

    def substitute_variables(
        self,
        template_str: str,
        variables: Dict[str, str]
    ) -> str:
        """Substitute variables in template using Handlebars syntax.

        Supports:
        - Basic substitution: {{variable}}
        - Conditionals: {{#if variable}}...{{/if}}
        - Conditionals: {{#unless variable}}...{{/unless}}

        Args:
            template_str: Template text with variables
            variables: Variable name -> value mapping

        Returns:
            Template with variables substituted
        """
        result = template_str

        # 1. Simple variable substitution {{variable}}
        for var_name, var_value in variables.items():
            result = result.replace(f"{{{{{var_name}}}}}", str(var_value))

        # 2. Process conditionals
        result = self._process_conditionals(result, variables)

        return result

    def _discover_builtin_templates(self) -> List[Template]:
        """Discover all built-in templates.

        Scans:
        - data/templates/*.yaml (flat, legacy)
        - data/templates/{category}/*.yaml (organized)

        Returns:
            List of Template objects
        """
        templates = []

        if not self.builtin_path.exists():
            return templates

        # Flat templates (legacy v0.4.7)
        for yaml_file in self.builtin_path.glob("*.yaml"):
            try:
                template = self._parse_template(yaml_file)
                templates.append(template)
            except Exception:
                # Skip invalid templates
                pass

        # Category-organized templates (v0.6.1+)
        for category in self.categories:
            category_path = self.builtin_path / category.value
            if category_path.exists():
                for yaml_file in category_path.glob("*.yaml"):
                    try:
                        template = self._parse_template(yaml_file)
                        templates.append(template)
                    except Exception:
                        # Skip invalid templates
                        pass

        return templates

    def _discover_user_templates(self) -> List[Template]:
        """Discover all user prompts.

        Scans:
        - ~/.aii/prompts/*.yaml (flat)
        - ~/.aii/prompts/{category}/*.yaml (organized)
        - ~/.aii/prompts/{custom}/*.yaml (custom folders)
        - ~/.aii/templates/*.yaml (legacy path for backward compatibility)

        Returns:
            List of Template objects
        """
        templates = []
        seen_names = set()

        # Check new location first (~/.aii/prompts/)
        if self.user_path.exists():
            for yaml_file in self.user_path.rglob("*.yaml"):
                try:
                    template = self._parse_template(yaml_file)
                    templates.append(template)
                    seen_names.add(template.name)
                except Exception:
                    # Skip invalid templates
                    pass

        # Check legacy location (~/.aii/templates/) for backward compatibility
        if hasattr(self, 'legacy_user_path') and self.legacy_user_path.exists():
            for yaml_file in self.legacy_user_path.rglob("*.yaml"):
                try:
                    template = self._parse_template(yaml_file)
                    # Only add if not already found in new location
                    if template.name not in seen_names:
                        templates.append(template)
                except Exception:
                    # Skip invalid templates
                    pass

        return templates

    def _parse_template(self, path: Path) -> Template:
        """Parse template YAML file into Template object.

        Args:
            path: Path to template YAML file

        Returns:
            Template object

        Raises:
            yaml.YAMLError: If YAML is invalid
        """
        with open(path, 'r', encoding='utf-8') as f:
            data = yaml.safe_load(f)

        # Parse input_type (default to natural_language)
        input_type_str = data.get("input_type", "natural_language")
        try:
            input_type = PromptInputType(input_type_str)
        except ValueError:
            # Fallback to natural_language for invalid values
            input_type = PromptInputType.NATURAL_LANGUAGE

        # Parse variables
        variables = []
        for var_data in data.get("variables", []):
            variables.append(TemplateVariable(
                name=var_data["name"],
                description=var_data.get("description", ""),
                required=var_data.get("required", False),
                type=var_data.get("type", "string"),
                default=var_data.get("default"),
                example=var_data.get("example"),
                validation=var_data.get("validation"),
            ))

        # Parse examples
        examples = []
        for ex_data in data.get("examples", []):
            examples.append(TemplateExample(
                description=ex_data.get("description", ""),
                command=ex_data.get("command", ""),
                output=ex_data.get("output"),
            ))

        return Template(
            name=data["name"],
            description=data.get("description", ""),
            category=data.get("category", "general"),
            template=data.get("template", ""),  # Optional for natural_language mode
            input_type=input_type,
            system_prompt=data.get("system_prompt"),  # For natural_language mode
            variables=variables,
            author=data.get("author"),
            version=data.get("version"),
            tags=data.get("tags", []),
            examples=examples,
            path=path,
        )

    def _process_conditionals(
        self,
        template_str: str,
        variables: Dict[str, str]
    ) -> str:
        """Process Handlebars conditionals ({{#if}}, {{#unless}}).

        Args:
            template_str: Template with conditionals
            variables: Variable name -> value mapping

        Returns:
            Template with conditionals processed
        """
        result = template_str

        # Process {{#if variable}}content{{/if}}
        def replace_if(match):
            var_name = match.group(1).strip()
            content = match.group(2)
            # Include content if variable exists and is not empty
            return content if variables.get(var_name) else ""

        pattern_if = r"\{\{#if\s+(\w+)\}\}(.*?)\{\{/if\}\}"
        result = re.sub(pattern_if, replace_if, result, flags=re.DOTALL)

        # Process {{#unless variable}}content{{/unless}}
        def replace_unless(match):
            var_name = match.group(1).strip()
            content = match.group(2)
            # Include content if variable does NOT exist or is empty
            return content if not variables.get(var_name) else ""

        pattern_unless = r"\{\{#unless\s+(\w+)\}\}(.*?)\{\{/unless\}\}"
        result = re.sub(pattern_unless, replace_unless, result, flags=re.DOTALL)

        return result

    def _validate_handlebars(self, template_str: str) -> List[str]:
        """Validate Handlebars syntax in template.

        Args:
            template_str: Template text to validate

        Returns:
            List of validation errors
        """
        errors = []

        # Check for unclosed {{#if}} tags
        if_pattern = r"\{\{#if\s+\w+\}\}"
        endif_pattern = r"\{\{/if\}\}"
        if_count = len(re.findall(if_pattern, template_str))
        endif_count = len(re.findall(endif_pattern, template_str))
        if if_count != endif_count:
            errors.append(f"Mismatched {{{{#if}}}} tags: {if_count} opening, {endif_count} closing")

        # Check for unclosed {{#unless}} tags
        unless_pattern = r"\{\{#unless\s+\w+\}\}"
        endunless_pattern = r"\{\{/unless\}\}"
        unless_count = len(re.findall(unless_pattern, template_str))
        endunless_count = len(re.findall(endunless_pattern, template_str))
        if unless_count != endunless_count:
            errors.append(f"Mismatched {{{{#unless}}}} tags: {unless_count} opening, {endunless_count} closing")

        # Check for malformed variable syntax (e.g., {{variable with spaces}})
        malformed_pattern = r"\{\{([^#/][^}]*\s[^}]*)\}\}"
        malformed_matches = re.findall(malformed_pattern, template_str)
        for match in malformed_matches:
            if not match.strip().startswith("if") and not match.strip().startswith("unless"):
                errors.append(f"Malformed variable syntax: {{{{{match}}}}}")

        return errors

    def _validate_variable_references(self, template: Template) -> List[str]:
        """Validate that all variables in template are defined.

        Args:
            template: Template object

        Returns:
            List of validation errors
        """
        errors = []

        # Extract all variable references from template
        var_pattern = r"\{\{(\w+)\}\}"
        referenced_vars = set(re.findall(var_pattern, template.template))

        # Extract variables from conditionals
        if_pattern = r"\{\{#if\s+(\w+)\}\}"
        unless_pattern = r"\{\{#unless\s+(\w+)\}\}"
        conditional_vars = set(re.findall(if_pattern, template.template))
        conditional_vars.update(re.findall(unless_pattern, template.template))

        all_referenced = referenced_vars.union(conditional_vars)

        # Check if all referenced variables are defined
        defined_vars = {v.name for v in template.variables}
        undefined_vars = all_referenced - defined_vars

        if undefined_vars:
            errors.append(f"Undefined variables referenced in template: {', '.join(sorted(undefined_vars))}")

        return errors
