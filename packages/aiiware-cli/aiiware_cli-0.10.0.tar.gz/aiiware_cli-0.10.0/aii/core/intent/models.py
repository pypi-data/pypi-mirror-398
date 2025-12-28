# Copyright 2025-present AiiWare.com. All Rights Reserved.
#
# This source code is proprietary and confidential to AiiWare.com.
# Unauthorized copying, modification, distribution, or use is strictly
# prohibited without prior written permission.

"""Intent recognition models"""


import re
from dataclasses import dataclass, field


@dataclass
class IntentTemplate:
    """Template for intent recognition patterns"""

    intent_name: str
    function_name: str
    patterns: list[str]
    keywords: list[str] = field(default_factory=list)
    examples: list[str] = field(default_factory=list)
    confidence_boost: float = 0.0  # Additional confidence for direct pattern matches

    def matches_pattern(self, text: str) -> bool:
        """Check if text matches any of the patterns"""
        text_lower = text.lower().strip()

        for pattern in self.patterns:
            try:
                if re.search(pattern, text_lower, re.IGNORECASE):
                    return True
            except re.error:
                # Fallback to simple string matching if regex fails
                if pattern.lower() in text_lower:
                    return True

        return False

    def has_keywords(self, text: str) -> int:
        """Count how many keywords are present in text"""
        text_lower = text.lower()
        return sum(1 for keyword in self.keywords if keyword.lower() in text_lower)


# Predefined intent templates
BUILT_IN_INTENTS = [
    IntentTemplate(
        intent_name="git_commit",
        function_name="git_commit",
        patterns=[
            r"^git commit",
            r"^commit(?:\s+(?:my|the|staged|these))?\s+changes",
            r"^(?:make|do|perform)\s+(?:a\s+)?commit",
            r"^generate\s+(?:a\s+)?commit\s+message$",
            r"^commit\s+staged",
            r"^commit$",  # Single word commit command
        ],
        keywords=["commit", "git", "staged", "changes"],
        examples=[
            "commit my changes",
            "generate a commit message",
            "git commit",
            "commit staged changes",
            "commit",
        ],
        confidence_boost=0.1,  # Reduced confidence boost to allow LLM to override
    ),
    IntentTemplate(
        intent_name="git_diff",
        function_name="git_diff",
        patterns=[
            r"^git diff",
            r"^show\s+(?:me\s+)?(?:the\s+)?(?:git\s+)?diff",
            r"what\s+changed",
            r"show\s+(?:me\s+)?(?:the\s+)?changes",
            r"diff\s+(?:of\s+)?(?:the\s+)?(?:last\s+)?commit",
            r"what\s+(?:was\s+)?(?:in\s+)?(?:the\s+)?last\s+commit",
        ],
        keywords=["diff", "changed", "changes", "commit", "show", "git"],
        examples=[
            "git diff",
            "show me the diff",
            "what changed in the last commit",
            "show me the changes",
            "diff of the last commit",
        ],
        confidence_boost=0.15,
    ),
    IntentTemplate(
        intent_name="git_status",
        function_name="git_status",
        patterns=[
            r"^git status",
            r"^show\s+(?:me\s+)?(?:the\s+)?(?:git\s+)?status",
            r"what\s+(?:is\s+)?(?:the\s+)?status",
            r"repository\s+status",
        ],
        keywords=["status", "git", "repository", "working", "tree"],
        examples=[
            "git status",
            "show me the git status",
            "what is the status",
            "repository status",
        ],
        confidence_boost=0.15,
    ),
    IntentTemplate(
        intent_name="translate",
        function_name="translate",
        patterns=[
            r"^translate\b",
            r"translate\s+.+\s+to\s+(spanish|french|german|italian|portuguese|chinese|japanese|korean)",
            r"what does .+ mean in english",
            r"how do you say .+ in",
            r"convert\s+.+\s+to\s+(spanish|french|german|italian|portuguese|chinese|japanese|korean)",
        ],
        keywords=[
            "translate",
            "spanish",
            "french",
            "german",
            "italian",
            "portuguese",
            "chinese",
            "japanese",
            "korean",
            "language",
        ],
        examples=[
            "translate hello world to spanish",
            "what does bonjour mean in english",
            "how do you say hello in french",
        ],
    ),
    IntentTemplate(
        intent_name="code_review",
        function_name="code_review",
        patterns=[
            r"review\s+(?:this\s+)?code",
            r"code review",
            r"check\s+(?:this\s+)?code",
            r"analyze\s+(?:this\s+)?code",
            r"review\s+[\w\./]+\.(?:py|js|ts|java|cpp|c|go|rs|rb)",
        ],
        keywords=["review", "code", "analyze", "check", "security", "performance"],
        examples=[
            "review this code",
            "code review for main.py",
            "analyze this javascript code",
        ],
    ),
    IntentTemplate(
        intent_name="code_generate",
        function_name="code_generate",
        patterns=[
            r"write\s+(?:a\s+)?(?:function|code|script|program)",
            r"create\s+(?:a\s+)?(?:function|code|script|program)",
            r"generate\s+(?:a\s+)?(?:function|code|script|program)",
            r"code\s+(?:to\s+|for\s+|that\s+)",
        ],
        keywords=[
            "write",
            "create",
            "generate",
            "function",
            "code",
            "script",
            "program",
            "algorithm",
        ],
        examples=[
            "write a function to calculate fibonacci",
            "create a Python script to parse CSV",
            "generate code for sorting algorithm",
        ],
    ),
    IntentTemplate(
        intent_name="content_generate",
        function_name="content_generate",  # Use dedicated content_generate function
        patterns=[
            r"generate\s+(?:a\s+|me\s+(?:a\s+)?)?(?:tweet|post|message|text|content|email|calendar|list)",
            r"write\s+(?:a\s+|me\s+(?:a\s+)?)?(?:tweet|post|message|text|email)",
            r"create\s+(?:a\s+|me\s+(?:a\s+)?)?(?:tweet|post|message|text|email|calendar|list)",
            r"make\s+(?:a\s+|me\s+(?:a\s+)?)?(?:tweet|post|message|email|calendar|list)",
            r"compose\s+(?:a\s+)?(?:tweet|post|message|email)",
            r"generate\s+me\s+(?:a\s+)?.*(?:list|calendar|content|document)",
        ],
        keywords=[
            "generate",
            "write",
            "create",
            "make",
            "compose",
            "tweet",
            "post",
            "message",
            "content",
            "text",
            "email",
            "calendar",
            "schedule",
            "list",
            "shopping",
            "social",
            "media",
        ],
        examples=[
            "generate a tweet about my project",
            "write me a tweet with emojis",
            "create a social media post",
            "generate me a Tweet with proper emoji and hashtag per the latest git commit",
            "generate a Email message per the last git commit",
        ],
        confidence_boost=0.2,
    ),
    IntentTemplate(
        intent_name="explain",
        function_name="explain",
        patterns=[
            r"explain\b",
            r"what\s+(?:is|are|does|do)\b",
            r"how\s+(?:does|do|to)\b",
            r"tell\s+me\s+about",
            r"describe\b",
        ],
        keywords=["explain", "what", "how", "describe", "tell", "about", "why"],
        examples=[
            "explain machine learning",
            "what is docker",
            "how does git work",
            "describe the algorithm",
        ],
    ),
    IntentTemplate(
        intent_name="summarize",
        function_name="summarize",
        patterns=[
            r"summarize\b",
            r"summary\s+of",
            r"sum\s+up",
            r"\btldr\b",
            r"give\s+me\s+(?:a\s+)?(?:summary|overview)",
            r"summarize.*in\s+(chinese|english|spanish|french|german|italian|portuguese|japanese|korean)",
            r"create\s+(?:a\s+)?summary.*in\s+(chinese|english|spanish|french|german|italian|portuguese|japanese|korean)",
            r"summarize.*output\s+in\s+(chinese|english|spanish|french|german|italian|portuguese|japanese|korean)",
        ],
        keywords=["summarize", "summary", "tldr", "overview", "brief"],
        examples=[
            "summarize this document",
            "give me a summary of the article",
            "tldr this content",
            "summarize in Chinese",
            "create a summary in Chinese",
        ],
        confidence_boost=0.4,  # High boost to compete with translation intent
    ),
    IntentTemplate(
        intent_name="research",
        function_name="research",
        patterns=[
            r"research\b",
            r"find\s+(?:information|info)\s+about",
            r"search\s+for",
            r"look\s+up",
            r"what\s+(?:is|are)\s+the\s+latest",
        ],
        keywords=[
            "research",
            "find",
            "search",
            "information",
            "latest",
            "current",
            "trends",
        ],
        examples=[
            "research the latest trends in AI",
            "find information about quantum computing",
            "search for recent developments in blockchain",
        ],
    ),
    IntentTemplate(
        intent_name="analyze_data",
        function_name="analyze_data",
        patterns=[
            r"analyze\s+(?:this\s+)?data",
            r"data\s+analysis",
            r"examine\s+(?:the\s+)?(?:data|dataset|file)",
            r"parse\s+(?:this\s+)?(?:csv|json|xml)",
        ],
        keywords=["analyze", "data", "dataset", "parse", "examine", "statistics"],
        examples=[
            "analyze this CSV file",
            "perform data analysis on the dataset",
            "examine the data in results.json",
        ],
    ),
    IntentTemplate(
        intent_name="help",
        function_name="help",
        patterns=[
            r"^help$",
            r"^\?$",
            r"what\s+can\s+you\s+do",
            r"show\s+(?:me\s+)?(?:help|commands)",
            r"how\s+do\s+i\s+use",
        ],
        keywords=["help", "commands", "usage", "guide", "how"],
        examples=["help", "what can you do", "show me available commands"],
        confidence_boost=0.3,  # Boost help confidence to avoid confirmation
    ),
    IntentTemplate(
        intent_name="shell_command",
        function_name="shell_command",
        patterns=[
            r"^(?:run|execute|shell|command|cmd)\s+",
            r"^ls\s+",
            r"^grep\s+",
            r"^(?:show|display)\s+.*(?:process|service|system)",
        ],
        keywords=[
            "run",
            "execute",
            "shell",
            "command",
            "cmd",
            "ls",
            "grep",
            "process",
            "service",
            "system",
            "terminal",
        ],
        examples=[
            "run ls -la in current directory",
            "execute ps aux to show processes",
            "shell command to check disk usage",
        ],
        confidence_boost=0.2,
    ),
    IntentTemplate(
        intent_name="enhanced_shell_command",
        function_name="shell_command",
        patterns=[
            r"^(?:enhanced|advanced|smart)\s+(?:shell\s+)?command",
            r"^use\s+(?:advanced|enhanced|smart)\s+tools?",
            r"^(?:ai|intelligent)\s+command",
            r"^structured\s+command",
            r"^pydantic\s+(?:ai\s+)?command",
        ],
        keywords=[
            "enhanced",
            "advanced",
            "smart",
            "ai",
            "intelligent",
            "pydantic",
            "structured",
            "tool",
            "calling",
            "native",
        ],
        examples=[
            "enhanced command to find largest files",
            "advanced shell operation for disk analysis",
            "smart command with tool calling",
            "ai-powered shell command",
            "pydantic ai command",
        ],
        confidence_boost=0.3,  # Higher boost for enhanced features
    ),
    IntentTemplate(
        intent_name="streaming_shell_command",
        function_name="streaming_shell",
        patterns=[
            r"^(?:stream|streaming|live|real[- ]time)\s+(?:shell\s+)?command",
            r"^(?:shell\s+)?command\s+with\s+(?:streaming|live|real[- ]time)",
            r"^interactive\s+(?:shell\s+)?command",
            r"^live\s+feedback\s+command",
        ],
        keywords=[
            "stream",
            "streaming",
            "live",
            "real-time",
            "interactive",
            "feedback",
            "progress",
            "watch",
            "monitor",
        ],
        examples=[
            "streaming command to find largest files",
            "live shell command with real-time feedback",
            "interactive command generation",
            "stream command execution progress",
        ],
        confidence_boost=0.4,  # Highest boost for streaming features
    ),
]
