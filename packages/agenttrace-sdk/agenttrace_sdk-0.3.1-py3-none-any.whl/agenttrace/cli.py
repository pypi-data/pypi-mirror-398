#!/usr/bin/env python3
"""
AgentTrace CLI - Command-line interface for time-travel debugging
"""
import sys
import os
import argparse
import json
from pathlib import Path
from agenttrace.branches import storage as branch_storage

def cmd_record(args):
    """Record a trace"""
    os.environ["AGENTTRACE_MODE"] = "RECORD"
    
    # Import and run the script
    script_path = args.script
    if not os.path.exists(script_path):
        print(f"Error: Script not found: {script_path}")
        return 1
    
    # Add script directory to path
    script_dir = os.path.dirname(os.path.abspath(script_path))
    sys.path.insert(0, script_dir)
    
    # Read script content for storage
    script_content = None
    try:
        with open(script_path, 'r', encoding='utf-8') as f:
            script_content = f.read()
    except Exception as e:
        print(f"Warning: Could not read script content: {e}")
    
    # Import agenttrace before running
    import agenttrace.instrumentation.bootstrap
    from agenttrace.core.tracer import Tracer
    
    # Set script info before bootstrap
    tracer = Tracer.get_instance()
    tracer.script_path = os.path.abspath(script_path)
    tracer.script_content = script_content
    
    agenttrace.instrumentation.bootstrap.bootstrap()
    
    # Execute the script (Sandboxed)
    from agenttrace.vfs.patch import patch_io
    print("🔒 VFS Sandbox: ACTIVE (File I/O will be virtualized)")
    with patch_io():
        with open(script_path, 'r') as f:
            code = compile(f.read(), script_path, 'exec')
            exec(code, {'__name__': '__main__', '__file__': script_path})
    
    # Get trace ID
    from agenttrace.core.tracer import Tracer
    tracer = Tracer.get_instance()
    if tracer.trace_id:
        print(f"\n✅ Trace recorded: {tracer.trace_id}")
        print(f"📁 Trace file: .agenttrace/traces/{tracer.trace_id}.json")
        return 0
    else:
        print("❌ No trace was recorded")
        return 1

def cmd_replay(args):
    """Replay a trace"""
    trace_id = args.trace_id
    step = args.step
    branch = args.branch
    
    os.environ["AGENTTRACE_MODE"] = "REPLAY"
    os.environ["AGENTTRACE_ID"] = trace_id
    if step is not None:
        os.environ["AGENTTRACE_STEP"] = str(step)
    if branch:
        os.environ["AGENTTRACE_BRANCH"] = branch
    
    # Load trace to get original script path (if stored)
    trace_file = Path(f".agenttrace/traces/{trace_id}.json")
    if not trace_file.exists():
        print(f"Error: Trace not found: {trace_id}")
        return 1
    
    print(f"🔄 Replaying trace: {trace_id}")
    if step is not None:
        print(f"📍 Jumping to step: {step}")
    if branch:
        print(f"🌿 Using branch: {branch}")
    
    # Import agenttrace
    import agenttrace.instrumentation.bootstrap
    agenttrace.instrumentation.bootstrap.bootstrap()
    
    # For now, we can't automatically rerun the script
    # User needs to run it manually or we store the script path
    print("⚠️  Note: Replay mode is active. Run your original script to see replay in action.")
    return 0

def cmd_list(args):
    """List all traces"""
    traces_dir = Path(".agenttrace/traces")
    if not traces_dir.exists():
        print("No traces found")
        return 0
    
    traces = []
    for trace_file in traces_dir.glob("*.json"):
        if trace_file.name.endswith("_keyframes.json"):
            continue
        
        trace_id = trace_file.stem
        try:
            with open(trace_file) as f:
                data = json.load(f)
                if data:
                    first_event = data[0]
                    last_event = data[-1]
                    traces.append({
                        "id": trace_id,
                        "events": len(data),
                        "start": first_event.get("timestamp", 0),
                        "end": last_event.get("timestamp", 0)
                    })
        except:
            pass
    
    if not traces:
        print("No traces found")
        return 0
    
    print(f"\n📊 Found {len(traces)} trace(s):\n")
    print(f"{'Trace ID':<40} {'Events':<10} {'Duration':<15}")
    print("-" * 65)
    
    for trace in sorted(traces, key=lambda x: x["start"], reverse=True):
        duration = trace["end"] - trace["start"]
        print(f"{trace['id']:<40} {trace['events']:<10} {duration:.2f}s")
    
    return 0

def cmd_ui(args):
    """Launch web UI (Next.js frontend)"""
    import subprocess
    import os
    import sys
    from pathlib import Path
    
    # Find frontend directory
    current_dir = Path(os.getcwd())
    frontend_dir = current_dir / "frontend"
    
    # Try relative to agenttrace package
    if not frontend_dir.exists():
        agenttrace_dir = Path(__file__).parent.parent
        frontend_dir = agenttrace_dir.parent / "frontend"
    
    if not frontend_dir.exists():
        print("❌ Frontend directory not found!")
        print("📝 To set up the frontend:")
        print("   1. cd frontend")
        print("   2. npm install")
        print("   3. npm run dev")
        return 1
    
    print("🌐 Starting AgentTrace Next.js Frontend...")
    print("📝 Open http://localhost:3000 in your browser")
    print("⚠️  Press Ctrl+C to stop\n")
    
    try:
        os.chdir(frontend_dir)
        subprocess.run(["npm", "run", "dev"], check=True)
    except KeyboardInterrupt:
        print("\n👋 Server stopped")
        return 0
    except FileNotFoundError:
        print("❌ npm not found. Please install Node.js:")
        print("   https://nodejs.org/")
        print("\nOr run manually:")
        print(f"   cd {frontend_dir}")
        print("   npm run dev")
        return 1
    except Exception as e:
        print(f"❌ Error: {e}")
        print("\nRun manually:")
        print(f"   cd {frontend_dir}")
        print("   npm run dev")
        return 1
    
    return 0

def cmd_fix(args):
    """Auto-fix errors in a trace using AI (Groq)"""
    from agenttrace.afe.local import auto_fix_local
    import json
    
    use_ai = not args.no_ai
    api_key = args.api_key
    model = args.model
    
    if use_ai:
        print("🤖 Using AI-powered auto-fix (Groq)...")
        if not api_key:
            print("💡 Tip: Set GROQ_API_KEY in .env file or use --api-key flag")
        if model:
            print(f"🧠 Using Groq model: {model}")
        else:
            print("🧠 Using default Groq model (override via GROQ_MODEL or --model)")
    else:
        print("🔧 Using heuristic-based suggestions...")
    
    result = auto_fix_local(
        args.trace_id,
        step=args.step,
        use_ai=use_ai,
        groq_api_key=api_key,
        groq_model=model
    )
    
    if "error" in result:
        print(f"❌ {result['error']}")
        if "GROQ_API_KEY" in result.get('error', ''):
            print("\n📝 To set up your API key/model:")
            print("   1. Create a .env file in the project root")
            print("   2. Add: GROQ_API_KEY=your_key_here")
            print("   3. (Optional) Add: GROQ_MODEL=preferred_model")
            print("   4. Or use: agenttrace fix <trace-id> --api-key your_key [--model llama3-8b-8192]")
        return 1
    
    print(f"\n🔧 Auto-Fix Analysis for {args.trace_id}")
    print(f"📊 {result.get('summary', '')}\n")
    
    for fix in result.get("fixes", []):
        error_type = fix['error_event'].get('type', 'unknown')
        payload = fix['error_event'].get('payload', {})
        error_name = payload.get('error_type', error_type)
        error_msg = payload.get('message', '')
        
        print(f"📍 Step {fix['step']}: {error_name}")
        if error_msg:
            print(f"   Message: {error_msg}")
        print()
        
        # Display AI-generated fix
        if fix.get('ai_fix') and not fix.get('ai_failed'):
            ai_fix = fix['ai_fix']
            print("🤖 AI-Generated Fix:")
            print("-" * 60)
            
            if isinstance(ai_fix, dict):
                if 'analysis' in ai_fix:
                    print(f"📋 Analysis: {ai_fix['analysis']}")
                if 'root_cause' in ai_fix:
                    print(f"🔍 Root Cause: {ai_fix['root_cause']}")
                
                fix_info = ai_fix.get('fix', {})
                if fix_info:
                    print(f"\n📝 Fix for {fix_info.get('file', 'unknown')} (line {fix_info.get('line', '?')}):")
                    if fix_info.get('original_code'):
                        print(f"\n❌ Original Code:\n{fix_info['original_code']}")
                    if fix_info.get('fixed_code'):
                        print(f"\n✅ Fixed Code:\n{fix_info['fixed_code']}")
                    if fix_info.get('explanation'):
                        print(f"\n💡 Explanation: {fix_info['explanation']}")
                
                if 'suggestions' in ai_fix and ai_fix['suggestions']:
                    print("\n💡 Additional Suggestions:")
                    for suggestion in ai_fix['suggestions']:
                        print(f"   • {suggestion}")
            else:
                # Raw response fallback
                print(ai_fix)
            
            print("-" * 60)
        
        # Display fallback suggestions
        elif fix.get('suggestions'):
            print("💡 Suggestions:")
            for suggestion in fix.get("suggestions", []):
                print(f"  ⚠️  {suggestion['issue']}")
                print(f"  💡 {suggestion['suggestion']}")
                if suggestion.get("code"):
                    print(f"  📝 Code:\n{suggestion['code']}")
        
        print()
    
    return 0


def cmd_branch(args):
    """Branch management commands"""
    sub = args.branch_command
    if not sub:
        print("Available actions: create, edit, list")
        return 1

    if sub == "create":
        try:
            data = branch_storage.create_branch(args.trace_id, args.step, args.name)
        except Exception as e:
            print(f"❌ Failed to create branch: {e}")
            return 1
        print(f"✅ Branch created: {data['branch_id']} (fork step {data['fork_step']})")
        return 0

    if sub == "edit":
        try:
            payload = json.loads(args.payload)
        except json.JSONDecodeError as e:
            print(f"❌ Invalid JSON payload: {e}")
            return 1
        try:
            branch_storage.update_override(args.branch_id, args.event, payload)
        except Exception as e:
            print(f"❌ Failed to update branch: {e}")
            return 1
        print(f"✅ Updated branch {args.branch_id} at event {args.event}")
        return 0

    if sub == "list":
        items = branch_storage.list_branches(args.trace_id)
        if not items:
            print("No branches found")
            return 0
        print(f"\n🌿 Branches ({len(items)}):\n")
        for item in items:
            print(f"- {item['branch_id']} (trace {item['parent_trace_id']}, step {item['fork_step']})")
        return 0

    print(f"Unknown branch action: {sub}")
    return 1

def main():
    parser = argparse.ArgumentParser(description="AgentTrace - Time-Travel Debugging for AI Agents")
    subparsers = parser.add_subparsers(dest="command", help="Command to run")
    
    # Record command
    record_parser = subparsers.add_parser("record", help="Record a new trace")
    record_parser.add_argument("script", help="Python script to record")
    
    # Replay command
    replay_parser = subparsers.add_parser("replay", help="Replay a trace")
    replay_parser.add_argument("trace_id", help="Trace ID to replay")
    replay_parser.add_argument("--step", type=int, help="Jump to specific step")
    replay_parser.add_argument("--branch", help="Replay using branch overrides")
    
    # List command
    list_parser = subparsers.add_parser("list", help="List all traces")
    
    # UI command
    ui_parser = subparsers.add_parser("ui", help="Launch web UI")
    
    # Fix command
    fix_parser = subparsers.add_parser("fix", help="Auto-fix errors in a trace using AI (Groq)")
    fix_parser.add_argument("trace_id", help="Trace ID to analyze")
    fix_parser.add_argument("--step", type=int, help="Specific step to fix")
    fix_parser.add_argument("--no-ai", action="store_true", help="Use heuristic suggestions instead of AI")
    fix_parser.add_argument("--api-key", help="Groq API key (overrides GROQ_API_KEY env var)")
    fix_parser.add_argument("--model", help="Groq model (overrides GROQ_MODEL env var)")

    # Branch command
    branch_parser = subparsers.add_parser("branch", help="Manage branches")
    branch_sub = branch_parser.add_subparsers(dest="branch_command")

    branch_create = branch_sub.add_parser("create", help="Create a branch")
    branch_create.add_argument("trace_id", help="Parent trace ID")
    branch_create.add_argument("--step", type=int, required=True, help="Fork step (must have snapshot)")
    branch_create.add_argument("--name", help="Branch name")

    branch_edit = branch_sub.add_parser("edit", help="Edit branch event payload")
    branch_edit.add_argument("branch_id")
    branch_edit.add_argument("--event", type=int, required=True, help="Event sequence number to override")
    branch_edit.add_argument("--payload", required=True, help="JSON payload override")

    branch_list = branch_sub.add_parser("list", help="List branches")
    branch_list.add_argument("--trace-id", help="Filter by parent trace")
    
    # Login command
    login_parser = subparsers.add_parser("login", help="Login to AgentTrace Cloud")
    login_parser.add_argument("--token", help="Supabase Access Token")
    
    # Push command
    push_parser = subparsers.add_parser("push", help="Push a trace to AgentTrace Cloud")
    push_parser.add_argument("trace_id", help="Trace ID to push")
    push_parser.add_argument("--project", help="Project ID to assign trace to")
    
    # Verify command - deterministic testing
    verify_parser = subparsers.add_parser("verify", help="Verify deterministic execution")
    verify_parser.add_argument("script", help="Script to verify")
    verify_parser.add_argument("--runs", type=int, default=2, help="Number of runs to compare (default: 2)")
    verify_parser.add_argument("--fork-step", type=int, help="Fork at this step with override")
    verify_parser.add_argument("--override", help="JSON event override for What-If testing")
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        return 1
    
    commands = {
        "record": cmd_record,
        "replay": cmd_replay,
        "list": cmd_list,
        "ui": cmd_ui,
        "fix": cmd_fix,
        "branch": cmd_branch,
        "login": cmd_login,
        "push": cmd_push,
        "verify": cmd_verify
    }
    
    return commands[args.command](args)

def cmd_login(args):
    """Login to AgentTrace Cloud"""
    from agenttrace import auth
    
    token = args.token
    if not token:
        import getpass
        print("🔑 Enter your Supabase Access Token:")
        print("   (Get one from your project dashboard or ask your admin)")
        token = getpass.getpass("Token: ")
    
    if not token:
        print("❌ Token required")
        return 1
        
    auth.login(token)
    print("✅ Successfully logged in!")
    return 0

def cmd_push(args):
    """Push a trace to AgentTrace Cloud"""
    from agenttrace import cloud
    
    result = cloud.upload_trace(args.trace_id, project_id=args.project)
    
    if "error" in result:
        print(f"❌ {result['error']}")
        return 1
    
    print(f"\n✨ Trace {args.trace_id} pushed successfully!")
    print(f"   View at: http://localhost:3000/trace/{args.trace_id}") # TODO: Use real URL
    return 0


def cmd_verify(args):
    """Verify deterministic execution by running script multiple times and comparing outputs."""
    import hashlib
    import tempfile
    import shutil
    
    script_path = args.script
    num_runs = args.runs
    fork_step = getattr(args, 'fork_step', None)
    override_json = getattr(args, 'override', None)
    
    if not os.path.exists(script_path):
        print(f"❌ Script not found: {script_path}")
        return 1
    
    print("=" * 60)
    print("AGENTTRACE DETERMINISM VERIFICATION")
    print("=" * 60)
    print(f"Script: {script_path}")
    print(f"Runs: {num_runs}")
    if fork_step:
        print(f"Fork step: {fork_step}")
    if override_json:
        print(f"Override: {override_json}")
    print()
    
    # Parse override if provided
    override = None
    if override_json:
        try:
            override = json.loads(override_json)
        except json.JSONDecodeError as e:
            print(f"❌ Invalid JSON override: {e}")
            return 1
    
    # Create temp directory for traces
    temp_dir = tempfile.mkdtemp(prefix="agenttrace_verify_")
    hashes = []
    
    try:
        for run in range(1, num_runs + 1):
            print(f"Run {run}/{num_runs}...")
            
            # Reset tracer singleton
            from agenttrace.core.tracer import Tracer
            Tracer._instance = None
            tracer = Tracer.get_instance()
            tracer.storage_root = temp_dir
            
            trace_id = f"verify-run-{run}"
            
            # Start recording with optional override
            tracer.start_recording(
                trace_id=trace_id,
                fork_step=fork_step,
                event_override=override,
                skip_instrumentation=True
            )
            
            # Execute the script
            script_dir = os.path.dirname(os.path.abspath(script_path))
            sys.path.insert(0, script_dir)
            
            try:
                with open(script_path, 'r') as f:
                    code = compile(f.read(), script_path, 'exec')
                    exec(code, {'__name__': '__main__', '__file__': script_path})
            except Exception as e:
                print(f"  ❌ Execution error: {e}")
                return 1
            
            # Compute hash of events (excluding timestamps)
            events_path = os.path.join(temp_dir, trace_id, "events.jsonl")
            if os.path.exists(events_path):
                with open(events_path, 'r') as f:
                    events = []
                    for line in f:
                        if line.strip():
                            try:
                                event = json.loads(line)
                                event.pop("timestamp", None)
                                events.append(json.dumps(event, sort_keys=True, separators=(',', ':')))
                            except:
                                events.append(line.strip())
                    
                    content = "\n".join(events)
                    hash_val = hashlib.sha256(content.encode()).hexdigest()
                    hashes.append(hash_val)
                    print(f"  Hash: {hash_val[:16]}...")
            else:
                print(f"  ❌ No events recorded")
                return 1
        
        print()
        print("=" * 60)
        
        # Compare hashes
        if len(set(hashes)) == 1:
            print("[PASS] All runs produced identical outputs!")
            print(f"  SHA256: {hashes[0]}")
            return 0
        else:
            print("[FAIL] Outputs differ between runs!")
            for i, h in enumerate(hashes, 1):
                print(f"  Run {i}: {h}")
            return 1
    
    finally:
        shutil.rmtree(temp_dir, ignore_errors=True)


if __name__ == "__main__":
    sys.exit(main())


