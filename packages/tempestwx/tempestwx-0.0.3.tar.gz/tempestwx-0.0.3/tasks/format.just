# run format tasks
[group('format')]
format: format-fix format-source

# apply safe auto-fixes (continues on error)
[group('format')]
format-fix:
    uv run ruff check --fix --exit-zero {{SOURCES}} {{TESTS}}

# format code source
[group('format')]
format-source:
    uv run ruff format {{SOURCES}} {{TESTS}}
