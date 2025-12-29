"""
AgentTrace Worker for Modal.io
==============================
Wraps the core worker/main.py logic for cloud execution.
"""

import modal
import os
import sys

# 1. Define Image & Dependencies
image = modal.Image.debian_slim(python_version="3.11").pip_install(
    "supabase",
    "python-dotenv",
    "requests",
    "groq",
    "psycopg2-binary",
    "fastapi"
)

# 2. Define App
app = modal.App("agenttrace-worker")

# 3. Define Secrets
secrets = modal.Secret.from_name("agenttrace-secrets")

# 4. Define Mounts
# Resolve paths relative to this script file to ensure they work regardless of CWD
script_dir = os.path.dirname(os.path.abspath(__file__))
root_dir = os.path.dirname(script_dir) # Go up one level to 'moat'
agenttrace_path = os.path.join(root_dir, "agenttrace")
worker_path = os.path.join(root_dir, "worker")

# Mount 'agenttrace' package
image = image.add_local_dir(
    agenttrace_path, 
    remote_path="/root/agenttrace",
)

# Mount 'worker' directory
image = image.add_local_dir(
    worker_path, 
    remote_path="/root/worker",
)

# -------------------------------------------------------------------
# HELPER FUNCTIONS
# -------------------------------------------------------------------

def init_supabase():
    """Initialize Supabase client inside the Modal container."""
    from supabase import create_client
    
    url = os.environ.get("NEXT_PUBLIC_SUPABASE_URL")
    key = os.environ.get("SUPABASE_SERVICE_ROLE_KEY")
    
    if not url or not key:
        raise ValueError("Missing Supabase credentials in environment")
    
    return create_client(url, key)

def get_org_id(client):
    """Fetch the first organization ID."""
    res = client.table("organizations").select("id").limit(1).execute()
    if res.data:
        return res.data[0]['id']
    return None

# -------------------------------------------------------------------
# MODAL FUNCTIONS
# -------------------------------------------------------------------

@app.function(
    image=image,
    secrets=[secrets],
    timeout=900, # 15 mins execution time
    concurrency_limit=50, # Limit parallel executions
)
def process_job_modal(job_id: str):
    """
    Execute a specific job using the core logic in worker/main.py.
    """
    print(f"☁️ Modal Worker: Received Job {job_id}")
    
    # Add /root to path for imports
    if "/root" not in sys.path:
        sys.path.insert(0, "/root")
    
    try:
        # Import the process_job function directly
        from worker.main import process_job, init_worker_globals
        
        # Initialize patches in this process
        init_worker_globals()
        
        # Create Supabase client
        client = init_supabase()
        
        # Get org ID
        org_id = get_org_id(client)
        worker_id = f"modal-{os.environ.get('MODAL_TASK_ID', 'unknown')}"
        
        print(f"   Org ID: {org_id}, Worker: {worker_id}")
        
        # Fetch the FULL job details
        response = client.table("jobs").select("*").eq("id", job_id).single().execute()
        
        if not response.data:
            print(f"❌ Job {job_id} not found in DB")
            return {"status": "error", "error": "Job not found"}
            
        job = response.data
        print(f"   Job trace_id: {job.get('trace_id')}")
        
        # Execute processing logic
        process_job(job, org_id, worker_id)
        
        return {"status": "success", "job_id": job_id}
        
    except Exception as e:
        print(f"❌ Modal Execution Failed: {e}")
        import traceback
        traceback.print_exc()
        raise

@app.function(
    image=image,
    secrets=[secrets],
    schedule=modal.Period(seconds=10), # Polling loop
)
def poller():
    """
    Periodically checks for pending jobs and spawns workers.
    Acting as a scalable dispatcher.
    """
    try:
        # Create Supabase client directly
        client = init_supabase()
        
        # Find pending jobs
        res = client.table("jobs") \
            .select("id, status") \
            .eq("status", "pending") \
            .limit(10) \
            .execute()
            
        jobs = res.data or []
        
        if jobs:
            print(f"👀 Poller found {len(jobs)} pending jobs.")
            
            for job in jobs:
                # Atomically claim for Modal Dispatch
                claim = client.table("jobs").update({
                    "status": "claimed",
                    "worker_id": "modal-dispatch",
                    "updated_at": "now()"
                }).eq("id", job['id']).eq("status", "pending").execute()
                
                if claim.data:
                    print(f"🚀 Spawning Modal Function for Job {job['id']}")
                    # Async spawn - does not block poller
                    process_job_modal.spawn(job['id'])
                    
    except Exception as e:
        print(f"⚠️ Poller Error: {e}")

@app.function(image=image)
@modal.web_endpoint()
def health():
    return {"status": "online", "mode": "modal-cloud-v3"}
