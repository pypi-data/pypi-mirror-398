# Copyright 2025-present AiiWare.com. All Rights Reserved.
#
# This source code is proprietary and confidential to AiiWare.com.
# Unauthorized copying, modification, distribution, or use is strictly
# prohibited without prior written permission.

"""Code Review Function - Review code for security, performance, and best practices."""


import ast
from pathlib import Path
from typing import Any

from ...core.models import (
    ExecutionContext,
    ExecutionResult,
    FunctionCategory,
    FunctionPlugin,
    FunctionSafety,
    OutputMode,
    ParameterSchema,
    ValidationResult,
)


class CodeReviewFunction(FunctionPlugin):
    """Review code files for security, performance, and best practices"""

    @property
    def name(self) -> str:
        return "code_review"

    @property
    def description(self) -> str:
        return """Review code files OR inline code snippets for security, performance, and best practices.

Use this function when the user wants to review code. Two modes:

**FILE MODE**: User provides a file path or directory
- Examples: "review src/api.py", "review utils/", "check security in auth.js"
- Extract 'file_path' parameter from user input

**INLINE MODE**: User provides code directly in their message
- Examples:
  - "review this code: def foo(): pass"
  - "check this function: const bar = () => {}"
  - "review: function add(a,b) { return a+b; }"
- Extract 'code' parameter (the actual code snippet after keywords like "review this:", "check this:", "review:", etc.)
- Extract 'language' if mentioned (Python, JavaScript, TypeScript, Java, etc.) or leave empty for auto-detection

**Parameters**:
- file_path (optional): Path to code file or directory
- code (optional): Inline code snippet to review
- language (optional): Programming language (auto-detected if not specified)
- focus (optional): security, performance, style, or all (default: all)

**Important**: Either 'file_path' OR 'code' must be provided (not both).
"""

    @property
    def category(self) -> FunctionCategory:
        return FunctionCategory.CODE

    @property
    def parameters(self) -> dict[str, ParameterSchema]:
        return {
            "file_path": ParameterSchema(
                name="file_path",
                type="string",
                required=False,  # Now optional (either file_path OR code)
                description="Path to the code file or directory to review (for FILE MODE)",
            ),
            "code": ParameterSchema(
                name="code",
                type="string",
                required=False,  # Optional (either file_path OR code)
                description="Inline code snippet to review (for INLINE MODE). Extract the actual code from user input after keywords like 'review this code:', 'check this:', etc.",
            ),
            "language": ParameterSchema(
                name="language",
                type="string",
                required=False,
                description="Programming language of the code (python, javascript, typescript, java, etc.). Auto-detected if not specified.",
            ),
            "focus": ParameterSchema(
                name="focus",
                type="string",
                required=False,
                description="Focus area: security, performance, style, or all",
                choices=["security", "performance", "style", "all"],
                default="all",
            ),
        }

    @property
    def requires_confirmation(self) -> bool:
        return False

    @property
    def safety_level(self) -> FunctionSafety:
        return FunctionSafety.SAFE

    async def validate_prerequisites(
        self, context: ExecutionContext
    ) -> ValidationResult:
        """Check if either file path or inline code is provided and valid"""
        file_path = context.parameters.get("file_path", "")
        code = context.parameters.get("code", "")

        # Validate: Either file_path OR code must be provided (not both, not neither)
        if not file_path and not code:
            return ValidationResult(
                valid=False,
                errors=[
                    "Either file path or code snippet is required for review",
                    "Examples:",
                    "  - File: 'review src/api.py'",
                    "  - Inline: 'review this code: def foo(): pass'"
                ]
            )

        if file_path and code:
            return ValidationResult(
                valid=False,
                errors=["Cannot review both file and inline code simultaneously. Please choose one mode."]
            )

        # FILE MODE validation
        if file_path:
            path = Path(file_path)
            if not path.exists():
                return ValidationResult(
                    valid=False, errors=[f"Path not found: {file_path}"]
                )

            # Handle both files and directories
            if path.is_file():
                # Check if file is too large (>100KB)
                if path.stat().st_size > 100 * 1024:
                    return ValidationResult(
                        valid=False,
                        errors=["File too large for review (max 100KB)"],
                    )
            elif path.is_dir():
                # For directories, check if they contain code files
                code_extensions = {'.py', '.js', '.ts', '.java', '.go', '.rs', '.cpp', '.c', '.h'}
                code_files = [f for f in path.rglob('*') if f.is_file() and f.suffix.lower() in code_extensions]

                if not code_files:
                    return ValidationResult(
                        valid=False,
                        errors=[f"No code files found in directory: {file_path}"]
                    )

                # Check total size of code files (max 500KB for directories)
                total_size = sum(f.stat().st_size for f in code_files)
                if total_size > 500 * 1024:
                    return ValidationResult(
                        valid=False,
                        errors=[f"Directory too large for review (max 500KB total, found {total_size//1024}KB)"],
                    )
            else:
                return ValidationResult(valid=False, errors=[f"Invalid path type: {file_path}"])

        # INLINE MODE validation
        if code:
            # Check if inline code is too large (max 10KB)
            code_size = len(code.encode('utf-8'))
            if code_size > 10 * 1024:
                return ValidationResult(
                    valid=False,
                    errors=[
                        f"Inline code too large ({code_size//1024}KB, max 10KB).",
                        "Please save to a file and use file path instead."
                    ]
                )

        return ValidationResult(valid=True)

    async def execute(
        self, parameters: dict[str, Any], context: ExecutionContext
    ) -> ExecutionResult:
        """Execute code review for file, directory, or inline code"""
        file_path = parameters.get("file_path")
        code = parameters.get("code")
        language = parameters.get("language", "")
        focus = parameters.get("focus", "all")

        try:
            # FILE MODE: Review file or directory
            if file_path:
                path = Path(file_path)

                if path.is_file():
                    # Single file analysis
                    return await self._analyze_single_file(path, focus, context)
                elif path.is_dir():
                    # Directory analysis
                    return await self._analyze_directory(path, focus, context)
                else:
                    return ExecutionResult(
                        success=False,
                        message=f"Invalid path type: {file_path}"
                    )

            # INLINE MODE: Review inline code snippet
            elif code:
                # Auto-detect language if not provided
                if not language:
                    language = self._detect_language_from_code(code)

                # Perform analysis on inline code
                return await self._analyze_inline_code(code, language, focus, context)

            else:
                # This should not happen due to validation, but handle it
                return ExecutionResult(
                    success=False,
                    message="Either file path or code snippet is required"
                )

        except Exception as e:
            return ExecutionResult(
                success=False, message=f"Code review failed: {str(e)}"
            )

    async def _analyze_single_file(self, path: Path, focus: str, context: ExecutionContext) -> ExecutionResult:
        """Analyze a single code file"""
        content = path.read_text(encoding="utf-8")

        # Perform analysis and capture token usage
        analysis, usage = await self._analyze_code_with_usage(content, path.suffix, focus, context)

        return ExecutionResult(
            success=True,
            message=f"Code review completed for {path}:\n\n{analysis}",
            data={
                "file_path": str(path),
                "analysis": analysis,
                "focus": focus,
                "file_size": len(content),
                "line_count": len(content.splitlines()),
                "analysis_type": "single_file",
                "input_tokens": usage.get("input_tokens", 0),
                "output_tokens": usage.get("output_tokens", 0),
                "total_tokens": usage.get("input_tokens", 0) + usage.get("output_tokens", 0)
            },
        )

    async def _analyze_directory(self, path: Path, focus: str, context: ExecutionContext) -> ExecutionResult:
        """Analyze all code files in a directory"""
        code_extensions = {'.py', '.js', '.ts', '.java', '.go', '.rs', '.cpp', '.c', '.h'}
        code_files = [f for f in path.rglob('*') if f.is_file() and f.suffix.lower() in code_extensions]

        if not code_files:
            return ExecutionResult(
                success=False,
                message=f"No code files found in directory: {path}"
            )

        # Limit to first 10 files for performance
        code_files = code_files[:10]

        analyses = []
        total_size = 0
        total_lines = 0
        total_input_tokens = 0
        total_output_tokens = 0

        for file_path in code_files:
            try:
                content = file_path.read_text(encoding="utf-8")

                # Track token usage from this file's analysis
                file_analysis, file_usage = await self._analyze_code_with_usage(
                    content, file_path.suffix, focus, context
                )

                analyses.append(f"## {file_path.relative_to(path)}\n{file_analysis}")
                total_size += len(content)
                total_lines += len(content.splitlines())

                # Accumulate actual token usage from LLM calls
                if file_usage:
                    total_input_tokens += file_usage.get('input_tokens', 0)
                    total_output_tokens += file_usage.get('output_tokens', 0)

            except Exception as e:
                analyses.append(f"## {file_path.relative_to(path)}\n❌ Error reading file: {str(e)}")

        # Create directory summary
        summary = f"📁 **Directory Analysis: {path}**\n\n"
        summary += f"📊 **Summary:**\n"
        summary += f"- Files analyzed: {len(analyses)}\n"
        summary += f"- Total size: {total_size:,} bytes\n"
        summary += f"- Total lines: {total_lines:,}\n"
        summary += f"- Focus area: {focus}\n\n"

        # Add individual file analyses
        summary += "📋 **Individual File Analyses:**\n\n" + "\n\n".join(analyses)

        return ExecutionResult(
            success=True,
            message=summary,
            data={
                "directory_path": str(path),
                "files_analyzed": len(analyses),
                "total_size": total_size,
                "total_lines": total_lines,
                "focus": focus,
                "analysis_type": "directory",
                "files": [str(f.relative_to(path)) for f in code_files],
                "input_tokens": total_input_tokens,
                "output_tokens": total_output_tokens,
                "total_tokens": total_input_tokens + total_output_tokens
            },
        )

    async def _analyze_inline_code(
        self, code: str, language: str, focus: str, context: ExecutionContext
    ) -> ExecutionResult:
        """Analyze inline code snippet"""
        # Convert language to file extension format for existing analysis methods
        file_ext = self._language_to_extension(language)

        # Perform analysis and capture token usage
        analysis, usage = await self._analyze_code_with_usage(code, file_ext, focus, context)

        # Create formatted output
        output = f"Code Review ({language}):\n\n{analysis}"

        return ExecutionResult(
            success=True,
            message=output,
            data={
                "code": code,
                "language": language,
                "analysis": analysis,
                "focus": focus,
                "code_size": len(code),
                "line_count": len(code.splitlines()),
                "analysis_type": "inline",
                "input_tokens": usage.get("input_tokens", 0),
                "output_tokens": usage.get("output_tokens", 0),
                "total_tokens": usage.get("input_tokens", 0) + usage.get("output_tokens", 0),
                "clean_output": output
            },
        )

    def _detect_language_from_code(self, code: str) -> str:
        """Auto-detect programming language from code syntax"""
        code_lower = code.lower().strip()

        # Python detection
        if any(keyword in code_lower for keyword in ["def ", "import ", "class ", "self.", "elif ", "async def"]):
            return "python"

        # JavaScript/TypeScript detection
        if any(keyword in code_lower for keyword in ["function ", "const ", "let ", "var ", "=>", "console.log"]):
            if "interface " in code_lower or ": " in code and "{" in code:
                return "typescript"
            return "javascript"

        # Java detection
        if any(keyword in code_lower for keyword in ["public class", "private class", "public static void", "system.out"]):
            return "java"

        # C/C++ detection
        if any(keyword in code_lower for keyword in ["#include", "int main(", "std::", "cout", "printf"]):
            return "cpp"

        # Go detection
        if any(keyword in code_lower for keyword in ["package ", "func ", "fmt."]):
            return "go"

        # Rust detection
        if any(keyword in code_lower for keyword in ["fn ", "let mut", "impl ", "use std::"]):
            return "rust"

        # Default to unknown if can't detect
        return "unknown"

    def _language_to_extension(self, language: str) -> str:
        """Convert language name to file extension"""
        language_map = {
            "python": ".py",
            "javascript": ".js",
            "typescript": ".ts",
            "java": ".java",
            "cpp": ".cpp",
            "c++": ".cpp",
            "c": ".c",
            "go": ".go",
            "rust": ".rs",
            "ruby": ".rb",
            "php": ".php",
            "swift": ".swift",
            "kotlin": ".kt",
            "unknown": ".txt"
        }
        return language_map.get(language.lower(), ".txt")

    async def _analyze_code(
        self, content: str, file_ext: str, focus: str, context: ExecutionContext
    ) -> str:
        """Analyze code content"""
        analyses = []

        # Basic metrics
        lines = content.splitlines()
        line_count = len(lines)
        blank_lines = sum(1 for line in lines if not line.strip())
        comment_lines = self._count_comment_lines(lines, file_ext)

        analyses.append("📊 **Code Metrics**")
        analyses.append(f"- Total lines: {line_count}")
        analyses.append(f"- Blank lines: {blank_lines}")
        analyses.append(f"- Comment lines: {comment_lines}")
        analyses.append(
            f"- Code density: {((line_count - blank_lines - comment_lines) / line_count * 100):.1f}%"
        )
        analyses.append("")

        # Static analysis based on file type
        if file_ext == ".py":
            analyses.extend(await self._analyze_python_code(content, focus))
        elif file_ext in [".js", ".ts", ".jsx", ".tsx"]:
            analyses.extend(await self._analyze_javascript_code(content, focus))
        elif file_ext in [".java"]:
            analyses.extend(await self._analyze_java_code(content, focus))
        else:
            analyses.append(
                "⚠️ **General Analysis** (file type not specifically supported)"
            )
            analyses.extend(await self._analyze_generic_code(content, focus))

        # LLM-powered analysis if available
        if context.llm_provider and focus in ["all", "security", "performance"]:
            analyses.append("")
            analyses.append("🤖 **AI-Powered Analysis**")
            ai_analysis, usage = await self._get_llm_analysis(
                content, file_ext, focus, context.llm_provider
            )
            analyses.append(ai_analysis)

            # Store usage in context for tracking (if supported)
            if hasattr(context, 'add_token_usage'):
                context.add_token_usage(usage)

        return "\n".join(analyses)

    async def _analyze_code_with_usage(
        self, content: str, file_ext: str, focus: str, context: ExecutionContext
    ) -> tuple[str, dict]:
        """Analyze code content and return both analysis and token usage"""
        analyses = []
        total_usage = {"input_tokens": 0, "output_tokens": 0}

        # Basic metrics
        lines = content.splitlines()
        line_count = len(lines)
        blank_lines = sum(1 for line in lines if not line.strip())
        comment_lines = self._count_comment_lines(lines, file_ext)

        analyses.append("📊 **Code Metrics**")
        analyses.append(f"- Total lines: {line_count}")
        analyses.append(f"- Blank lines: {blank_lines}")
        analyses.append(f"- Comment lines: {comment_lines}")
        analyses.append(
            f"- Code density: {((line_count - blank_lines - comment_lines) / line_count * 100):.1f}%"
        )
        analyses.append("")

        # Static analysis based on file type
        if file_ext == ".py":
            analyses.extend(await self._analyze_python_code(content, focus))
        elif file_ext in [".js", ".ts", ".jsx", ".tsx"]:
            analyses.extend(await self._analyze_javascript_code(content, focus))
        elif file_ext in [".java"]:
            analyses.extend(await self._analyze_java_code(content, focus))
        else:
            analyses.append(
                "⚠️ **General Analysis** (file type not specifically supported)"
            )
            analyses.extend(await self._analyze_generic_code(content, focus))

        # LLM-powered analysis if available
        if context.llm_provider and focus in ["all", "security", "performance"]:
            analyses.append("")
            analyses.append("🤖 **AI-Powered Analysis**")
            ai_analysis, usage = await self._get_llm_analysis(
                content, file_ext, focus, context.llm_provider
            )
            analyses.append(ai_analysis)

            # Accumulate token usage
            if usage:
                total_usage["input_tokens"] += usage.get("input_tokens", 0)
                total_usage["output_tokens"] += usage.get("output_tokens", 0)

        return "\n".join(analyses), total_usage

    def _count_comment_lines(self, lines: list[str], file_ext: str) -> int:
        """Count comment lines based on file type"""
        comment_count = 0
        comment_chars = {
            ".py": ["#"],
            ".js": ["//"],
            ".ts": ["//"],
            ".jsx": ["//"],
            ".tsx": ["//"],
            ".java": ["//"],
            ".cpp": ["//"],
            ".c": ["//"],
            ".h": ["//"],
        }

        chars = comment_chars.get(file_ext, ["#", "//"])

        for line in lines:
            stripped = line.strip()
            if any(stripped.startswith(char) for char in chars):
                comment_count += 1

        return comment_count

    async def _analyze_python_code(self, content: str, focus: str) -> list[str]:
        """Analyze Python-specific patterns"""
        analyses = []

        try:
            tree = ast.parse(content)
            analyses.append("🐍 **Python Analysis**")

            # Count different node types
            functions = sum(
                1 for node in ast.walk(tree) if isinstance(node, ast.FunctionDef)
            )
            classes = sum(
                1 for node in ast.walk(tree) if isinstance(node, ast.ClassDef)
            )
            imports = sum(
                1
                for node in ast.walk(tree)
                if isinstance(node, (ast.Import, ast.ImportFrom))
            )

            analyses.append(f"- Functions: {functions}")
            analyses.append(f"- Classes: {classes}")
            analyses.append(f"- Imports: {imports}")

            if focus in ["all", "style"]:
                # Check for common style issues
                style_issues = []
                if "print(" in content:
                    style_issues.append("Contains print statements (consider logging)")
                if "TODO" in content or "FIXME" in content:
                    style_issues.append("Contains TODO/FIXME comments")
                if len(content.splitlines()) > 1000:
                    style_issues.append("File is very large (>1000 lines)")

                if style_issues:
                    analyses.append("- Style notes: " + "; ".join(style_issues))

            if focus in ["all", "security"]:
                # Basic security checks
                security_issues = []
                if "eval(" in content:
                    security_issues.append("Uses eval() - potential security risk")
                if "exec(" in content:
                    security_issues.append("Uses exec() - potential security risk")
                if "os.system(" in content:
                    security_issues.append(
                        "Uses os.system() - potential command injection"
                    )

                if security_issues:
                    analyses.append(
                        "- Security concerns: " + "; ".join(security_issues)
                    )

        except SyntaxError:
            analyses.append("🐍 **Python Analysis**")
            analyses.append("- ❌ Syntax errors detected in Python code")

        return analyses

    async def _analyze_javascript_code(self, content: str, focus: str) -> list[str]:
        """Analyze JavaScript/TypeScript patterns"""
        analyses = []
        analyses.append("🟨 **JavaScript/TypeScript Analysis**")

        # Basic pattern detection
        patterns = {
            "functions": content.count("function ") + content.count("=>"),
            "classes": content.count("class "),
            "imports": content.count("import ") + content.count("require("),
            "exports": content.count("export ") + content.count("module.exports"),
        }

        for pattern, count in patterns.items():
            if count > 0:
                analyses.append(f"- {pattern.title()}: {count}")

        if focus in ["all", "security"]:
            security_issues = []
            if "eval(" in content:
                security_issues.append("Uses eval() - security risk")
            if "innerHTML" in content:
                security_issues.append("Uses innerHTML - potential XSS risk")
            if "document.write(" in content:
                security_issues.append("Uses document.write() - deprecated")

            if security_issues:
                analyses.append("- Security concerns: " + "; ".join(security_issues))

        return analyses

    async def _analyze_java_code(self, content: str, focus: str) -> list[str]:
        """Analyze Java-specific patterns"""
        analyses = []
        analyses.append("☕ **Java Analysis**")

        # Basic pattern detection
        class_count = content.count("class ") + content.count("interface ")
        method_count = (
            content.count(" void ")
            + content.count(" public ")
            + content.count(" private ")
        )

        analyses.append(f"- Classes/Interfaces: {class_count}")
        analyses.append(f"- Methods: {method_count}")

        if focus in ["all", "security"]:
            security_issues = []
            if "Runtime.getRuntime().exec(" in content:
                security_issues.append("Uses Runtime.exec() - command injection risk")
            if "System.out.println" in content:
                security_issues.append("Contains debug prints")

            if security_issues:
                analyses.append("- Security concerns: " + "; ".join(security_issues))

        return analyses

    async def _analyze_generic_code(self, content: str, focus: str) -> list[str]:
        """Generic code analysis for unsupported file types"""
        analyses = []

        # Basic patterns that apply to most languages
        if focus in ["all", "security"]:
            security_keywords = ["password", "secret", "key", "token", "api_key"]
            found_keywords = [
                kw for kw in security_keywords if kw.lower() in content.lower()
            ]
            if found_keywords:
                analyses.append(
                    f"- Potential secrets found: {', '.join(found_keywords)}"
                )

        return analyses

    async def _get_llm_analysis(
        self, content: str, file_ext: str, focus: str, llm_provider: Any
    ) -> tuple[str, dict]:
        """Get AI-powered code analysis with token tracking"""
        prompt = f"""Review this {file_ext} code for {focus if focus != 'all' else 'security, performance, and style'}.

Code:
```{file_ext.lstrip('.')}
{content[:2000]}{'...' if len(content) > 2000 else ''}
```

Provide a concise analysis focusing on:
1. Code quality and maintainability
2. Potential security vulnerabilities
3. Performance considerations
4. Best practice recommendations

Keep the analysis practical and specific to the code shown."""

        try:
            # Use complete_with_usage for token tracking if available
            if hasattr(llm_provider, "complete_with_usage"):
                llm_response = await llm_provider.complete_with_usage(prompt)
                result = llm_response.content.strip()
                usage = llm_response.usage or {}
            else:
                result = await llm_provider.complete(prompt)
                result = str(result) if result is not None else "AI analysis unavailable"
                usage = {}

            return result, usage
        except Exception:
            return "AI analysis unavailable", {}
