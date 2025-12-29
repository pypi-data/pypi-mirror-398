# worker/main.py — PRODUCTION WORKER WITH BRANCHING SUPPORT

import os
import sys
import time
import json
import traceback
import socket
import tempfile
import shutil
import concurrent.futures
import threading
import signal
from http.server import HTTPServer, BaseHTTPRequestHandler
from datetime import datetime
from pathlib import Path

# Ensure local agenttrace package is used
sys.path.insert(0, str(Path(__file__).parent.parent))

from dotenv import load_dotenv
from supabase import create_client, Client

from agenttrace.core.tracer import Tracer
import agenttrace
print(f"🔍 Worker using agenttrace from: {agenttrace.__file__}")
from agenttrace.core.checkpoint import CheckpointManager
from agenttrace.notifications.manager import NotificationManager

# -------------------------------------------------------------------
# LOAD ENV + INIT
# -------------------------------------------------------------------

if sys.platform == 'win32':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

# Redirect stdout/stderr to file for debugging
# sys.stdout = open("worker_debug.log", "a", encoding="utf-8", buffering=1)
# sys.stderr = open("worker_debug.log", "a", encoding="utf-8", buffering=1)

env_file = Path(__file__).parent.parent / "frontend" / ".env.local"
if env_file.exists():
    load_dotenv(dotenv_path=env_file)
load_dotenv()

SUPABASE_URL = os.environ.get("NEXT_PUBLIC_SUPABASE_URL")
SUPABASE_SERVICE_KEY = os.environ.get("SUPABASE_SERVICE_ROLE_KEY")
print(f"DEBUG: Supabase URL: {SUPABASE_URL}", flush=True)

WORKER_ID = f"worker-{socket.gethostname()}-{os.getpid()}"
POLL_INTERVAL = 2

if os.environ.get("GROQ_API_KEY"):
    print("✅ Worker: GROQ_API_KEY found. AFE LLM features ENABLED.")
else:
    print("❌ Worker: GROQ_API_KEY NOT found. AFE LLM features DISABLED.")

supabase: Client = create_client(SUPABASE_URL, SUPABASE_SERVICE_KEY)
checkpoint_manager = CheckpointManager()
tracer = Tracer.get_instance()
notification_manager = None

# -------------------------------------------------------------------
# GLOBAL TRACER CACHING (Performance Optimization)
# -------------------------------------------------------------------
from agenttrace.instrumentation.patch import apply_patches
from agenttrace.runtime.exceptions import install_exception_hook

print("🚀 Worker: Initializing Global Tracer & Patches...", flush=True)
apply_patches()
install_exception_hook()
print("✅ Worker: Global Tracer Ready", flush=True)
# -------------------------------------------------------------------

# Fetch Org ID once at startup
ORG_ID = None
try:
    # Fetch all organizations
    res = supabase.table("organizations").select("id, name, email_config").execute()

    if res.data:
        # 1. Prefer Env Var
        env_org_id = os.environ.get("AGENTTRACE_ORG_ID")
        target_org = None
        
        if env_org_id:
            target_org = next((org for org in res.data if org['id'] == env_org_id), None)
            if target_org:
                print(f"🏢 Worker bound to Org ID (Env): {target_org['id']} ({target_org.get('name')})")
        
        # 2. Prefer Org with Email Config
        if not target_org:
             target_org = next((org for org in res.data if org.get('email_config')), None)
        
        # 3. Fallback to First Available
        if not target_org:
             target_org = res.data[0]
             print(f"ℹ️ Env/Config not matched, binding to first available Org.")

        ORG_ID = target_org['id']
        print(f"🏢 Worker bound to Org ID: {ORG_ID} ({target_org.get('name')})")
        
        if target_org.get('email_config'):
             notification_manager = NotificationManager(supabase, ORG_ID)
             print("🔔 Notification Manager initialized")
        else:
             print("ℹ️ Notification Manager NOT initialized (no config found)")
             
    else:
        print("⚠ No organization found. Worker will idle until an Org is created.")
except Exception as e:
    print(f"⚠ Failed to fetch Org ID: {e}")


# -------------------------------------------------------------------
# FUNCTION: init_worker_globals (for ProcessPoolExecutor)
# -------------------------------------------------------------------
def init_worker_globals():
    """Initialize worker process state"""
    print(f"🔧 Worker Process {os.getpid()} initializing...", flush=True)
    
    # Apply patches and hooks in the subprocess
    from agenttrace.instrumentation.patch import apply_patches
    from agenttrace.runtime.exceptions import install_exception_hook
    
    apply_patches()
    install_exception_hook()
    
    # Ensure Tracer is initialized
    Tracer.get_instance()
    
    print(f"✅ Worker Process {os.getpid()} ready", flush=True)

# -------------------------------------------------------------------
# FUNCTION: reclaim_stale_jobs - Reclaim jobs stuck in 'claimed' for too long
# -------------------------------------------------------------------
STALE_JOB_TIMEOUT_MINUTES = 2  # Aggressive: 2 minutes
MAX_JOB_RETRIES = 3  # Maximum retry attempts per job
HEALTH_PORT = 8080  # Health check endpoint port

# -------------------------------------------------------------------
# HEALTH CHECK HTTP SERVER
# -------------------------------------------------------------------
class HealthHandler(BaseHTTPRequestHandler):
    """HTTP handler for health check endpoint"""
    
    def log_message(self, format, *args):
        pass  # Suppress HTTP access logs
    
    def do_GET(self):
        if self.path == '/health' or self.path == '/':
            self.send_response(200)
            self.send_header('Content-Type', 'application/json')
            self.end_headers()
            
            # Get job stats
            try:
                pending = supabase.table("jobs").select("id", count="exact").eq("status", "pending").execute()
                claimed = supabase.table("jobs").select("id", count="exact").eq("status", "claimed").execute()
                pending_count = pending.count if pending.count else 0
                claimed_count = claimed.count if claimed.count else 0
            except:
                pending_count = -1
                claimed_count = -1
            
            health_data = {
                "status": "healthy",
                "worker_id": WORKER_ID,
                "org_id": ORG_ID,
                "timestamp": datetime.utcnow().isoformat(),
                "jobs": {
                    "pending": pending_count,
                    "claimed": claimed_count
                }
            }
            self.wfile.write(json.dumps(health_data).encode())
        else:
            self.send_response(404)
            self.end_headers()

def start_health_server():
    """Start health check HTTP server in background thread"""
    try:
        server = HTTPServer(('0.0.0.0', HEALTH_PORT), HealthHandler)
        thread = threading.Thread(target=server.serve_forever, daemon=True)
        thread.start()
        print(f"🏥 Health check server running on http://0.0.0.0:{HEALTH_PORT}/health", flush=True)
        return server
    except Exception as e:
        print(f"⚠️ Could not start health server: {e}", flush=True)
        return None

# -------------------------------------------------------------------
# GRACEFUL SHUTDOWN HANDLER
# -------------------------------------------------------------------
shutdown_requested = False

def handle_shutdown(signum, frame):
    """Handle shutdown signals gracefully"""
    global shutdown_requested
    print(f"\n🛑 Shutdown signal received ({signum}). Finishing current jobs...", flush=True)
    shutdown_requested = True

# Register signal handlers
signal.signal(signal.SIGTERM, handle_shutdown)
signal.signal(signal.SIGINT, handle_shutdown)

def reclaim_stale_jobs():
    """Release jobs that have been 'claimed' for more than STALE_JOB_TIMEOUT_MINUTES."""
    try:
        # Direct SQL update via RPC for reliable timestamp comparison
        from datetime import datetime, timedelta
        cutoff = (datetime.utcnow() - timedelta(minutes=STALE_JOB_TIMEOUT_MINUTES)).isoformat()
        
        result = supabase.table("jobs").update({
            "status": "pending",
            "worker_id": None
        }).eq("status", "claimed").lt("updated_at", cutoff).execute()
        
        if result.data and len(result.data) > 0:
            print(f"♻️ RECLAIMED {len(result.data)} stale jobs (claimed > {STALE_JOB_TIMEOUT_MINUTES}min)", flush=True)
    except Exception as e:
        print(f"⚠️ Stale job reclaim failed: {e}", flush=True)

def claim_job():
    if not ORG_ID:
        return None
    try:
        response = supabase.rpc("claim_next_job", {"p_worker_id": WORKER_ID, "p_org_id": ORG_ID}).execute()
        if response.data and len(response.data) > 0:
            return response.data[0]
    except Exception as e:
        print(f"⚠ Error claiming job: {e}")
    return None

# -------------------------------------------------------------------
# FUNCTION: process_job — UPDATED FOR BRANCHING
# -------------------------------------------------------------------

def process_job(job, org_id, worker_id):
    # CRITICAL FIX: Refresh global tracer for this forked process (Zombie Singleton Fix)
    # The global 'tracer' variable points to the parent process's instance.
    # We need the instance for THIS process so configuration matches the script.
    global tracer
    tracer = Tracer.get_instance()
    # Sanity check to ensure we truly have a fresh instance for this PID
    if hasattr(tracer, "_instance_pid"):
        assert tracer._instance_pid == os.getpid(), f"Tracer PID mismatch! Expected {os.getpid()}, got {tracer._instance_pid}"

    job_id = job["id"]

    # Refetch job to ensure all fields are present (RPC might return partial data)
    try:
        api_job = supabase.table("jobs").select("*").eq("id", job_id).single().execute()
        if api_job.data:
            job.update(api_job.data)
            print(f"   🔄 Refetched job details. Parent Trace: {job.get('parent_trace_id')}", flush=True)
    except Exception as e:
        print(f"⚠ Failed to refetch job details: {e}")

    trace_id = job["trace_id"]
    parent_trace_id = job.get("parent_trace_id")
    fork_step = job.get("fork_step")
    is_branch = job.get("is_branch", False)

    print(f"\n🚀 Running Job {job_id}  (Trace {trace_id})", flush=True)
    print(f"Worker: {worker_id}", flush=True)
    print(f"Branch Mode: {is_branch}", flush=True)

    # Initialize Notification Manager for this worker process
    notification_manager = None
    if org_id:
        notification_manager = NotificationManager(supabase, org_id)

    # Create a temporary directory for this job to ensure isolation
    # This is crucial for Async Worker where multiple jobs run in parallel
    temp_dir = tempfile.mkdtemp(prefix=f"job-{job_id}-")
    original_cwd = os.getcwd()
    os.chdir(temp_dir)
    print(f"📂 Working in isolated temp dir: {temp_dir}", flush=True)

    try:
        # -------------------------------------------------------------
        # 1. DOWNLOAD SCRIPT
        # -------------------------------------------------------------
        print("⬇️ Downloading script.py…", flush=True)
        script_downloaded = False
        try:
            res = supabase.storage.from_("traces").download(f"{trace_id}/script.py")
            with open("script.py", "wb") as f:
                f.write(res)
            script_downloaded = True
            print(f"   ✅ Script downloaded from trace {trace_id[:8]}")
        except Exception as e:
            print(f"⚠ Failed to download script.py from {trace_id}: {e}", flush=True)
            # If script not found in current trace, try parent trace
            if parent_trace_id:
                print(f"   Trying parent trace {parent_trace_id[:8]}...", flush=True)
                try:
                    res = supabase.storage.from_("traces").download(f"{parent_trace_id}/script.py")
                    with open("script.py", "wb") as f:
                        f.write(res)
                    script_downloaded = True
                    print(f"   ✅ Script downloaded from parent trace")
                except Exception as e2:
                    print(f"   ⚠ Parent trace also has no script: {e2}", flush=True)
        
        if not script_downloaded:
            raise RuntimeError(
                f"Cannot replay: No script.py found in storage for trace {trace_id} or parent {parent_trace_id}. "
                "The original trace was recorded without uploading the script. "
                "Use 'agenttrace push' to upload the script to cloud storage first."
            )

        # -------------------------------------------------------------
        # 2. RESTORE STATE (BRANCH OR NORMAL)
        # -------------------------------------------------------------
        if is_branch:
            print(f"🌱 Branch Replay Detected — parent={parent_trace_id}, fork_step={fork_step}", flush=True)

            # Load the special -1 checkpoint which contains the forked state
            print("   Loading branch checkpoint -1...", flush=True)
            try:
                checkpoint_data = supabase.storage.from_("traces").download(
                    f"{trace_id}/checkpoints/{trace_id}_-1.json"
                )
                checkpoint_json = json.loads(checkpoint_data)
                state = checkpoint_json.get("state", checkpoint_json)  # Handle nested or flat structure
                
                print(f"   🔄 Loaded branch fork-state: {list(state.keys())}")
                
                # Load parent events and hydrate state up to fork_step
                if parent_trace_id and fork_step is not None:
                    print(f"   ⬇️ Loading parent events from {parent_trace_id}...")
                    from agenttrace.core.replay import load_parent_events, hydrate_state_from_events
                    
                    parent_events = load_parent_events(supabase, parent_trace_id)
                    if parent_events:
                        print(f"   🔁 Hydrating state from {len(parent_events)} parent events up to step {fork_step}...")
                        state = hydrate_state_from_events(state, parent_events, fork_step)
                        print(f"   ✅ State hydrated: {list(state.keys())}")
                
                # Feed pending restore to the tracer
                tracer._pending_restore_state = state
                tracer.replay_cursor = fork_step if fork_step is not None else 0

            except Exception as e:
                print(f"⚠ Failed to load branch checkpoint: {e}")
                traceback.print_exc()
                raise RuntimeError("Branch checkpoint -1 not found or invalid.")

        else:
            # Normal replay: try to load a checkpoint
            print("🧠 Normal replay mode")
            try:
                # Try loading checkpoint 0 or latest
                state = checkpoint_manager.load_checkpoint(trace_id, 0)
                if state:
                    tracer._pending_restore_state = state
                    tracer.replay_cursor = 0
                    print("   Loaded checkpoint 0")
                else:
                    print("   No checkpoint found, starting fresh")
            except Exception as e:
                print(f"   No checkpoint available: {e}")

        # -------------------------------------------------------------
        # 3. EXECUTE SCRIPT USING RESTORED STATE
        # -------------------------------------------------------------
        # -------------------------------------------------------------
        # 3. EXECUTE SCRIPT USING RESTORED STATE
        # -------------------------------------------------------------
        print("▶️ Running script.py with restored state…", flush=True)

        # Set environment variables for AgentTrace SDK
        os.environ["AGENTTRACE_MODE"] = "RECORD"
        os.environ["AGENTTRACE_ID"] = trace_id
        
        # CRITICAL: Set tracer storage root to current temp directory
        # This ensures events.jsonl is written to a path we can find for upload
        tracer.storage_root = temp_dir
        
        # Start the tracer in RECORD mode with the trace_id
        tracer.start_recording(trace_id=trace_id)
        print(f"   📋 Tracer recording: mode={tracer.mode}, storage={tracer.storage_root}", flush=True)
        print(f"   📁 Events file: {tracer._events_file_path}", flush=True)
        
        # DEBUG LOGGING
        with open("worker_debug.log", "a", encoding="utf-8") as log:
            log.write(f"\n--- Processing Job {job_id} ---\n")
            log.write(f"Trace ID: {trace_id}\n")
            log.write(f"Tracer Mode: {tracer.mode}\n")
            log.write(f"Env: AGENTTRACE_MODE={os.environ.get('AGENTTRACE_MODE')}, AGENTTRACE_ID={os.environ.get('AGENTTRACE_ID')}\n")
            log.write(f"CWD: {os.getcwd()}\n")
            log.write(f"CWD: {os.getcwd()}\n")
            log.write(f"Script exists: {os.path.exists('script.py')}\n")

        # Record start event
        tracer.record_event("trace_start", {"script": "script.py", "parent_trace_id": parent_trace_id})

        import runpy
        script_success = False
        try:
            print(f"DEBUG: Pre-Run Mode: {tracer.mode}", flush=True)
            result = runpy.run_path("script.py", run_name="__main__")
            print(f"DEBUG: Post-Run Mode: {tracer.mode}", flush=True)
            print("   ✅ Script completed", flush=True)
            
            print("   ✅ Script completed", flush=True)
            # Job completion will be handled in finally block after upload
            script_success = True

        except BaseException as script_error:
            print(f"   ❌ Script crashed (BaseException): {script_error}")
            with open("worker_debug.log", "a", encoding="utf-8") as log:
                log.write(f"Script crashed (BaseException): {script_error}\n")
                traceback.print_exc(file=log)  # Uses global traceback import
            
            # Manually trigger AgentTrace exception capture since we caught it
            try:
                import sys
                from agenttrace.runtime.exceptions import exception_interceptor
                exc_type, exc_value, exc_traceback = sys.exc_info()
                exception_interceptor(exc_type, exc_value, exc_traceback)
                print("   ✅ Captured crash event via AgentTrace")
            except Exception as capture_err:
                print(f"   ⚠ Failed to capture crash event: {capture_err}")

            raise script_error
            
        finally:
            # -------------------------------------------------------------
            # 3.5 UPLOAD EVENTS (Always run, even on crash)
            # -------------------------------------------------------------
            # Record end event
            try:
                tracer.record_event("trace_end", {"status": "completed" if script_success else "failed"})
            except:
                pass

            # Flush any remaining events in memory
            # Flush any remaining events in memory
            try:
                # Access the tracer instance and flush
                if hasattr(tracer, "_flush_events_to_disk"):
                    tracer._flush_events_to_disk()
                    print("   ✅ Flushed tracer events to disk")
            except Exception as flush_err:
                print(f"   ⚠ Failed to flush tracer: {flush_err}")

            # Get the actual events file path from the tracer
            events_path = None
            if hasattr(tracer, "_events_file_path") and tracer._events_file_path:
                events_path = tracer._events_file_path
            else:
                # Fallback to relative path
                events_path = f".agenttrace/traces/{trace_id}/events.jsonl"
            
            exists = os.path.exists(events_path) if events_path else False
            
            with open("worker_debug.log", "a", encoding="utf-8") as log:
                log.write(f"Events path: {events_path}, exists: {exists}\n")
                if not exists:
                     log.write("No events.jsonl found\n")
                else:
                    log.write(f"Size: {os.path.getsize(events_path)} bytes\n")

            if exists:
                print(f"   ⬆️ Uploading {events_path} to Storage...", flush=True)
                try:
                    # RAW BYPASS: Use os.fdopen to read real disk file, bypassing any VFS interference
                    # This matches the write-side bypass in Tracer
                    fd = os.open(events_path, os.O_RDONLY | getattr(os, "O_BINARY", 0))
                    with os.fdopen(fd, "rb") as f:
                        dest_path = f"{trace_id}/events.jsonl"
                        supabase.storage.from_("traces").upload(
                            dest_path,
                            f,
                            {"content-type": "application/jsonl", "upsert": "true"}
                        )
                    print(f"   📦 Events uploaded to: {dest_path}")
                    with open("worker_debug.log", "a", encoding="utf-8") as log:
                        log.write("Events uploaded successfully\n")
                except Exception as e:
                    print(f"   ⚠ Failed to upload events: {e}")
                    with open("worker_debug.log", "a", encoding="utf-8") as log:
                        log.write(f"Failed to upload events: {e}\n")
            else:
                print("   ⚠ No events.jsonl found to upload")
                with open("worker_debug.log", "a", encoding="utf-8") as log:
                    log.write("No events.jsonl found\n")

            # -------------------------------------------------------------
            # 4. UPDATE JOB STATUS
            # -------------------------------------------------------------
            if script_success and exists:
                 supabase.table("jobs").update({
                    "status": "completed",
                    "finished_at": "now()",
                    "result_metadata": {"exit_code": 0}
                }).eq("id", job_id).execute()
                 print("   🟢 Job completed successfully.")
            elif script_success and not exists:
                 # Script ran but no events generated/found
                 print("   ⚠️ Job finished but no events found - marking as failed for visibility", flush=True)
                 supabase.table("jobs").update({
                    "status": "failed",
                    "finished_at": "now()",
                    "result_metadata": {"error": "Script completed but no events.jsonl generated"}
                }).eq("id", job_id).execute()


    except BaseException as e:
        print("❌ Worker failed:", e)
        traceback.print_exc()
        
        # AFE Integration: Detect and classify failure
        try:
            from agenttrace.afe.detector import AFEDetector
            detector = AFEDetector(supabase)
            # Pass traceback for deep context extraction
            tb_str = traceback.format_exc()
            
            events_path = getattr(tracer, "_events_file_path", None)
            
            detector.detect_failure(job_id, trace_id, str(e), tb_str, events_path=events_path)
        except Exception as afe_e:
            print(f"⚠ AFE failed to run: {afe_e}")
            traceback.print_exc()

        # Notification: Job Failed
        if notification_manager:
            notification_manager.notify_failure(job_id, trace_id, str(e))

        # AFE Validation Integration
        try:
            # Check if any candidates were generated for this job
            # We can query Supabase or modify AFEDetector to return candidates
            # For now, let's query
            res = supabase.table("afe_candidates").select("*").eq("detection_id", detector.last_detection_id).execute()
            candidates = res.data
            
            if candidates:
                from agenttrace.afe.validator import SandboxValidator
                from agenttrace.afe.models import AFECandidate
                
                validator = SandboxValidator()
                
                # Get script content (it was downloaded to script.py)
                with open("script.py", "r", encoding="utf-8") as f:
                    script_content = f.read()
                
                for cand_data in candidates:
                    cand = AFECandidate(**cand_data)
                    print(f"🧪 AFE: Validating candidate {cand.id} ({cand.type})...")
                    
                    # Run validation
                    val_result = validator.validate(cand, trace_id, script_content)
                    
                    # Update candidate status
                    status = "verified" if val_result["success"] else "failed"
                    
                    supabase.table("afe_candidates").update({
                        "status": status,
                        "validation_results": val_result
                    }).eq("id", cand.id).execute()
                    
                    print(f"   AFE: Candidate {cand.id} marked as {status}")

                # Ranking & Selection
                from agenttrace.afe.policy import PolicyEngine
                policy = PolicyEngine()
                
                # Re-fetch candidates to get updated status
                res = supabase.table("afe_candidates").select("*").eq("detection_id", detector.last_detection_id).execute()
                updated_candidates = [AFECandidate(**c) for c in res.data]
                
                ranked = policy.rank_candidates(updated_candidates)
                if ranked:
                    winner = ranked[0]
                    print(f"🏆 AFE: Winner is {winner.id} ({winner.type}, conf={winner.confidence})")
                    
                    # Mark winner
                    # Note: is_selected column doesn't exist in schema, skipping update
                    # supabase.table("afe_candidates").update({"is_selected": True}).eq("id", winner.id).execute()
                    
                    # Notification: Fix Found
                    if notification_manager:
                        notification_manager.notify_fix_found(job_id, winner.id, winner.confidence)
                    
                    # Check Auto-Apply
                    if policy.should_auto_apply(winner):
                        print(f"🚀 AFE: Auto-Applying candidate {winner.id}...")
                        # TODO: Trigger ApplyEngine on actual source and re-queue job
                        # For now, just log it
                        supabase.table("afe_candidates").update({"applied_at": "now()"}).eq("id", winner.id).execute()
                    else:
                        print(f"✋ AFE: Candidate {winner.id} requires manual approval.")

        except Exception as val_e:
            print(f"⚠ AFE Validation/Policy failed: {val_e}")
            traceback.print_exc()

        # ---- JOB RETRY LOGIC ----
        retry_count = job.get('retry_count', 0) + 1
        max_retries = job.get('max_retries', MAX_JOB_RETRIES)
        
        # Log error to job_errors table
        try:
            supabase.table("job_errors").insert({
                "job_id": job_id,
                "org_id": org_id,
                "error_type": type(e).__name__,
                "error_message": str(e)[:1000],
                "stack_trace": traceback.format_exc()[:4000],
                "attempt_number": retry_count
            }).execute()
            print(f"📝 Error logged to job_errors table", flush=True)
        except Exception as log_err:
            print(f"⚠️ Failed to log error: {log_err}", flush=True)

        # Retry or fail permanently
        if retry_count < max_retries:
            supabase.table("jobs").update({
                "status": "pending",
                "worker_id": None,
                "retry_count": retry_count,
                "last_error": str(e)[:500]
            }).eq("id", job_id).execute()
            print(f"🔄 Job {job_id} will retry ({retry_count}/{max_retries})", flush=True)
        else:
            supabase.table("jobs").update({
                "status": "failed",
                "finished_at": "now()",
                "retry_count": retry_count,
                "last_error": str(e)[:500],
                "result_metadata": {"error": str(e), "final_attempt": retry_count}
            }).eq("id", job_id).execute()
            print(f"💀 Job {job_id} permanently failed after {retry_count} attempts", flush=True)

        # AFE: Report Detection
        try:
            print(f"🔍 AFE: Reporting failure for Job {job_id}...", flush=True)
            supabase.table("afe_detections").insert({
                "job_id": job_id,
                "failure_type": type(e).__name__,
                "confidence": 0.95,
                "created_at": "now()"
            }).execute()
            print(f"✅ AFE: Detection reported.", flush=True)
        except Exception as afe_err:
            print(f"⚠️ AFE Report Failed: {afe_err}", flush=True)

    finally:
        # Restore CWD and cleanup temp dir
        os.chdir(original_cwd)
        if 'temp_dir' in locals():
            try:
                shutil.rmtree(temp_dir, ignore_errors=True)
                print(f"🧹 Cleaned up temp dir: {temp_dir}", flush=True)
            except Exception as cleanup_err:
                print(f"⚠ Failed to cleanup temp dir: {cleanup_err}", flush=True)


# -------------------------------------------------------------------
# MAIN LOOP WITH REALTIME
# -------------------------------------------------------------------

# -------------------------------------------------------------------
# WORKER LOOP
# -------------------------------------------------------------------

MAX_WORKERS = int(os.environ.get("AGENTTRACE_MAX_WORKERS", "4"))

def worker_loop():
    global shutdown_requested
    
    print(f"👷 Worker started with ID: {WORKER_ID}")
    print(f"🚀 Parallel Processing Enabled (Max Workers: {MAX_WORKERS})")
    
    # Start health check server
    health_server = start_health_server()
    
    print("   Waiting for jobs...")

    # Use ProcessPoolExecutor for true parallelism and isolation
    with concurrent.futures.ProcessPoolExecutor(
        max_workers=MAX_WORKERS, 
        initializer=init_worker_globals
    ) as executor:
        
        futures = set()
        last_reclaim_time = 0
        
        while not shutdown_requested:
            try:
                # Periodically reclaim stale jobs (every 30 seconds for aggressive recovery)
                current_time = time.time()
                if current_time - last_reclaim_time > 30:
                    reclaim_stale_jobs()
                    last_reclaim_time = current_time
                
                # Clean up finished futures to avoid memory leaks
                # wait(timeout=0) returns immediately with completed futures
                done, _ = concurrent.futures.wait(futures, timeout=0)
                for f in done:
                    try:
                        f.result() # Check for exceptions
                    except Exception as e:
                        print(f"❌ Job failed with exception: {e}")
                    futures.remove(f)

                # Fetch next job if we have capacity
                if len(futures) < MAX_WORKERS:
                    job = claim_job()
                    if job:
                        print(f"📥 Claimed Job {job['id']}. Submitting to pool. ({len(futures)+1}/{MAX_WORKERS} active)")
                        future = executor.submit(process_job, job, ORG_ID, WORKER_ID)
                        futures.add(future)
                    else:
                        # Sleep only if no job found to avoid busy loop
                        time.sleep(POLL_INTERVAL)
                else:
                    # Pool full, wait a bit
                    time.sleep(1)
                    
            except KeyboardInterrupt:
                print("\n🛑 Worker stopping...")
                break
            except Exception as e:
                print(f"⚠ Main loop error: {e}")
                time.sleep(POLL_INTERVAL)

if __name__ == "__main__":
    try:
        worker_loop()
    except KeyboardInterrupt:
        pass
    finally:
        print("👋 Worker shutdown complete.", flush=True)
