# Check trace status in database and storage
import os
from dotenv import load_dotenv
from supabase import create_client

load_dotenv('frontend/.env')

url = os.environ.get("NEXT_PUBLIC_SUPABASE_URL")
key = os.environ.get("SUPABASE_SERVICE_ROLE_KEY")
client = create_client(url, key)

# Traces to check
trace_ids = [
    "81d2f474-a80d-4aeb-918b-69e8ab7bc297",  # Stuck
    "845e9f6d-346d-473d-8153-e9992def82f1",  # Stuck
    "2f450b23-73ff-410d-86c7-2051b13c1947",  # Working
]

print("="*60)
print("TRACE INVESTIGATION")
print("="*60)

for tid in trace_ids:
    print(f"\n📋 Trace: {tid[:8]}...")
    
    # 1. Check if trace exists in DB
    db_result = client.table("traces").select("id, title, org_id").eq("id", tid).maybeSingle().execute()
    if db_result.data:
        print(f"   ✅ DB: {db_result.data['title']}")
    else:
        print(f"   ❌ DB: NOT FOUND")
    
    # 2. Check storage for events
    try:
        files = client.storage.from_("traces").list(tid)
        if files:
            print(f"   📁 Storage files: {[f['name'] for f in files]}")
        else:
            print(f"   ❌ Storage: EMPTY FOLDER")
    except Exception as e:
        print(f"   ❌ Storage error: {e}")
    
    # 3. Check if events.jsonl exists
    try:
        data = client.storage.from_("traces").download(f"{tid}/events.jsonl")
        if data:
            lines = data.decode('utf-8').strip().split('\n')
            print(f"   ✅ events.jsonl: {len(lines)} events")
        else:
            print(f"   ❌ events.jsonl: EMPTY")
    except Exception as e:
        if "404" in str(e) or "not found" in str(e).lower():
            print(f"   ❌ events.jsonl: NOT FOUND")
        else:
            print(f"   ❌ events.jsonl error: {e}")
    
    # 4. Check if script.py exists
    try:
        data = client.storage.from_("traces").download(f"{tid}/script.py")
        if data:
            print(f"   ✅ script.py: {len(data)} bytes")
        else:
            print(f"   ⚠ script.py: EMPTY")
    except Exception as e:
        if "404" in str(e) or "not found" in str(e).lower():
            print(f"   ⚠ script.py: NOT FOUND")
        else:
            print(f"   ⚠ script.py error: {e}")

print("\n" + "="*60)
