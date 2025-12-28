# Copyright 2025-present AiiWare.com. All Rights Reserved.
#
# This source code is proprietary and confidential to AiiWare.com.
# Unauthorized copying, modification, distribution, or use is strictly
# prohibited without prior written permission.

"""Template-based content generation functions."""


from pathlib import Path
from typing import Dict, Any, List
import yaml
import re
from aii.core.models import (
    ExecutionContext,
    ExecutionResult,
    FunctionCategory,
    FunctionPlugin,
    FunctionSafety,
    OutputMode,
    ParameterSchema,
    ValidationResult,
)


class TemplateFunction(FunctionPlugin):
    """Generate content from pre-built templates with variable substitution."""

    @property
    def name(self) -> str:
        return "template"

    @property
    def description(self) -> str:
        return "Generate content from pre-built templates with variable substitution"

    @property
    def category(self) -> FunctionCategory:
        return FunctionCategory.CONTENT

    @property
    def parameters(self) -> dict[str, ParameterSchema]:
        return {
            "template_name": ParameterSchema(
                name="template_name",
                type="string",
                required=True,
                description="Name of template to use (product-announcement, blog-intro, email-professional, tweet-launch, pr-description, meeting-notes, release-notes, social-post)",
            ),
            "variables": ParameterSchema(
                name="variables",
                type="object",
                required=False,
                description="Variables to fill in template (e.g., {product: 'AII', version: 'v0.5.0'})",
            ),
        }

    @property
    def requires_confirmation(self) -> bool:
        return False

    @property
    def safety_level(self) -> FunctionSafety:
        return FunctionSafety.SAFE

    @property
    def default_output_mode(self) -> OutputMode:
        """Default to CLEAN mode - users want just the generated content."""
        return OutputMode.CLEAN

    @property
    def supports_output_modes(self) -> list[OutputMode]:
        """Supports CLEAN, STANDARD, and THINKING modes."""
        return [OutputMode.CLEAN, OutputMode.STANDARD, OutputMode.THINKING]

    async def validate_prerequisites(
        self, context: ExecutionContext
    ) -> ValidationResult:
        """Check if LLM provider is available"""
        if not context.llm_provider:
            return ValidationResult(
                valid=False, errors=["LLM provider required for template generation"]
            )
        return ValidationResult(valid=True)

    async def execute(
        self,
        parameters: Dict[str, Any],
        context: ExecutionContext
    ) -> ExecutionResult:
        """Execute template generation.

        Args:
            parameters: Template name and variables
            context: Execution context with LLM provider

        Returns:
            ExecutionResult with generated content
        """
        template_name = parameters.get("template_name", "")
        variables = parameters.get("variables", {})

        try:
            # Load template
            template = self._load_template(template_name)

            # Validate required variables
            missing_vars = self._validate_variables(template, variables)
            if missing_vars:
                return ExecutionResult(
                    success=False,
                    message=f"Missing required variables: {', '.join(missing_vars)}",
                    data={
                        "template_name": template_name,
                        "missing_variables": missing_vars,
                        "clean_output": f"Error: Missing required variables: {', '.join(missing_vars)}"
                    }
                )

            # Generate content using template
            content = await self._generate_from_template(
                template,
                variables,
                context.llm_provider
            )

            return ExecutionResult(
                success=True,
                message=f"Generated content from template: {template_name}",
                data={
                    "content": content,
                    "template_used": template_name,
                    "template_category": template.get("category", "general"),
                    "variables": variables,
                    "clean_output": content  # For CLEAN mode
                }
            )

        except FileNotFoundError:
            return ExecutionResult(
                success=False,
                message=f"Template not found: {template_name}",
                data={
                    "template_name": template_name,
                    "clean_output": f"Error: Template '{template_name}' not found"
                }
            )
        except Exception as e:
            return ExecutionResult(
                success=False,
                message=f"Error generating from template: {str(e)}",
                data={
                    "template_name": template_name,
                    "error": str(e),
                    "clean_output": f"Error: {str(e)}"
                }
            )

    def _load_template(self, template_name: str) -> Dict[str, Any]:
        """Load template from built-in or user templates.

        User templates in ~/.aii/templates/ override built-in templates.

        Args:
            template_name: Name of the template

        Returns:
            Template dictionary

        Raises:
            FileNotFoundError: If template doesn't exist
        """
        # Check user templates first (allows overrides)
        user_template_path = Path.home() / ".aii" / "templates" / f"{template_name}.yaml"
        if user_template_path.exists():
            with open(user_template_path, 'r', encoding='utf-8') as f:
                return yaml.safe_load(f)

        # Fall back to built-in templates
        builtin_template_path = Path(__file__).parent.parent.parent / "data" / "templates" / f"{template_name}.yaml"
        if builtin_template_path.exists():
            with open(builtin_template_path, 'r', encoding='utf-8') as f:
                return yaml.safe_load(f)

        raise FileNotFoundError(f"Template not found: {template_name}")

    def _validate_variables(
        self,
        template: Dict[str, Any],
        variables: Dict[str, str]
    ) -> List[str]:
        """Check for missing required variables.

        Args:
            template: Template dictionary
            variables: User-provided variables

        Returns:
            List of missing required variable names
        """
        missing = []
        for var_spec in template.get("variables", []):
            if var_spec.get("required", False):
                if var_spec["name"] not in variables:
                    missing.append(var_spec["name"])
        return missing

    async def _generate_from_template(
        self,
        template: Dict[str, Any],
        variables: Dict[str, str],
        llm_provider
    ) -> str:
        """Generate content using template and LLM.

        Args:
            template: Template dictionary
            variables: User-provided variables
            llm_provider: LLM provider for content generation

        Returns:
            Generated content
        """
        # Get template prompt
        prompt = template["template"]

        # Simple variable substitution
        for var_name, var_value in variables.items():
            prompt = prompt.replace(f"{{{{{var_name}}}}}", str(var_value))

        # Handle conditionals (basic Handlebars-style)
        prompt = self._process_conditionals(prompt, variables)

        # Generate with LLM (use complete method for PydanticAI providers)
        if hasattr(llm_provider, 'complete'):
            result = await llm_provider.complete(prompt)
        elif hasattr(llm_provider, 'generate'):
            result = await llm_provider.generate(prompt)
        else:
            raise AttributeError(f"LLM provider has no compatible generation method")

        return result.strip() if isinstance(result, str) else str(result).strip()

    def _process_conditionals(
        self,
        prompt: str,
        variables: Dict[str, str]
    ) -> str:
        """Process {{#if var}}...{{/if}} conditionals.

        Args:
            prompt: Template prompt with conditionals
            variables: User-provided variables

        Returns:
            Prompt with conditionals processed
        """
        def replace_conditional(match):
            var_name = match.group(1).strip()
            content = match.group(2)
            # Include content if variable exists and is not empty
            return content if variables.get(var_name) else ""

        # Pattern: {{#if variable}}content{{/if}}
        pattern = r"\{\{#if\s+(\w+)\}\}(.*?)\{\{/if\}\}"
        return re.sub(pattern, replace_conditional, prompt, flags=re.DOTALL)


class TemplateListFunction(FunctionPlugin):
    """List all available content templates."""

    @property
    def name(self) -> str:
        return "template_list"

    @property
    def description(self) -> str:
        return "List all available content templates with their descriptions and required variables"

    @property
    def category(self) -> FunctionCategory:
        return FunctionCategory.CONTENT

    @property
    def parameters(self) -> dict[str, ParameterSchema]:
        return {}

    @property
    def requires_confirmation(self) -> bool:
        return False

    @property
    def safety_level(self) -> FunctionSafety:
        return FunctionSafety.SAFE

    @property
    def default_output_mode(self) -> OutputMode:
        """Default to CLEAN mode - users want formatted template list."""
        return OutputMode.CLEAN

    @property
    def supports_output_modes(self) -> list[OutputMode]:
        """Supports CLEAN and STANDARD modes."""
        return [OutputMode.CLEAN, OutputMode.STANDARD]

    async def validate_prerequisites(
        self, context: ExecutionContext
    ) -> ValidationResult:
        """No prerequisites needed for listing templates"""
        return ValidationResult(valid=True)

    async def execute(
        self,
        parameters: Dict[str, Any],
        context: ExecutionContext
    ) -> ExecutionResult:
        """List all available templates.

        Args:
            parameters: No parameters required
            context: Execution context

        Returns:
            ExecutionResult with template list
        """
        try:
            templates = self._discover_templates()

            template_list = []
            for template in templates:
                template_list.append({
                    "name": template["name"],
                    "description": template["description"],
                    "category": template.get("category", "general"),
                    "variables": [v["name"] for v in template.get("variables", [])]
                })

            # Sort by category, then name
            template_list.sort(key=lambda t: (t["category"], t["name"]))

            formatted_output = self._format_template_list(template_list)

            return ExecutionResult(
                success=True,
                message=f"Found {len(template_list)} templates",
                data={
                    "templates": template_list,
                    "total_count": len(template_list),
                    "clean_output": formatted_output
                }
            )

        except Exception as e:
            return ExecutionResult(
                success=False,
                message=f"Error listing templates: {str(e)}",
                data={
                    "error": str(e),
                    "clean_output": f"Error: {str(e)}"
                }
            )

    def _discover_templates(self) -> List[Dict[str, Any]]:
        """Discover all built-in and user templates.

        User templates override built-in templates with the same name.

        Returns:
            List of template dictionaries
        """
        templates = []
        template_names = set()

        # Built-in templates
        builtin_dir = Path(__file__).parent.parent.parent / "data" / "templates"
        if builtin_dir.exists():
            for template_file in builtin_dir.glob("*.yaml"):
                with open(template_file, 'r', encoding='utf-8') as f:
                    template_data = yaml.safe_load(f)
                    templates.append(template_data)
                    template_names.add(template_data["name"])

        # User templates (override built-in if same name)
        user_dir = Path.home() / ".aii" / "templates"
        if user_dir.exists():
            for template_file in user_dir.glob("*.yaml"):
                with open(template_file, 'r', encoding='utf-8') as f:
                    template_data = yaml.safe_load(f)

                    # Replace built-in if exists
                    if template_data["name"] in template_names:
                        templates = [t for t in templates if t["name"] != template_data["name"]]

                    templates.append(template_data)
                    template_names.add(template_data["name"])

        return templates

    def _format_template_list(self, templates: List[Dict[str, Any]]) -> str:
        """Format template list for display.

        Args:
            templates: List of template dictionaries

        Returns:
            Formatted string for display
        """
        lines = ["Available templates:\n"]

        category_icons = {
            "marketing": "📧",
            "content": "📝",
            "development": "📋",
            "business": "📅",
            "social": "🐦",
            "general": "📄"
        }

        current_category = None
        for template in templates:
            category = template["category"]

            # Category header with blank line separator
            if category != current_category:
                if current_category is not None:
                    lines.append("")  # Blank line between categories
                current_category = category

            icon = category_icons.get(category, "📄")
            name = template["name"]
            desc = template["description"]
            vars_list = template["variables"]
            vars_str = ", ".join(vars_list) if vars_list else "none"

            lines.append(f"{icon} {name}")
            lines.append(f"   {desc}")
            lines.append(f"   Variables: {vars_str}")

        return "\n".join(lines)
