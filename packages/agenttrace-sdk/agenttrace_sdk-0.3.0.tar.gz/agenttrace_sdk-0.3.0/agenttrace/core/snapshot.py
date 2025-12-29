import cloudpickle
import os
import time

class Snapshotter:
    def __init__(self, storage_dir=".agenttrace/snapshots"):
        self.storage_dir = storage_dir
        os.makedirs(self.storage_dir, exist_ok=True)

    def save_snapshot(self, trace_id, step_id, obj_graph):
        """
        Serializes the current state (obj_graph) to disk.
        In a real implementation, this would inspect the stack frame.
        For the POC, we accept an explicit state dict.
        """
        filename = f"{trace_id}_{step_id}.pkl"
        path = os.path.join(self.storage_dir, filename)
        
        try:
            with open(path, "wb") as f:
                cloudpickle.dump(obj_graph, f)
            return path
        except Exception as e:
            print(f"Warning: Failed to snapshot state at step {step_id}: {e}")
            return None

    def load_snapshot(self, trace_id, step_id):
        filename = f"{trace_id}_{step_id}.pkl"
        path = os.path.join(self.storage_dir, filename)
        
        if not os.path.exists(path):
            raise FileNotFoundError(f"Snapshot not found: {path}")
            
        with open(path, "rb") as f:
            return cloudpickle.load(f)

