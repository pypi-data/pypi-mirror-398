import sys
import os
import shutil
import argparse
import datetime
import tempfile
import subprocess
import glob
from .agent import Agent
from .config import Config
from .utils import parse_input_file

def get_log_dir():
    """Returns the directory for log files."""
    log_dir = os.path.expanduser("~/.llm-editor/logs")
    os.makedirs(log_dir, exist_ok=True)
    return log_dir

def log_error(message):
    timestamp = datetime.datetime.now().isoformat()
    log_file = os.path.join(get_log_dir(), "error.log")
    try:
        with open(log_file, "a", encoding="utf-8") as f:
            f.write(f"[{timestamp}] {message}\n")
    except Exception:
        pass # Fallback if logging fails

def get_default_editor():
    editor = os.environ.get('EDITOR')
    if not editor:
        if shutil.which('vim'):
            editor = 'vim'
        elif shutil.which('nano'):
            editor = 'nano'
        elif shutil.which('vi'):
            editor = 'vi'
    return editor

def expand_paths(paths):
    """
    Expands file paths, handling glob patterns and directories.
    """
    expanded = []
    for path in paths:
        if any(char in path for char in ['*', '?', '[']):
            # It's a glob pattern
            matches = glob.glob(path, recursive=True)
            expanded.extend(matches)
        elif os.path.isdir(path):
            # It's a directory, walk it
            for root, _, files in os.walk(path):
                for file in files:
                    expanded.append(os.path.join(root, file))
        else:
            # It's a file (or doesn't exist yet)
            expanded.append(path)
    
    # Filter out directories and duplicates
    final_paths = []
    for p in expanded:
        if os.path.isdir(p):
            continue
        final_paths.append(p)
        
    return sorted(list(set(final_paths)))

def get_prompt_from_editor():
    """
    Opens the user's preferred editor to capture the prompt.
    """
    editor = get_default_editor()
    if not editor:
        # Last resort
        print("Error: No text editor found. Please set the EDITOR environment variable.")
        return None

    with tempfile.NamedTemporaryFile(suffix=".txt", mode='w+', delete=False) as tf:
        tf.write("\n# Please enter your instructions here.\n# Lines starting with '#' will be ignored.\n")
        tf_path = tf.name
    
    try:
        subprocess.call([editor, tf_path])
        
        with open(tf_path, 'r') as f:
            lines = f.readlines()
            
        prompt_lines = [line for line in lines if not line.strip().startswith('#')]
        return "".join(prompt_lines).strip()
    except Exception as e:
        log_error(f"Error opening editor: {e}")
        return None
    finally:
        if os.path.exists(tf_path):
            os.remove(tf_path)

def main():
    # 1. Parse Arguments
    parser = argparse.ArgumentParser(description="LLM Text Editor")
    parser.add_argument("input_files", nargs="*", help="Path to the input file(s)")
    parser.add_argument("--outfile", help="Path to the output file. If provided, the input file will not be modified.", default=None)
    parser.add_argument("--inplace", help="Modify the input file in-place, skipping backup regardless of config.", action="store_true")
    parser.add_argument("--init-config", help="Initialize configuration in ~/.llm-editor/", action="store_true")
    parser.add_argument("--chat", help="Start an interactive chat session about the file(s).", action="store_true")
    args = parser.parse_args()

    if args.init_config:
        config_dir = os.path.expanduser("~/.llm-editor")
        os.makedirs(config_dir, exist_ok=True)
        config_path = os.path.join(config_dir, "config.yaml")
        
        if not os.path.exists(config_path):
            default_config = """llm:
  provider: openai
  api_key: "your_api_key_here"
  model: "gpt-4o"

app:
  backup_enabled: true
  backup_suffix: ".backup"
"""
            with open(config_path, 'w') as f:
                f.write(default_config)
            print(f"Created default config at {config_path}")
        else:
            print(f"Config file already exists at {config_path}")

        editor = get_default_editor()
        if editor:
            print(f"Opening config file in {editor}...")
            subprocess.call([editor, config_path])
        else:
            print("Please edit it to add your API key.")
        return

    if not args.input_files:
        parser.print_help()
        return

    # 2. Load and Validate Config
    try:
        Config.load()
        Config.validate()
    except FileNotFoundError:
        print("Configuration file not found.")
        print("Please run 'edit --init-config' to generate a default configuration.")
        return
    except ValueError as e:
        log_error(f"Configuration Error: {e}")
        print(f"Configuration Error: {e}")
        print(f"Failure. Check {os.path.join(get_log_dir(), 'error.log')} for details.")
        return

    # Expand files
    files = expand_paths(args.input_files)
    if not files:
        print("Error: No valid files found.")
        return

    # Handle Chat Mode
    if args.chat:
        context_files = {}
        for filepath in files:
            try:
                with open(filepath, 'r', encoding='utf-8') as f:
                    context_files[filepath] = f.read()
            except Exception as e:
                print(f"Error reading {filepath}: {e}")
                continue

        system_prompt = "You are a helpful coding assistant. You have access to the user's files."
        agent = Agent(system_prompt=system_prompt)
        agent.chat(context_files)
        return

    # Handle Edit Mode
    if len(files) > 1:
        print("Error: Editing multiple files is not yet supported. Use --chat to discuss multiple files.")
        return

    input_filepath = files[0]

    # 3. Parse File
    try:
        user_prompt, content = parse_input_file(input_filepath)
        
        if not user_prompt:
            print("No prompt tags found in file. Opening editor for instructions...")
            user_prompt = get_prompt_from_editor()
            
            if not user_prompt:
                print("Operation cancelled: No instructions provided.")
                return
        
    except Exception as e:
        log_error(f"Error parsing file: {e}")
        print(f"Failure. Check {os.path.join(get_log_dir(), 'error.log')} for details.")
        return

    # 4. Initialize Agent
    # You can customize the system prompt here
    system_prompt = (
        "You are an expert text editor. Your task is to rewrite the provided content based on the user's instructions. "
        "You must output ONLY the rewritten content. Do not add any introductory or concluding remarks. "
        "Do not wrap the output in markdown code blocks (```) unless the user asks for it or the file format requires it. "
        "If the user asks to convert code to another language, output ONLY the code in the new language, without markdown formatting."
    )
    agent = Agent(system_prompt=system_prompt)

    # 5. Run Agent
    try:
        result = agent.process(user_prompt, content)
    except Exception as e:
        log_error(f"Error during LLM processing: {e}")
        print(f"Failure. Check {os.path.join(get_log_dir(), 'error.log')} for details.")
        return

    # 6. Output Result and Backup
    
    # Determine output mode
    if args.inplace:
        # In-place mode: Overwrite input file, skip backup
        target_file = input_filepath
        should_backup = False
    elif args.outfile:
        # Outfile mode: Write to new file, no backup needed
        target_file = args.outfile
        should_backup = False
    else:
        # Default mode: Overwrite input file, respect backup config
        target_file = input_filepath
        should_backup = Config.BACKUP_ENABLED

    # Perform write operation
    backup_path = None
    try:
        # Create backup if needed
        if should_backup:
            backup_path = input_filepath + Config.BACKUP_SUFFIX
            shutil.copy2(input_filepath, backup_path)

        # Write to target file
        with open(target_file, 'w', encoding='utf-8') as f:
            f.write(result)
            
        success_msg = f"Successful. Output: {target_file}"
        if backup_path:
            success_msg += f", Backup: {backup_path}"
        print(success_msg)
            
    except Exception as e:
        log_error(f"Error saving file: {e}")
        # Only attempt restore if we were overwriting the input file AND made a backup
        if target_file == input_filepath and backup_path and os.path.exists(backup_path):
            log_error(f"Attempting to restore from backup: {backup_path}")
            try:
                shutil.copy2(backup_path, input_filepath)
                log_error("Restoration successful.")
            except Exception as restore_error:
                log_error(f"CRITICAL: Failed to restore from backup: {restore_error}")
        
        print(f"Failure. Check {os.path.join(get_log_dir(), 'error.log')} for details.")

if __name__ == "__main__":
    main()
