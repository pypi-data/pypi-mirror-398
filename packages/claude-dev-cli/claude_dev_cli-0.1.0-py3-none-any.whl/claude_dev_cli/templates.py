"""Prompt templates for various commands."""

TEST_GENERATION_PROMPT = """Generate comprehensive pytest tests for the following Python code from {filename}.

Code:
```python
{code}
```

Requirements:
- Use pytest framework
- Include fixtures where appropriate
- Test normal cases, edge cases, and error conditions
- Use descriptive test names
- Add docstrings to test functions
- Mock external dependencies if needed

Please provide only the test code without explanations."""

CODE_REVIEW_PROMPT = """Review the following Python code from {filename} for:

1. **Bugs and Logic Errors**: Identify potential bugs
2. **Security Issues**: Check for vulnerabilities
3. **Performance**: Suggest optimizations
4. **Best Practices**: Python idioms and patterns
5. **Code Quality**: Readability and maintainability

Code:
```python
{code}
```

Please provide a structured review with specific line numbers where applicable."""

DEBUG_PROMPT = """Analyze the following error and code to identify the root cause and provide a fix.

File: {filename}

Code:
```python
{code}
```

Error:
```
{error}
```

Please provide:
1. Root cause analysis
2. Specific fix with code
3. Explanation of why the error occurred"""

DOCS_GENERATION_PROMPT = """Generate comprehensive documentation for the following Python code from {filename}.

Code:
```python
{code}
```

Please provide:
1. Module-level docstring
2. Function/class docstrings in Google style
3. Usage examples
4. A README section explaining the module

Use clear, concise language suitable for developers."""

REFACTOR_PROMPT = """Analyze the following Python code from {filename} and suggest refactoring improvements.

Code:
```python
{code}
```

Focus on:
1. Code duplication (DRY principle)
2. Function/class complexity
3. Naming conventions
4. Code organization
5. Design patterns that could be applied
6. Type hints and documentation

Please provide refactored code with explanations."""

GIT_COMMIT_PROMPT = """Generate a conventional commit message for the following git diff.

Diff:
```
{diff}
```

Format:
```
<type>(<scope>): <subject>

<body>

<footer>
```

Types: feat, fix, docs, style, refactor, test, chore

Keep the subject under 50 characters. Use present tense. Be specific about what changed and why."""
