import os
import sys
import site

# Add the current directory to sys.path to ensure agenttrace can be imported
sys.path.insert(0, os.getcwd())

print("AgentTrace: Initializing auto-instrumentation...")

try:
    from agenttrace.instrumentation.bootstrap import bootstrap
    bootstrap()
except ImportError as e:
    print(f"AgentTrace: Failed to load bootstrap: {e}")
except Exception as e:
    print(f"AgentTrace: Error during bootstrap: {e}")

