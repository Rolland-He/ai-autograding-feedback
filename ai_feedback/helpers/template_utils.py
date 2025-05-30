import os


def render_prompt_template(prompt_content: str, **kwargs) -> str:
    """Render a prompt template by replacing placeholders with actual values.
    
    Args:
        prompt_content (str): The prompt template with placeholders like {file_contents}
        **kwargs: Key-value pairs for placeholder replacement
        
    Returns:
        str: The rendered prompt with placeholders replaced
    """
    return prompt_content.format(**kwargs)


def gather_file_references(assignment_files: list[str]) -> str:
    """Generate file reference descriptions for prompt templates.
    
    Args:
        assignment_files (list[str]): List of file paths to process
        
    Returns:
        str: File reference descriptions like "The instructor's solution file..."
    """
    references = []
    
    for file_path in assignment_files:
        filename = os.path.basename(file_path)
        name_without_ext, _ = os.path.splitext(filename)
        
        if name_without_ext.endswith("_solution"):
            references.append(f"The instructor's solution file you should reference is {filename}.")
        elif name_without_ext.endswith("_submission"):
            references.append(f"The student's code submission file you should reference is {filename}.")
        elif name_without_ext.endswith("test_output"):
            references.append(f"The student's error trace file you should reference is {filename}.")
    
    return "\n".join(references)


def gather_file_contents(assignment_files: list[str]) -> str:
    """Generate file contents with line numbers for prompt templates.
    
    Args:
        assignment_files (list[str]): List of file paths to process
        
    Returns:
        str: File contents formatted with line numbers
    """
    file_contents = ""
    
    for file_path in assignment_files:
        filename = os.path.basename(file_path)
        try:
            with open(file_path, "r") as file:
                lines = file.readlines()
        except Exception as e:
            print(f"Error reading file {filename}: {e}")
            continue
        
        file_contents += f"=== {filename} ===\n"
        for i, line in enumerate(lines, start=1):
            stripped_line = line.rstrip("\n")
            if stripped_line.strip():
                file_contents += f"(Line {i}) {stripped_line}\n"
            else:
                file_contents += f"(Line {i}) {line}"
        file_contents += "\n"
    
    return file_contents 