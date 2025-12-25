import re
from functools import cache

# pattern matching likely external urls (missing protocol)
LIKELY_EXTERNAL_PATTERN = (
	r"^(?![./#])(?:[a-zA-Z0-9-]+\.)+[a-zA-Z]{2,}(?::\d+)?(?:/[^\s\\]*)?$"
)
# matching emails
EMAIL_PATTERN = r"(mailto:)?((?:[a-z0-9!#$%&'*+/=?^_`{|}~-]+(?:\.[a-z0-9!#$%&'*+/=?^_`{|}~-]+)*|\"(?:[\x01-\x08\x0b\x0c\x0e-\x1f\x21\x23-\x5b\x5d-\x7f]|\\[\x01-\x09\x0b\x0c\x0e-\x7f])*\")@(?:(?:[a-z0-9](?:[a-z0-9-]*[a-z0-9])?\.)+[a-z0-9](?:[a-z0-9-]*[a-z0-9])?|\[(?:(?:(2(5[0-5]|[0-4][0-9])|1[0-9][0-9]|[1-9]?[0-9]))\.){3}(?:(2(5[0-5]|[0-4][0-9])|1[0-9][0-9]|[1-9]?[0-9])|[a-z0-9-]*[a-z0-9]:(?:[\x01-\x08\x0b\x0c\x0e-\x1f\x21-\x5a\x53-\x7f]|\\[\x01-\x09\x0b\x0c\x0e-\x7f])+)\]))"

# identify comments and whitespace in javascript
MINIFY_JS_PATTERN = r"""
    //.*?$    |
    /\*.*?\*/ |
    \s+
    """


@cache
def likely_external():
	"""Returns a compiled regex for identifying likely external links."""
	return re.compile(LIKELY_EXTERNAL_PATTERN)


@cache
def email():
	"""Returns a compiled regex for matching email addresses.
	The first group is an optional mailto: prefix."""
	return re.compile(EMAIL_PATTERN)


@cache
def minify_js():
	"""Returns a compiled regex for JavaScript minifications."""
	return re.compile(MINIFY_JS_PATTERN, re.MULTILINE | re.DOTALL | re.VERBOSE)
