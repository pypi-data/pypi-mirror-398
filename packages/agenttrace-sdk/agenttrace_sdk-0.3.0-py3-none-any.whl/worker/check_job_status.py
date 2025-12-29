#!/usr/bin/env python3
"""Check job status"""

import os
import sys
from pathlib import Path
from dotenv import load_dotenv
from supabase import create_client

# Load environment variables
env_file = Path(__file__).parent.parent / "frontend" / ".env.local"
if env_file.exists():
    load_dotenv(dotenv_path=env_file)

SUPABASE_URL = os.environ.get("NEXT_PUBLIC_SUPABASE_URL")
SUPABASE_SERVICE_KEY = os.environ.get("SUPABASE_SERVICE_ROLE_KEY")

if len(sys.argv) > 1:
    job_id = sys.argv[1]
else:
    # Get latest job
    supabase = create_client(SUPABASE_URL, SUPABASE_SERVICE_KEY)
    jobs = supabase.table("jobs").select("*").order("created_at", desc=True).limit(1).execute()
    if not jobs.data:
        print("No jobs found")
        sys.exit(1)
    job_id = jobs.data[0]["id"]

supabase = create_client(SUPABASE_URL, SUPABASE_SERVICE_KEY)
job = supabase.table("jobs").select("*").eq("id", job_id).single().execute()

if job.data:
    j = job.data
    print(f"Job: {j['id']}")
    print(f"Status: {j['status']}")
    print(f"Trace: {j['trace_id']}")
    if j.get('output_url'):
        print(f"Output URL: {j['output_url']}")
    if j.get('error'):
        print(f"Error: {j['error']}")
    print(f"Created: {j.get('created_at')}")
    print(f"Started: {j.get('started_at')}")
    print(f"Finished: {j.get('finished_at')}")



