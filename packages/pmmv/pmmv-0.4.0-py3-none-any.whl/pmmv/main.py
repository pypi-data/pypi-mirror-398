#!/usr/bin/env python3
import os
import sys
import argparse
import tempfile
import subprocess
import shutil
from pathlib import Path
from datetime import datetime
import re
import uuid
import tomllib


class PMMVError(Exception):
    """Base exception for PMMV errors"""
    pass


class ValidationError(PMMVError):
    """Raised when file validation fails"""
    pass


def validate_separator(sep):
    """Validate that separator is non-empty and non-whitespace"""
    if not sep or sep.isspace():
        raise ValueError("Separator must be non-empty and non-whitespace")
    return sep


def is_valid_path(path, sep):
    """Check if path contains invalid separator usage"""
    # Check for ### in any part of path components
    # Invalid: some###/path, ###abc, abc###, ###/path
    # The separator should only appear as the middle delimiter, not in paths

    # Check if separator appears anywhere in the path
    if sep in path:
        return False

    return True


def get_common_parent(files):
    """Get the common parent directory of all files"""
    if not files:
        return Path.cwd()

    abs_paths = [Path(f).resolve() for f in files]

    if len(abs_paths) == 1:
        return abs_paths[0].parent

    # Find common parent
    common = abs_paths[0].parent
    for p in abs_paths[1:]:
        # Find common ancestor
        while not str(p).startswith(str(common) + os.sep) and p != common:
            common = common.parent
            if common == common.parent:  # reached root
                break

    return common


def expand_path(path, sep, parent_dir):
    """Expand a path that may start with ./ (relative path notation)"""
    if path.startswith('./'):
        # Replace ./ with parent directory
        return str(parent_dir / path[2:])
    return path


def create_edit_file(files, sep, short_mode):
    """Create the initial edit file content"""
    abs_files = [Path(f).resolve() for f in files]
    parent_dir = Path.cwd()

    lines = []
    max_left_len = 0

    for f in abs_files:
        abs_path = str(f)

        if short_mode:
            # Create relative path from parent with ./ prefix
            try:
                rel_path = f.relative_to(parent_dir)
                left = f"./{rel_path}"
            except ValueError:
                # Can't make relative, use absolute
                left = abs_path
        else:
            left = abs_path

        max_left_len = max(max_left_len, len(left))
        lines.append((left, left))

    # Align to exactly 3 spaces past the longest
    alignment = max_left_len + 3

    result = []
    for left, right in lines:
        spaces = ' ' * (alignment - len(left))
        result.append(f"{left}{spaces}{sep} {right}")

    return '\n'.join(result) + '\n', parent_dir


def parse_edit_file(content, sep, parent_dir):
    """Parse the edited file and return list of (source, dest) tuples.

    If source (RHS) is empty, it indicates a delete operation and source will be None.
    """
    moves = []

    for line_no, line in enumerate(content.split('\n'), 1):
        line = line.rstrip('\n')
        if not line.strip():
            continue

        # Check for delete operation (empty RHS): "path ###" or "path   ###"
        # Pattern: destination followed by whitespace, separator, and optional trailing whitespace
        delete_pattern = r'^(.+?)\s+' + re.escape(sep) + r'\s*$'
        delete_match = re.match(delete_pattern, line)

        if delete_match:
            # Delete operation
            dest_str = delete_match.group(1).strip()

            if not is_valid_path(dest_str, sep):
                raise ValidationError(f"Line {line_no}: Invalid separator usage in path: {dest_str}")

            if parent_dir:
                dest_str = expand_path(dest_str, sep, parent_dir)

            dest = Path(dest_str).resolve()
            moves.append((None, dest))  # None source = delete
            continue

        # Find separator with at least one space on each side
        pattern = r'\s+' + re.escape(sep) + r'\s+'
        parts = re.split(pattern, line)

        if len(parts) != 2:
            raise ValidationError(f"Line {line_no}: Invalid format, must have exactly one '{sep}' separator with spaces")

        dest_str, src_str = parts
        dest_str = dest_str.strip()
        src_str = src_str.strip()

        # Validate paths don't contain invalid separator usage
        if not is_valid_path(dest_str, sep):
            raise ValidationError(f"Line {line_no}: Invalid separator usage in destination path: {dest_str}")
        if not is_valid_path(src_str, sep):
            raise ValidationError(f"Line {line_no}: Invalid separator usage in source path: {src_str}")

        # Expand paths
        if parent_dir:
            dest_str = expand_path(dest_str, sep, parent_dir)
            src_str = expand_path(src_str, sep, parent_dir)

        # Convert to absolute paths
        src = Path(src_str).resolve()
        dest = Path(dest_str).resolve()

        moves.append((src, dest))

    return moves


def validate_moves(moves, use_git=False):
    """Validate that all moves are possible.

    Moves can be:
    - (src, dest): Move/copy src to dest
    - (None, dest): Delete dest
    """
    # Separate delete operations from moves
    deletes = [(src, dest) for src, dest in moves if src is None]
    actual_moves = [(src, dest) for src, dest in moves if src is not None]

    # Validate delete operations
    for _, dest in deletes:
        if not dest.exists():
            raise ValidationError(f"Cannot delete, file does not exist: {dest}")
        if not dest.is_file() and not dest.is_dir():
            raise ValidationError(f"Cannot delete, not a file or directory: {dest}")

    # Check that all source files/directories exist
    for src, dest in actual_moves:
        if not src.exists():
            raise ValidationError(f"Source does not exist: {src}")
        if not src.is_file() and not src.is_dir():
            raise ValidationError(f"Source is not a file or directory: {src}")

    # Check for destination conflicts (multiple sources to same dest)
    dest_map = {}
    for src, dest in actual_moves:
        if src == dest:
            continue  # No-op move

        if dest in dest_map:
            raise ValidationError(
                f"Multiple files being moved to same destination:\n"
                f"  {dest_map[dest]} -> {dest}\n"
                f"  {src} -> {dest}"
            )
        dest_map[dest] = src

    # Check for duplicate sources (same source to multiple destinations = copy)
    # Directory duplication is not supported
    src_count = {}
    for src, dest in actual_moves:
        if src == dest:
            continue
        src_count[src] = src_count.get(src, 0) + 1

    for src, count in src_count.items():
        if count > 1 and src.is_dir():
            raise ValidationError(f"Cannot duplicate directories: {src}")

    # Check that destinations that exist are being moved elsewhere or being deleted
    deleted_paths = {dest for _, dest in deletes}
    for src, dest in actual_moves:
        if src == dest:
            continue

        if dest.exists():
            # Check if this dest is a source in our moves AND is actually being moved away
            # (not a no-op where src == dest)
            dest_is_being_moved = any(s == dest and d != dest for s, d in actual_moves)
            dest_is_being_deleted = dest in deleted_paths
            if not dest_is_being_moved and not dest_is_being_deleted:
                raise ValidationError(f"Destination already exists and is not being moved: {dest}")

    # Check destination directory permissions (only for moves, not deletes)
    for src, dest in actual_moves:
        if src == dest:
            continue

        dest_dir = dest.parent
        if not dest_dir.exists():
            # Check if we can create it
            try:
                dest_dir.mkdir(parents=True, exist_ok=True)
            except Exception as e:
                raise ValidationError(f"Cannot create destination directory {dest_dir}: {e}")

        if not os.access(dest_dir, os.W_OK):
            raise ValidationError(f"No write permission for directory: {dest_dir}")

    # Git-specific validation (only for actual moves, not deletes)
    if use_git:
        validate_git_moves(actual_moves)


def validate_git_moves(moves):
    """Validate that all files are in git and moves are within same repo"""
    repos = {}

    for src, dest in moves:
        if src is None or src == dest:
            continue

        # Check if source is in a git repo
        src_repo = get_git_repo(src)
        if src_repo is None:
            raise ValidationError(f"File is not in a git repository: {src}")

        # Check if destination is in same git repo
        dest_repo = get_git_repo(dest.parent)
        if dest_repo is None:
            raise ValidationError(f"Destination is not in a git repository: {dest}")

        if src_repo != dest_repo:
            raise ValidationError(
                f"Source and destination are in different git repositories:\n"
                f"  {src} (repo: {src_repo})\n"
                f"  {dest} (repo: {dest_repo})"
            )


def get_git_repo(path):
    """Get the git repository root for a path, or None if not in a repo"""
    try:
        if path.is_file():
            path = path.parent
        result = subprocess.run(
            ['git', '-C', str(path), 'rev-parse', '--show-toplevel'],
            capture_output=True,
            text=True,
            check=True
        )
        return Path(result.stdout.strip())
    except (subprocess.CalledProcessError, FileNotFoundError):
        return None


def apply_moves(moves, use_git=False):
    """Apply all moves simultaneously, handling cycles, duplications, and deletions.

    Moves can be:
    - (src, dest): Move/copy src to dest
    - (None, dest): Delete dest
    """
    # Separate delete operations from moves
    deletes = [(src, dest) for src, dest in moves if src is None]
    non_delete_moves = [(src, dest) for src, dest in moves if src is not None]

    # Identify sources that should be preserved (have a no-op: src == dest)
    sources_to_keep = {src for src, dest in non_delete_moves if src == dest}

    # Filter out no-op moves
    actual_moves = [(src, dest) for src, dest in non_delete_moves if src != dest]

    # Process deletions first (so destinations can be overwritten)
    for _, dest in deletes:
        if dest.exists():
            if use_git:
                subprocess.run(['git', 'rm', '-f', str(dest)], check=True)
            elif dest.is_dir():
                shutil.rmtree(str(dest))
            else:
                dest.unlink()

    if not actual_moves:
        return

    # Identify sources that appear multiple times (duplication)
    src_count = {}
    for src, dest in actual_moves:
        src_count[src] = src_count.get(src, 0) + 1

    # Track which sources have been copied (for duplication handling)
    src_copied = set()

    # Create temporary directory for intermediate files
    temp_dir = Path(tempfile.mkdtemp(prefix='pmmv_'))
    temp_map = {}  # temp_path -> (dest, is_copy)

    try:
        # Step 1: Move/copy all files to temporary locations
        for src, dest in actual_moves:
            temp_name = temp_dir / str(uuid.uuid4())

            if src_count[src] > 1 or src in sources_to_keep:
                # This source is being duplicated or should be kept
                shutil.copy2(str(src), str(temp_name))
                temp_map[temp_name] = (dest, True)
                src_copied.add(src)
            else:
                # Normal move (single destination)
                if use_git:
                    subprocess.run(['git', 'mv', str(src), str(temp_name)], check=True)
                else:
                    shutil.move(str(src), str(temp_name))
                temp_map[temp_name] = (dest, False)

        # Remove original files for duplicated sources (after all copies are made)
        # but only if they are NOT meant to be kept
        for src in src_copied:
            if src.exists() and src not in sources_to_keep:
                if use_git:
                    subprocess.run(['git', 'rm', str(src)], check=True)
                else:
                    src.unlink()

        # Step 2: Move all files to final destinations
        for temp_path, (dest, is_copy) in temp_map.items():
            # Ensure destination directory exists
            dest.parent.mkdir(parents=True, exist_ok=True)

            if use_git and not is_copy:
                subprocess.run(['git', 'mv', str(temp_path), str(dest)], check=True)
            else:
                # For copies (duplications) or non-git moves, just move the temp file
                shutil.move(str(temp_path), str(dest))

    finally:
        # Clean up temp directory
        if temp_dir.exists():
            shutil.rmtree(temp_dir)


def create_undo_file(moves, sep):
    """Create an undo file with inverted moves.

    For duplications (same source to multiple destinations), only the first
    destination gets the source in the undo file. Additional copies get an
    empty RHS, meaning they should be deleted on undo.

    If the source is kept (has a no-op: src == dest), then ALL copies are
    deletions since the source remains in place.
    """
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    undo_filename = f"{timestamp}.undo.pmmv"

    # Identify sources that are kept (have a no-op: src == dest)
    sources_kept = {src for src, dest in moves if src == dest}

    # Filter out no-op moves
    actual_moves = [(src, dest) for src, dest in moves if src != dest]

    if not actual_moves:
        return None

    # Track which sources have been seen (for duplication handling)
    # First occurrence gets the real undo (dest -> src), rest get deletion (dest ->)
    # Exception: if source is kept, ALL destinations are deletions
    src_seen = set()
    undo_moves = []  # (dest, src_or_none)

    for src, dest in actual_moves:
        if src in sources_kept:
            # Source is kept, so this copy should just be deleted
            undo_moves.append((dest, None))
        elif src in src_seen:
            # This was a copy, undo = delete
            undo_moves.append((dest, None))
        else:
            # First occurrence or regular move, undo = move back
            # Format: new_location ### old_location, so src ### dest means "move dest to src"
            undo_moves.append((src, dest))
            src_seen.add(src)

    lines = []
    max_left_len = 0

    for left, right in undo_moves:
        max_left_len = max(max_left_len, len(str(left)))

    alignment = ((max_left_len + 2) // 2 + 1) * 2

    for left, right in undo_moves:
        spaces = ' ' * (alignment - len(str(left)))
        if right is None:
            # Empty RHS = delete
            lines.append(f"{left}{spaces}{sep}")
        else:
            lines.append(f"{left}{spaces}{sep} {right}")

    with open(undo_filename, 'w') as f:
        f.write('\n'.join(lines) + '\n')

    return undo_filename


def get_editor():
    """Get the user's preferred editor"""
    editor = os.environ.get('EDITOR', os.environ.get('VISUAL', 'vi'))
    if editor in ('vi', 'vim', 'nvim'):
        os.environ['VIM_OPTIONS'] = '+set nowrap'

    return editor


def apply_undo_file(undo_path, sep, use_git=False):
    """Apply an undo file directly without opening editor"""
    undo_file = Path(undo_path)
    if not undo_file.exists():
        print(f"Error: Undo file does not exist: {undo_path}", file=sys.stderr)
        return 1

    try:
        content = undo_file.read_text()

        # Parse moves (use parent directory of undo file for relative paths)
        parent_dir = undo_file.parent.resolve()
        moves = parse_edit_file(content, sep, parent_dir)

        # Validate moves
        validate_moves(moves, use_git=use_git)

        # Apply moves
        apply_moves(moves, use_git=use_git)

        # Count actual operations
        actual_moves = [(src, dest) for src, dest in moves if src is not None and src != dest]
        deletes = [(src, dest) for src, dest in moves if src is None]

        if actual_moves or deletes:
            parts = []
            if actual_moves:
                parts.append(f"moved {len(actual_moves)} file(s)")
            if deletes:
                parts.append(f"deleted {len(deletes)} file(s)")
            print(f"Undo successful: {', '.join(parts)}")
        else:
            print("No changes made")

        return 0

    except ValidationError as e:
        print(f"Validation error: {e}", file=sys.stderr)
        return 1
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1


def get_version():
    """Get version from pyproject.toml"""
    try:
        with open("pyproject.toml", "rb") as f:
            pyproject_data = tomllib.load(f)
        return pyproject_data["project"]["version"]
    except Exception:
        # Fallback to hardcoded version if we can't read pyproject.toml
        return "0.1.5"


def main():
    parser = argparse.ArgumentParser(
        description='PMMV - Python Mass Move: Batch rename/move files interactively'
    )
    parser.add_argument('paths', nargs='*', help='Files or directories to move/rename')
    parser.add_argument('-a', '--absolute', action='store_true', help='Use absolute paths instead of relative')
    parser.add_argument('--sep', default='###', help='Separator token (default: ###)')
    parser.add_argument('--git', action='store_true', help='Use git mv for moving files')
    parser.add_argument('--undo', metavar='FILE', help='Apply an undo file directly (no editor)')
    parser.add_argument('--version', action='version', version=f'%(prog)s {get_version()}')

    args = parser.parse_args()

    try:
        sep = validate_separator(args.sep)
    except ValueError as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1

    # Handle undo file mode
    if args.undo:
        return apply_undo_file(args.undo, sep, args.git)

    # Get paths from stdin if not provided as arguments
    if len(args.paths) == 1 and args.paths[0] == "-" and not sys.stdin.isatty():
        args.paths = [line.strip() for line in sys.stdin if line.strip()]
    elif len(args.paths) == 1 and args.paths[0] == "-":
        parser.error("No paths specified")
    elif len(args.paths) == 0:
        parser.error("No paths specified. Use '-' to read from stdin.")

    # Handle case where a single directory is passed
    if len(args.paths) == 1:
        dir_path = Path(args.paths[0])
        if dir_path.is_dir():
            # Get all items (files and directories) in the directory
            items_in_dir = []
            for item in dir_path.iterdir():
                items_in_dir.append(str(item))

            # If we found items, use them instead of the directory itself
            if items_in_dir:
                args.paths = items_in_dir
            # If no items found, keep the original behavior (treat as single file)

    # Validate paths exist
    for f in args.paths:
        if not Path(f).exists():
            print(f"Error: Path does not exist: {f}", file=sys.stderr)
            return 1

    # Validate that we don't have conflicting paths (e.g., a directory and files inside it)
    # This prevents issues where a directory and its contents are both being moved
    if len(args.paths) > 1:
        # Check if we have a mix of directories and files that could conflict
        abs_paths = [Path(f).resolve() for f in args.paths]

        # Check for any directory that is a parent of another file/directory
        for i, path1 in enumerate(abs_paths):
            for j, path2 in enumerate(abs_paths):
                if i != j and path1.is_dir() and path2.is_relative_to(path1):
                    print(f"Error: Conflicting paths detected in input", file=sys.stderr)
                    print(f"  Directory: {path1}", file=sys.stderr)
                    print(f"  Path inside: {path2}", file=sys.stderr)
                    return 1

    # Create edit file
    try:
        content, parent_dir = create_edit_file(args.paths, sep, not args.absolute)
    except Exception as e:
        print(f"Error creating edit file: {e}", file=sys.stderr)
        return 1

    # Write to temporary file and open editor
    with tempfile.NamedTemporaryFile(mode='w', suffix='.pmmv', delete=False) as tf:
        tf.write(content)
        temp_path = tf.name

    try:
        editor = get_editor()
        subprocess.run([editor, temp_path], check=True)

        # Read edited content
        with open(temp_path, 'r') as f:
            edited_content = f.read()

        # Parse moves
        moves = parse_edit_file(edited_content, sep, parent_dir)

        # Validate moves
        validate_moves(moves, use_git=args.git)

        # Create undo file before applying changes
        undo_file = create_undo_file(moves, sep)

        # Apply moves
        apply_moves(moves, use_git=args.git)

        # Report results
        actual_moves = [(src, dest) for src, dest in moves if src != dest]
        if actual_moves:
            print(f"Successfully moved {len(actual_moves)} file(s)")
            if undo_file:
                print(f"Undo file created: {undo_file}")
        else:
            print("No changes made")

    except ValidationError as e:
        print(f"Validation error: {e}", file=sys.stderr)
        return 1
    except subprocess.CalledProcessError:
        print("Editor was cancelled or failed", file=sys.stderr)
        return 1
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1
    finally:
        # Clean up temp file
        if Path(temp_path).exists():
            Path(temp_path).unlink()

    return 0


if __name__ == '__main__':
    sys.exit(main())

