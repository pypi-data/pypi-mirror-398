"""
LLM Judge Evaluator for real-time span evaluation.

Uses LLM to detect errors, drift, hallucination, and other issues
in real-time, enabling step-level retry with remediation.
"""

import asyncio
import json
import logging
import time
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional, Callable, Union, TYPE_CHECKING

from .criteria import (
    JudgeCriteria,
    EvaluationResult,
    IssueType,
    IssueSeverity,
    DetectedIssue,
)

if TYPE_CHECKING:
    from ..interceptor.protocols import InterceptionContext

logger = logging.getLogger("aigie.judge")


class JudgeDecision(Enum):
    """Decision made by the judge after evaluation."""

    PASS = "pass"
    """Output is acceptable, continue execution."""

    RETRY = "retry"
    """Output has issues, retry this step with remediation."""

    STOP = "stop"
    """Critical issue detected, stop execution."""

    CONSULT = "consult"
    """Need backend consultation for complex decision."""


@dataclass
class JudgeConfig:
    """Configuration for the LLM Judge."""

    # Judge model settings
    judge_model: str = "gpt-4o-mini"
    """Model to use for judging (default: fast, cheap model)."""

    judge_provider: str = "openai"
    """Provider for judge model."""

    # Timeout settings
    evaluation_timeout_ms: float = 500.0
    """Timeout for evaluation (target <500ms for real-time)."""

    # Fallback settings
    fallback_to_heuristics: bool = True
    """Fall back to heuristics if LLM judge fails."""

    # Caching
    enable_cache: bool = True
    """Cache similar evaluations for performance."""

    cache_ttl_seconds: int = 300
    """Cache TTL in seconds."""

    # Batch settings
    enable_batch: bool = False
    """Enable batch evaluation for multiple spans."""

    batch_size: int = 5
    """Maximum batch size for evaluation."""

    # Backend integration
    consult_backend_on_low_confidence: bool = True
    """Consult backend when confidence is low."""

    confidence_threshold: float = 0.7
    """Minimum confidence threshold for local decisions."""

    # Criteria
    criteria: JudgeCriteria = field(default_factory=JudgeCriteria.balanced)
    """Evaluation criteria to use."""


@dataclass
class SpanEvaluation:
    """Evaluation of a single span by the judge."""

    span_id: str
    """ID of the evaluated span."""

    decision: JudgeDecision
    """Judge's decision for this span."""

    result: EvaluationResult
    """Detailed evaluation result."""

    remediation: Optional[Dict[str, Any]] = None
    """Suggested remediation if issues detected."""

    retry_prompt: Optional[str] = None
    """Modified prompt for retry if needed."""

    retry_kwargs: Optional[Dict[str, Any]] = None
    """Modified kwargs for retry if needed."""

    confidence: float = 1.0
    """Judge's confidence in the decision."""

    judge_model: Optional[str] = None
    """Model used for this evaluation."""

    evaluation_time_ms: float = 0.0
    """Time taken for evaluation."""


class LLMJudge:
    """
    LLM-based judge for real-time span evaluation.

    Evaluates each span's output for errors, drift, hallucination,
    and other issues, enabling step-level retry with remediation.

    Features:
    - Fast local evaluation (<500ms target)
    - Multiple issue type detection
    - Automatic remediation suggestions
    - Backend consultation for complex cases
    - Caching for performance
    """

    def __init__(
        self,
        config: Optional[JudgeConfig] = None,
        llm_client: Optional[Any] = None,
        backend_client: Optional[Any] = None,
    ):
        """
        Initialize the LLM Judge.

        Args:
            config: Judge configuration
            llm_client: OpenAI/Anthropic client for judge calls
            backend_client: Aigie backend client for consultation
        """
        self.config = config or JudgeConfig()
        self._llm_client = llm_client
        self._backend_client = backend_client
        self._cache: Dict[str, tuple] = {}  # hash -> (result, timestamp)
        self._stats = {
            "evaluations": 0,
            "passes": 0,
            "retries": 0,
            "stops": 0,
            "cache_hits": 0,
            "fallbacks": 0,
            "backend_consultations": 0,
            "total_latency_ms": 0.0,
        }

    def set_llm_client(self, client: Any) -> None:
        """Set the LLM client for judge calls."""
        self._llm_client = client

    def set_backend_client(self, client: Any) -> None:
        """Set the backend client for consultation."""
        self._backend_client = client

    async def evaluate_span(
        self,
        span_id: str,
        input_messages: List[Dict[str, Any]],
        output_content: str,
        context: Optional["InterceptionContext"] = None,
        full_history: Optional[List[Dict[str, Any]]] = None,
        tool_results: Optional[List[Dict[str, Any]]] = None,
    ) -> SpanEvaluation:
        """
        Evaluate a single span's output.

        Args:
            span_id: ID of the span being evaluated
            input_messages: Input messages sent to the LLM
            output_content: Output content from the LLM
            context: Full interception context if available
            full_history: Full conversation history if available
            tool_results: Tool call results if any

        Returns:
            SpanEvaluation with decision and potential remediation
        """
        start_time = time.perf_counter()
        self._stats["evaluations"] += 1

        # Check cache first
        if self.config.enable_cache:
            cache_result = self._check_cache(input_messages, output_content)
            if cache_result:
                self._stats["cache_hits"] += 1
                return SpanEvaluation(
                    span_id=span_id,
                    decision=cache_result.decision,
                    result=cache_result.result,
                    confidence=cache_result.confidence,
                    evaluation_time_ms=(time.perf_counter() - start_time) * 1000,
                )

        try:
            # Try LLM-based evaluation
            if self._llm_client:
                result = await self._evaluate_with_llm(
                    span_id=span_id,
                    input_messages=input_messages,
                    output_content=output_content,
                    context=context,
                    full_history=full_history,
                    tool_results=tool_results,
                )
            elif self.config.fallback_to_heuristics:
                # Fall back to heuristics
                result = await self._evaluate_with_heuristics(
                    span_id=span_id,
                    input_messages=input_messages,
                    output_content=output_content,
                    context=context,
                )
                self._stats["fallbacks"] += 1
            else:
                # No evaluation possible - pass by default
                result = SpanEvaluation(
                    span_id=span_id,
                    decision=JudgeDecision.PASS,
                    result=EvaluationResult.passed(),
                    confidence=0.5,
                )

            # Consult backend if confidence is low
            if (
                self.config.consult_backend_on_low_confidence
                and result.confidence < self.config.confidence_threshold
                and self._backend_client
            ):
                result = await self._consult_backend(result, context)
                self._stats["backend_consultations"] += 1

            # Update stats
            eval_time = (time.perf_counter() - start_time) * 1000
            result.evaluation_time_ms = eval_time
            self._stats["total_latency_ms"] += eval_time

            if result.decision == JudgeDecision.PASS:
                self._stats["passes"] += 1
            elif result.decision == JudgeDecision.RETRY:
                self._stats["retries"] += 1
            elif result.decision == JudgeDecision.STOP:
                self._stats["stops"] += 1

            # Cache result
            if self.config.enable_cache:
                self._cache_result(input_messages, output_content, result)

            return result

        except asyncio.TimeoutError:
            logger.warning(f"Judge evaluation timed out for span {span_id}")
            if self.config.fallback_to_heuristics:
                return await self._evaluate_with_heuristics(
                    span_id=span_id,
                    input_messages=input_messages,
                    output_content=output_content,
                    context=context,
                )
            return SpanEvaluation(
                span_id=span_id,
                decision=JudgeDecision.PASS,
                result=EvaluationResult.passed(),
                confidence=0.3,
                evaluation_time_ms=(time.perf_counter() - start_time) * 1000,
            )
        except Exception as e:
            logger.error(f"Judge evaluation error for span {span_id}: {e}")
            # On error, default to pass with low confidence
            return SpanEvaluation(
                span_id=span_id,
                decision=JudgeDecision.PASS,
                result=EvaluationResult.passed(),
                confidence=0.3,
                evaluation_time_ms=(time.perf_counter() - start_time) * 1000,
            )

    async def _evaluate_with_llm(
        self,
        span_id: str,
        input_messages: List[Dict[str, Any]],
        output_content: str,
        context: Optional["InterceptionContext"] = None,
        full_history: Optional[List[Dict[str, Any]]] = None,
        tool_results: Optional[List[Dict[str, Any]]] = None,
    ) -> SpanEvaluation:
        """Evaluate using LLM as judge."""
        # Build the evaluation prompt
        prompt = self._build_evaluation_prompt(
            input_messages=input_messages,
            output_content=output_content,
            context=context,
            full_history=full_history,
            tool_results=tool_results,
        )

        try:
            # Call the judge LLM
            response = await asyncio.wait_for(
                self._call_judge_llm(prompt),
                timeout=self.config.evaluation_timeout_ms / 1000.0,
            )

            # Parse the judge's response
            return self._parse_judge_response(span_id, response, output_content)

        except Exception as e:
            logger.warning(f"LLM judge failed: {e}")
            raise

    def _build_evaluation_prompt(
        self,
        input_messages: List[Dict[str, Any]],
        output_content: str,
        context: Optional["InterceptionContext"] = None,
        full_history: Optional[List[Dict[str, Any]]] = None,
        tool_results: Optional[List[Dict[str, Any]]] = None,
    ) -> str:
        """Build the evaluation prompt for the judge LLM."""
        criteria = self.config.criteria

        # Build issue types to check
        check_list = []
        if criteria.check_errors:
            check_list.append("- Runtime and validation errors")
        if criteria.check_drift:
            check_list.append("- Context drift from original task")
        if criteria.check_hallucination:
            check_list.append("- Factual hallucinations or made-up information")
        if criteria.check_quality:
            check_list.append("- Coherence and relevance issues")
        if criteria.check_safety:
            check_list.append("- Safety issues (harmful content, PII)")
        if criteria.check_loops:
            check_list.append("- Repetition loops or circular reasoning")

        checks_str = "\n".join(check_list)

        # Build context section
        context_str = ""
        if full_history and criteria.include_full_history:
            history_preview = json.dumps(full_history[-10:], indent=2, default=str)[:2000]
            context_str += f"\n\nConversation History (last 10 messages):\n{history_preview}"
        elif context and context.messages:
            recent = context.messages[-criteria.history_window:]
            history_preview = json.dumps(recent, indent=2, default=str)[:1500]
            context_str += f"\n\nRecent Messages:\n{history_preview}"

        if tool_results and criteria.include_tool_results:
            tools_preview = json.dumps(tool_results[-5:], indent=2, default=str)[:500]
            context_str += f"\n\nRecent Tool Results:\n{tools_preview}"

        # Build blocked/required patterns
        patterns_str = ""
        if criteria.blocked_patterns:
            patterns_str += f"\nBlocked patterns (must NOT appear): {criteria.blocked_patterns}"
        if criteria.required_patterns:
            patterns_str += f"\nRequired patterns (must appear): {criteria.required_patterns}"

        # Build custom instructions
        custom_str = ""
        if criteria.custom_instructions:
            custom_str = f"\n\nCustom Instructions:\n{criteria.custom_instructions}"

        # Input preview
        input_preview = json.dumps(input_messages[-3:], indent=2, default=str)[:1000]

        prompt = f"""You are an AI output quality judge. Evaluate the following LLM output for issues.

INPUT (last 3 messages):
{input_preview}

OUTPUT TO EVALUATE:
{output_content[:2000]}
{context_str}

Check for the following issues:
{checks_str}
{patterns_str}
{custom_str}

Thresholds:
- Drift threshold: {criteria.drift_threshold}
- Hallucination threshold: {criteria.hallucination_threshold}
- Quality threshold: {criteria.quality_threshold}
- Repetition threshold: {criteria.repetition_threshold}

Return ONLY valid JSON (no markdown, no code blocks):
{{
    "has_issues": true/false,
    "decision": "pass|retry|stop",
    "confidence": 0.0-1.0,
    "overall_score": 0.0-1.0,
    "issues": [
        {{
            "type": "drift_context|hallucination_factual|quality_coherence|...",
            "severity": "critical|high|medium|low|info",
            "description": "Description of the issue",
            "evidence": "Specific text that shows the issue",
            "suggested_fix": "How to fix this issue"
        }}
    ],
    "reasoning": "Brief explanation of the evaluation",
    "suggested_remediation": "Overall suggested remediation if issues found",
    "retry_prompt_modification": "How to modify the prompt for retry if needed"
}}"""

        return prompt

    async def _call_judge_llm(self, prompt: str) -> str:
        """Call the judge LLM with the evaluation prompt."""
        if not self._llm_client:
            raise ValueError("No LLM client configured for judge")

        # Determine client type and call appropriately
        if hasattr(self._llm_client, "chat"):
            # OpenAI-style client
            response = await asyncio.get_event_loop().run_in_executor(
                None,
                lambda: self._llm_client.chat.completions.create(
                    model=self.config.judge_model,
                    messages=[{"role": "user", "content": prompt}],
                    temperature=0.1,
                    max_tokens=1000,
                ),
            )
            return response.choices[0].message.content
        elif hasattr(self._llm_client, "messages"):
            # Anthropic-style client
            response = await asyncio.get_event_loop().run_in_executor(
                None,
                lambda: self._llm_client.messages.create(
                    model=self.config.judge_model,
                    max_tokens=1000,
                    messages=[{"role": "user", "content": prompt}],
                ),
            )
            return response.content[0].text
        else:
            raise ValueError(f"Unknown LLM client type: {type(self._llm_client)}")

    def _parse_judge_response(
        self, span_id: str, response: str, output_content: str
    ) -> SpanEvaluation:
        """Parse the judge's response into a SpanEvaluation."""
        try:
            # Clean up response - remove markdown code blocks
            if "```json" in response:
                response = response.split("```json")[1].split("```")[0].strip()
            elif "```" in response:
                response = response.split("```")[1].split("```")[0].strip()

            # Extract JSON
            start_idx = response.find("{")
            end_idx = response.rfind("}") + 1
            if start_idx >= 0 and end_idx > start_idx:
                json_str = response[start_idx:end_idx]
                data = json.loads(json_str)
            else:
                raise ValueError("No JSON found in response")

            # Parse issues
            issues = []
            for issue_data in data.get("issues", []):
                try:
                    issue_type = IssueType(issue_data.get("type", "other"))
                except ValueError:
                    issue_type = IssueType.OTHER

                try:
                    severity = IssueSeverity(issue_data.get("severity", "medium"))
                except ValueError:
                    severity = IssueSeverity.MEDIUM

                issues.append(
                    DetectedIssue(
                        issue_type=issue_type,
                        severity=severity,
                        description=issue_data.get("description", ""),
                        confidence=data.get("confidence", 0.8),
                        evidence=issue_data.get("evidence"),
                        span_id=span_id,
                        suggested_fix=issue_data.get("suggested_fix"),
                    )
                )

            # Create evaluation result
            has_issues = data.get("has_issues", False)
            if has_issues:
                result = EvaluationResult.failed(
                    issues=issues,
                    should_retry=data.get("decision") == "retry",
                    should_stop=data.get("decision") == "stop",
                    reasoning=data.get("reasoning"),
                    suggested_remediation=data.get("suggested_remediation"),
                )
            else:
                result = EvaluationResult.passed(
                    score=data.get("overall_score", 1.0)
                )

            # Map decision
            decision_str = data.get("decision", "pass")
            if decision_str == "retry":
                decision = JudgeDecision.RETRY
            elif decision_str == "stop":
                decision = JudgeDecision.STOP
            else:
                decision = JudgeDecision.PASS

            # Build remediation
            remediation = None
            if decision == JudgeDecision.RETRY:
                remediation = {
                    "suggested_remediation": data.get("suggested_remediation"),
                    "retry_prompt_modification": data.get("retry_prompt_modification"),
                    "issues_to_address": [i.description for i in issues],
                }

            return SpanEvaluation(
                span_id=span_id,
                decision=decision,
                result=result,
                remediation=remediation,
                retry_prompt=data.get("retry_prompt_modification"),
                confidence=data.get("confidence", 0.8),
                judge_model=self.config.judge_model,
            )

        except Exception as e:
            logger.warning(f"Failed to parse judge response: {e}")
            # Default to pass with low confidence
            return SpanEvaluation(
                span_id=span_id,
                decision=JudgeDecision.PASS,
                result=EvaluationResult.passed(score=0.7),
                confidence=0.5,
                judge_model=self.config.judge_model,
            )

    async def _evaluate_with_heuristics(
        self,
        span_id: str,
        input_messages: List[Dict[str, Any]],
        output_content: str,
        context: Optional["InterceptionContext"] = None,
    ) -> SpanEvaluation:
        """Evaluate using fast heuristics (no LLM call)."""
        issues = []
        criteria = self.config.criteria

        # Check for blocked patterns
        for pattern in criteria.blocked_patterns:
            if pattern.lower() in output_content.lower():
                issues.append(
                    DetectedIssue(
                        issue_type=IssueType.SAFETY_HARMFUL,
                        severity=IssueSeverity.HIGH,
                        description=f"Blocked pattern detected: {pattern}",
                        confidence=1.0,
                        evidence=pattern,
                        span_id=span_id,
                        suggested_fix="Remove or rephrase blocked content",
                    )
                )

        # Check for required patterns
        for pattern in criteria.required_patterns:
            if pattern.lower() not in output_content.lower():
                issues.append(
                    DetectedIssue(
                        issue_type=IssueType.QUALITY_COMPLETENESS,
                        severity=IssueSeverity.MEDIUM,
                        description=f"Required pattern missing: {pattern}",
                        confidence=0.9,
                        span_id=span_id,
                        suggested_fix=f"Include required element: {pattern}",
                    )
                )

        # Check for repetition (simple heuristic)
        if criteria.check_loops:
            words = output_content.split()
            if len(words) > 20:
                # Check for repeated sequences
                sequences = [" ".join(words[i : i + 5]) for i in range(len(words) - 4)]
                seen = {}
                for seq in sequences:
                    seen[seq] = seen.get(seq, 0) + 1
                    if seen[seq] > 3:
                        issues.append(
                            DetectedIssue(
                                issue_type=IssueType.LOOP_REPETITION,
                                severity=IssueSeverity.HIGH,
                                description="Repetitive content detected",
                                confidence=0.85,
                                evidence=seq,
                                span_id=span_id,
                                suggested_fix="Reduce repetition, rephrase content",
                            )
                        )
                        break

        # Check for empty or very short output
        if len(output_content.strip()) < 10:
            issues.append(
                DetectedIssue(
                    issue_type=IssueType.QUALITY_COMPLETENESS,
                    severity=IssueSeverity.HIGH,
                    description="Output is too short or empty",
                    confidence=0.95,
                    span_id=span_id,
                    suggested_fix="Generate a more complete response",
                )
            )

        # Check for error patterns
        if criteria.check_errors:
            error_patterns = [
                "error:",
                "exception:",
                "failed to",
                "cannot ",
                "unable to",
                "traceback",
            ]
            for pattern in error_patterns:
                if pattern in output_content.lower():
                    issues.append(
                        DetectedIssue(
                            issue_type=IssueType.ERROR_RUNTIME,
                            severity=IssueSeverity.MEDIUM,
                            description=f"Error pattern detected: {pattern}",
                            confidence=0.7,
                            evidence=pattern,
                            span_id=span_id,
                            suggested_fix="Handle the error or retry the operation",
                        )
                    )
                    break

        # Determine decision
        if issues:
            critical_issues = [i for i in issues if i.severity == IssueSeverity.CRITICAL]
            high_issues = [i for i in issues if i.severity == IssueSeverity.HIGH]

            if critical_issues:
                decision = JudgeDecision.STOP
                should_stop = True
                should_retry = False
            elif high_issues and criteria.auto_retry_on_high:
                decision = JudgeDecision.RETRY
                should_stop = False
                should_retry = True
            else:
                decision = JudgeDecision.RETRY
                should_stop = False
                should_retry = True

            result = EvaluationResult.failed(
                issues=issues,
                should_retry=should_retry,
                should_stop=should_stop,
            )
        else:
            decision = JudgeDecision.PASS
            result = EvaluationResult.passed(score=0.9)

        return SpanEvaluation(
            span_id=span_id,
            decision=decision,
            result=result,
            confidence=0.75,  # Heuristics have lower confidence
        )

    async def _consult_backend(
        self,
        local_result: SpanEvaluation,
        context: Optional["InterceptionContext"] = None,
    ) -> SpanEvaluation:
        """Consult backend for additional evaluation."""
        if not self._backend_client:
            return local_result

        try:
            # Call backend evaluation endpoint
            if hasattr(self._backend_client, "evaluate_span"):
                backend_result = await self._backend_client.evaluate_span(
                    span_id=local_result.span_id,
                    local_evaluation=local_result.result,
                    context=context,
                )
                # Merge with local result (backend takes precedence)
                if backend_result:
                    local_result.confidence = max(
                        local_result.confidence,
                        backend_result.get("confidence", 0.5),
                    )
                    if backend_result.get("decision"):
                        local_result.decision = JudgeDecision(backend_result["decision"])
        except Exception as e:
            logger.warning(f"Backend consultation failed: {e}")

        return local_result

    def _check_cache(
        self, input_messages: List[Dict[str, Any]], output_content: str
    ) -> Optional[SpanEvaluation]:
        """Check if we have a cached evaluation for similar input/output."""
        import hashlib

        cache_key = hashlib.sha256(
            (str(input_messages) + output_content[:500]).encode()
        ).hexdigest()[:16]

        if cache_key in self._cache:
            result, timestamp = self._cache[cache_key]
            # Check if cache is still valid
            if time.time() - timestamp < self.config.cache_ttl_seconds:
                return result
            else:
                del self._cache[cache_key]

        return None

    def _cache_result(
        self,
        input_messages: List[Dict[str, Any]],
        output_content: str,
        result: SpanEvaluation,
    ) -> None:
        """Cache an evaluation result."""
        import hashlib

        cache_key = hashlib.sha256(
            (str(input_messages) + output_content[:500]).encode()
        ).hexdigest()[:16]

        # Limit cache size
        if len(self._cache) > 1000:
            # Remove oldest entries
            oldest_keys = sorted(
                self._cache.keys(), key=lambda k: self._cache[k][1]
            )[:100]
            for key in oldest_keys:
                del self._cache[key]

        self._cache[cache_key] = (result, time.time())

    def get_stats(self) -> Dict[str, Any]:
        """Get judge statistics."""
        return {
            **self._stats,
            "avg_latency_ms": (
                self._stats["total_latency_ms"]
                / max(self._stats["evaluations"], 1)
            ),
            "pass_rate": (
                self._stats["passes"] / max(self._stats["evaluations"], 1)
            ),
            "cache_hit_rate": (
                self._stats["cache_hits"] / max(self._stats["evaluations"], 1)
            ),
        }

    def reset_stats(self) -> None:
        """Reset judge statistics."""
        self._stats = {
            "evaluations": 0,
            "passes": 0,
            "retries": 0,
            "stops": 0,
            "cache_hits": 0,
            "fallbacks": 0,
            "backend_consultations": 0,
            "total_latency_ms": 0.0,
        }

    def clear_cache(self) -> None:
        """Clear the evaluation cache."""
        self._cache.clear()
