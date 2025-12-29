import os
import json
import traceback
from supabase import Client
from .classifier import FailureClassifier
from .rca import RCAEngine
from .generator import CandidateGenerator
from .extractor import ExceptionExtractor
from .utils import format_trace_context

class AFEDetector:
    def __init__(self, supabase_client: Client):
        self.supabase = supabase_client
        self.rca_engine = RCAEngine()
        self.extractor = ExceptionExtractor()
        # Pass API key from env if available
        self.generator = CandidateGenerator(groq_api_key=os.environ.get("GROQ_API_KEY"))
        self.last_detection_id = None

    def detect_failure(self, job_id: str, trace_id: str, error_details: str, traceback_str: str = None, events_path: str = None):
        """
        Classifies the failure, runs RCA, generates candidates, and stores everything.
        """
        self.last_detection_id = None # Reset
        print(f"🔍 AFE: Analyzing failure for Job {job_id}...")
        
        # 1. Classification
        failure_type, confidence = FailureClassifier.classify(error_details)
        print(f"   AFE: Classified as '{failure_type}' (conf={confidence})")

        try:
            # 2. Store Detection
            data = {
                "job_id": job_id,
                "trace_id": trace_id,
                "failure_type": failure_type,
                "confidence": confidence
            }
            det_res = self.supabase.table("afe_detections").insert(data).execute()
            if not det_res.data:
                print("   ❌ AFE: Failed to insert detection record.")
                return
                
            detection_id = det_res.data[0]['id']
            self.last_detection_id = detection_id
            print(f"   ✅ AFE: Detection recorded (ID: {detection_id})")
            
            # 3. Read Trace Context (Local)
            trace_context = ""
            try:
                # Use passed path, or try singleton, or fallback
                final_events_path = events_path
                
                if not final_events_path:
                    try:
                        from agenttrace.core.tracer import Tracer
                        t = Tracer.get_instance()
                        if t and hasattr(t, "_events_file_path") and t._events_file_path:
                            final_events_path = t._events_file_path
                    except: pass

                if not final_events_path:
                    final_events_path = f".agenttrace/traces/{trace_id}/events.jsonl"

                if os.path.exists(final_events_path):
                    steps = []
                    with open(final_events_path, "r", encoding="utf-8") as f:
                        for line in f:
                            try:
                                steps.append(json.loads(line))
                            except: pass
                    trace_context = format_trace_context(steps)
                    print(f"   AFE: Loaded trace context ({len(trace_context)} chars)")
                else:
                    print(f"   ⚠️ AFE: Events file not found at {events_path}")
            except Exception as e:
                print(f"   ⚠️ AFE: Could not read trace logs: {e}")

            # 3.5 Extract Exception Context
            ctx = None
            if traceback_str:
                # Construct synthetic event for extractor
                event = {
                    "message": error_details,
                    "traceback": traceback_str,
                    # Do NOT set exception_type here, let extractor parse it from traceback
                }
                # We don't have source code here easily unless we read script.py
                # But extractor can work without it (just less context)
                ctx = self.extractor.extract(event, "")
                print(f"   AFE: Extracted context for {ctx.exception_type} at line {ctx.lineno}")

            # 4. Run RCA
            rca_result = self.rca_engine.analyze(
                # Create a temporary object or just pass failure_type string if analyze supports it
                # The analyze method expects AFEDetector object, let's mock it or fix analyze signature
                # Actually analyze expects AFEDetection model.
                # Let's construct it.
                type("AFEDetection", (), {"failure_type": failure_type}), 
                error_details,
                ctx=ctx
            )
            print(f"   AFE: RCA Root Cause: {rca_result.root_cause}")

            # 5. Generate Candidates
            candidates = self.generator.generate(
                rca_result, 
                detection_id, 
                trace_context=trace_context, 
                error_details=error_details
            )
            
            # 6. Store Candidates
            if candidates:
                print(f"   AFE: Generated {len(candidates)} candidates.")
                for cand in candidates:
                    cand_data = cand.model_dump(exclude={"id", "created_at"})
                    
                    # Hack: Remove is_selected if present (DB schema mismatch)
                    if "is_selected" in cand_data:
                        del cand_data["is_selected"]
                        
                    print(f"   AFE: Inserting candidate keys: {list(cand_data.keys())}")
                    self.supabase.table("afe_candidates").insert(cand_data).execute()
                print("   ✅ AFE: Candidates stored.")
            else:
                print("   AFE: No candidates generated.")

        except Exception as e:
            print(f"   ❌ AFE: Pipeline failed: {e}")
            traceback.print_exc()
