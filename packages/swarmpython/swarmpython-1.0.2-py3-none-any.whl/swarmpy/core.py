import os
import inspect 
from concurrent.futures import ThreadPoolExecutor # <--- The Speed Engine
from .loader import BundleExecutor
from .strategies import NumericalStrategy, VotingStrategy 

class Swarm:
    def __init__(self, *bundles):
        self.agents = []
        
        # --- MAGIC: Auto-detect caller's directory ---
        caller_frame = inspect.stack()[1]
        caller_file = caller_frame.filename
        base_dir = os.path.dirname(os.path.abspath(caller_file))

        for b in bundles:
            func_name = None

            # Normalize Input (Handle Tuples, Lists, Strings)
            if isinstance(b, tuple): 
                raw_files = b[0] if isinstance(b[0], list) else [b[0]]
                func_name = b[1]
            elif isinstance(b, list):
                raw_files = b
            elif isinstance(b, str):
                raw_files = [b]
            else:
                continue

            # --- PATH RESOLUTION ---
            clean_files = []
            for f in raw_files:
                if not os.path.isabs(f):
                    clean_files.append(os.path.join(base_dir, f))
                else:
                    clean_files.append(f)

            self.agents.append({
                "files": clean_files,
                "func": func_name
            })

    def run(self, input_data, priorities: list = None, mode: str = "auto", sensitivity: float = 1.5):
        
        # --- HELPER: Runs inside a thread ---
        def run_single_agent(agent_data):
            # We need the index just for logging, but map doesn't give it easily.
            # So we just run the execution safely.
            try:
                return BundleExecutor.execute_bundle(
                    agent_data["files"], 
                    input_data, 
                    function_name=agent_data["func"]
                )
            except Exception as e:
                # We catch errors here so one thread doesn't kill the whole Swarm
                # print(f"⚠️ Agent failed: {e}") # Optional: Uncomment for debugging
                return None

        # --- PARALLEL EXECUTION ENGINE ---
        # This spins up threads equal to the number of agents
        with ThreadPoolExecutor() as executor:
            # executor.map ensures results come back in the SAME ORDER as agents
            # This is crucial so your 'priorities' list still matches up!
            results = list(executor.map(run_single_agent, self.agents))

        # --- AUTO-DETECT MODE ---
        if mode == "auto":
            valid_sample = next((r for r in results if r is not None), None)
            if valid_sample is None:
                mode = "numeric" # Default if all fail
            elif isinstance(valid_sample, str):
                mode = "classification"
            else:
                mode = "numeric"

        # --- STRATEGY SELECTION ---
        if mode == "classification":
            strategy = VotingStrategy()
            return strategy.aggregate(results, priorities=priorities)
        
        elif mode == "numeric":
            strategy = NumericalStrategy(sensitivity=sensitivity)
            return strategy.aggregate(results, priorities=priorities)
        
        else:
            raise ValueError(f"Unknown mode: {mode}")