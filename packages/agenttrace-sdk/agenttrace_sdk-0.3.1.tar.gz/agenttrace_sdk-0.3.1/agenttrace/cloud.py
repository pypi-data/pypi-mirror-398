import os
import json
from pathlib import Path
from typing import Optional, Dict, Any
from datetime import datetime

try:
    from supabase import create_client, Client
except ImportError:
    create_client = None

from agenttrace import auth

# Supabase Configuration (SaaS)
# SECURITY: Credentials must be set via environment variables
SUPABASE_URL = os.environ.get("NEXT_PUBLIC_SUPABASE_URL")
SUPABASE_ANON_KEY = os.environ.get("NEXT_PUBLIC_SUPABASE_ANON_KEY")

# Validate credentials are configured
if not SUPABASE_URL or not SUPABASE_ANON_KEY:
    import warnings
    warnings.warn("Supabase credentials not configured. Set NEXT_PUBLIC_SUPABASE_URL and NEXT_PUBLIC_SUPABASE_ANON_KEY")

def get_supabase_client(token: str) -> Optional[Any]:
    """Create authenticated Supabase client"""
    if not create_client:
        return None
    
    if not SUPABASE_URL or not SUPABASE_ANON_KEY:
        return None
    
    client = create_client(SUPABASE_URL, SUPABASE_ANON_KEY)
    # FIX 2.3: Use postgrest auth instead of session with dummy refresh token
    # This avoids potential issues with token refresh
    client.postgrest.auth(token)
    return client

def upload_trace(trace_id: str, project_id: Optional[str] = None) -> Dict[str, Any]:
    """Upload a local trace to the cloud"""
    if not create_client:
        return {"error": "supabase-py not installed. Run: pip install supabase"}

    token = auth.get_token()
    if not token:
        return {"error": "Not logged in. Run: agenttrace login"}

    client = get_supabase_client(token)
    
    # Verify user
    try:
        user = client.auth.get_user()
        if not user:
             return {"error": "Invalid session. Please login again."}
    except Exception as e:
        return {"error": f"Authentication failed: {e}"}

    # Locate trace file
    trace_path = Path(f".agenttrace/traces/{trace_id}.json")
    if not trace_path.exists():
        return {"error": f"Trace not found: {trace_path}"}

    print(f"🚀 Uploading trace {trace_id}...")
    if project_id:
        print(f"  📂 Project: {project_id}")

    try:
        # 1. Upload to Storage
        with open(trace_path, "rb") as f:
            client.storage.from_("traces").upload(
                f"{trace_id}/events.json",
                f,
                file_options={"content-type": "application/json", "upsert": "true"}
            )
        print("  ✅ Events uploaded")

        # 2. Upload Keyframes (if exist)
        keyframes_path = Path(f".agenttrace/traces/{trace_id}_keyframes.json")
        if keyframes_path.exists():
            with open(keyframes_path, "rb") as f:
                client.storage.from_("snapshots").upload(
                    f"{trace_id}/keyframes.json",
                    f,
                    file_options={"content-type": "application/json", "upsert": "true"}
                )
            print("  ✅ Keyframes uploaded")
            
            # Upload individual snapshots
            try:
                keyframes_data = json.loads(keyframes_path.read_text())
                snapshots_dir = Path(".agenttrace/snapshots")
                count = 0
                for step, path_str in keyframes_data.items():
                    # path_str is likely absolute or relative to cwd, we need to find the file
                    # The recorder saves absolute paths usually, or relative to script
                    # Let's try to find it in .agenttrace/snapshots based on filename
                    filename = Path(path_str).name
                    snapshot_file = snapshots_dir / filename
                    
                    if snapshot_file.exists():
                         with open(snapshot_file, "rb") as f:
                            client.storage.from_("snapshots").upload(
                                f"{trace_id}/snapshots/{filename}",
                                f,
                                file_options={"content-type": "application/octet-stream", "upsert": "true"}
                            )
                         count += 1
                if count > 0:
                    print(f"  ✅ {count} snapshots uploaded")
            except Exception as e:
                print(f"  ⚠️  Snapshot upload warning: {e}")

        # 2b. Upload Script (Critical for Replay)
        metadata_path = Path(f".agenttrace/traces/{trace_id}/metadata.json")
        script_uploaded = False
        if metadata_path.exists():
            try:
                meta = json.loads(metadata_path.read_text("utf-8"))
                script_content = meta.get("script_content")
                script_path_str = meta.get("script_path")

                if script_content:
                    client.storage.from_("traces").upload(
                        f"{trace_id}/script.py",
                        script_content.encode("utf-8") if isinstance(script_content, str) else script_content,
                        file_options={"content-type": "text/x-python", "upsert": "true"}
                    )
                    script_uploaded = True
                    print("  ✅ Script uploaded (from metadata)")
                elif script_path_str and Path(script_path_str).exists():
                     with open(script_path_str, "rb") as f:
                        client.storage.from_("traces").upload(
                            f"{trace_id}/script.py",
                            f,
                            file_options={"content-type": "text/x-python", "upsert": "true"}
                        )
                     script_uploaded = True
                     print(f"  ✅ Script uploaded (from {Path(script_path_str).name})")
            except Exception as e:
                print(f"  ⚠️  Script upload warning: {e}")
        
        if not script_uploaded:
             print("  ⚠️  Warning: No script found to upload. Replay may fail.")

        # 3. Create Trace Record in DB
        # We need to get the org_id first. 
        # In a real app, we'd have an API for this or use a stored proc.
        # For now, we'll query the profiles table which RLS allows reading own profile.
        
        user_id = user.user.id
        profile_resp = client.table("profiles").select("organization_id").eq("user_id", user_id).single().execute()
        if not profile_resp.data:
             return {"error": "Profile not found. Please contact support."}
        
        org_id = profile_resp.data["organization_id"]

        # Read trace metadata for duration/status
        trace_data = json.loads(trace_path.read_text())
        start_time = trace_data[0]["timestamp"]
        end_time = trace_data[-1]["timestamp"]
        duration = end_time - start_time
        
        trace_record = {
            "id": trace_id,
            "org_id": org_id,
            "project_id": project_id,
            "title": f"Uploaded Trace {trace_id[:8]}",
            # NOTE: status column does not exist in traces table
            "created_at": datetime.fromtimestamp(start_time).isoformat(),
            "updated_at": datetime.now().isoformat()
        }

        # Uses Upsert
        client.table("traces").upsert(trace_record).execute()
        print("  ✅ Trace record created")

        # FIX 3.1: Clean up local trace after successful upload
        import shutil
        local_trace_dir = Path(f".agenttrace/traces/{trace_id}")
        if local_trace_dir.exists():
            shutil.rmtree(local_trace_dir)
            print("  🧹 Local trace cleaned up")

        return {"success": True, "trace_id": trace_id}

    except Exception as e:
        return {"error": f"Upload failed: {e}"}

