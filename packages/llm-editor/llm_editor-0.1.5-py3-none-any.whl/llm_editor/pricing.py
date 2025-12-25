import yaml
import os
import importlib.resources

def load_pricing(filepath=None):
    # 1. Try user-defined pricing file
    if filepath is None:
        filepath = os.path.expanduser("~/.llm-editor/pricing.yaml")
    
    data = None
    
    if os.path.exists(filepath):
        try:
            with open(filepath, 'r') as f:
                data = yaml.safe_load(f)
        except Exception as e:
            print(f"Warning: Error loading user pricing.yaml: {e}")

    # 2. Fallback to bundled pricing.yaml
    if data is None:
        try:
            # For Python 3.9+
            from . import pricing as pricing_module # dummy import to get package
            # Actually we are in the package.
            # Let's use pkg_resources style or importlib.files
            # For compatibility, let's try to find it relative to this file
            bundled_path = os.path.join(os.path.dirname(__file__), "pricing.yaml")
            if os.path.exists(bundled_path):
                with open(bundled_path, 'r') as f:
                    data = yaml.safe_load(f)
        except Exception as e:
            print(f"Warning: Error loading bundled pricing.yaml: {e}")

    if not data:
        print(f"Warning: No pricing configuration found. Cost estimation will be unavailable.")
        return {}

    try:
        latest_version = data.get("latest_version")
        if not latest_version:
            print("Warning: 'latest_version' not specified in pricing.yaml")
            return {}
            
        versions = data.get("versions", {})
        if latest_version not in versions:
            print(f"Warning: Version {latest_version} not found in pricing.yaml versions")
            return {}
            
        return versions[latest_version]
    except Exception as e:
        print(f"Error loading pricing.yaml: {e}")
        return {}

# Load rates when module is imported
PRICING_RATES = load_pricing()
