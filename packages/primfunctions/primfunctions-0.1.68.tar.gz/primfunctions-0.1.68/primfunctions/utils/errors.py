import traceback
import re


def _sanitize_sensitive_info(text: str) -> str:
    """
    Remove sensitive information from text using pattern matching.
    """
    # Patterns for sensitive information
    sensitive_patterns = [
        # API keys and tokens
        (r'api_key["\s]*[:=]["\s]*([a-zA-Z0-9_\-]{10,})', r'api_key="[REDACTED]"'),
        (r'token["\s]*[:=]["\s]*([a-zA-Z0-9_\-\.]{10,})', r'token="[REDACTED]"'),
        (r"bearer\s+([a-zA-Z0-9_\-\.]{10,})", r"bearer [REDACTED]"),
        # Database credentials
        (r'password["\s]*[:=]["\s]*([^"\s,)]+)', r'password="[REDACTED]"'),
        (r'passwd["\s]*[:=]["\s]*([^"\s,)]+)', r'passwd="[REDACTED]"'),
        (r'pwd["\s]*[:=]["\s]*([^"\s,)]+)', r'pwd="[REDACTED]"'),
        # URLs with credentials
        (r"://([^:]+):([^@]+)@", r"://[USER]:[PASS]@"),
        # Secret keys
        (
            r'secret[_\s]*key["\s]*[:=]["\s]*([a-zA-Z0-9_\-]{8,})',
            r'secret_key="[REDACTED]"',
        ),
        (r'private[_\s]*key["\s]*[:=]["\s]*([^"\s,)]+)', r'private_key="[REDACTED]"'),
        # Phone numbers (more specific pattern to avoid timestamps)
        (
            r"\b\+?1?[-.\s]?\(?([0-9]{3})\)?[-.\s]?([0-9]{3})[-.\s]?([0-9]{4})\b(?!\d)",
            r"[PHONE-REDACTED]",
        ),
        # Phone numbers (10-digit unformatted, avoiding timestamps by checking context)
        (
            r"\b(?<![0-9])([2-9][0-9]{2}[2-9][0-9]{2}[0-9]{4})(?![0-9])",
            r"[PHONE-REDACTED]",
        ),
        # Email addresses
        (r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b", r"[EMAIL-REDACTED]"),
        # Credit card patterns (basic)
        (
            r"\b(?:4[0-9]{12}(?:[0-9]{3})?|5[1-5][0-9]{14}|3[47][0-9]{13}|3[0-9]{13}|6(?:011|5[0-9]{2})[0-9]{12})\b",
            r"[CARD-REDACTED]",
        ),
    ]

    sanitized = text
    for pattern, replacement in sensitive_patterns:
        sanitized = re.sub(pattern, replacement, sanitized, flags=re.IGNORECASE)

    return sanitized


def _extract_files_from_error_message(error_message):
    """Extract user code file paths mentioned in the error message."""
    user_files = []

    # Look for files in parentheses (common in Python errors)
    paren_matches = re.findall(r"\(([^)]+\.py)\)", error_message)
    for match in paren_matches:
        if "/app/modules/" in match or "/modules/" in match:
            user_files.append((match, "?"))  # Return (file_path, line_num)

    # Look for files in quotes
    quote_matches = re.findall(r'"([^"]+\.py)"', error_message)
    for match in quote_matches:
        if "/app/modules/" in match or "/modules/" in match:
            user_files.append((match, "?"))  # Return (file_path, line_num)

    return user_files


def _find_user_code_lines(tb_lines):
    """Find all user code lines in traceback, returning (deepest, latest)."""
    user_lines = []

    for i, line in enumerate(tb_lines):
        # Check for both production (/app/modules/) and local development paths
        is_user_code = (
            ("/app/modules/" in line or "/modules/" in line)
            and 'File "' in line
            and not any(
                exclude in line
                for exclude in [
                    ".venv/",
                    "site-packages/",
                    "dist-packages/",
                    "/usr/lib/python",
                    "/usr/local/lib/python",
                ]
            )
        )

        if is_user_code:
            # Get the problematic code if available
            problematic_code = None
            if (
                i + 1 < len(tb_lines)
                and tb_lines[i + 1].strip()
                and not tb_lines[i + 1].startswith("File")
            ):
                problematic_code = tb_lines[i + 1].strip()

            user_lines.append((line, problematic_code))

    if not user_lines:
        return None, None

    # Return (deepest/last, latest/first)
    # In traceback: first entry = outermost/latest, last entry = innermost/deepest
    return user_lines[-1], user_lines[0]


def _try_find_similar_name_in_file(file_path, missing_name):
    """Try to find a similar variable/function name in the target file."""
    try:
        with open(file_path, "r") as f:
            lines = f.readlines()

        import difflib

        candidates = []

        for line_num, line in enumerate(lines, 1):
            # Look for variable definitions, function definitions, etc.
            if (
                "=" in line or "def " in line or "class " in line
            ) and not line.strip().startswith("#"):
                # Extract names from various definition patterns
                patterns = [
                    r"^\s*([A-Za-z_][A-Za-z0-9_]*)\s*=",  # variable = value
                    r"^\s*def\s+([A-Za-z_][A-Za-z0-9_]*)\s*\(",  # def function(
                    r"^\s*class\s+([A-Za-z_][A-Za-z0-9_]*)\s*[:(]",  # class Name:
                ]

                for pattern in patterns:
                    match = re.search(pattern, line)
                    if match:
                        name = match.group(1)
                        similarity = difflib.SequenceMatcher(
                            None, missing_name.lower(), name.lower()
                        ).ratio()
                        if similarity > 0.6:  # 60% similarity threshold
                            candidates.append(
                                (similarity, line_num, line.strip(), name)
                            )

        # Return the best match
        if candidates:
            candidates.sort(reverse=True)  # Sort by similarity (highest first)
            _, line_num, code, found_name = candidates[0]
            return line_num, code

        return None, None
    except (FileNotFoundError, IOError, PermissionError):
        return None, None


def _trace_missing_definition_error(error_message, tb_lines):
    """
    General function to trace errors where something can't be found back to where it should be defined.
    Handles ImportError, NameError, AttributeError, etc.
    """
    import os

    # Extract what Python was looking for and where
    patterns = [
        # ImportError: cannot import name 'VARNAME' from 'module' (with file path)
        (
            r"cannot import name '([^']+)' from '([^']+)' \(([^)]+)\)",
            "import_with_path",
        ),
        # ImportError: cannot import name 'VARNAME' from 'module'
        (r"cannot import name '([^']+)' from '([^']+)'", "import"),
        # NameError: name 'VARNAME' is not defined
        (r"name '([^']+)' is not defined", "name"),
        # AttributeError: module 'MODULE' has no attribute 'ATTR'
        (r"module '([^']+)' has no attribute '([^']+)'", "attribute"),
    ]

    for pattern, error_type in patterns:
        match = re.search(pattern, error_message)
        if match:
            if error_type == "import_with_path":
                missing_name, module_name, file_path = match.groups()
                # Use the file path directly from the error message
                target_files = [file_path]
            elif error_type == "import":
                missing_name, module_name = match.groups()
                # Find the module file
                target_files = _find_module_files(module_name, tb_lines)
            elif error_type == "name":
                missing_name = match.group(1)
                # Look in the current file context from traceback
                target_files = _get_current_context_files(tb_lines)
            elif error_type == "attribute":
                module_name, missing_name = match.groups()
                target_files = _find_module_files(module_name, tb_lines)

            # Search each potential target file for the missing definition
            for file_path in target_files:
                line_num, code = _try_find_similar_name_in_file(file_path, missing_name)
                if line_num and code:
                    return file_path, str(line_num), code

    return None


def _find_module_files(module_name, tb_lines):
    """Find potential files for a given module name."""
    candidates = []

    # Look for explicit file paths in traceback that match the module
    for line in tb_lines:
        if f"{module_name}.py" in line and (
            "modules/" in line or "/app/modules/" in line
        ):
            file_match = re.search(r'File "([^"]+)"', line)
            if file_match:
                candidates.append(file_match.group(1))

    # Also try to construct the path based on the module name
    for line in tb_lines:
        if "/modules/" in line or "/app/modules/" in line:
            base_match = re.search(r"(.*?/modules/[^/]+)/", line)
            if base_match:
                base_path = base_match.group(1)
                potential_file = f"{base_path}/{module_name}.py"
                if potential_file not in candidates:
                    candidates.append(potential_file)

    return candidates


def _get_current_context_files(tb_lines):
    """Get files from the current execution context (for NameError)."""
    files = []
    for line in tb_lines:
        if ("modules/" in line or "/app/modules/" in line) and 'File "' in line:
            file_match = re.search(r'File "([^"]+)"', line)
            if file_match:
                files.append(file_match.group(1))
    return files


def _find_best_error_location(error_message, tb_lines):
    """Use priority system to find the best location to show for the error."""

    # Priority 0: Try to trace "not found" errors to their source
    traced_location = _trace_missing_definition_error(error_message, tb_lines)
    if traced_location:
        return traced_location

    # Priority 1: Find the deepest user code location (where error actually occurs)
    deepest_user, latest_user = _find_user_code_lines(tb_lines)

    # Always prefer deepest (root cause) over latest (where error gets caught)
    if deepest_user:
        line, code = deepest_user
        file_match = re.search(r'File "([^"]+)", line (\d+)', line)
        if file_match:
            return file_match.group(1), file_match.group(2), code

    # Fallback to latest user code if deepest isn't available
    if latest_user:
        line, code = latest_user
        file_match = re.search(r'File "([^"]+)", line (\d+)', line)
        if file_match:
            return file_match.group(1), file_match.group(2), code

    # Priority 2: Files mentioned in error message (fallback)
    error_files = _extract_files_from_error_message(error_message)
    if error_files:
        file_path, line_num = error_files[0]
        return file_path, line_num, None

    return None, None, None


def format_error_with_filtered_traceback(e: Exception) -> str:
    """
    Format an exception with clean, focused output that highlights user code
    and sanitizes sensitive information. Uses a priority system to find the
    most relevant location to show.
    """
    # Get the root cause exception by following the chain
    root_exception = e
    while root_exception.__cause__ or root_exception.__context__:
        root_exception = root_exception.__cause__ or root_exception.__context__

    # Get traceback from the root cause if possible
    if root_exception.__traceback__:
        tb_lines = traceback.format_exception(
            type(root_exception), root_exception, root_exception.__traceback__
        )
        tb_lines = "".join(tb_lines).split("\n")
    else:
        # Fallback to current exception traceback
        tb_lines = traceback.format_exc().split("\n")

    # Use the root cause exception for error info
    error_type = type(root_exception).__name__
    error_message = str(root_exception)

    # Sanitize the error message
    sanitized_error_message = _sanitize_sensitive_info(error_message)

    # Clean up module names in error messages (make them more readable)
    # Replace long hash-based module names with just the module name
    sanitized_error_message = re.sub(
        r"'([a-zA-Z_]*[a-f0-9]{32,})\.([^']+)'", r"'\2'", sanitized_error_message
    )

    # Clean up file paths with hash-based directory names
    sanitized_error_message = re.sub(
        r"/app/modules/[a-f0-9]{32,}/([^/)]+\.py)", r"\1", sanitized_error_message
    )

    # Find the best location to show using priority system
    best_file, best_line, best_code = _find_best_error_location(error_message, tb_lines)

    if best_file:
        filename = best_file.split("/")[-1]

        clean_error = f"**ERROR IN YOUR CODE:**\n"
        clean_error += f"File: {filename}, Line: {best_line}\n"
        clean_error += f"{error_type}: {sanitized_error_message}\n"

        if best_code:
            # Sanitize the problematic code as well
            sanitized_code = _sanitize_sensitive_info(best_code)
            clean_error += f"Code: {sanitized_code}\n"

        return clean_error

    # Fallback to original traceback format if we can't find user code
    filtered_lines = []
    for line in tb_lines:
        # Sanitize sensitive information first
        sanitized_line = _sanitize_sensitive_info(line)

        # Check if this is user code
        is_user_code = ("/app/modules/" in line or "/modules/" in line) and not any(
            exclude in line
            for exclude in [
                ".venv/",
                "site-packages/",
                "dist-packages/",
                "/usr/lib/python",
                "/usr/local/lib/python",
            ]
        )

        if is_user_code:
            # Highlight user code with >>> prefix
            filtered_lines.append(f">>> {sanitized_line}")
        elif any(
            exclude in line
            for exclude in [".venv/", "site-packages/", "dist-packages/"]
        ):
            # Collapse library code
            if 'File "' in line:
                match = re.search(r'File ".*?([^/]+\.py)", line (\d+)', line)
                if match:
                    filename, line_num = match.groups()
                    filtered_lines.append(f"    [library: {filename}:{line_num}]")
                else:
                    filtered_lines.append(f"    [library code]")
        elif (
            line.strip()
            and not line.startswith(" ")
            and not line.startswith("Traceback")
        ):
            # Keep error messages and exception names
            filtered_lines.append(sanitized_line)
        else:
            # Keep traceback header and other structural lines
            filtered_lines.append(sanitized_line)

    filtered_traceback = "\n".join(filtered_lines)
    sanitized_exception = _sanitize_sensitive_info(repr(e))
    return f"{sanitized_exception}\n{filtered_traceback}"
