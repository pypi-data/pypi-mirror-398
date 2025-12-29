# Check if script.py exists in Supabase storage for the new trace
import os
from dotenv import load_dotenv
from supabase import create_client

load_dotenv('frontend/.env')

url = os.environ.get("NEXT_PUBLIC_SUPABASE_URL")
key = os.environ.get("SUPABASE_SERVICE_ROLE_KEY")
client = create_client(url, key)

trace_id = "f65a7427-eaa0-4a2b-bb21-3da17c359396"

print(f"Checking trace: {trace_id}")

# List files
files = client.storage.from_("traces").list(trace_id)
print(f"Files in storage: {[f['name'] for f in files] if files else 'NONE'}")

# Check if script.py exists
try:
    data = client.storage.from_("traces").download(f"{trace_id}/script.py")
    if data:
        print(f"\n✅ script.py FOUND! Size: {len(data)} bytes")
        print(f"First 200 chars:\n{data.decode('utf-8')[:200]}")
    else:
        print("❌ script.py is EMPTY")
except Exception as e:
    print(f"❌ script.py NOT FOUND: {e}")
