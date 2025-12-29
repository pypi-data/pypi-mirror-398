import os
import json
from pathlib import Path
from typing import Dict, Any, Optional, List

from .classifier import FailureClassifier
from .rca import RCAEngine
from .generator import CandidateGenerator
from .models import AFEDetection, AFECandidate
from .utils import format_trace_context
from .extractor import ExceptionExtractor


def load_local_trace(trace_id: str) -> List[Dict[str, Any]]:
    """Load trace events from local file system."""
    # Try new format (directory with events.jsonl)
    jsonl_path = Path(f".agenttrace/traces/{trace_id}/events.jsonl")
    if jsonl_path.exists():
        events = []
        with open(jsonl_path, 'r', encoding='utf-8') as f:
            for line in f:
                if line.strip():
                    events.append(json.loads(line))
        return events

    # Try old format (single json file)
    json_path = Path(f".agenttrace/traces/{trace_id}.json")
    if json_path.exists():
        with open(json_path, 'r', encoding='utf-8') as f:
            return json.load(f)
            
    return []


def load_source_code(trace_id: str) -> str:
    """Try to load source code from trace directory."""
    script_path = Path(f".agenttrace/traces/{trace_id}/script.py")
    if script_path.exists():
        return script_path.read_text(encoding='utf-8')
    return ""


def auto_fix_local(
    trace_id: str,
    step: Optional[int] = None,
    use_ai: bool = True,
    groq_api_key: Optional[str] = None,
    groq_model: Optional[str] = None
) -> Dict[str, Any]:
    """
    Run AFE v2 locally on a trace without database dependency.
    Enhanced with ExceptionExtractor for structured context.
    """
    events = load_local_trace(trace_id)
    if not events:
        return {"error": f"Trace {trace_id} not found locally."}

    # Find error event
    error_event = None
    for event in events:
        if event.get("type") == "error" or "exception" in event.get("type", "").lower():
            if step is None or event.get("seq") == step:
                error_event = event
                break
    
    if not error_event:
        return {
            "status": "success",
            "message": "No errors found in trace",
            "trace_id": trace_id
        }

    # Extract error details
    payload = error_event.get("payload", {})
    error_details = str(payload)
    if isinstance(payload, dict):
        error_details = f"{payload.get('error_type', 'Error')}: {payload.get('message', '')}\n{payload.get('traceback', '')}"

    # NEW: Use ExceptionExtractor for structured context
    extractor = ExceptionExtractor()
    source_code = load_source_code(trace_id)
    exception_ctx = extractor.extract(payload, source_code)
    
    # 1. Classification
    failure_type, confidence = FailureClassifier.classify(error_details)
    
    # 2. RCA with enhanced context
    detection = AFEDetection(
        id="local-detection",
        job_id="local-job",
        trace_id=trace_id,
        failure_type=failure_type,
        confidence=confidence,
        created_at="now"
    )
    
    rca_engine = RCAEngine()
    rca_result = rca_engine.analyze(detection, error_details, exception_ctx)
    
    # 3. Generation
    trace_context = format_trace_context(events)
    
    # Initialize generator with API key
    api_key = groq_api_key or os.environ.get("GROQ_API_KEY")
    generator = CandidateGenerator(groq_api_key=api_key)
    
    candidates = []
    if use_ai and api_key:
        candidates = generator.generate(
            rca_result=rca_result,
            detection_id="local-detection",
            trace_context=trace_context,
            error_details=error_details,
            ctx=exception_ctx  # Pass structured context for enhanced LLM prompts
        )
    else:
        # Fallback if no AI or API key
        candidates = [] # TODO: Implement heuristic fallback in generator if needed
        
    # Format output for CLI
    formatted_fixes = []
    for cand in candidates:
        formatted_fixes.append({
            "error_event": error_event,
            "step": error_event.get("seq", 0),
            "ai_fix": {
                "analysis": f"Classified as {failure_type}. Root cause: {rca_result.root_cause}",
                "root_cause": rca_result.root_cause,
                "fix": {
                    "explanation": cand.summary,
                    "fixed_code": cand.diff or "See summary"
                }
            },
            "ai_failed": False
        })

    return {
        "trace_id": trace_id,
        "error_count": 1,
        "fixes": formatted_fixes,
        "summary": f"Found error: {failure_type}. Generated {len(candidates)} fix candidate(s).",
        "ai_enabled": use_ai and bool(api_key)
    }
