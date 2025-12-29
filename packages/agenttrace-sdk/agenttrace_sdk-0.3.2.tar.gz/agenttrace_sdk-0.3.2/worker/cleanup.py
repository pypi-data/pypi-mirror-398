
import os
import sys
from dotenv import load_dotenv
from supabase import create_client, Client

# Load environment variables
load_dotenv('.env') 
load_dotenv('frontend/.env.local')

URL = os.getenv("NEXT_PUBLIC_SUPABASE_URL")
KEY = os.getenv("SUPABASE_SERVICE_ROLE_KEY")

if not URL or not KEY:
    print("Missing env vars")
    sys.exit(1)

supabase: Client = create_client(URL, KEY)

print("🗑️ Deleting all traces...")

# Delete all traces
res = supabase.table("traces").delete().neq("id", "00000000-0000-0000-0000-000000000000").execute()

print(f"✅ Deleted {len(res.data) if res.data else 0} traces.")
