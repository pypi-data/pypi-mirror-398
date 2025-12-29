import modal
import os
import random
import json
import time
from datetime import datetime, timedelta

# Define Modal App
app = modal.App("agenttrace-seeder")

# Define Image
image = modal.Image.debian_slim().pip_install("supabase==2.3.0", "gotrue==2.3.0")

@app.function(
    image=image,
    secrets=[modal.Secret.from_name("agenttrace-secrets")]
)
def seed_traces(user_email: str = None):
    from supabase import create_client, Client

    # 1. Connect to Supabase
    url = os.environ["NEXT_PUBLIC_SUPABASE_URL"]
    key = os.environ["SUPABASE_SERVICE_ROLE_KEY"]
    supabase: Client = create_client(url, key)

    print("🌱 Connecting to Supabase...")

    # 2. Find User (SaaS 3.0)
    user_id = None
    if user_email:
        # Check profiles or public users if available, otherwise just pick one
        pass
    
    # Fallback: Get most recent user from public.users
    if not user_id:
        res = supabase.table("users").select("id").limit(1).execute()
        if res.data:
            user_id = res.data[0]['id']
    
    if not user_id:
        print("❌ No users found in database.")
        return

    # Find Org
    res = supabase.table("organization_members").select("organization_id").eq("user_id", user_id).limit(1).execute()
    if not res.data:
        print(f"❌ User {user_id} has no organization.")
        return
    
    org_id = res.data[0]['organization_id']
    print(f"🎯 Seeding for User: {user_id} | Org: {org_id}")

    # 3. Generate Traces
    statuses = ['completed', 'failed', 'completed', 'completed', 'failed'] # mostly completed for demo
    titles = [
        'Modal Test Run', 'Cloud Inference', 'Distributed Scrape',
        'Analyze Large Dataset', 'Video Processing Pipeline'
    ]

    traces_to_insert = []
    
    # We need to insert one by one to get IDs for storage upload
    for i in range(5):
        title_base = random.choice(titles)
        title = f"{title_base} #{random.randint(1000, 9999)}"
        status = random.choice(statuses)
        
        # Create Trace Row
        trace_row = {
            "organization_id": org_id, # CORRECT COLUMN
            "owner_id": user_id,
            "title": title,
            "status": status,
            "total_steps": random.randint(5, 20),
            "script_path": "/scripts/demo.py",
            "tags": ["modal", "demo", "seed"],
            "created_at": (datetime.now() - timedelta(days=random.randint(0, 3))).isoformat()
        }
        
        # Insert to get ID
        insert_res = supabase.table("traces").insert(trace_row).execute()
        if not insert_res.data:
            print(f"Failed to insert trace {title}")
            continue
            
        trace_id = insert_res.data[0]['id']
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
        
        # Upload to Storage
        try:
             supabase.storage.from_("traces").upload(
                path=file_path,
                file=events_json.encode('utf-8'),
                file_options={"content-type": "application/json"}
            )
             print(f"   ✅ Uploaded events.json for {trace_id}")
        except Exception as e:
            print(f"   ⚠️ Failed to upload events.json: {e}")

    print(f"✅ Seeding Complete!")

@app.local_entrypoint()
def main():
    seed_traces.remote()
