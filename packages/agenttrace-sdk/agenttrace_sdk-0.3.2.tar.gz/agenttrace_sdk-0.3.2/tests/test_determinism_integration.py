"""
Integration test for What-If Determinism

Verifies that running the same job with the same override twice produces
identical outputs (SHA256 match).

Usage:
    python tests/test_determinism_integration.py

What it does:
1. Creates a test script with deterministic @tool functions
2. Runs trace recording twice with same fork_step and event_override
3. Compares events.jsonl SHA256 hashes
4. Reports PASS if identical, FAIL if different
"""

import os
import sys
import hashlib
import tempfile
import json
import shutil

# Add parent to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from agenttrace.core.tracer import Tracer


# Test script that simulates a simple agent workflow
TEST_SCRIPT = '''
from agenttrace import tracer, tool, trace

@tool
def get_market_data(ticker: str):
    """Simulates fetching market data"""
    return {"price": 175.5, "trend": "bullish", "volume": 5000000}

@tool
def generate_recommendation(data: dict):
    """Generate recommendation based on market data"""
    if data.get("trend") == "bearish":
        return {"action": "SELL", "confidence": 0.9}
    else:
        return {"action": "BUY", "confidence": 0.85}

@trace
def analyze_market(ticker: str):
    data = get_market_data(ticker)
    rec = generate_recommendation(data)
    return {"recommendation": f"{rec['action']} with {int(rec['confidence']*100)}% confidence"}

if __name__ == "__main__":
    result = analyze_market("AAPL")
    print(f"Result: {result}")
'''

# Override to inject: change trend from bullish to bearish
OVERRIDE = {
    "type": "tool_end",
    "payload": {
        "tool": "get_market_data",
        "result": {"price": 175.5, "trend": "bearish", "volume": 5000000}
    }
}


def compute_events_hash(events_path: str) -> str:
    """Compute SHA256 hash of events.jsonl content (normalized)"""
    if not os.path.exists(events_path):
        return "FILE_NOT_FOUND"
    
    with open(events_path, 'r', encoding='utf-8') as f:
        lines = f.readlines()
    
    # Parse, normalize (remove timestamps), and re-serialize for stable comparison
    normalized = []
    for line in lines:
        if not line.strip():
            continue
        try:
            event = json.loads(line)
            # Remove timestamp for comparison (varies between runs)
            event.pop("timestamp", None)
            normalized.append(json.dumps(event, sort_keys=True, separators=(',', ':')))
        except json.JSONDecodeError:
            normalized.append(line.strip())
    
    content = "\n".join(normalized)
    return hashlib.sha256(content.encode()).hexdigest()


def run_trace(run_id: str, storage_root: str) -> str:
    """Run the test script with injection and return the events file path"""
    trace_id = f"test-determinism-{run_id}"
    
    # Reset singleton
    Tracer._instance = None
    tracer = Tracer.get_instance()
    tracer.storage_root = storage_root
    
    # Start recording with same override both times
    tracer.start_recording(
        trace_id=trace_id,
        fork_step=2,  # Inject at get_market_data tool_end
        event_override=OVERRIDE,
        skip_instrumentation=True
    )
    
    # Execute the test functions
    from agenttrace import tool, trace
    
    @tool
    def get_market_data(ticker: str):
        return {"price": 175.5, "trend": "bullish", "volume": 5000000}
    
    @tool
    def generate_recommendation(data: dict):
        if data.get("trend") == "bearish":
            return {"action": "SELL", "confidence": 0.9}
        else:
            return {"action": "BUY", "confidence": 0.85}
    
    @trace
    def analyze_market(ticker: str):
        data = get_market_data(ticker)
        rec = generate_recommendation(data)
        return {"recommendation": f"{rec['action']} with {int(rec['confidence']*100)}% confidence"}
    
    # Run the analysis
    result = analyze_market("AAPL")
    print(f"  Run {run_id}: {result}")
    
    # Flush events to disk (atomic injection already persists immediately, 
    # but ensure any remaining events are written)
    if hasattr(tracer, "_flush_events_to_disk"):
        tracer._flush_events_to_disk()
    
    return os.path.join(storage_root, trace_id, "events.jsonl")


def main():
    print("=" * 60)
    print("DETERMINISM INTEGRATION TEST")
    print("=" * 60)
    print()
    print("Testing: Same job + same override → identical outputs?")
    print()
    
    # Create temp directory
    temp_dir = tempfile.mkdtemp(prefix="agenttrace_determinism_")
    print(f"Storage: {temp_dir}")
    print()
    
    try:
        # Run 1
        print("Run 1:")
        events_path_1 = run_trace("run1", temp_dir)
        hash_1 = compute_events_hash(events_path_1)
        print(f"  Hash: {hash_1[:16]}...")
        print()
        
        # Run 2
        print("Run 2:")
        events_path_2 = run_trace("run2", temp_dir)
        hash_2 = compute_events_hash(events_path_2)
        print(f"  Hash: {hash_2[:16]}...")
        print()
        
        # Compare
        print("=" * 60)
        if hash_1 == hash_2:
            print("[PASS] Both runs produced identical outputs!")
            print(f"   SHA256: {hash_1}")
            return 0
        else:
            print("[FAIL] Outputs differ between runs!")
            print(f"   Run 1: {hash_1}")
            print(f"   Run 2: {hash_2}")
            
            # Show diff
            print()
            print("Diff:")
            with open(events_path_1) as f1, open(events_path_2) as f2:
                events1 = [json.loads(l) for l in f1 if l.strip()]
                events2 = [json.loads(l) for l in f2 if l.strip()]
                
                for i, (e1, e2) in enumerate(zip(events1, events2)):
                    e1.pop("timestamp", None)
                    e2.pop("timestamp", None)
                    if e1 != e2:
                        print(f"  Event {i} differs:")
                        print(f"    Run1: {e1}")
                        print(f"    Run2: {e2}")
            
            return 1
    finally:
        # Cleanup
        shutil.rmtree(temp_dir, ignore_errors=True)


if __name__ == "__main__":
    sys.exit(main())
