#!/usr/bin/env python3
import re
import logging

from langchain_core.tools import tool


@tool
def strip_tests_from_diff(
    diff_content: str, test_regex: str | re.Pattern = r"test"
) -> str:
    """
    Remove file sections from a unified git diff where either path contains a test indicator.

    Args:
        diff_content: Full diff as a string (required).
        test_regex: Regex (string or compiled) used to detect test files in paths.
                    Defaults to a case-insensitive "test" substring match.

    Returns:
        A diff string with sections for matched test files removed.

    Notes:
        - Preserves any leading content before the first "diff --git ..." header.
        - Recognizes git diff file headers of the form: `diff --git a/<path> b/<path>`.
    """

    logger = logging.getLogger(__name__)

    if not isinstance(diff_content, str):
        raise TypeError("diff_content must be a string")

    if diff_content == "":
        return diff_content

    # Prepare regexes
    header_re = re.compile(r"^diff --git a/(.+?) b/(.+?)$", re.MULTILINE)
    if isinstance(test_regex, str):
        test_re = re.compile(test_regex, re.IGNORECASE)
    elif isinstance(test_regex, re.Pattern):
        test_re = test_regex
    else:
        raise TypeError("test_regex must be a string or compiled re.Pattern")

    matches = list(header_re.finditer(diff_content))
    if not matches:
        return diff_content

    parts: list[str] = []
    first = matches[0]
    if first.start() > 0:
        parts.append(diff_content[: first.start()])

    removed = 0
    for i, m in enumerate(matches):
        start = m.start()
        end = matches[i + 1].start() if i + 1 < len(matches) else len(diff_content)
        section = diff_content[start:end]
        a_path, b_path = m.group(1), m.group(2)

        # If either side matches the test pattern, skip this section
        try:
            if test_re.search(a_path) or test_re.search(b_path):
                removed += 1
                continue
        except re.error:
            # If the provided regex is invalid at runtime, don't remove anything and log
            logger.exception("Invalid test_regex provided; returning original diff")
            return diff_content

        parts.append(section)

    logger.debug("strip_tests_from_diff: removed %d file sections", removed)
    return "".join(parts)
