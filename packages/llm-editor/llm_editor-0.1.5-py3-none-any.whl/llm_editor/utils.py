import os

def parse_input_file(filepath):
    """
    Parses the file to separate the prompt (between tags) from the content.
    """
    if not os.path.exists(filepath):
        raise FileNotFoundError(f"File not found: {filepath}")

    with open(filepath, 'r', encoding='utf-8') as f:
        lines = f.readlines()

    prompt_lines = []
    content_lines = []
    
    in_prompt_block = False
    prompt_found = False

    for line in lines:
        stripped = line.strip()
        
        # Check for start tag
        if "<tag> start_prompt" in stripped:
            in_prompt_block = True
            prompt_found = True
            continue
        
        # Check for end tag
        if "<tag> end_prompt" in stripped:
            in_prompt_block = False
            continue

        if in_prompt_block:
            prompt_lines.append(line)
        else:
            content_lines.append(line)

    user_prompt = "".join(prompt_lines).strip()
    content = "".join(content_lines).strip()

    return user_prompt, content
