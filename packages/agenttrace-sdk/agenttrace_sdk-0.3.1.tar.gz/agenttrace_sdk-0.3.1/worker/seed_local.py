import os
import random
import json
import time
import requests
from datetime import datetime, timedelta
from dotenv import load_dotenv

# Load environment variables
load_dotenv('.env') 
load_dotenv('frontend/.env.local')

URL = os.getenv("NEXT_PUBLIC_SUPABASE_URL")
KEY = os.getenv("SUPABASE_SERVICE_ROLE_KEY")

HEADERS = {
    "apikey": KEY,
    "Authorization": f"Bearer {KEY}",
    "Content-Type": "application/json",
    "Prefer": "return=representation" # Force return of data
}

def seed_traces():
    if not URL or not KEY:
        print("❌ Missing env vars")
        return

    print("🌱 Connecting to Supabase (via HTTP)...")

    # 1. Find User
    # Fallback: Get most recent user
    resp = requests.get(f"{URL}/rest/v1/users?select=id&limit=1", headers=HEADERS)
    if resp.status_code != 200:
        print(f"Failed to fetch users: {resp.text}")
        return
        
    users_data = resp.json()
    if not users_data:
        print("❌ No users found in database.")
        return
        
    user_id = users_data[0]['id']

    # Find Org
    resp = requests.get(f"{URL}/rest/v1/organization_members?select=organization_id&user_id=eq.{user_id}&limit=1", headers=HEADERS)
    org_data = resp.json()
    
    if not org_data:
        print(f"❌ User {user_id} has no organization.")
        return
    
    org_id = org_data[0]['organization_id']
    print(f"🎯 Seeding for User: {user_id} | Org: {org_id}")

    # 3. Generate Traces
    statuses = ['ok', 'error', 'ok', 'ok', 'error'] 
    titles = [
        'Local Test Run', 'Debug Session', 'Data Pipeline',
        'Model Training', 'API Integration'
    ]

    for i in range(5):
        title_base = random.choice(titles)
        title = f"{title_base} #{random.randint(1000, 9999)}"
        status = random.choice(statuses)
        
        # Create Trace Row
        trace_row = {
            "organization_id": org_id,
           # "owner_id": user_id,
            "title": title,
            "status": status,
            "total_steps": random.randint(5, 20),
            "script_path": "/scripts/local_debug.py",
            "tags": ["local", "debug"],
            "created_at": (datetime.now() - timedelta(days=random.randint(0, 3))).isoformat()
        }
        
        # Insert (Raw HTTP)
        resp = requests.post(f"{URL}/rest/v1/traces", headers=HEADERS, json=trace_row)
        
        if resp.status_code not in [200, 201]:
            print(f"Failed to insert trace {title}: {resp.status_code} {resp.text}")
            continue
            
        inserted_data = resp.json()
        if not inserted_data:
             print(f"Inserted but no data returned for {title}")
             continue
             
        trace_id = inserted_data[0]['id']
        print(f"   Trace created: {trace_id}")

        # 4. Generate & Upload events.json
        events = []
        step_count = trace_row['total_steps']
        
        for step in range(step_count):
            event_type = "tool_start" if step % 2 == 0 else "tool_end"
            if step == 0: event_type = "call_start"
            if step == step_count - 1: event_type = "call_end"
            
            event = {
                "seq": step,
                "type": event_type,
                "timestamp": time.time() + step,
                "payload": {
                    "step": step,
                    "content": f"Step {step} execution content...",
                    "tool": "demo-tool" if "tool" in event_type else None
                },
                "is_keyframe": False
            }
            events.append(event)
            
        # Serialize
        events_json = json.dumps(events)
        file_path = f"{trace_id}/events.json"
        
        # Upload to Storage (Raw HTTP)
        # Storage API: POST /storage/v1/object/{bucket}/{wildcard}
        # Note: Usually requires different endpoint /storage/v1/object...
        
        # Try finding the storage URL. Typically it's {SUPABASE_URL}/storage/v1/object/{bucket}/{path}
        storage_url = f"{URL}/storage/v1/object/traces/{file_path}"
        storage_headers = {
            "apikey": KEY,
            "Authorization": f"Bearer {KEY}",
            "Content-Type": "application/json",
            "x-upsert": "true"
        }
        
        storage_resp = requests.post(storage_url, headers=storage_headers, data=events_json)
        
        if storage_resp.status_code in [200, 201, 204]:
             print(f"   ✅ Uploaded events.json for {trace_id}")
        else:
            print(f"   ⚠️ Failed to upload events.json: {storage_resp.status_code} {storage_resp.text}")

    print(f"✅ Seeding Complete (Raw HTTP)!")

if __name__ == "__main__":
    seed_traces()
