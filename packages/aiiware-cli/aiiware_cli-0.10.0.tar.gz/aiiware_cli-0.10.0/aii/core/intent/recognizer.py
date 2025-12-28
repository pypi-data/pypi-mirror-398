# Copyright 2025-present AiiWare.com. All Rights Reserved.
#
# This source code is proprietary and confidential to AiiWare.com.
# Unauthorized copying, modification, distribution, or use is strictly
# prohibited without prior written permission.

"""Intent Recognizer - Analyze user input and determine intended action"""


import json
import os
import re
from typing import Any

from ..context.models import ChatContext
from ..models import FunctionSafety, RecognitionResult, RouteSource
from .models import BUILT_IN_INTENTS, IntentTemplate
from .parameter_enhancers import get_enhancer_registry

# LLMOrchestrator imported dynamically when needed to avoid circular imports

# Debug mode flag (set via environment variable)
DEBUG_MODE = os.getenv("AII_DEBUG", "").lower() in ("1", "true", "yes")


class IntentRecognizer:
    """LLM-powered intent classification engine"""

    def __init__(self, llm_provider: Any | None = None):
        """Initialize with LLM provider"""
        self.llm_provider = llm_provider
        self.intent_templates = BUILT_IN_INTENTS.copy()
        self.function_registry: Any | None = None  # Will be injected
        self.recognition_cache: dict[str, RecognitionResult] = {}

        # Initialize enhancer registry for parameter enhancement
        self.enhancer_registry = get_enhancer_registry()

    def register_function_registry(self, registry: Any) -> None:
        """Register function registry for dynamic function discovery"""
        self.function_registry = registry

    def add_intent_template(self, template: IntentTemplate) -> None:
        """Add custom intent template"""
        self.intent_templates.append(template)

    async def recognize_intent(
        self, user_input: str, context: ChatContext | None = None
    ) -> RecognitionResult:
        """Analyze user input and return recognized intent with confidence"""
        import os
        if os.getenv("AII_DEBUG"):
            print(f"🔍 DEBUG [Layer 2A - ENTRY]: recognize_intent() called with user_input='{user_input}'")

        if not user_input or not user_input.strip():
            return RecognitionResult(
                intent="invalid_input",
                confidence=0.0,
                parameters={},
                function_name="help",
                requires_confirmation=False,
                reasoning="Empty input provided",
                source=RouteSource.DIRECT_MATCH,
            )

        user_input = user_input.strip()

        # DIRECT MATCH: Git PR keywords (before LLM to avoid misclassification)
        pr_keywords = ["pull request", "create pr", "github pr", "make pr", "pr create", "create pull request"]
        if any(keyword in user_input.lower() for keyword in pr_keywords) or user_input.lower() in ["pr", "pullrequest"]:
            return RecognitionResult(
                intent="git_pr",
                confidence=0.95,
                parameters={},
                function_name="git_pr",
                requires_confirmation=False,  # Function handles its own confirmation with PR preview
                reasoning="Direct match for pull request creation keywords",
                source=RouteSource.DIRECT_MATCH,
            )

        # DIRECT MATCH: Git branch keywords
        user_lower = user_input.lower()

        # Check for "branch <description>" pattern (simple case)
        if user_lower.startswith("branch "):
            description = user_input[7:].strip()  # Remove "branch " prefix
            if description:
                return RecognitionResult(
                    intent="git_branch",
                    confidence=0.95,
                    parameters={"description": description},
                    function_name="git_branch",
                    requires_confirmation=False,  # Function handles its own confirmation with branch name preview
                    reasoning="Direct match for 'branch <description>' pattern",
                    source=RouteSource.DIRECT_MATCH,
                )

        # Check for longer branch keywords
        branch_keywords = ["create branch", "new branch", "make branch", "branch create"]
        if any(keyword in user_lower for keyword in branch_keywords):
            # Extract description from input
            for keyword in branch_keywords:
                if keyword in user_lower:
                    description = user_input.lower().replace(keyword, "").strip()
                    if description:
                        return RecognitionResult(
                            intent="git_branch",
                            confidence=0.90,
                            parameters={"description": description},
                            function_name="git_branch",
                            requires_confirmation=False,  # Function handles its own confirmation with branch name preview
                            reasoning="Direct match for branch creation keywords",
                            source=RouteSource.DIRECT_MATCH,
                        )

        # LLM-First Approach: Try LLM recognition first for better flexibility
        llm_result = None
        if self.llm_provider:
            try:
                import os
                if os.getenv("AII_DEBUG"):
                    print(f"🔍 DEBUG [Layer 2A - recognizer.recognize_intent]: BEFORE _llm_recognition call")

                llm_result = await self._llm_recognition(user_input, context)

                if os.getenv("AII_DEBUG"):
                    print(f"🔍 DEBUG [Layer 2A - recognizer.recognize_intent]: AFTER _llm_recognition call")
                    if llm_result:
                        tokens = llm_result.intent_recognition_tokens or {}
                        print(f"🔍 DEBUG [Layer 2A]: LLM result - function={llm_result.function_name}, confidence={llm_result.confidence}")
                        print(f"🔍 DEBUG [Layer 2A]: Intent tokens={tokens}")
                    else:
                        print(f"🔍 DEBUG [Layer 2A]: llm_result is None!")

                # Accept LLM results with moderate confidence
                if llm_result and llm_result.confidence >= 0.7:
                    # Apply smart confirmation logic to direct LLM results
                    needs_confirmation, confirmation_reason = (
                        self.should_confirm_function(
                            llm_result.function_name,
                            llm_result.confidence,
                            llm_result.parameters,
                        )
                    )

                    # v0.11.0: Debug token passing
                    import os
                    if os.getenv("AII_DEBUG"):
                        print("🔍 DEBUG [Layer 2A - recognize_intent]: Creating new RecognitionResult")
                        print(f"🔍 DEBUG [Layer 2A]: llm_result.intent_recognition_tokens = {llm_result.intent_recognition_tokens}")

                    result = RecognitionResult(
                        intent=llm_result.intent,
                        confidence=llm_result.confidence,
                        parameters=llm_result.parameters,
                        function_name=llm_result.function_name,
                        requires_confirmation=needs_confirmation,
                        reasoning=f"{llm_result.reasoning}. Confirmation: {confirmation_reason}",
                        source=llm_result.source,
                        intent_recognition_tokens=llm_result.intent_recognition_tokens,  # v0.11.0: Pass tokens in constructor
                    )

                    if os.getenv("AII_DEBUG"):
                        print(f"🔍 DEBUG [Layer 2A]: NEW result.intent_recognition_tokens = {result.intent_recognition_tokens}")

                    return result
            except Exception as e:
                print(f"LLM recognition failed: {e}")

        # Check if this should use universal orchestrator for content generation
        if self.llm_provider and self._is_universal_content_request(user_input):
            universal_result = await self._route_to_universal_orchestrator(
                user_input, context
            )
            if universal_result:
                return universal_result

        # Fallback to direct pattern matching for validation/enhancement
        direct_result = self._try_direct_pattern_match(user_input)
        if direct_result:
            # If we have both LLM and pattern results, enhance with pattern validation
            if llm_result:
                return self._enhance_with_patterns(llm_result, direct_result)
            # v0.6.0: Pattern matching alone is NOT sufficient - always require LLM for token tracking
            # If LLM failed, we should fail too (don't use pattern-only results)
            # This ensures accurate token/cost tracking for all requests

        # Last resort - suggest help or clarification
        return RecognitionResult(
            intent="clarification_needed",
            confidence=0.2,
            parameters={"original_input": user_input},
            function_name="clarify",
            requires_confirmation=True,
            reasoning="Could not determine intent from input",
            source=RouteSource.FALLBACK,
        )

    def _try_direct_pattern_match(self, user_input: str) -> RecognitionResult | None:
        """Try to match input against direct patterns"""
        best_match = None
        best_score = 0.0

        for template in self.intent_templates:
            score = 0.0

            # Check pattern match
            if template.matches_pattern(user_input):
                score += 0.6  # Base score for pattern match

            # Check keyword presence
            keyword_count = template.has_keywords(user_input)
            if keyword_count > 0:
                keyword_score = min(0.3, keyword_count * 0.1)  # Up to 0.3 for keywords
                score += keyword_score

            # Add template-specific confidence boost
            score += template.confidence_boost

            # Ensure score doesn't exceed 1.0
            score = min(1.0, score)

            if (
                score > best_score and score >= 0.3
            ):  # Lowered threshold - let LLM handle more cases
                best_score = score
                best_match = template

        if best_match:
            # Extract parameters based on the matched template
            parameters = self._extract_parameters(user_input, best_match)

            return RecognitionResult(
                intent=best_match.intent_name,
                confidence=best_score,
                parameters=parameters,
                function_name=best_match.function_name,
                requires_confirmation=best_score < 0.8,
                reasoning=f"Matched pattern for {best_match.intent_name}",
                source=RouteSource.DIRECT_MATCH,
            )

        return None

    async def _llm_recognition(
        self, user_input: str, context: ChatContext | None = None
    ) -> RecognitionResult | None:
        """Use LLM for intent recognition"""
        if not self.llm_provider:
            return None

        try:
            prompt = self._build_recognition_prompt(user_input, context)

            # Use complete_with_usage to track token consumption
            if hasattr(self.llm_provider, "complete_with_usage"):
                llm_response = await self.llm_provider.complete_with_usage(prompt)
                response = llm_response.content
                usage = llm_response.usage or {}
            else:
                response = await self.llm_provider.complete(prompt)
                usage = {}

            result = self._parse_llm_response(response, user_input, context)

            import os
            if os.getenv("AII_DEBUG"):
                print(f"🔍 DEBUG [recognizer._llm_recognition]: usage={usage}")
                print(f"🔍 DEBUG [recognizer._llm_recognition]: result={result}")

            # Add token usage to the result if available
            if result and usage:
                result.intent_recognition_tokens = {
                    "input_tokens": usage.get("input_tokens", 0),
                    "output_tokens": usage.get("output_tokens", 0),
                    "reasoning_tokens": usage.get("reasoning_tokens", 0)
                }
                if os.getenv("AII_DEBUG"):
                    print(f"🔍 DEBUG [recognizer._llm_recognition]: Set intent_recognition_tokens={result.intent_recognition_tokens}")
            else:
                if os.getenv("AII_DEBUG"):
                    print(f"🔍 DEBUG [recognizer._llm_recognition]: NOT setting tokens - result={result is not None}, usage={bool(usage)}")

            return result
        except Exception as e:
            print(f"LLM recognition failed: {e}")
            return None

    def _get_current_date_context(self) -> str:
        """Get current date context for prompt (v0.4.10)."""
        from datetime import datetime

        now = datetime.now()
        return now.strftime("%Y-%m-%d (%B %d, %Y)")

    def _get_tomorrow_date(self) -> str:
        """Get tomorrow's date (v0.4.10)."""
        from datetime import datetime, timedelta

        tomorrow = datetime.now() + timedelta(days=1)
        return tomorrow.strftime("%Y-%m-%d")

    def _interpret_date_example(self, month_day: str) -> str:
        """
        Generate date interpretation example for prompt (v0.4.10).

        Args:
            month_day: Date in MM-DD format (e.g., "10-12")

        Returns:
            Interpreted date with year (e.g., "2025-10-12" or "2026-10-12")
        """
        from datetime import datetime

        now = datetime.now()
        month, day = map(int, month_day.split("-"))

        # Create date with current year
        try:
            candidate_date = datetime(now.year, month, day)
        except ValueError:
            # Invalid date (like Feb 30)
            return f"{now.year}-{month:02d}-{day:02d}"

        # If date is in the past, use next year
        if candidate_date.date() < now.date():
            return f"{now.year + 1}-{month:02d}-{day:02d}"
        else:
            return f"{now.year}-{month:02d}-{day:02d}"

    def _build_recognition_prompt(
        self, user_input: str, context: ChatContext | None = None
    ) -> str:
        """Build prompt for LLM intent recognition"""
        # Get available functions
        available_functions = self._get_function_descriptions()

        # Build context summary with location awareness
        context_summary = ""
        if context and context.messages:
            recent_messages = context.get_recent_messages(5)
            context_lines = []
            for msg in recent_messages[-3:]:  # Last 3 messages for context
                role = msg.role
                content = (
                    msg.content[:100] + "..." if len(msg.content) > 100 else msg.content
                )
                context_lines.append(f"{role}: {content}")

                # Extract location patterns from previous commands/responses
                if "Downloads" in content or "~/Downloads" in content:
                    context_lines.append(
                        "LOCATION_CONTEXT: Previous operation involved ~/Downloads"
                    )
                elif "Documents" in content or "~/Documents" in content:
                    context_lines.append(
                        "LOCATION_CONTEXT: Previous operation involved ~/Documents"
                    )
                elif "Desktop" in content or "~/Desktop" in content:
                    context_lines.append(
                        "LOCATION_CONTEXT: Previous operation involved ~/Desktop"
                    )

            context_summary = "\\n".join(context_lines)

        prompt = f"""You are an intent classifier for the "aii" CLI application. Analyze the user input and determine the most likely intended action.

Available Functions:
{available_functions}

{"Recent Chat Context:" + chr(10) + context_summary + chr(10) if context_summary else ""}
User Input: "{user_input}"

🗓️ CRITICAL DATE INTERPRETATION RULE (v0.4.10):
Current date: {self._get_current_date_context()}

When users specify dates WITHOUT year (e.g., "10月12日", "October 12", "12号"), ALWAYS assume:
- If date is in FUTURE of current month/year → use CURRENT YEAR
- If date is in PAST (earlier than today) → use NEXT YEAR (next occurrence)

Date Interpretation Examples (today is {self._get_current_date_context()}):
- "10月12日" (Oct 12) → {self._interpret_date_example("10-12")}
- "10月5日" (Oct 5) → {self._interpret_date_example("10-05")}
- "1月15日" (Jan 15) → {self._interpret_date_example("01-15")}
- "12月25日" (Dec 25) → {self._interpret_date_example("12-25")}
- "明天" (tomorrow) → {self._get_tomorrow_date()}
- "下周一" (next Monday) → Calculate based on current date

🎯 CRITICAL: If resulting date is in the PAST, ADD 1 YEAR to get next occurrence.

Examples with context (today is {self._get_current_date_context()}):
✅ CORRECT: "10月5日" → {self._interpret_date_example("10-05")} (next occurrence)
❌ WRONG: "10月5日" → 2024-10-05 (would be in the past!)

CRITICAL GIT OPERATIONS RULE: If the user mentions "pr", "pull request", "create pr", or "github pr", they want to use the git_pr function to create a GitHub pull request, NOT shell_command or content_generate.

If the user mentions "branch", "create branch", "new branch", they want to use the git_branch function to create a git branch with a conventional name, NOT shell_command.

CRITICAL MCP/RAILWAY OPERATIONS RULE - HIGHEST PRIORITY:
If the user query contains ANY of these Chinese railway keywords: "火车票", "高铁", "动车", "余票", "12306", "车站", "列车", "查询火车", "查询车票", "北京", "上海", "车次" combined with train/ticket context, you MUST use the mcp_tool function to query the 12306-mcp server.
DO NOT use research, web_search, universal_generate, or any other function for Chinese railway ticket queries.
The mcp_tool function has direct access to real-time 12306 railway data through MCP servers.

CRITICAL GITHUB OPERATIONS RULE - HIGHEST PRIORITY:
If the user query contains ANY mention of GitHub operations including:
- Repository search: "search github", "find github repos", "search for repos", "popular repos", "search repositories", "find repositories"
- Repository listing: "list my repos", "my repositories", "my github repos"
- Repository creation/forking: "create github repo", "fork repository"
- Issues/PRs: "github issues", "create github issue", "pull requests"
- Code search: "search github code", "find code on github"
- ANY combination of "github" + "search/find/list/create"

You MUST use the mcp_tool function, NOT research or web_search.
The mcp_tool has direct GitHub API access through MCP servers.
The research function is ONLY for web articles/news/documentation, NOT for GitHub repository operations.

Examples that should use mcp_tool:
- "search github for popular python ML repos" → mcp_tool (GitHub repository search)
- "find popular ML repositories" → mcp_tool (GitHub repository search)
- "search for python repos on github" → mcp_tool (GitHub repository search)
- "list my github repositories" → mcp_tool (GitHub API call)
- "search github code for function definition" → mcp_tool (GitHub code search)

Examples that should use research:
- "research machine learning trends" → research (web articles/news)
- "find articles about Python ML" → research (web content, not GitHub repos)

🔍 CRITICAL MCP INTROSPECTION RULE (v0.4.10) - ABSOLUTE PRIORITY:
When user asks about MCP server capabilities, tools, or operations, ALWAYS use mcp_tool, NEVER web_search.

MCP Introspection queries (USE mcp_tool):
- "what tools are available in [server]?" → mcp_tool (list_tools for server)
- "list tools in github mcp" → mcp_tool (NOT web_search!)
- "what can [server] do?" → mcp_tool (server capabilities)
- "show me github server capabilities" → mcp_tool (NOT web_search!)
- "capabilities of [server]" → mcp_tool (introspection)
- ANY query mentioning MCP server by name + "tools/capabilities/features" → mcp_tool

Conceptual queries (USE web_search):
- "what is github?" → web_search (concept explanation, not MCP introspection)
- "what is MCP?" → web_search (general information)

🎯 KEY DISTINCTION:
- MCP server operations/capabilities → mcp_tool (introspection via MCP protocol)
- Concept/definition/general info → web_search or research

Other MCP operations:
- Filesystem: "read file", "list directory", "write file" (when mentioning specific file paths, use mcp_tool with filesystem server)

CRITICAL CONTEXT RULE: If the user says "second largest", "now check", "next one", etc., and the recent context shows a previous command used a specific directory (~/Downloads, ~/Documents, etc.), you MUST use that same directory as the path parameter.

For example:
- If previous context shows "find ~/Downloads" or "Downloads" directory
- And user says "now check the second largest"
- You MUST set path parameter to "~/Downloads"

Look for these location patterns in the context:
- ~/Downloads, ~/Documents, ~/Desktop
- Any path that starts with ~/ or /
- Any mention of Downloads, Documents, Desktop folders

🎯 CRITICAL FUNCTION DISAMBIGUATION RULE (v0.6.0) - TRANSLATION FUNCTIONS:

**detect_language** (language identification ONLY):
- User wants to IDENTIFY/DETECT what language text is written in
- User wants the LANGUAGE NAME as output (e.g., "french", "spanish")
- NO translation requested - just identification
- Patterns: "what language", "detect language", "identify language", "which language"
- Keywords: detect/what/identify/which + language (WITHOUT "to" or "translate")
- Examples:
  ✅ "what language is this: Bonjour" → detect_language
  ✅ "detect the language of: Hola mundo" → detect_language
  ✅ "identify language: 你好" → detect_language
  ✅ "which language is this written in: Guten Tag" → detect_language
  ✅ "is this french: Bonjour" → detect_language

**translate** (language translation):
- User wants to TRANSLATE text from one language to another
- User wants the TRANSLATED TEXT as output
- Keywords: translate, convert, "to spanish", "in french", "to english"
- Patterns: "translate [text]", "[text] to [language]", "convert to [language]"
- Examples:
  ✅ "translate hello to spanish" → translate
  ✅ "Bonjour to english" → translate
  ✅ "convert this to french: hello" → translate
  ✅ "what does Bonjour mean" → translate

🚨 CRITICAL: If user asks "what language" or "detect language" → USE detect_language (NOT translate)
If user asks "translate" or "to [language]" → USE translate (NOT detect_language)

Key distinction:
- detect_language → Returns language NAME ("french")
- translate → Returns TRANSLATED TEXT ("bonjour" → "hello")

---

🎯 CRITICAL FUNCTION DISAMBIGUATION RULE (v0.4.13) - EXPLAIN FUNCTIONS:

**explain_command** (shell commands):
- User wants to explain a SHELL COMMAND
- Command syntax present: flags (--, -), pipes (|), redirection (>, >>)
- Shell commands: rm, find, grep, chmod, dd, ls, cd, mv, cp, git, curl, wget, etc.
- Patterns: "explain [command]", "what does [command] do", "analyze this command"
- Keywords: explain + (shell/bash/command/terminal) OR command syntax present
- Examples:
  ✅ "explain rm -rf /" → explain_command
  ✅ "what does find . -name '*.py' do" → explain_command
  ✅ "analyze this command: ls -la" → explain_command
  ✅ "describe the shell command chmod 777" → explain_command
  ✅ "explain git status" → explain_command

**explain** (concepts):
- User asks about CONCEPT, IDEA, or TOPIC
- NO command syntax present
- General knowledge questions
- Examples:
  ✅ "explain machine learning" → explain
  ✅ "what is kubernetes" → explain
  ✅ "describe how DNS works" → explain
  ✅ "explain the concept of recursion" → explain

🚨 CRITICAL: If input contains shell command syntax (flags, pipes, shell commands) → USE explain_command
Shell syntax indicators:
- Flags: --, -, flags like -la, -rf, --help
- Pipes: |
- Redirection: >, >>, <
- Shell commands: rm, find, grep, chmod, dd, mkfs, ls, cd, mv, cp, cat, git, curl, wget, etc.

If BOTH "explain" keyword AND shell syntax present → ALWAYS use explain_command (NOT explain)

🚨 CRITICAL FUNCTION NAME VALIDATION (v0.6.2):
The "intent" field MUST be EXACTLY one of the function names listed in "Available Functions" above.
DO NOT create new function names, combine function names, or use variations.
DO NOT use: "streaming_shell_command", "enhanced_shell_command", or any unlisted names.

✅ VALID: "shell_command", "streaming_shell", "contextual_shell"
❌ INVALID: "streaming_shell_command", "enhanced_shell_command", "shell", "command"

If uncertain which shell function to use:
- "shell_command" → General shell command execution
- "streaming_shell" → Long-running commands with streaming output
- "contextual_shell" → Commands that use conversation context

Analyze the input and respond with JSON only:
{{
  "intent": "function_name",
  "confidence": 0.95,
  "parameters": {{"key": "value", "path": "contextual_path_if_applicable"}},
  "reasoning": "Why this function was selected and any contextual information used"
}}

Rules:
1. The "intent" field MUST match a function name from "Available Functions" EXACTLY
2. Confidence > 0.8 for direct execution
3. Confidence 0.5-0.8 requires user confirmation
4. Confidence < 0.5 requires clarification
5. Extract relevant parameters from the input
6. For contextual requests like "second largest", "now check", etc.:
   - Set search_request to a descriptive version like "find second largest file"
   - If LOCATION_CONTEXT shows a previous location, use that as the path parameter
   - Always include required parameters even if they need to be inferred from context
7. Consider the chat context when determining intent
8. Respond with valid JSON only, no additional text"""

        return prompt

    def _parse_llm_response(
        self, response: str, user_input: str, context: ChatContext | None = None
    ) -> RecognitionResult | None:
        """Parse LLM response into RecognitionResult"""
        try:
            # Clean response - sometimes LLMs add extra text
            response = response.strip()

            # Find JSON in response
            start_idx = response.find("{")
            end_idx = response.rfind("}") + 1

            if start_idx == -1 or end_idx == 0:
                return None

            json_str = response[start_idx:end_idx]
            data = json.loads(json_str)

            # Debug: Print what LLM generated for troubleshooting
            if "path" in data.get("parameters", {}):
                # LLM parameter mapping with path
                pass
            else:
                # LLM parameter mapping completed
                pass

            # Validate required fields
            if not all(key in data for key in ["intent", "confidence", "parameters"]):
                return None

            # v0.6.2: Validate that the intent matches a registered function
            intent = data["intent"]
            if self.function_registry:
                # Get all valid function names
                valid_functions = set(self.function_registry.plugins.keys())

                # Also include template function names
                template_functions = {t.function_name for t in self.intent_templates}
                valid_functions.update(template_functions)

                # Check if intent is valid
                if intent not in valid_functions:
                    if DEBUG_MODE:
                        print(f"❌ INVALID FUNCTION: LLM returned '{intent}' which is not in registry")
                        print(f"   Valid functions: {sorted(valid_functions)[:10]}...")

                    # Try to find closest match (common hallucinations)
                    hallucination_fixes = {
                        "streaming_shell_command": "streaming_shell",
                        "enhanced_shell_command": "shell_command",
                        "shell": "shell_command",
                        "command": "shell_command",
                    }

                    if intent in hallucination_fixes:
                        corrected = hallucination_fixes[intent]
                        if DEBUG_MODE:
                            print(f"   Auto-correcting '{intent}' → '{corrected}'")
                        intent = corrected
                        data["intent"] = corrected
                    else:
                        # Cannot correct - return None to trigger fallback
                        if DEBUG_MODE:
                            print(f"   No auto-correction available for '{intent}'")
                        return None

            confidence = float(data["confidence"])
            confidence = max(0.0, min(1.0, confidence))  # Clamp to 0-1 range

            # BULLETPROOF CONTEXT EXTRACTION - Override LLM with deterministic logic
            parameters = data.get("parameters", {})

            # v0.6.2: Normalize parameters for all shell function variants
            if data.get("intent") in ["shell_command", "streaming_shell", "contextual_shell"]:
                # Normalize shell parameters - LLM might return 'command' but function expects 'request'
                if "command" in parameters and "request" not in parameters:
                    parameters["request"] = parameters.pop("command")
                elif "request" not in parameters:
                    # Fallback: use the original user input
                    parameters["request"] = user_input.strip()

                # For shell functions, default execute to True (with confirmation) unless explicitly set
                if "execute" not in parameters:
                    parameters["execute"] = True

                if DEBUG_MODE: print(f"🔍 DEBUG: Normalized {data.get('intent')} parameters: {parameters}")

            # Fix parameter mapping for content generation
            if data.get("intent") == "content_generate":
                # If LLM didn't provide specification, create it from the original input
                if "specification" not in parameters:
                    parameters["specification"] = user_input
                # Map common LLM parameter names
                if "type" in parameters and "content_type" not in parameters:
                    parameters["content_type"] = parameters.pop("type")

                # Map content type variations to supported types
                if "content_type" in parameters:
                    content_type = str(parameters["content_type"]).lower()
                    content_type_mapping = {
                        # Direct mappings
                        "thank_you_note": "note",
                        "thanks": "note",
                        "note": "note",
                        "letter": "document",
                        "post": "message",
                        "tweet": "message",
                        "email": "email",
                        # Style/format mappings to content types
                        "technical": "document",
                        "professional": "document",
                        "casual": "text",
                        "formal": "document",
                        "business": "document",
                        "academic": "document",
                        "summary": "document",
                        "guide": "document",
                        "tutorial": "document",
                        "explanation": "text",
                        "overview": "document",
                    }

                    # Try direct mapping first
                    if content_type in content_type_mapping:
                        parameters["content_type"] = content_type_mapping[content_type]
                    else:
                        # Fallback to "auto" for any unrecognized content type
                        parameters["content_type"] = "auto"

                # Handle format parameter mapping
                if "format" in parameters:
                    format_val = str(parameters["format"]).lower()
                    format_mapping = {
                        "list": "structured",
                        "bullet": "structured",
                        "points": "structured",
                        "markdown": "markdown",
                        "md": "markdown",
                        "plain": "plain",
                        "text": "plain",
                    }
                    if format_val in format_mapping:
                        parameters["format"] = format_mapping[format_val]
                    else:
                        parameters["format"] = "auto"

                # Clean up any unrecognized parameters that might cause validation errors
                # Keep only parameters that content_generate function recognizes
                recognized_params = {
                    "content_type",
                    "specification",
                    "start_date",
                    "duration",
                    "format",
                }
                cleaned_parameters = {}

                for key, value in parameters.items():
                    if key in recognized_params:
                        cleaned_parameters[key] = value
                    else:
                        # Map common alternative parameter names
                        if key in ["topic", "subject", "theme"]:
                            if "specification" not in cleaned_parameters:
                                cleaned_parameters["specification"] = str(value)
                        elif key in ["style", "tone", "mode"]:
                            # Style/tone can affect format choice
                            if "format" not in cleaned_parameters:
                                if str(value).lower() in [
                                    "structured",
                                    "list",
                                    "points",
                                ]:
                                    cleaned_parameters["format"] = "structured"
                                else:
                                    cleaned_parameters["format"] = "auto"

                parameters = cleaned_parameters

            # Enhanced parameter mapping via registry
            parameters = self.enhancer_registry.enhance(
                function_name=data.get("intent"),
                parameters=parameters,
                user_input=user_input,
                context=context
            )

            return RecognitionResult(
                intent=data["intent"],
                confidence=confidence,
                parameters=parameters,
                function_name=data.get(
                    "intent"
                ),  # Use intent as function name by default
                requires_confirmation=confidence < 0.8,
                reasoning=data.get("reasoning", "LLM classification"),
                source=RouteSource.LLM_RECOGNITION,
            )

        except (json.JSONDecodeError, ValueError, KeyError) as e:
            print(f"Failed to parse LLM response: {e}")
            return None

    def _force_contextual_parameters(
        self,
        original_params: dict[str, Any],
        user_input: str,
        context: ChatContext | None = None,
    ) -> dict[str, Any]:
        """BULLETPROOF: Force correct contextual parameters regardless of LLM output"""

        # Copy original parameters
        params = original_params.copy()

        # Detect contextual patterns in user input
        user_lower = user_input.lower()
        contextual_patterns = [
            "second",
            "next",
            "another",
            "third",
            "now",
            "then",
            "also",
        ]
        detected_patterns = [
            pattern for pattern in contextual_patterns if pattern in user_lower
        ]
        is_contextual = len(detected_patterns) > 0

        if DEBUG_MODE: print(f"🔍 DEBUG: User input: '{user_input}'")
        if DEBUG_MODE: print(f"🔍 DEBUG: Detected contextual patterns: {detected_patterns}")
        if DEBUG_MODE: print(f"🔍 DEBUG: Is contextual: {is_contextual}")

        if is_contextual and context and context.messages:
            # DETERMINISTIC LOCATION EXTRACTION from chat history
            extracted_path = self._extract_location_from_chat_history(context)
            if DEBUG_MODE: print(f"🔍 DEBUG: Extracted path from chat history: {extracted_path}")

            if extracted_path:
                params["path"] = extracted_path
                if DEBUG_MODE: print(f"🔧 BULLETPROOF FIX: Forcing path parameter to {extracted_path}")
            else:
                if DEBUG_MODE: print("🔍 DEBUG: No path extracted from chat history")

            # Ensure search_request is present for contextual queries
            if "search_request" not in params or not params["search_request"]:
                if "second" in user_lower:
                    params["search_request"] = "find second largest file"
                elif "third" in user_lower:
                    params["search_request"] = "find third largest file"
                elif any(word in user_lower for word in ["next", "another"]):
                    params["search_request"] = "find next largest file"
                else:
                    params["search_request"] = user_input

        return params

    def _extract_location_from_chat_history(self, context: ChatContext) -> str | None:
        """DETERMINISTIC: Extract location from chat history and recent chat files"""
        import json
        import re
        from pathlib import Path

        # First try context messages
        recent_messages = context.get_recent_messages(5)
        # Debug: print(f"🔍 DEBUG: Examining {len(recent_messages)} context messages for path extraction")

        for message in reversed(recent_messages):
            content = message.content.lower()
            # Pattern 1: ~/Directory paths
            home_paths: list[str] = re.findall(
                r"~/[a-zA-Z][a-zA-Z0-9_-]*", message.content
            )
            if home_paths:
                if DEBUG_MODE: print(f"🔍 DEBUG: Found home path in context: {home_paths[-1]}")
                return home_paths[-1]

            # Pattern 2: Common directory names
            if "downloads" in content:
                if DEBUG_MODE: print("🔍 DEBUG: Found 'downloads' in context message")
                return "~/Downloads"

        # If no path found in context, check recent chat files on disk
        if DEBUG_MODE: print("🔍 DEBUG: No path in context, checking recent chat files on disk")
        try:
            chat_dir = Path.home() / ".aii"
            chat_files = list(chat_dir.glob("chat-*.json"))

            # Sort by modification time, newest first
            chat_files.sort(key=lambda f: f.stat().st_mtime, reverse=True)

            # Check the most recent 10 chat files
            for chat_file in chat_files[:10]:
                try:
                    if DEBUG_MODE: print(f"🔍 DEBUG: Checking chat file: {chat_file.name}")
                    with open(chat_file) as f:
                        chat_data = json.load(f)

                    for message in chat_data.get("messages", []):
                        content = message.get("content", "").lower()
                        if DEBUG_MODE: print(f"🔍 DEBUG: File message content: '{content[:50]}...'")

                        # Pattern 1: ~/Directory paths
                        chat_home_paths: list[str] = re.findall(
                            r"~/[a-zA-Z][a-zA-Z0-9_-]*", message.get("content", "")
                        )
                        if chat_home_paths:
                            print(
                                f"🔍 DEBUG: Found home path in recent chat file: {chat_home_paths[-1]}"
                            )
                            return chat_home_paths[-1]

                        # Pattern 2: Common directory names
                        if "downloads" in content:
                            if DEBUG_MODE: print(
                                f"🔍 DEBUG: Found 'downloads' in recent chat file: {chat_file.name}"
                            )
                            return "~/Downloads"
                except Exception as e:
                    if DEBUG_MODE: print(f"🔍 DEBUG: Error processing {chat_file.name}: {e}")
                    continue  # Skip corrupted files

        except Exception as e:
            if DEBUG_MODE: print(f"🔍 DEBUG: Error checking chat files: {e}")

        if DEBUG_MODE: print("🔍 DEBUG: No path found in context or recent chat files")
        return None

    def _get_function_descriptions(self) -> str:
        """Get descriptions of available functions"""
        descriptions = []

        # Add built-in intents
        for template in self.intent_templates:
            example = template.examples[0] if template.examples else "No example"
            descriptions.append(
                f'- {template.function_name}: {template.intent_name} (e.g., "{example}")'
            )

        # Add functions from registry if available
        # CRITICAL FIX: Use live plugin descriptions from self.plugins instead of stale FunctionDefinition
        if self.function_registry:
            try:
                # Get template function names to avoid duplicates
                template_functions = [t.function_name for t in self.intent_templates]

                # First priority: Use plugin descriptions (they have full enhanced descriptions)
                for func_name, plugin in self.function_registry.plugins.items():
                    if func_name not in template_functions:
                        # Get the LIVE description property from the plugin
                        descriptions.append(f"- {func_name}: {plugin.description}")

                # Fallback: Use FunctionDefinition for any functions without plugins
                for func_name, func_def in self.function_registry.functions.items():
                    if func_name not in template_functions and func_name not in self.function_registry.plugins:
                        descriptions.append(f"- {func_name}: {func_def.description}")
            except AttributeError:
                pass

        return "\\n".join(descriptions[:20])  # Limit to prevent prompt bloat

    def _extract_parameters(
        self, user_input: str, template: IntentTemplate
    ) -> dict[str, Any]:
        """Extract parameters from input based on template"""
        import re  # Import at the top of the function to avoid scoping issues

        parameters = {}

        # Basic parameter extraction patterns
        if template.function_name == "translate":
            # Extract target language

            lang_match = re.search(r"\\bto\\s+(\\w+)", user_input, re.IGNORECASE)
            if lang_match:
                parameters["target_language"] = lang_match.group(1).lower()

            # Extract text to translate (remove command words)
            text = user_input
            for pattern in ["translate", "to " + parameters.get("target_language", "")]:
                text = re.sub(pattern, "", text, flags=re.IGNORECASE)
            text = text.strip().strip('"').strip("'")
            if text:
                parameters["text"] = text

        elif template.function_name == "code_review":
            # Extract file path
            file_match = re.search(r"([\\w\\./]+\\.\\w+)", user_input)
            if file_match:
                parameters["file_path"] = file_match.group(1)

        elif template.function_name == "code_generate":
            # Extract specification for code/content generation
            # For content generation (tweets, posts, emails, etc.)
            if any(
                content_type in user_input.lower()
                for content_type in ["tweet", "post", "message", "content", "email"]
            ):
                # This is content generation, extract the full request as specification
                parameters["specification"] = user_input
                parameters["language"] = (
                    "text"  # Use 'text' to indicate non-code content
                )
            else:
                # This is code generation, extract code specification
                spec = user_input
                for keyword in [
                    "write",
                    "create",
                    "generate",
                    "code",
                    "function",
                    "script",
                    "program",
                ]:
                    spec = re.sub(rf"\\b{keyword}\\b", "", spec, flags=re.IGNORECASE)
                spec = spec.strip().strip('"').strip("'")
                if spec:
                    parameters["specification"] = spec

        elif template.function_name == "content_generate":
            # Extract parameters for flexible content generation
            # Extract the full request as specification
            parameters["specification"] = user_input

            # Detect content type from user input
            content_types = {
                "calendar": ["calendar", "schedule"],
                "list": ["list", "todo", "checklist"],
                "document": ["document", "doc", "report"],
                "message": ["message", "note"],
            }

            detected_type = "auto"
            for content_type, keywords in content_types.items():
                if any(keyword in user_input.lower() for keyword in keywords):
                    detected_type = content_type
                    break

            parameters["content_type"] = detected_type

            # Extract date if mentioned (YYYY-MM-DD format)
            date_match = re.search(r"(\d{4})-(\d{1,2})-(\d{1,2})", user_input)
            if date_match:
                parameters["start_date"] = date_match.group(0)

            # Extract duration
            duration_patterns = [
                r"for\s+(\d+\s+(?:month|week|day|year)s?)",
                r"(\d+\s+(?:month|week|day|year)s?)",
                r"(one\s+(?:month|week|day|year))",
                r"(1\s+(?:month|week|day|year))",
            ]
            for pattern in duration_patterns:
                duration_match = re.search(pattern, user_input, re.IGNORECASE)
                if duration_match:
                    parameters["duration"] = duration_match.group(1)
                    break

        elif template.function_name in ["explain", "summarize", "research"]:
            # v0.6.0: Pass FULL user input as topic to preserve constraints like "in 100 words"
            # The LLM will extract the actual topic and respect any constraints in the input
            parameters["topic"] = user_input.strip()
        elif template.function_name == "shell_command":
            # Extract request for shell command generation
            parameters["request"] = user_input.strip()
            # Check if user wants to execute (run, execute keywords)
            execute_keywords = ["run", "execute", "perform", "do"]
            user_lower = user_input.lower()
            should_execute = any(keyword in user_lower for keyword in execute_keywords)
            parameters["execute"] = should_execute
        elif template.intent_name == "enhanced_shell_command":
            # Extract request for enhanced shell command generation
            # Remove the trigger words to get the actual request
            cleaned_input = user_input
            for trigger in [
                "enhanced command to",
                "advanced command to",
                "smart command to",
                "ai command to",
                "enhanced",
                "advanced",
                "smart",
            ]:
                cleaned_input = re.sub(
                    rf"^{trigger}\s*", "", cleaned_input, flags=re.IGNORECASE
                )

            parameters["request"] = cleaned_input.strip()
            # Enhanced shell always executes by default
            parameters["execute"] = True
        elif template.function_name == "streaming_shell":
            # Extract request for streaming shell command generation
            # Remove streaming trigger words
            cleaned_input = user_input
            for trigger in [
                "streaming command to",
                "live command to",
                "stream",
                "streaming",
                "live",
                "real-time",
            ]:
                cleaned_input = re.sub(
                    rf"^{trigger}\s*", "", cleaned_input, flags=re.IGNORECASE
                )

            parameters["request"] = cleaned_input.strip()
            parameters["execute"] = True  # Always execute for streaming
            parameters["stream"] = True  # Enable streaming

        return parameters

    def _enhance_with_patterns(
        self, llm_result: RecognitionResult, pattern_result: RecognitionResult
    ) -> RecognitionResult:
        """Enhance LLM result with pattern validation"""
        # If both point to same function, boost confidence and merge parameters
        if llm_result.function_name == pattern_result.function_name:
            enhanced_confidence = min(1.0, llm_result.confidence + 0.15)
            # Use smart confirmation logic
            needs_confirmation, confirmation_reason = self.should_confirm_function(
                llm_result.function_name,
                enhanced_confidence,
                {**pattern_result.parameters, **llm_result.parameters},
            )

            return RecognitionResult(
                intent=llm_result.intent,
                confidence=enhanced_confidence,
                parameters={**pattern_result.parameters, **llm_result.parameters},
                function_name=llm_result.function_name,
                requires_confirmation=needs_confirmation,
                reasoning=f"LLM enhanced by pattern match: {llm_result.reasoning}. Confirmation: {confirmation_reason}",
                source=RouteSource.LLM_RECOGNITION,
            )

        # If they disagree but pattern has high confidence, consider hybrid approach
        if pattern_result.confidence >= 0.9:
            hybrid_confidence = (llm_result.confidence + pattern_result.confidence) / 2
            # Use smart confirmation logic
            needs_confirmation, confirmation_reason = self.should_confirm_function(
                pattern_result.function_name,
                hybrid_confidence,
                {**llm_result.parameters, **pattern_result.parameters},
            )

            return RecognitionResult(
                intent=pattern_result.intent,
                confidence=hybrid_confidence,
                parameters={**llm_result.parameters, **pattern_result.parameters},
                function_name=pattern_result.function_name,
                requires_confirmation=needs_confirmation,
                reasoning=f"Pattern validation over LLM: {pattern_result.intent} (pattern: {pattern_result.confidence:.2f}, llm: {llm_result.confidence:.2f}). Confirmation: {confirmation_reason}",
                source=RouteSource.LLM_RECOGNITION,
            )

        # Otherwise, trust the LLM result
        # Use smart confirmation logic for LLM result too
        needs_confirmation, confirmation_reason = self.should_confirm_function(
            llm_result.function_name, llm_result.confidence, llm_result.parameters
        )

        return RecognitionResult(
            intent=llm_result.intent,
            confidence=llm_result.confidence,
            parameters=llm_result.parameters,
            function_name=llm_result.function_name,
            requires_confirmation=needs_confirmation,
            reasoning=f"{llm_result.reasoning}. Confirmation: {confirmation_reason}",
            source=llm_result.source,
        )

    def _combine_results(
        self, direct_result: RecognitionResult, llm_result: RecognitionResult
    ) -> RecognitionResult:
        """Combine direct pattern match with LLM result"""
        # If both point to same function, boost confidence
        if direct_result.function_name == llm_result.function_name:
            combined_confidence = min(1.0, direct_result.confidence + 0.2)
            return RecognitionResult(
                intent=llm_result.intent,
                confidence=combined_confidence,
                parameters={**direct_result.parameters, **llm_result.parameters},
                function_name=llm_result.function_name,
                requires_confirmation=combined_confidence < 0.8,
                reasoning=f"Pattern match + LLM agreement: {llm_result.reasoning}",
                source=RouteSource.LLM_RECOGNITION,
            )

        # If different functions, prefer higher confidence
        if llm_result.confidence > direct_result.confidence:
            return llm_result
        else:
            return direct_result

    def should_confirm_function(
        self,
        function_name: str,
        confidence: float,
        parameters: dict[str, Any],
        user_context: dict[str, Any] | None = None,
    ) -> tuple[bool, str]:
        """Smart risk-based confirmation logic"""

        # Define function safety categories (can be moved to config later)
        FUNCTION_SAFETY = {
            # SAFE - No confirmation needed (or handles own confirmation internally)
            "explain": FunctionSafety.SAFE,
            "translate": FunctionSafety.SAFE,
            "content_generate": FunctionSafety.SAFE,
            "summarize": FunctionSafety.SAFE,
            "research": FunctionSafety.SAFE,  # read-only
            # Shell commands handle their own confirmation internally (v0.4.13 bugfix)
            "shell_command": FunctionSafety.SAFE,  # Handles own confirmation - no double prompt
            "streaming_shell": FunctionSafety.SAFE,  # Handles own confirmation - no double prompt
            # Git operations handle their own confirmation
            "git_commit": FunctionSafety.SAFE,  # Handles own confirmation with thinking mode preview
            "git_pr": FunctionSafety.SAFE,  # Handles own confirmation with PR preview
            "git_branch": FunctionSafety.SAFE,  # Handles own confirmation with branch preview
            # CONTEXT_DEPENDENT - Confirm based on confidence/context
            "code_generate": FunctionSafety.CONTEXT_DEPENDENT,
            "email_generate": FunctionSafety.CONTEXT_DEPENDENT,
        }

        safety_level = FUNCTION_SAFETY.get(
            function_name, FunctionSafety.CONTEXT_DEPENDENT
        )
        user_context = user_context or {}

        # SAFE functions never need confirmation
        if safety_level == FunctionSafety.SAFE:
            return False, "Safe function - no confirmation needed"

        # RISKY and DESTRUCTIVE functions always need confirmation
        if safety_level in [FunctionSafety.RISKY, FunctionSafety.DESTRUCTIVE]:
            risk_level = (
                "HIGH RISK"
                if safety_level == FunctionSafety.DESTRUCTIVE
                else "MEDIUM RISK"
            )
            return True, f"{risk_level} operation requires confirmation"

        # CONTEXT_DEPENDENT functions - decide based on confidence and context
        if safety_level == FunctionSafety.CONTEXT_DEPENDENT:
            # Low confidence always requires confirmation
            if confidence < 0.7:
                return True, f"Low confidence ({confidence:.0%}) requires confirmation"

            # Check for destructive operations in parameters
            destructive_indicators = [
                "rm",
                "del",
                "delete",
                "remove",
                "drop",
                "destroy",
                "format",
                "wipe",
                "clear",
                "reset",
                "--force",
                "-f",
                "sudo",
                "admin",
                "system",
                "critical",
            ]

            param_str = " ".join(str(v).lower() for v in parameters.values())
            if any(indicator in param_str for indicator in destructive_indicators):
                return True, "Potentially destructive operation detected"

            # Check context for previous risky operations
            if user_context.get("recent_risky_operation", False):
                return True, "Following previous risky operation - extra caution"

        return False, "Context assessment passed - no confirmation needed"

    def _is_universal_content_request(self, user_input: str) -> bool:
        """Check if the request should use universal orchestrator"""
        user_input_lower = user_input.lower()

        # Patterns that indicate universal content generation
        universal_patterns = [
            "generate me a tweet",
            "create a tweet",
            "write me an email",
            "generate an email",
            "create a post",
            "write a post",
            "generate content",
            "create content",
            "create a social media post",
            "generate a social media post",
            "write a social media post",
            "social media post about",
        ]

        # Also check for git context references
        git_context_patterns = [
            "per the latest git commit",
            "based on the latest commit",
            "from the last git commit",
            "using git history",
        ]

        has_universal_pattern = any(
            pattern in user_input_lower for pattern in universal_patterns
        )
        has_git_context = any(
            pattern in user_input_lower for pattern in git_context_patterns
        )

        return has_universal_pattern or (
            has_git_context
            and any(
                content in user_input_lower for content in ["tweet", "email", "post"]
            )
        )

    async def _route_to_universal_orchestrator(
        self, user_input: str, context: ChatContext | None = None
    ) -> RecognitionResult | None:
        """Route to universal orchestrator for content generation"""
        try:
            return RecognitionResult(
                intent="universal_content_generation",
                confidence=0.9,  # High confidence for universal routing
                parameters={"request": user_input},
                function_name="universal_generate",
                requires_confirmation=False,
                reasoning="Routed to universal orchestrator for context-aware content generation",
                source=RouteSource.LLM_RECOGNITION,
            )
        except Exception as e:
            print(f"Universal orchestrator routing failed: {e}")
            return None
