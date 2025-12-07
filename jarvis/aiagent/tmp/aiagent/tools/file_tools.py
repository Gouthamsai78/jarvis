# tools/file_tools.py
import os

def read_code_file(file_path: str) -> str:
    """
    Reads the content of a specified code file.

    Args:
        file_path: The relative path to the file.

    Returns:
        The content of the file as a string.
    """
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            return f.read()
    except Exception as e:
        return f"Error reading file: {e}"

def write_code_file(file_path: str, content: str) -> str:
    """
    Writes content to a specified code file. Creates directories if they don't exist.

    Args:
        file_path: The relative path to the file.
        content: The code or text to write to the file.

    Returns:
        A confirmation message.
    """
    try:
        # Create parent directories if they don't exist
        dir_name = os.path.dirname(file_path)
        if dir_name:
            os.makedirs(dir_name, exist_ok=True)

        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(content)
        return f"Successfully wrote to {file_path}"
    except Exception as e:
        return f"Error writing to file: {e}"
