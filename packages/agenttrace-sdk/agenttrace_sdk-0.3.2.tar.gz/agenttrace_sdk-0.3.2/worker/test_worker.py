#!/usr/bin/env python3
"""
Quick test script for the worker
Tests connection and job polling without running full worker loop
"""

import os
import sys
from pathlib import Path

# Add parent directory to path for agenttrace imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from dotenv import load_dotenv
from supabase import create_client

# Load environment variables from frontend/.env.local or worker/.env
load_dotenv(dotenv_path=Path(__file__).parent.parent / "frontend" / ".env.local")
load_dotenv(dotenv_path=Path(__file__).parent / ".env")

SUPABASE_URL = os.environ.get("SUPABASE_URL") or os.environ.get("NEXT_PUBLIC_SUPABASE_URL")
SUPABASE_SERVICE_KEY = os.environ.get("SUPABASE_SERVICE_ROLE_KEY") or os.environ.get("SUPABASE_SERVICE_ROLE_KEY")

print("🧪 Testing Worker Connection...")
print(f"   SUPABASE_URL: {SUPABASE_URL[:50] if SUPABASE_URL else 'NOT SET'}...")
print(f"   SUPABASE_SERVICE_KEY: {'SET' if SUPABASE_SERVICE_KEY else 'NOT SET'}")
print()

if not SUPABASE_URL or not SUPABASE_SERVICE_KEY:
    print("❌ Error: SUPABASE_URL and SUPABASE_SERVICE_ROLE_KEY must be set")
    print("\n💡 Create worker/.env with:")
    print("   SUPABASE_URL=...")
    print("   SUPABASE_SERVICE_ROLE_KEY=...")
    sys.exit(1)

try:
    # Test Supabase connection
    supabase = create_client(SUPABASE_URL, SUPABASE_SERVICE_KEY)
    print("✅ Supabase client created")
    
    # Test database connection
    response = supabase.table("jobs").select("id").limit(1).execute()
    print("✅ Database connection working")
    
    # Test storage connection
    buckets = supabase.storage.list_buckets()
    print(f"✅ Storage connection working ({len(buckets)} buckets)")
    
    # Check for queued jobs
    jobs = supabase.table("jobs").select("*").eq("status", "queued").limit(5).execute()
    job_count = len(jobs.data) if hasattr(jobs, 'data') else 0
    print(f"✅ Found {job_count} queued job(s)")
    
    if job_count > 0:
        print("\n📋 Queued jobs:")
        for job in jobs.data:
            print(f"   - Job {job['id']}: Trace {job['trace_id']}")
    
    print("\n✅ All tests passed! Worker is ready to run.")
    print("\n💡 To start the worker:")
    print("   cd worker")
    print("   python main.py")
    
except Exception as e:
    print(f"\n❌ Error: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)



