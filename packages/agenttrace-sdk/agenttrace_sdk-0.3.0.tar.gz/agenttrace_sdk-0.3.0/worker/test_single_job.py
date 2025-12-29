#!/usr/bin/env python3
"""
Test worker with a single job (processes one job and exits)
"""

import os
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from dotenv import load_dotenv
from supabase import create_client

# Load environment variables from frontend/.env.local
env_file = Path(__file__).parent.parent / "frontend" / ".env.local"
if env_file.exists():
    load_dotenv(dotenv_path=env_file)
else:
    load_dotenv(dotenv_path=Path(__file__).parent / ".env")

SUPABASE_URL = os.environ.get("NEXT_PUBLIC_SUPABASE_URL") or os.environ.get("SUPABASE_URL")
SUPABASE_SERVICE_KEY = os.environ.get("SUPABASE_SERVICE_ROLE_KEY")

if not SUPABASE_URL or not SUPABASE_SERVICE_KEY:
    print("❌ Error: SUPABASE_URL and SUPABASE_SERVICE_ROLE_KEY must be set")
    print(f"   Looking for env file: {env_file}")
    print(f"   File exists: {env_file.exists()}")
    sys.exit(1)

# Initialize Supabase client
from supabase import create_client
supabase = create_client(SUPABASE_URL, SUPABASE_SERVICE_KEY)

# Import worker functions
sys.path.insert(0, str(Path(__file__).parent))
from main import process_job

print("Testing Worker - Single Job Mode")
print("=" * 60)

# Find a queued job
response = supabase.table("jobs").select("*").eq("status", "queued").limit(1).execute()
jobs = response.data if hasattr(response, "data") else []

if not jobs:
    print("No queued jobs found. Create a job first:")
    print("   python create_test_job.py")
    sys.exit(1)

job = jobs[0]
print(f"Processing job: {job['id']}")
print(f"   Trace: {job['trace_id']}")
print()

# Process the job
try:
    success = process_job(job)
    
    if success:
        print("\nTest completed successfully!")
        print("\nCheck the job status in Supabase:")
        print(f"   GET /api/cloud/jobs/{job['id']}")
    else:
        print("\nTest failed. Check the error messages above.")
        sys.exit(1)
except Exception as e:
    print(f"\nError processing job: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

