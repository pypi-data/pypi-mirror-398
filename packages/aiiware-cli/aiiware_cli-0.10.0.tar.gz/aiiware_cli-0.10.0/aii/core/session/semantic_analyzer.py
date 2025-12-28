# Copyright 2025-present AiiWare.com. All Rights Reserved.
#
# This source code is proprietary and confidential to AiiWare.com.
# Unauthorized copying, modification, distribution, or use is strictly
# prohibited without prior written permission.

"""Semantic Analysis Engine - LLM-powered session outcome analysis"""


import json
import logging
import time
from dataclasses import dataclass
from typing import Any, Optional, Dict, List

from .manager import SessionManager
from .models import SessionMetrics, FunctionExecution
from ..performance.cache_manager import get_token_cache, get_prompt_cache
from ..error_handling import (
    get_error_handler, get_fallback_manager, get_retry_manager,
    with_retry, LLM_PROVIDER_RETRY
)

logger = logging.getLogger(__name__)


@dataclass
class SessionInsights:
    """Structured insights from semantic analysis"""

    # Core analysis
    session_summary: str
    user_intent_clarity: float  # 0.0 - 1.0
    task_completion_quality: float  # 0.0 - 1.0

    # Function analysis
    function_efficiency: str  # "excellent", "good", "needs_improvement"
    unexpected_behaviors: List[str]
    optimization_suggestions: List[str]

    # User experience
    user_satisfaction_estimate: float  # 0.0 - 1.0
    learning_opportunities: List[str]

    # Technical metrics
    token_efficiency: str  # "optimal", "acceptable", "wasteful"
    performance_notes: List[str]

    # Analysis metadata
    analysis_confidence: float  # 0.0 - 1.0
    analysis_tokens_used: int
    fallback_mode: bool = False


class SessionSemanticAnalyzer:
    """LLM-powered analyzer for session outcomes with self-tracking"""

    def __init__(self, llm_provider: Any):
        """Initialize with LLM provider"""
        self.llm_provider = llm_provider

    async def analyze_session_outcomes(
        self,
        user_input: str,
        session: SessionMetrics
    ) -> SessionInsights:
        """
        Analyze session outcomes using LLM

        CRITICAL: This method tracks its own token consumption in the session
        """
        if not self.llm_provider:
            return self._generate_fallback_insights(session)

        start_time = time.time()

        try:
            # Build analysis prompt
            analysis_prompt = self._build_analysis_prompt(user_input, session)

            # Check prompt cache first for performance
            prompt_cache = get_prompt_cache()
            model_name = getattr(self.llm_provider, 'model_name', 'unknown')

            cached_response = prompt_cache.get_prompt_response(analysis_prompt, model_name)
            if cached_response:
                # Use cached response - significant performance improvement
                analysis_content = cached_response['content']
                usage = cached_response['usage']
                insights = self._parse_insights(analysis_content, usage)
                # Mark as cached to avoid double-counting tokens
                insights.analysis_tokens_used = 0
            else:
                # Get LLM analysis with token tracking
                if hasattr(self.llm_provider, 'complete_with_usage'):
                    llm_response = await self.llm_provider.complete_with_usage(analysis_prompt)
                    usage = llm_response.usage or {}
                    analysis_content = llm_response.content
                else:
                    # Fallback for providers without usage tracking
                    analysis_content = await self.llm_provider.complete(analysis_prompt)
                    usage = {
                        'input_tokens': self._estimate_tokens(analysis_prompt),
                        'output_tokens': self._estimate_tokens(analysis_content),
                        'total_tokens': 0
                    }
                    usage['total_tokens'] = usage['input_tokens'] + usage['output_tokens']

                # Parse insights from LLM response
                insights = self._parse_insights(analysis_content, usage)

                # Cache the response for future sessions with similar patterns
                prompt_cache.put_prompt_response(analysis_prompt, model_name, {
                    'content': analysis_content,
                    'usage': usage
                })

            # Track the analysis itself as a function execution
            analysis_execution = FunctionExecution(
                function_name="semantic_analysis",
                start_time=start_time,
                end_time=time.time(),
                input_tokens=usage.get('input_tokens', 0),
                output_tokens=usage.get('output_tokens', 0),
                reasoning_tokens=usage.get('reasoning_tokens', 0),
                success=True,
                confidence=insights.analysis_confidence,
                artifacts=["session_insights"]
            )

            # Add to current session (self-tracking!)
            current_session = SessionManager.get_current_session()
            if current_session:
                current_session.add_function_execution(analysis_execution)

            return insights

        except Exception as e:
            # Use comprehensive error handling and fallback
            logger.warning(f"Semantic analysis failed: {e}")

            # Try fallback strategies
            fallback_result = await self._handle_analysis_failure(e, user_input, session, start_time)
            if fallback_result:
                return fallback_result

            # If all fallbacks fail, track the error and return minimal insights
            error_execution = FunctionExecution(
                function_name="semantic_analysis",
                start_time=start_time,
                end_time=time.time(),
                input_tokens=0,
                output_tokens=0,
                reasoning_tokens=0,
                success=False,
                confidence=0.0,
                artifacts=[]
            )

            current_session = SessionManager.get_current_session()
            if current_session:
                current_session.add_function_execution(error_execution)

            # Return basic fallback insights
            return self._generate_fallback_insights(session)

    async def _handle_analysis_failure(self, error: Exception, user_input: str,
                                     session: SessionMetrics, start_time: float) -> Optional[SessionInsights]:
        """Handle semantic analysis failure with comprehensive fallback strategies"""
        error_handler = get_error_handler()
        fallback_manager = get_fallback_manager()

        # Classify the error and determine recovery strategy
        error_context = error_handler.classify_error(error, "semantic_analysis")

        # Try fallback strategies
        fallback_context = {
            'operation': 'semantic_analysis',
            'user_input': user_input,
            'session': session,
            'model': self.llm_provider.model_name if self.llm_provider else 'unknown'
        }

        try:
            fallback_result = await fallback_manager.execute_fallback(error, fallback_context)

            if fallback_result.success:
                logger.info(f"Using fallback strategy: {fallback_result.strategy_used}")

                # Track successful fallback execution
                fallback_execution = FunctionExecution(
                    function_name="semantic_analysis_fallback",
                    start_time=start_time,
                    end_time=time.time(),
                    input_tokens=0,  # No new tokens used
                    output_tokens=0,
                    reasoning_tokens=0,
                    success=True,
                    confidence=0.7,  # Moderate confidence for fallback
                    artifacts=[f"fallback_{fallback_result.strategy_used}"]
                )

                current_session = SessionManager.get_current_session()
                if current_session:
                    current_session.add_function_execution(fallback_execution)

                # Convert fallback result to SessionInsights
                if isinstance(fallback_result.result, dict):
                    return self._convert_fallback_to_insights(fallback_result.result, session)

        except Exception as fallback_error:
            logger.error(f"Fallback strategies failed: {fallback_error}")

        # Try retry with exponential backoff if appropriate
        if error_context.category.value in ['network', 'llm_provider']:
            try:
                retry_manager = get_retry_manager()
                retry_result = await retry_manager.retry_async(
                    self._attempt_analysis_with_retry,
                    LLM_PROVIDER_RETRY,
                    user_input,
                    session
                )

                if retry_result.success:
                    logger.info(f"Analysis succeeded after {retry_result.attempts} attempts")
                    return retry_result.result

            except Exception as retry_error:
                logger.error(f"Retry attempts failed: {retry_error}")

        return None

    async def _attempt_analysis_with_retry(self, user_input: str, session: SessionMetrics) -> SessionInsights:
        """Attempt analysis for retry mechanism - simplified version"""
        if not self.llm_provider:
            raise ValueError("LLM provider not available")

        analysis_prompt = self._build_analysis_prompt(user_input, session)

        # Use simplified prompt for retries to reduce token usage
        simplified_prompt = f"""Analyze this session briefly:
User: {user_input[:200]}...
Functions: {session.total_functions}, Success: {session.success_rate:.1f}
Provide JSON: {{"summary": "brief summary", "confidence": 0.8}}"""

        response = await self.llm_provider.complete_with_usage(simplified_prompt)

        try:
            analysis_data = json.loads(response.content)
            return SessionInsights(
                session_summary=analysis_data.get('summary', 'Session analyzed'),
                user_intent_clarity=analysis_data.get('confidence', 0.7),
                task_completion_quality=session.success_rate,
                function_efficiency="good",
                unexpected_behaviors=[],
                optimization_suggestions=[],
                user_satisfaction_estimate=analysis_data.get('confidence', 0.7),
                learning_opportunities=[],
                token_efficiency="acceptable",
                performance_notes=["retry_analysis"],
                analysis_confidence=analysis_data.get('confidence', 0.7),
                analysis_tokens_used=response.usage.get('total_tokens', 0),
                fallback_mode=False
            )
        except (json.JSONDecodeError, KeyError):
            raise ValueError("Invalid analysis response format")

    def _convert_fallback_to_insights(self, fallback_data: Dict[str, Any], session: SessionMetrics) -> SessionInsights:
        """Convert fallback response data to SessionInsights"""
        if fallback_data.get('minimal_mode'):
            return self._generate_fallback_insights(session)

        # Handle cached response fallback
        if fallback_data.get('cached'):
            try:
                cached_content = fallback_data.get('content', '{}')
                if isinstance(cached_content, str):
                    analysis_data = json.loads(cached_content)
                else:
                    analysis_data = cached_content

                return self._parse_insights(json.dumps(analysis_data), fallback_data.get('usage', {}))
            except (json.JSONDecodeError, KeyError):
                logger.warning("Failed to parse cached analysis data")

        # Handle local analysis fallback
        if fallback_data.get('fallback_mode') == 'local_analysis':
            return SessionInsights(
                session_summary=fallback_data.get('session_summary', 'Local analysis completed'),
                user_intent_clarity=0.7,
                task_completion_quality=session.success_rate,
                function_efficiency=fallback_data.get('insights', {}).get('performance_rating', 'good'),
                unexpected_behaviors=[],
                optimization_suggestions=[],
                user_satisfaction_estimate=0.7,
                learning_opportunities=[],
                token_efficiency=fallback_data.get('insights', {}).get('cost_efficiency', 'moderate'),
                performance_notes=["local_analysis"],
                analysis_confidence=fallback_data.get('analysis_confidence', 0.6),
                analysis_tokens_used=0,
                fallback_mode=True
            )

        # Default fallback
        return self._generate_fallback_insights(session)

    def _build_analysis_prompt(self, user_input: str, session: SessionMetrics) -> str:
        """Build optimized analysis prompt for LLM - performance focused"""

        # Gather essential session context only
        total_functions = session.total_functions
        successful_functions = session.successful_functions
        success_rate = session.success_rate
        total_tokens = session.total_tokens
        total_time = time.time() - session.start_time

        # Simplified function summary (not full details for performance)
        function_names = [exec.function_name for exec in session.function_executions]
        avg_confidence = sum(
            exec.confidence for exec in session.function_executions
            if exec.confidence is not None
        ) / max(len(session.function_executions), 1)

        # Optimized prompt - more focused, fewer tokens
        prompt = f"""Analyze this AI session briefly:

USER: "{user_input}"
FUNCTIONS: {', '.join(function_names[:3])}{'...' if len(function_names) > 3 else ''}
SUCCESS: {successful_functions}/{total_functions} ({success_rate:.0%})
TOKENS: {total_tokens}, TIME: {total_time:.1f}s, CONFIDENCE: {avg_confidence:.1f}

Respond with JSON only:
{{
    "session_summary": "Brief outcome",
    "user_intent_clarity": {min(avg_confidence + 0.1, 1.0):.1f},
    "task_completion_quality": {success_rate:.1f},
    "function_efficiency": "{'excellent' if success_rate >= 0.9 else 'good' if success_rate >= 0.7 else 'needs_improvement'}",
    "optimization_suggestions": ["1-2 key suggestions"],
    "token_efficiency": "{'optimal' if total_tokens < 500 else 'acceptable' if total_tokens < 1500 else 'wasteful'}",
    "analysis_confidence": 0.8
}}"""

        return prompt

    def _parse_insights(self, response: str, usage: Dict[str, int]) -> SessionInsights:
        """Parse LLM response into structured insights"""
        try:
            # Extract JSON from response
            response = response.strip()
            if response.startswith('```json'):
                response = response[7:]
            if response.endswith('```'):
                response = response[:-3]

            data = json.loads(response)

            # Create insights with parsed data
            insights = SessionInsights(
                session_summary=data.get('session_summary', 'Session completed'),
                user_intent_clarity=float(data.get('user_intent_clarity', 0.8)),
                task_completion_quality=float(data.get('task_completion_quality', 0.8)),
                function_efficiency=data.get('function_efficiency', 'good'),
                unexpected_behaviors=data.get('unexpected_behaviors', []),
                optimization_suggestions=data.get('optimization_suggestions', []),
                user_satisfaction_estimate=float(data.get('user_satisfaction_estimate', 0.8)),
                learning_opportunities=data.get('learning_opportunities', []),
                token_efficiency=data.get('token_efficiency', 'acceptable'),
                performance_notes=data.get('performance_notes', []),
                analysis_confidence=float(data.get('analysis_confidence', 0.8)),
                analysis_tokens_used=usage.get('total_tokens', 0),
                fallback_mode=False
            )

            return insights

        except (json.JSONDecodeError, KeyError, ValueError) as e:
            # JSON parsing failed, create basic insights
            return SessionInsights(
                session_summary="Analysis parsing failed, using basic metrics",
                user_intent_clarity=0.7,
                task_completion_quality=0.7,
                function_efficiency="good",
                unexpected_behaviors=["JSON parsing error in analysis"],
                optimization_suggestions=["Improve analysis prompt"],
                user_satisfaction_estimate=0.7,
                learning_opportunities=[],
                token_efficiency="acceptable",
                performance_notes=["Analysis parsing failed"],
                analysis_confidence=0.5,
                analysis_tokens_used=usage.get('total_tokens', 0),
                fallback_mode=True
            )

    def _generate_fallback_insights(self, session: SessionMetrics) -> SessionInsights:
        """Generate basic insights when LLM unavailable"""

        # Calculate basic metrics
        success_rate = session.success_rate
        avg_confidence = sum(
            exec.confidence for exec in session.function_executions
            if exec.confidence is not None
        ) / max(len(session.function_executions), 1)

        # Determine efficiency based on metrics
        if success_rate >= 0.9 and avg_confidence >= 0.8:
            efficiency = "excellent"
            satisfaction = 0.9
        elif success_rate >= 0.7 and avg_confidence >= 0.6:
            efficiency = "good"
            satisfaction = 0.75
        else:
            efficiency = "needs_improvement"
            satisfaction = 0.6

        # Generate basic suggestions
        suggestions = []
        if success_rate < 1.0:
            suggestions.append("Review failed function executions")
        if avg_confidence < 0.8:
            suggestions.append("Consider more specific user requests")
        if session.total_tokens > 1000:
            suggestions.append("Monitor token usage for cost optimization")

        return SessionInsights(
            session_summary=f"Session completed with {session.total_functions} functions",
            user_intent_clarity=min(avg_confidence + 0.1, 1.0),
            task_completion_quality=success_rate,
            function_efficiency=efficiency,
            unexpected_behaviors=[],
            optimization_suggestions=suggestions,
            user_satisfaction_estimate=satisfaction,
            learning_opportunities=[],
            token_efficiency="acceptable" if session.total_tokens < 500 else "review_needed",
            performance_notes=[],
            analysis_confidence=0.6,
            analysis_tokens_used=0,
            fallback_mode=True
        )

    def _estimate_tokens(self, text: str) -> int:
        """Estimate token count using cached estimation"""
        token_cache = get_token_cache()
        return token_cache.estimate_tokens_with_cache(text)
