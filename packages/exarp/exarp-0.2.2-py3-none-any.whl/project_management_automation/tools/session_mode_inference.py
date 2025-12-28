"""
Session Mode Inference Engine for MODE-002.

Analyzes tool call patterns and file edits to infer Cursor session modes:
- AGENT: High tool frequency, multi-file edits, longer sessions
- ASK: Lower frequency, single queries, shorter interactions
- MANUAL: Very low/no tool calls, direct file edits
"""

import time
from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from typing import Any, Optional

from .dynamic_tools import FileEditTracker, ToolUsageTracker


class SessionMode(str, Enum):
    """
    Cursor session modes inferred from tool patterns.
    
    These correspond to different Cursor interaction patterns:
    - AGENT: AI agent actively making changes (high tool usage)
    - ASK: User asking questions (moderate tool usage)
    - MANUAL: User editing manually (low/no tool usage)
    """
    AGENT = "agent"      # High tool frequency, multi-file, longer sessions
    ASK = "ask"          # Lower frequency, single queries, shorter
    MANUAL = "manual"    # No tool calls, direct file edits
    UNKNOWN = "unknown"  # Insufficient data


@dataclass
class ModeInferenceResult:
    """
    Result of mode inference with confidence and reasoning.
    
    Attributes:
        mode: Inferred session mode
        confidence: Confidence score from 0.0 to 1.0
        reasoning: Human-readable explanations for the inference
        metrics: Raw metrics used for inference
    """
    mode: SessionMode
    confidence: float  # 0.0 to 1.0
    reasoning: list[str]
    metrics: dict[str, Any]
    
    def to_dict(self) -> dict[str, Any]:
        """Serialize for JSON/API responses."""
        return {
            "mode": self.mode.value,
            "confidence": self.confidence,
            "reasoning": self.reasoning,
            "metrics": self.metrics,
        }


class SessionModeInference:
    """
    Analyzes patterns to infer AGENT/ASK/MANUAL modes with confidence scores.
    
    Detection Heuristics:
    - AGENT: High tool frequency (>5/min), multi-file (>2), longer sessions (>5min)
    - ASK: Lower frequency (1-3/min), single/few files (≤2), shorter (<5min)
    - MANUAL: Very low/no tool calls (<1/min), direct file edits
    
    Usage:
        inference = SessionModeInference()
        result = inference.infer_mode(
            tool_tracker=tool_tracker,
            file_tracker=file_tracker,
            session_duration_seconds=300.0
        )
    """
    
    # Thresholds for mode detection
    AGENT_TOOL_FREQ_THRESHOLD = 5.0  # tools per minute
    AGENT_FILE_THRESHOLD = 2  # minimum files for multi-file
    AGENT_SESSION_DURATION_THRESHOLD = 300.0  # 5 minutes
    
    ASK_TOOL_FREQ_MIN = 1.0  # minimum tools per minute
    ASK_TOOL_FREQ_MAX = 3.0  # maximum tools per minute
    ASK_FILE_THRESHOLD = 2  # maximum files
    ASK_SESSION_DURATION_THRESHOLD = 300.0  # 5 minutes
    
    MANUAL_TOOL_FREQ_THRESHOLD = 1.0  # maximum tools per minute
    
    def infer_mode(
        self,
        tool_tracker: ToolUsageTracker,
        file_tracker: FileEditTracker,
        session_duration_seconds: float
    ) -> ModeInferenceResult:
        """
        Infer session mode from tool and file patterns.
        
        Args:
            tool_tracker: ToolUsageTracker instance with tool call data
            file_tracker: FileEditTracker instance with file edit data
            session_duration_seconds: Current session duration in seconds
            
        Returns:
            ModeInferenceResult with inferred mode, confidence, and reasoning
        """
        # Calculate metrics
        total_tool_calls = sum(tool_tracker.tool_counts.values())
        tool_frequency = self._calculate_tool_frequency(
            total_tool_calls, session_duration_seconds
        )
        unique_files = file_tracker.get_unique_files_count()
        is_multi_file = file_tracker.is_multi_file_session(threshold=self.AGENT_FILE_THRESHOLD)
        edit_frequency = file_tracker.get_edit_frequency(window_seconds=60)
        
        metrics = {
            "total_tool_calls": total_tool_calls,
            "tool_frequency_per_min": tool_frequency,
            "unique_files_edited": unique_files,
            "is_multi_file": is_multi_file,
            "edit_frequency_per_min": edit_frequency,
            "session_duration_seconds": session_duration_seconds,
        }
        
        # Check for insufficient data
        if session_duration_seconds < 10 or total_tool_calls == 0:
            return ModeInferenceResult(
                mode=SessionMode.UNKNOWN,
                confidence=0.0,
                reasoning=[
                    f"Insufficient data: session duration {session_duration_seconds:.1f}s, "
                    f"tool calls {total_tool_calls}"
                ],
                metrics=metrics,
            )
        
        # Infer mode based on heuristics
        mode_scores = {
            SessionMode.AGENT: self._score_agent_mode(
                tool_frequency, is_multi_file, session_duration_seconds, unique_files
            ),
            SessionMode.ASK: self._score_ask_mode(
                tool_frequency, unique_files, session_duration_seconds
            ),
            SessionMode.MANUAL: self._score_manual_mode(
                tool_frequency, edit_frequency, unique_files
            ),
        }
        
        # Select best mode
        best_mode = max(mode_scores.items(), key=lambda x: x[1])
        inferred_mode, confidence = best_mode
        
        # Generate reasoning
        reasoning = self._generate_reasoning(
            inferred_mode, confidence, metrics, mode_scores
        )
        
        return ModeInferenceResult(
            mode=inferred_mode,
            confidence=confidence,
            reasoning=reasoning,
            metrics=metrics,
        )
    
    def _calculate_tool_frequency(
        self, total_calls: int, duration_seconds: float
    ) -> float:
        """Calculate tools per minute."""
        if duration_seconds <= 0:
            return 0.0
        return (total_calls / duration_seconds) * 60.0
    
    def _score_agent_mode(
        self,
        tool_frequency: float,
        is_multi_file: bool,
        session_duration: float,
        unique_files: int
    ) -> float:
        """Score how well the pattern matches AGENT mode."""
        score = 0.0
        
        # High tool frequency (strong indicator)
        if tool_frequency >= self.AGENT_TOOL_FREQ_THRESHOLD:
            score += 0.4
        elif tool_frequency >= self.AGENT_TOOL_FREQ_THRESHOLD * 0.7:
            score += 0.2
        
        # Multi-file edits (strong indicator)
        if is_multi_file:
            score += 0.3
        elif unique_files == 1:
            score -= 0.2  # Penalize single-file for AGENT mode
        
        # Longer session duration
        if session_duration >= self.AGENT_SESSION_DURATION_THRESHOLD:
            score += 0.2
        elif session_duration >= self.AGENT_SESSION_DURATION_THRESHOLD * 0.5:
            score += 0.1
        
        # Bonus for very high tool frequency
        if tool_frequency >= self.AGENT_TOOL_FREQ_THRESHOLD * 2:
            score += 0.1
        
        return min(score, 1.0)
    
    def _score_ask_mode(
        self,
        tool_frequency: float,
        unique_files: int,
        session_duration: float
    ) -> float:
        """Score how well the pattern matches ASK mode."""
        score = 0.0
        
        # Moderate tool frequency
        if self.ASK_TOOL_FREQ_MIN <= tool_frequency <= self.ASK_TOOL_FREQ_MAX:
            score += 0.4
        elif tool_frequency < self.ASK_TOOL_FREQ_MIN:
            score += 0.2
        elif tool_frequency <= self.ASK_TOOL_FREQ_MAX * 1.5:
            score += 0.1
        
        # Single or few files
        if unique_files <= self.ASK_FILE_THRESHOLD:
            score += 0.3
        else:
            score -= 0.2  # Penalize multi-file for ASK mode
        
        # Shorter session duration
        if session_duration < self.ASK_SESSION_DURATION_THRESHOLD:
            score += 0.2
        else:
            score -= 0.1  # Penalize long sessions for ASK mode
        
        return min(max(score, 0.0), 1.0)
    
    def _score_manual_mode(
        self,
        tool_frequency: float,
        edit_frequency: float,
        unique_files: int
    ) -> float:
        """Score how well the pattern matches MANUAL mode."""
        score = 0.0
        
        # Very low tool frequency (strong indicator)
        if tool_frequency <= self.MANUAL_TOOL_FREQ_THRESHOLD:
            score += 0.5
        elif tool_frequency <= self.MANUAL_TOOL_FREQ_THRESHOLD * 2:
            score += 0.2
        
        # But there are file edits happening
        if edit_frequency > 0:
            score += 0.3
        
        # Single file edits
        if unique_files == 1:
            score += 0.2
        
        return min(score, 1.0)
    
    def _generate_reasoning(
        self,
        mode: SessionMode,
        confidence: float,
        metrics: dict[str, Any],
        mode_scores: dict[SessionMode, float]
    ) -> list[str]:
        """Generate human-readable reasoning for the inference."""
        reasoning = []
        
        tool_freq = metrics["tool_frequency_per_min"]
        unique_files = metrics["unique_files_edited"]
        duration = metrics["session_duration_seconds"]
        
        if mode == SessionMode.AGENT:
            reasoning.append(
                f"Inferred AGENT mode (confidence: {confidence:.1%})"
            )
            if tool_freq >= self.AGENT_TOOL_FREQ_THRESHOLD:
                reasoning.append(
                    f"High tool frequency: {tool_freq:.1f} tools/min "
                    f"(threshold: {self.AGENT_TOOL_FREQ_THRESHOLD})"
                )
            if unique_files > self.AGENT_FILE_THRESHOLD:
                reasoning.append(
                    f"Multi-file editing: {unique_files} files "
                    f"(threshold: {self.AGENT_FILE_THRESHOLD})"
                )
            if duration >= self.AGENT_SESSION_DURATION_THRESHOLD:
                reasoning.append(
                    f"Long session duration: {duration/60:.1f} minutes"
                )
        
        elif mode == SessionMode.ASK:
            reasoning.append(
                f"Inferred ASK mode (confidence: {confidence:.1%})"
            )
            if self.ASK_TOOL_FREQ_MIN <= tool_freq <= self.ASK_TOOL_FREQ_MAX:
                reasoning.append(
                    f"Moderate tool frequency: {tool_freq:.1f} tools/min"
                )
            if unique_files <= self.ASK_FILE_THRESHOLD:
                reasoning.append(
                    f"Single/few files: {unique_files} files"
                )
            if duration < self.ASK_SESSION_DURATION_THRESHOLD:
                reasoning.append(
                    f"Shorter session: {duration/60:.1f} minutes"
                )
        
        elif mode == SessionMode.MANUAL:
            reasoning.append(
                f"Inferred MANUAL mode (confidence: {confidence:.1%})"
            )
            if tool_freq <= self.MANUAL_TOOL_FREQ_THRESHOLD:
                reasoning.append(
                    f"Very low tool frequency: {tool_freq:.1f} tools/min"
                )
            if metrics.get("edit_frequency_per_min", 0) > 0:
                reasoning.append("File edits detected without tool calls")
        
        else:  # UNKNOWN
            reasoning.append("Insufficient data for mode inference")
        
        # Add alternative mode scores if close
        other_scores = {
            k: v for k, v in mode_scores.items()
            if k != mode and v > confidence * 0.7
        }
        if other_scores:
            reasoning.append(
                f"Alternative modes considered: "
                f"{', '.join(f'{m.value}={v:.1%}' for m, v in other_scores.items())}"
            )
        
        return reasoning
    
    def analyze_sliding_window(
        self,
        tool_tracker: ToolUsageTracker,
        file_tracker: FileEditTracker,
        window_size_seconds: float = 300,  # 5 minutes
        step_size_seconds: float = 60     # 1 minute
    ) -> list[ModeInferenceResult]:
        """
        Analyze mode changes over time using a sliding window.
        
        Args:
            tool_tracker: ToolUsageTracker instance
            file_tracker: FileEditTracker instance
            window_size_seconds: Size of analysis window (default: 300s = 5min)
            step_size_seconds: Step size between windows (default: 60s = 1min)
            
        Returns:
            List of ModeInferenceResult for each window
        """
        # For now, return single inference result
        # Full sliding window implementation would require timestamped tool calls
        # This is a placeholder for future enhancement
        current_time = time.time()
        session_start = datetime.fromisoformat(tool_tracker.session_start).timestamp()
        session_duration = current_time - session_start
        
        return [self.infer_mode(tool_tracker, file_tracker, session_duration)]
