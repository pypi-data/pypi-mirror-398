#!/usr/bin/env python3
"""
Create a test job for the worker to process
"""

import os
import sys
import uuid
from pathlib import Path
from dotenv import load_dotenv
from supabase import create_client

# Load environment variables
load_dotenv(dotenv_path=Path(__file__).parent.parent / "frontend" / ".env.local")
load_dotenv(dotenv_path=Path(__file__).parent / ".env")

SUPABASE_URL = os.environ.get("SUPABASE_URL") or os.environ.get("NEXT_PUBLIC_SUPABASE_URL")
SUPABASE_SERVICE_KEY = os.environ.get("SUPABASE_SERVICE_ROLE_KEY")

if not SUPABASE_URL or not SUPABASE_SERVICE_KEY:
    print("❌ Error: SUPABASE_URL and SUPABASE_SERVICE_ROLE_KEY must be set")
    sys.exit(1)

supabase = create_client(SUPABASE_URL, SUPABASE_SERVICE_KEY)

# Get first trace from database
traces = supabase.table("traces").select("id, org_id").limit(1).execute()

if not traces.data:
    print("❌ No traces found in database. Upload a trace first!")
    sys.exit(1)

trace = traces.data[0]
trace_id = trace["id"]
org_id = trace["org_id"]

print(f"📋 Creating test job for trace: {trace_id}")

# Create a test job
job_id = str(uuid.uuid4())
job = {
    "id": job_id,
    "trace_id": trace_id,
    "org_id": org_id,
    "status": "pending",  # Changed from queued
    "fork_step": None,    # Changed from step
    "parent_trace_id": None, # Changed from branch_id
    "input_overrides": {},   # Changed from overrides
    "result_metadata": {     # Changed from metadata
        "test": True,
        "created_by": "test_script"
    }
}

result = supabase.table("jobs").insert(job).execute()

if result.data:
    print(f"✅ Job created: {job_id}")
    print(f"   Status: queued")
    print(f"   Trace: {trace_id}")
    print(f"\n💡 Now run the worker:")
    print(f"   cd worker")
    print(f"   python main.py")
else:
    print(f"❌ Failed to create job")
    print(result)



