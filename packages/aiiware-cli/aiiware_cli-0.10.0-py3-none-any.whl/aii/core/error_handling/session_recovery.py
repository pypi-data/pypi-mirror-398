# Copyright 2025-present AiiWare.com. All Rights Reserved.
#
# This source code is proprietary and confidential to AiiWare.com.
# Unauthorized copying, modification, distribution, or use is strictly
# prohibited without prior written permission.

"""Session corruption detection and recovery system"""


import asyncio
import json
import logging
import os
import shutil
import sqlite3
import time
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional, Set, Tuple
from threading import Lock

from ..session.models import SessionMetrics, FunctionExecution

logger = logging.getLogger(__name__)


class RecoveryAction(Enum):
    """Available recovery actions for corrupted sessions"""
    REPAIR_IN_PLACE = "repair_in_place"      # Fix corruption without losing data
    RESTORE_FROM_BACKUP = "restore_from_backup"  # Use backup copy
    REBUILD_FROM_LOGS = "rebuild_from_logs"  # Reconstruct from execution logs
    CREATE_NEW = "create_new"                # Start fresh session
    GRACEFUL_DEGRADATION = "graceful_degradation"  # Continue with limited data


@dataclass
class CorruptionReport:
    """Report of detected session corruption"""
    session_id: str
    corruption_type: str
    severity: str  # low, medium, high, critical
    affected_components: List[str]
    recoverable: bool
    recommended_action: RecoveryAction
    details: Dict[str, Any] = field(default_factory=dict)
    timestamp: float = field(default_factory=time.time)


@dataclass
class RecoveryPlan:
    """Plan for recovering from session corruption"""
    corruption_report: CorruptionReport
    primary_action: RecoveryAction
    fallback_actions: List[RecoveryAction]
    estimated_data_loss: float  # Percentage
    recovery_steps: List[str]
    requires_user_confirmation: bool = False


class SessionCorruptionDetector:
    """Detects various types of session corruption"""

    def __init__(self):
        self._known_corruptions = set()

    def detect_corruption(self, session: SessionMetrics) -> Optional[CorruptionReport]:
        """Detect corruption in a session"""
        corruptions = []

        # Check for data inconsistencies
        corruptions.extend(self._check_data_consistency(session))

        # Check for incomplete data
        corruptions.extend(self._check_completeness(session))

        # Check for invalid states
        corruptions.extend(self._check_state_validity(session))

        if not corruptions:
            return None

        # Return the most severe corruption
        most_severe = max(corruptions, key=lambda c: self._severity_score(c.severity))
        return most_severe

    def _check_data_consistency(self, session: SessionMetrics) -> List[CorruptionReport]:
        """Check for data consistency issues"""
        corruptions = []

        # Check token count consistency
        calculated_tokens = sum(
            exec.input_tokens + exec.output_tokens + exec.reasoning_tokens
            for exec in session.function_executions
        )
        if abs(calculated_tokens - session.total_tokens) > 10:  # Allow small discrepancy
            corruptions.append(CorruptionReport(
                session_id=session.session_id,
                corruption_type="token_count_mismatch",
                severity="medium",
                affected_components=["token_tracking"],
                recoverable=True,
                recommended_action=RecoveryAction.REPAIR_IN_PLACE,
                details={
                    "calculated_tokens": calculated_tokens,
                    "recorded_tokens": session.total_tokens,
                    "discrepancy": abs(calculated_tokens - session.total_tokens)
                }
            ))

        # Check function count consistency
        if len(session.function_executions) != session.total_functions:
            corruptions.append(CorruptionReport(
                session_id=session.session_id,
                corruption_type="function_count_mismatch",
                severity="high",
                affected_components=["function_tracking"],
                recoverable=True,
                recommended_action=RecoveryAction.REPAIR_IN_PLACE,
                details={
                    "execution_count": len(session.function_executions),
                    "recorded_count": session.total_functions
                }
            ))

        # Check success rate consistency
        actual_successes = sum(1 for exec in session.function_executions if exec.success)
        if actual_successes != session.successful_functions:
            corruptions.append(CorruptionReport(
                session_id=session.session_id,
                corruption_type="success_count_mismatch",
                severity="medium",
                affected_components=["success_tracking"],
                recoverable=True,
                recommended_action=RecoveryAction.REPAIR_IN_PLACE,
                details={
                    "actual_successes": actual_successes,
                    "recorded_successes": session.successful_functions
                }
            ))

        return corruptions

    def _check_completeness(self, session: SessionMetrics) -> List[CorruptionReport]:
        """Check for incomplete or missing data"""
        corruptions = []

        # Check for missing required fields
        if not session.session_id:
            corruptions.append(CorruptionReport(
                session_id="unknown",
                corruption_type="missing_session_id",
                severity="critical",
                affected_components=["session_identity"],
                recoverable=False,
                recommended_action=RecoveryAction.CREATE_NEW
            ))

        if not session.user_input:
            corruptions.append(CorruptionReport(
                session_id=session.session_id,
                corruption_type="missing_user_input",
                severity="medium",
                affected_components=["session_context"],
                recoverable=True,
                recommended_action=RecoveryAction.GRACEFUL_DEGRADATION
            ))

        # Check for incomplete function executions
        incomplete_executions = [
            exec for exec in session.function_executions
            if not exec.function_name or exec.start_time is None or exec.end_time is None
        ]
        if incomplete_executions:
            corruptions.append(CorruptionReport(
                session_id=session.session_id,
                corruption_type="incomplete_executions",
                severity="high",
                affected_components=["function_executions"],
                recoverable=True,
                recommended_action=RecoveryAction.REPAIR_IN_PLACE,
                details={"incomplete_count": len(incomplete_executions)}
            ))

        return corruptions

    def _check_state_validity(self, session: SessionMetrics) -> List[CorruptionReport]:
        """Check for invalid state conditions"""
        corruptions = []

        # Check for negative values
        if (session.total_input_tokens < 0 or session.total_output_tokens < 0 or
            session.total_reasoning_tokens < 0 or session.total_cost < 0):
            corruptions.append(CorruptionReport(
                session_id=session.session_id,
                corruption_type="negative_values",
                severity="high",
                affected_components=["metrics"],
                recoverable=True,
                recommended_action=RecoveryAction.REPAIR_IN_PLACE,
                details={
                    "negative_input_tokens": session.total_input_tokens < 0,
                    "negative_output_tokens": session.total_output_tokens < 0,
                    "negative_reasoning_tokens": session.total_reasoning_tokens < 0,
                    "negative_cost": session.total_cost < 0
                }
            ))

        # Check for invalid timestamps
        if session.start_time > time.time() or (session.end_time and session.end_time < session.start_time):
            corruptions.append(CorruptionReport(
                session_id=session.session_id,
                corruption_type="invalid_timestamps",
                severity="high",
                affected_components=["timing"],
                recoverable=True,
                recommended_action=RecoveryAction.REPAIR_IN_PLACE,
                details={
                    "start_time": session.start_time,
                    "end_time": session.end_time,
                    "current_time": time.time()
                }
            ))

        # Check for impossible success rates
        if session.total_functions > 0:
            calculated_rate = session.successful_functions / session.total_functions
            if abs(calculated_rate - session.success_rate) > 0.01:  # Allow small floating point errors
                corruptions.append(CorruptionReport(
                    session_id=session.session_id,
                    corruption_type="invalid_success_rate",
                    severity="medium",
                    affected_components=["success_tracking"],
                    recoverable=True,
                    recommended_action=RecoveryAction.REPAIR_IN_PLACE,
                    details={
                        "calculated_rate": calculated_rate,
                        "recorded_rate": session.success_rate
                    }
                ))

        return corruptions

    def _severity_score(self, severity: str) -> int:
        """Convert severity to numeric score for comparison"""
        scores = {"low": 1, "medium": 2, "high": 3, "critical": 4}
        return scores.get(severity, 0)


class SessionRecoveryManager:
    """Manages session recovery operations"""

    def __init__(self, backup_dir: Optional[str] = None):
        self.backup_dir = backup_dir or os.path.expanduser("~/.aii/session_backups")
        self.detector = SessionCorruptionDetector()
        self._lock = Lock()
        self._recovery_history: List[Dict[str, Any]] = []
        self._ensure_backup_dir()

    def _ensure_backup_dir(self):
        """Ensure backup directory exists"""
        os.makedirs(self.backup_dir, exist_ok=True)

    async def check_and_recover_session(self, session: SessionMetrics) -> Tuple[SessionMetrics, Optional[CorruptionReport]]:
        """Check session for corruption and recover if needed"""
        corruption_report = self.detector.detect_corruption(session)

        if not corruption_report:
            return session, None

        logger.warning(f"Session corruption detected: {corruption_report.corruption_type}")

        # Create recovery plan
        recovery_plan = self._create_recovery_plan(corruption_report)

        # Execute recovery
        recovered_session = await self._execute_recovery(session, recovery_plan)

        # Record recovery attempt
        self._record_recovery(corruption_report, recovery_plan, recovered_session is not None)

        return recovered_session or session, corruption_report

    def _create_recovery_plan(self, corruption_report: CorruptionReport) -> RecoveryPlan:
        """Create a recovery plan based on corruption report"""
        primary_action = corruption_report.recommended_action
        fallback_actions = []

        # Define fallback sequence based on corruption type
        if corruption_report.corruption_type in ["token_count_mismatch", "function_count_mismatch"]:
            fallback_actions = [RecoveryAction.REPAIR_IN_PLACE, RecoveryAction.GRACEFUL_DEGRADATION]
            estimated_loss = 0.0

        elif corruption_report.corruption_type in ["incomplete_executions", "invalid_timestamps"]:
            fallback_actions = [RecoveryAction.REPAIR_IN_PLACE, RecoveryAction.REBUILD_FROM_LOGS, RecoveryAction.GRACEFUL_DEGRADATION]
            estimated_loss = 10.0

        elif corruption_report.corruption_type == "missing_session_id":
            fallback_actions = [RecoveryAction.CREATE_NEW]
            estimated_loss = 100.0

        else:
            fallback_actions = [RecoveryAction.GRACEFUL_DEGRADATION, RecoveryAction.CREATE_NEW]
            estimated_loss = 50.0

        # Generate recovery steps
        steps = self._generate_recovery_steps(primary_action, corruption_report)

        return RecoveryPlan(
            corruption_report=corruption_report,
            primary_action=primary_action,
            fallback_actions=fallback_actions,
            estimated_data_loss=estimated_loss,
            recovery_steps=steps,
            requires_user_confirmation=corruption_report.severity in ["high", "critical"]
        )

    def _generate_recovery_steps(self, action: RecoveryAction, corruption_report: CorruptionReport) -> List[str]:
        """Generate detailed recovery steps"""
        if action == RecoveryAction.REPAIR_IN_PLACE:
            return [
                "Backup current session state",
                "Recalculate derived metrics",
                "Fix data inconsistencies",
                "Validate repaired data",
                "Restore session if validation fails"
            ]
        elif action == RecoveryAction.RESTORE_FROM_BACKUP:
            return [
                "Locate most recent backup",
                "Validate backup integrity",
                "Restore session from backup",
                "Update with any recent changes"
            ]
        elif action == RecoveryAction.REBUILD_FROM_LOGS:
            return [
                "Collect execution logs",
                "Parse log entries",
                "Reconstruct session state",
                "Validate reconstructed data"
            ]
        elif action == RecoveryAction.CREATE_NEW:
            return [
                "Archive corrupted session",
                "Initialize new session",
                "Migrate salvageable data"
            ]
        else:  # GRACEFUL_DEGRADATION
            return [
                "Identify safe data components",
                "Disable unreliable features",
                "Continue with reduced functionality"
            ]

    async def _execute_recovery(self, session: SessionMetrics, recovery_plan: RecoveryPlan) -> Optional[SessionMetrics]:
        """Execute the recovery plan"""
        # Create backup before recovery
        await self._create_session_backup(session)

        # Try primary action first
        try:
            result = await self._execute_recovery_action(session, recovery_plan.primary_action, recovery_plan.corruption_report)
            if result:
                logger.info(f"Session recovered using {recovery_plan.primary_action.value}")
                return result
        except Exception as e:
            logger.error(f"Primary recovery action failed: {e}")

        # Try fallback actions
        for fallback_action in recovery_plan.fallback_actions:
            try:
                result = await self._execute_recovery_action(session, fallback_action, recovery_plan.corruption_report)
                if result:
                    logger.info(f"Session recovered using fallback {fallback_action.value}")
                    return result
            except Exception as e:
                logger.error(f"Fallback recovery action {fallback_action.value} failed: {e}")

        logger.error("All recovery attempts failed")
        return None

    async def _execute_recovery_action(self, session: SessionMetrics, action: RecoveryAction,
                                     corruption_report: CorruptionReport) -> Optional[SessionMetrics]:
        """Execute a specific recovery action"""
        if action == RecoveryAction.REPAIR_IN_PLACE:
            return await self._repair_session(session, corruption_report)
        elif action == RecoveryAction.RESTORE_FROM_BACKUP:
            return await self._restore_from_backup(session.session_id)
        elif action == RecoveryAction.REBUILD_FROM_LOGS:
            return await self._rebuild_from_logs(session.session_id)
        elif action == RecoveryAction.CREATE_NEW:
            return await self._create_new_session(session)
        elif action == RecoveryAction.GRACEFUL_DEGRADATION:
            return await self._apply_graceful_degradation(session, corruption_report)

        return None

    async def _repair_session(self, session: SessionMetrics, corruption_report: CorruptionReport) -> SessionMetrics:
        """Repair session by fixing data inconsistencies"""
        # Create a new session with the same data to avoid threading lock issues
        repaired_session = SessionMetrics(
            session_id=session.session_id,
            user_input=session.user_input,
            start_time=session.start_time,
            end_time=session.end_time
        )

        # Copy other attributes
        repaired_session.artifacts_created = session.artifacts_created.copy() if session.artifacts_created else []

        corruption_type = corruption_report.corruption_type

        # Apply fixes based on corruption type before copying executions
        if corruption_type == "token_count_mismatch":
            # Copy function executions
            for execution in session.function_executions:
                repaired_session.add_function_execution(execution)
            # Recalculate token counts from function executions (this will be done automatically by add_function_execution)
            # But let's ensure they're correct
            repaired_session.total_input_tokens = sum(exec.input_tokens for exec in repaired_session.function_executions)
            repaired_session.total_output_tokens = sum(exec.output_tokens for exec in repaired_session.function_executions)
            repaired_session.total_reasoning_tokens = sum(exec.reasoning_tokens for exec in repaired_session.function_executions)

        elif corruption_type == "function_count_mismatch":
            # Copy function executions and fix counts
            for execution in session.function_executions:
                repaired_session.add_function_execution(execution)

        elif corruption_type == "success_count_mismatch":
            # Copy function executions
            for execution in session.function_executions:
                repaired_session.add_function_execution(execution)

        elif corruption_type == "negative_values":
            # Copy function executions first
            for execution in session.function_executions:
                repaired_session.add_function_execution(execution)
            # Fix negative values
            if repaired_session.total_input_tokens < 0:
                repaired_session.total_input_tokens = 0
            if repaired_session.total_output_tokens < 0:
                repaired_session.total_output_tokens = 0
            if repaired_session.total_reasoning_tokens < 0:
                repaired_session.total_reasoning_tokens = 0
            if repaired_session.total_cost < 0:
                repaired_session.total_cost = 0.0

        elif corruption_type == "invalid_timestamps":
            # Copy function executions
            for execution in session.function_executions:
                repaired_session.add_function_execution(execution)
            # Fix timestamp issues
            current_time = time.time()
            if repaired_session.start_time > current_time:
                repaired_session.start_time = current_time - 3600  # 1 hour ago
            if repaired_session.end_time and repaired_session.end_time < repaired_session.start_time:
                repaired_session.end_time = None  # Mark as not finalized

        elif corruption_type == "incomplete_executions":
            # Filter and fix incomplete executions
            for exec in session.function_executions:
                if exec.function_name and exec.start_time is not None and exec.end_time is not None:
                    repaired_session.add_function_execution(exec)
                elif exec.function_name and exec.start_time is not None:
                    # Try to fix missing end_time
                    fixed_exec = FunctionExecution(
                        function_name=exec.function_name,
                        start_time=exec.start_time,
                        end_time=exec.start_time + 1.0,  # Default 1 second duration
                        input_tokens=exec.input_tokens,
                        output_tokens=exec.output_tokens,
                        reasoning_tokens=exec.reasoning_tokens,
                        success=exec.success,
                        confidence=exec.confidence,
                        artifacts=exec.artifacts,
                        cost=exec.cost,
                        provider=exec.provider,
                        model=exec.model
                    )
                    repaired_session.add_function_execution(fixed_exec)

        else:
            # Default: copy all executions
            for execution in session.function_executions:
                repaired_session.add_function_execution(execution)

        return repaired_session

    async def _restore_from_backup(self, session_id: str) -> Optional[SessionMetrics]:
        """Restore session from backup"""
        backup_path = os.path.join(self.backup_dir, f"{session_id}.json")
        if not os.path.exists(backup_path):
            return None

        try:
            with open(backup_path, 'r') as f:
                backup_data = json.load(f)

            # Reconstruct session from backup data
            session = SessionMetrics(
                session_id=backup_data['session_id'],
                user_input=backup_data['user_input'],
                start_time=backup_data['start_time'],
                end_time=backup_data.get('end_time')
            )

            # Restore function executions
            for exec_data in backup_data.get('function_executions', []):
                execution = FunctionExecution(
                    function_name=exec_data['function_name'],
                    start_time=exec_data['start_time'],
                    end_time=exec_data['end_time'],
                    input_tokens=exec_data['input_tokens'],
                    output_tokens=exec_data['output_tokens'],
                    reasoning_tokens=exec_data['reasoning_tokens'],
                    success=exec_data['success'],
                    confidence=exec_data.get('confidence'),
                    cost=exec_data.get('cost', 0.0)
                )
                session.add_function_execution(execution)

            return session

        except Exception as e:
            logger.error(f"Failed to restore session from backup: {e}")
            return None

    async def _rebuild_from_logs(self, session_id: str) -> Optional[SessionMetrics]:
        """Rebuild session from execution logs"""
        # This would typically read from application logs
        # For now, return None to indicate this method needs implementation
        logger.warning("Log-based session reconstruction not yet implemented")
        return None

    async def _create_new_session(self, corrupted_session: SessionMetrics) -> SessionMetrics:
        """Create a new session, preserving what data we can"""
        new_session_id = f"{corrupted_session.session_id}_recovered_{int(time.time())}"

        new_session = SessionMetrics(
            session_id=new_session_id,
            user_input=corrupted_session.user_input or "Recovered session",
            start_time=time.time()
        )

        # Try to preserve valid function executions
        for exec in corrupted_session.function_executions:
            if exec.function_name and exec.start_time is not None and exec.end_time is not None:
                new_session.add_function_execution(exec)

        return new_session

    async def _apply_graceful_degradation(self, session: SessionMetrics,
                                        corruption_report: CorruptionReport) -> SessionMetrics:
        """Apply graceful degradation to handle corruption"""
        # Mark session as degraded and disable unreliable features
        session.artifacts_created = session.artifacts_created or []
        session.artifacts_created.append("session_degraded_due_to_corruption")

        # Set conservative values for unreliable metrics
        if corruption_report.corruption_type in ["token_count_mismatch", "negative_values"]:
            # Use conservative token estimates
            session.total_input_tokens = max(0, session.total_input_tokens)
            session.total_output_tokens = max(0, session.total_output_tokens)
            session.total_reasoning_tokens = max(0, session.total_reasoning_tokens)

        return session

    async def _create_session_backup(self, session: SessionMetrics):
        """Create a backup of the session before recovery"""
        backup_path = os.path.join(self.backup_dir, f"{session.session_id}_{int(time.time())}.json")

        try:
            backup_data = session.to_summary_dict()
            backup_data['function_executions'] = [exec.to_dict() for exec in session.function_executions]

            with open(backup_path, 'w') as f:
                json.dump(backup_data, f, indent=2)

            logger.info(f"Session backup created at {backup_path}")
        except Exception as e:
            logger.error(f"Failed to create session backup: {e}")

    def _record_recovery(self, corruption_report: CorruptionReport, recovery_plan: RecoveryPlan, success: bool):
        """Record recovery attempt for analytics"""
        with self._lock:
            record = {
                'session_id': corruption_report.session_id,
                'corruption_type': corruption_report.corruption_type,
                'severity': corruption_report.severity,
                'recovery_action': recovery_plan.primary_action.value,
                'success': success,
                'timestamp': time.time(),
                'estimated_data_loss': recovery_plan.estimated_data_loss
            }
            self._recovery_history.append(record)

            # Keep only recent history
            if len(self._recovery_history) > 500:
                self._recovery_history = self._recovery_history[-500:]

    def get_recovery_statistics(self) -> Dict[str, Any]:
        """Get recovery statistics"""
        with self._lock:
            if not self._recovery_history:
                return {"total_recoveries": 0, "success_rate": 0.0, "corruption_types": {}}

            corruption_types = {}
            successful_recoveries = 0

            for record in self._recovery_history:
                corruption_type = record['corruption_type']
                if corruption_type not in corruption_types:
                    corruption_types[corruption_type] = {'count': 0, 'successes': 0}

                corruption_types[corruption_type]['count'] += 1
                if record['success']:
                    corruption_types[corruption_type]['successes'] += 1
                    successful_recoveries += 1

            return {
                "total_recoveries": len(self._recovery_history),
                "success_rate": successful_recoveries / len(self._recovery_history),
                "corruption_types": corruption_types,
                "most_common_corruption": max(corruption_types.items(), key=lambda x: x[1]['count'])[0] if corruption_types else None
            }


# Global session recovery manager instance
_session_recovery_manager = SessionRecoveryManager()


def get_session_recovery_manager() -> SessionRecoveryManager:
    """Get global session recovery manager instance"""
    return _session_recovery_manager
