# (No changes needed, keeping existing logic for treeignore)
import os
import pathspec
import logging

def is_text_file(file_path):
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            f.read(1024)
            return True
    except (UnicodeDecodeError, OSError):
        return False

def load_treeignore_patterns(root_path):
    patterns = [
        '.git/', '__pycache__/', 'node_modules/', '.DS_Store',
        'venv/', 'env/', '.env', '*.log', '*.pyc',
        'dist/', 'build/', '*.egg-info/'
    ]

    treeignore_path = os.path.join(root_path, ".treeignore")
    if os.path.exists(treeignore_path):
        with open(treeignore_path, 'r') as f:
            patterns.extend(f.readlines())

    return pathspec.PathSpec.from_lines('gitwildmatch', patterns)

def generate_tree_markdown(start_path):
    start_path = os.path.abspath(start_path)
    output = []
    spec = load_treeignore_patterns(start_path)

    for root, dirs, files in os.walk(start_path):
        rel_root = os.path.relpath(root, start_path)
        dirs[:] = [
            d for d in dirs
            if not spec.match_file(os.path.join(rel_root, d))
            and not d.startswith('.')
        ]

        for file in files:
            file_path = os.path.join(root, file)
            rel_path = os.path.relpath(file_path, start_path)

            if spec.match_file(rel_path) or file.startswith('.'):
                continue

            if not is_text_file(file_path):
                continue

            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                ext = os.path.splitext(file)[1].lstrip('.') or 'text'
                output.append(f"{rel_path}:")
                output.append(f"```{ext}")
                output.append(content)
                output.append("```\n")
            except Exception as e:
                logging.warning(f"Could not read {rel_path}: {e}")
                continue

    return "\n".join(output)