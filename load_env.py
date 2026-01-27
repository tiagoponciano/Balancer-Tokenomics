import os
from pathlib import Path

def load_env_file(env_file_path: str = None):
    if env_file_path is None:
        script_dir = Path(__file__).parent
        env_file_path = script_dir.parent / '.env'
    
    env_file = Path(env_file_path)
    
    if env_file.exists():
        with open(env_file, 'r') as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#'):
                    if '=' in line:
                        key, value = line.split('=', 1)
                        key = key.strip()
                        value = value.strip().strip('"').strip("'")
                        os.environ[key] = value
        return True
    return False
