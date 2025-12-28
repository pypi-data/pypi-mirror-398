# Copyright 2025-present AiiWare.com. All Rights Reserved.
#
# This source code is proprietary and confidential to AiiWare.com.
# Unauthorized copying, modification, distribution, or use is strictly
# prohibited without prior written permission.

"""Function Registry - Plugin management and discovery system"""


import importlib
import inspect
import pkgutil
from collections.abc import Callable
from pathlib import Path
from typing import Any

from ..models import (
    ExecutionContext,
    ExecutionResult,
    FunctionCategory,
    FunctionDefinition,
    FunctionPlugin,
    ParameterSchema,
    ValidationResult,
)


class FunctionRegistry:
    """Manages function plugins and their execution"""

    def __init__(self) -> None:
        """Initialize empty registry"""
        self.functions: dict[str, FunctionDefinition] = {}
        self.categories: dict[FunctionCategory, list[str]] = {}
        self.plugins: dict[str, FunctionPlugin] = {}

    def register(self, function_def: FunctionDefinition) -> bool:
        """Register a new function plugin"""
        try:
            # Validate function definition
            if not function_def.name or function_def.execution_handler is None:
                return False

            # Check if function already exists
            if function_def.name in self.functions:
                print(
                    f"Warning: Function {function_def.name} already registered, overwriting"
                )

            # Register function
            self.functions[function_def.name] = function_def

            # Update categories
            category = function_def.category
            if category not in self.categories:
                self.categories[category] = []

            if function_def.name not in self.categories[category]:
                self.categories[category].append(function_def.name)

            return True

        except Exception as e:
            print(f"Error registering function {function_def.name}: {e}")
            return False

    def register_plugin(self, plugin: FunctionPlugin) -> bool:
        """Register a plugin instance"""
        try:
            # Create function definition from plugin
            function_def = FunctionDefinition(
                name=plugin.name,
                description=plugin.description,
                category=plugin.category,
                parameters=plugin.parameters,
                execution_handler=plugin.execute,
                confirmation_required=plugin.requires_confirmation,
            )

            # Store plugin reference
            self.plugins[plugin.name] = plugin

            return self.register(function_def)

        except Exception as e:
            print(f"Error registering plugin {plugin.name}: {e}")
            return False

    def register_from_decorator(
        self,
        name: str,
        description: str,
        category: FunctionCategory = FunctionCategory.CUSTOM,
        parameters: dict[str, ParameterSchema] | None = None,
        confirmation_required: bool = True,
        requires_web: bool = False,
        requires_mcp: bool = False,
        requires_files: bool = False,
    ) -> Callable:
        """Decorator for registering functions"""

        def decorator(func: Callable) -> Callable:
            function_def = FunctionDefinition(
                name=name,
                description=description,
                category=category,
                parameters=parameters or {},
                execution_handler=func,
                confirmation_required=confirmation_required,
                requires_web=requires_web,
                requires_mcp=requires_mcp,
                requires_files=requires_files,
            )
            self.register(function_def)
            return func

        return decorator

    async def execute(
        self, function_name: str, parameters: dict[str, Any], context: ExecutionContext
    ) -> ExecutionResult:
        """Execute a registered function with parameters"""
        if function_name not in self.functions:
            return ExecutionResult(
                success=False,
                message=f"Function '{function_name}' not found",
                function_name=function_name,
            )

        func_def = self.functions[function_name]

        try:
            # Validate prerequisites
            if function_name in self.plugins:
                validation = await self.plugins[function_name].validate_prerequisites(
                    context
                )
                if not validation.valid:
                    error_msg = f"Prerequisites not met: {', '.join(validation.errors)}"

                    # Add helpful setup suggestion if LLM provider missing
                    if "LLM provider required" in error_msg:
                        error_msg += "\n\n💡 To set up AII, run: aii config init\n   (Takes ~2 minutes)"

                    return ExecutionResult(
                        success=False,
                        message=error_msg,
                        function_name=function_name,
                    )

            # Validate parameters
            param_validation = self._validate_parameters(
                parameters, func_def.parameters
            )
            if not param_validation.valid:
                return ExecutionResult(
                    success=False,
                    message=f"Parameter validation failed: {', '.join(param_validation.errors)}",
                    function_name=function_name,
                )

            # Use normalized parameters
            validated_params = param_validation.normalized_params

            # Execute function
            if inspect.iscoroutinefunction(func_def.execution_handler):
                result = await func_def.execution_handler(validated_params, context)
            else:
                result = func_def.execution_handler(validated_params, context)

            # Ensure result is ExecutionResult
            if not isinstance(result, ExecutionResult):
                result = ExecutionResult(
                    success=True,
                    message=str(result),
                    data={"result": result},
                    function_name=function_name,
                )

            result.function_name = function_name
            return result

        except Exception as e:
            return ExecutionResult(
                success=False,
                message=f"Execution failed: {str(e)}",
                function_name=function_name,
            )

    def get_function(self, name: str) -> FunctionDefinition | None:
        """Get function definition by name"""
        return self.functions.get(name)

    def function_exists(self, name: str) -> bool:
        """Check if a function exists by name"""
        return name in self.functions

    def unregister_function(self, name: str) -> bool:
        """Unregister a function by name"""
        if name not in self.functions:
            return False

        # Remove from functions
        func_def = self.functions.pop(name)

        # Remove from categories
        if func_def.category in self.categories:
            if name in self.categories[func_def.category]:
                self.categories[func_def.category].remove(name)

        # Remove from plugins if exists
        if name in self.plugins:
            self.plugins.pop(name)

        return True

    def get_functions_by_category(
        self, category: FunctionCategory
    ) -> list[FunctionPlugin]:
        """Get all function plugins by category"""
        result = []
        if category in self.categories:
            for func_name in self.categories[category]:
                if func_name in self.plugins:
                    result.append(self.plugins[func_name])
        return result

    def list_functions(
        self, category: FunctionCategory | None = None, search_term: str | None = None
    ) -> list[FunctionDefinition]:
        """List available functions with optional filtering"""
        functions = list(self.functions.values())

        # Filter by category
        if category:
            functions = [f for f in functions if f.category == category]

        # Filter by search term
        if search_term:
            search_lower = search_term.lower()
            functions = [
                f
                for f in functions
                if (
                    search_lower in f.name.lower()
                    or search_lower in f.description.lower()
                    or any(search_lower in tag.lower() for tag in f.tags)
                )
            ]

        return functions

    def get_categories(self) -> dict[FunctionCategory, list[str]]:
        """Get all categories and their functions"""
        return self.categories.copy()

    def get_function_help(self, name: str) -> str | None:
        """Generate help text for a function"""
        func_def = self.get_function(name)
        if not func_def:
            return None

        help_lines = [
            f"Function: {func_def.name}",
            f"Category: {func_def.category.value}",
            f"Description: {func_def.description}",
            "",
        ]

        # Parameters
        if func_def.parameters:
            help_lines.append("Parameters:")
            for param_name, param_schema in func_def.parameters.items():
                required_text = (
                    " (required)" if param_schema.required else " (optional)"
                )
                default_text = (
                    f" [default: {param_schema.default}]"
                    if param_schema.default is not None
                    else ""
                )
                help_lines.append(
                    f"  {param_name}: {param_schema.description}{required_text}{default_text}"
                )
            help_lines.append("")

        # Examples
        if func_def.examples:
            help_lines.append("Examples:")
            for example in func_def.examples:
                help_lines.append(f"  {example}")
            help_lines.append("")

        # Requirements
        requirements = []
        if func_def.requires_web:
            requirements.append("web access")
        if func_def.requires_mcp:
            requirements.append("MCP connection")
        if func_def.requires_files:
            requirements.append("file access")
        if func_def.confirmation_required:
            requirements.append("user confirmation")

        if requirements:
            help_lines.append(f"Requirements: {', '.join(requirements)}")

        return "\\n".join(help_lines)

    def auto_discover_plugins(self, plugin_dirs: list[Path]) -> int:
        """Auto-discover and register plugins from directories"""
        discovered_count = 0

        for plugin_dir in plugin_dirs:
            if not plugin_dir.exists():
                continue

            try:
                # Add to Python path temporarily
                import sys

                if str(plugin_dir) not in sys.path:
                    sys.path.insert(0, str(plugin_dir))

                # Discover Python modules
                for _importer, modname, _ispkg in pkgutil.iter_modules(
                    [str(plugin_dir)]
                ):
                    try:
                        module = importlib.import_module(modname)

                        # Look for plugin classes
                        for name in dir(module):
                            obj = getattr(module, name)

                            # Check if it's a plugin class
                            if (
                                inspect.isclass(obj)
                                and hasattr(obj, "__bases__")
                                and self._implements_plugin_protocol(obj)
                            ):
                                # Instantiate and register
                                plugin_instance = obj()
                                if self.register_plugin(plugin_instance):
                                    discovered_count += 1

                    except Exception as e:
                        print(f"Error loading plugin module {modname}: {e}")
                        continue

            except Exception as e:
                print(f"Error discovering plugins in {plugin_dir}: {e}")
                continue

        return discovered_count

    def _validate_parameters(
        self,
        provided_params: dict[str, Any],
        expected_params: dict[str, ParameterSchema],
    ) -> ValidationResult:
        """Validate function parameters"""
        errors = []
        warnings = []
        normalized = {}

        # Check required parameters
        for param_name, param_schema in expected_params.items():
            if param_schema.required and param_name not in provided_params:
                errors.append(f"Missing required parameter: {param_name}")
                continue

            # Get value (use default if not provided)
            if param_name in provided_params:
                value = provided_params[param_name]
            else:
                value = param_schema.default
                if value is None:
                    continue

            # Type validation (basic)
            validated_value = self._validate_parameter_type(
                value, param_schema.type, param_schema.choices
            )

            if validated_value is None:
                errors.append(
                    f"Invalid type for parameter {param_name}: expected {param_schema.type}"
                )
                continue

            normalized[param_name] = validated_value

        # Check for unexpected parameters
        for param_name in provided_params:
            if param_name not in expected_params:
                warnings.append(f"Unexpected parameter: {param_name}")

        return ValidationResult(
            valid=len(errors) == 0,
            errors=errors,
            warnings=warnings,
            normalized_params=normalized,
        )

    def _validate_parameter_type(
        self, value: Any, expected_type: str, choices: list[str] | None = None
    ) -> Any:
        """Validate and convert parameter type"""
        try:
            # Handle choices first
            if choices and str(value) not in choices:
                return None

            # Type conversion
            if expected_type == "string" or expected_type == "str":
                return str(value)
            elif expected_type == "integer" or expected_type == "int":
                return int(value)
            elif expected_type == "float":
                return float(value)
            elif expected_type == "boolean" or expected_type == "bool":
                if isinstance(value, bool):
                    return value
                if isinstance(value, str):
                    return value.lower() in ("true", "yes", "1", "on")
                return bool(value)
            elif expected_type == "list":
                if isinstance(value, list):
                    return value
                if isinstance(value, str):
                    return [item.strip() for item in value.split(",")]
                return [value]
            else:
                # Default: return as-is
                return value

        except (ValueError, TypeError):
            return None

    def _implements_plugin_protocol(self, cls: type) -> bool:
        """Check if class implements the FunctionPlugin protocol"""
        required_methods = ["name", "description", "category", "parameters", "execute"]
        return all(hasattr(cls, method) for method in required_methods)
