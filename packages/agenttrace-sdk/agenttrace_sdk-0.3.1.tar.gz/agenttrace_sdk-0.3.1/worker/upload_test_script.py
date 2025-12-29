# worker/upload_test_script.py
# Uploads a simple test script to a trace in storage so replay can work

import os
import sys
from pathlib import Path

# Add parent to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from dotenv import load_dotenv
from supabase import create_client

# Load env
env_file = Path(__file__).parent.parent / "frontend" / ".env"
if env_file.exists():
    load_dotenv(dotenv_path=env_file)

SUPABASE_URL = os.environ.get("NEXT_PUBLIC_SUPABASE_URL")
SUPABASE_SERVICE_KEY = os.environ.get("SUPABASE_SERVICE_ROLE_KEY")

if not SUPABASE_URL or not SUPABASE_SERVICE_KEY:
    print("❌ Missing Supabase credentials")
    sys.exit(1)

client = create_client(SUPABASE_URL, SUPABASE_SERVICE_KEY)

# Simple test script that the worker can execute
test_script = '''
# test_script.py - Simple script for replay testing
import time
import json

print("🚀 Test script started")

# Simulate some work
for i in range(3):
    print(f"Step {i+1}/3: Processing...")
    time.sleep(0.5)

# Generate a result
result = {
    "status": "success",
    "steps_completed": 3,
    "timestamp": time.time()
}

print(f"✅ Test complete: {json.dumps(result)}")
'''

# Get a trace ID from the database to upload to
print("📋 Fetching traces from database...")
res = client.table("traces").select("id, title, parent_trace_id").order("created_at", desc=True).limit(10).execute()

if not res.data:
    print("❌ No traces found")
    sys.exit(1)

print("\nTraces found:")
for i, trace in enumerate(res.data):
    print(f"  {i+1}. {trace['id'][:8]}... - {trace['title']} (parent: {trace.get('parent_trace_id', 'N/A')[:8] if trace.get('parent_trace_id') else 'None'})")

# Upload script to ALL traces (including parent traces)
trace_ids_to_upload = set()
for trace in res.data:
    trace_ids_to_upload.add(trace['id'])
    if trace.get('parent_trace_id'):
        trace_ids_to_upload.add(trace['parent_trace_id'])

print(f"\n🚀 Uploading test script to {len(trace_ids_to_upload)} trace storage folders...")

for trace_id in trace_ids_to_upload:
    try:
        client.storage.from_("traces").upload(
            f"{trace_id}/script.py",
            test_script.encode("utf-8"),
            {"content-type": "text/x-python", "upsert": "true"}
        )
        print(f"   ✅ Uploaded to {trace_id[:8]}...")
    except Exception as e:
        if "already exists" in str(e).lower():
            # Try upsert
            try:
                client.storage.from_("traces").update(
                    f"{trace_id}/script.py",
                    test_script.encode("utf-8"),
                    {"content-type": "text/x-python"}
                )
                print(f"   ✅ Updated {trace_id[:8]}...")
            except Exception as e2:
                print(f"   ⚠️ Skip {trace_id[:8]}: {e2}")
        else:
            print(f"   ⚠️ Skip {trace_id[:8]}: {e}")

print("\n✅ Done! Try clicking Replay on a trace now.")
