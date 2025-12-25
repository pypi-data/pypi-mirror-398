import os
import sys
import importlib.util

class BundleExecutor:
    @staticmethod
    def execute_bundle(file_list, input_data, function_name=None):
        """
        Takes a list of file paths (bundle), finds the .py file,
        and executes its function (returning ANY type).
        """
        # 1. Find the Python script
        script_path = None
        for path in file_list:
            if path.endswith(".py"):
                script_path = path
                break
        
        if not script_path:
            raise ValueError(f"No .py entry point found in bundle: {file_list}")

        if not os.path.exists(script_path):
            raise FileNotFoundError(f"Script path does not exist: {script_path}")

        # 2. Dynamic Import
        module_name = "agent_" + os.path.basename(script_path).replace(".py", "")
        
        try:
            spec = importlib.util.spec_from_file_location(module_name, script_path)
            module = importlib.util.module_from_spec(spec)
            
            script_dir = os.path.dirname(os.path.abspath(script_path))
            if script_dir not in sys.path:
                sys.path.append(script_dir)

            spec.loader.exec_module(module)

            # 3. Execution (NO MORE FLOAT CASTING!)
            
            # A. Custom Function Name
            if function_name:
                if hasattr(module, function_name):
                    func = getattr(module, function_name)
                    return func(input_data)  # <--- FIXED: Returns raw value (str/int/float)
                else:
                    raise ValueError(f"Function '{function_name}' not found in {script_path}")

            # B. Default Standard Functions
            if hasattr(module, "predict"):
                return module.predict(input_data) # <--- FIXED
            elif hasattr(module, "run"):
                return module.run(input_data)     # <--- FIXED
            else:
                raise ValueError(f"Script {os.path.basename(script_path)} needs 'predict(data)' or '{function_name}'")
                
        except Exception as e:
            raise RuntimeError(f"Error executing {os.path.basename(script_path)}: {e}")