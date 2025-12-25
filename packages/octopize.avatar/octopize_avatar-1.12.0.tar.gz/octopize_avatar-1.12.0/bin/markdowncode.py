import re
import sys

"""Extract python code blocks from markdown."""
print(f"Processing file: {sys.argv[2]}", file=sys.stderr)  # noqa: T201
doc = open(sys.argv[2])
blocks = re.findall(r"\n```python\n(.*?)\n```", doc.read(), re.DOTALL)
print("\n\n\n".join(block for block in blocks))  # noqa: T201
