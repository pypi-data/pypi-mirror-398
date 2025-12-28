# UAT (User Acceptance Testing) Suite

**Location**: `tests/uat/`
**Type**: Top-level test suite for user acceptance testing

This directory contains user acceptance tests that verify end-to-end functionality from a user's perspective.

## Purpose

UAT tests ensure that Aii CLI meets user requirements and behaves correctly in real-world scenarios. These tests:

- Run actual CLI commands (not mocked)
- Verify complete workflows end-to-end
- Test user-facing behavior and output
- Validate product specifications and acceptance criteria

## Tests

### OUTPUT Mode Policy Test

**File**: `test_output_mode_policy.py`
**Purpose**: Verify OUTPUT mode policy compliance across all SAFE functions
**Documentation**: `system-dev-docs/aii-cli/aii-cli-0.6.0-output-mode-implementation-summary.md`

**Coverage**:
- 3 SAFE functions (translate, explain, summarize)
- 4 output modes per function (CLEAN, STANDARD, THINKING, VERBOSE)
- 12 total test cases

**Usage**:
```bash
# Run all tests
python tests/uat/test_output_mode_policy.py

# Test specific function
python tests/uat/test_output_mode_policy.py --function translate

# Test specific mode
python tests/uat/test_output_mode_policy.py --mode THINKING

# Verbose output
python tests/uat/test_output_mode_policy.py --verbose
```

**Prerequisites**:
- Aii server must be running: `uv run aii serve --port 16169`
- All functions must have reasoning implemented

**Expected Results**: 100% pass rate (12/12 tests)

## Running UAT Tests

### Prerequisites

1. **Start Aii Server**:
   ```bash
   cd /path/to/aii-cli
   uv run aii serve --port 16169
   ```

2. **Verify Server Health**:
   ```bash
   curl http://localhost:16169/api/status
   ```

### Running Tests

```bash
# Run all UAT tests
cd /path/to/aii-cli
python tests/uat/test_output_mode_policy.py

# Run with pytest (if integrated)
pytest tests/uat/ -v
```

## Test Structure

UAT tests should follow this pattern:

```python
async def test_user_workflow():
    """
    Test a complete user workflow end-to-end.

    Example: User translates text in THINKING mode
    """
    # 1. Run actual CLI command
    result = await run_cli_command("translate hello to spanish --thinking")

    # 2. Verify output matches user expectations
    assert "hola" in result.output
    assert "💭 Reasoning:" in result.output
    assert "📊 Session Summary:" in result.output

    # 3. Verify no errors
    assert result.exit_code == 0
```

## Adding New UAT Tests

1. **Identify User Acceptance Criteria**:
   - What does the user expect to see?
   - What workflow are they performing?
   - What are the acceptance criteria?

2. **Create Test File**:
   - Name: `test_[feature]_uat.py`
   - Document: Link to design spec/requirements
   - Coverage: Test all acceptance criteria

3. **Run Test**:
   ```bash
   python tests/uat/test_[feature]_uat.py
   ```

4. **Update This README**:
   - Add test description
   - Document usage
   - Note prerequisites

## UAT vs Integration Tests

| Aspect | UAT Tests | Integration Tests |
|--------|-----------|-------------------|
| **Perspective** | User's perspective | Developer's perspective |
| **Scope** | Complete workflows | Component interactions |
| **Mocking** | Minimal (real server, real LLM) | More mocking allowed |
| **Speed** | Slower (real operations) | Faster (mocked dependencies) |
| **Purpose** | Verify user requirements | Verify technical integration |
| **Location** | `tests/uat/` | `tests/integration/` |

## Best Practices

1. **Keep Tests User-Focused**:
   - Test what users see and experience
   - Don't test internal implementation details

2. **Use Real Components**:
   - Run actual CLI commands
   - Use real Aii server (not mocked)
   - Call real LLM APIs (with rate limiting)

3. **Document Acceptance Criteria**:
   - Link to design specs
   - Reference user stories
   - Document expected behavior

4. **Make Tests Reproducible**:
   - Document prerequisites
   - Use consistent test data
   - Handle timing/flakiness

5. **Maintain Fast Feedback**:
   - Keep test suite under 5 minutes
   - Support filtering (by function, mode, etc.)
   - Provide clear failure messages

## Documentation References

- **Design Specs**: `system-design-docs/aii-cli/`
- **Implementation Guides**: `system-dev-docs/aii-cli/`
- **Test Strategy**: `docs/CONTRIBUTING.md` (Testing section)

## Troubleshooting

### Server Not Running

**Error**: `Connection refused` or `Server not available`

**Solution**:
```bash
# Start server
cd /path/to/aii-cli
uv run aii serve --port 16169

# Verify health
curl http://localhost:16169/api/status
```

### Tests Timing Out

**Error**: `Test timed out (>30s)`

**Solutions**:
- Check server logs: `/tmp/aii-server-*.log`
- Increase timeout in test code
- Check LLM API rate limits

### Missing Patterns in Output

**Error**: `Missing patterns: ['💭 Reasoning:']`

**Solutions**:
- Verify function has reasoning implemented
- Check server metadata includes reasoning
- Ensure WebSocket client extracts reasoning
- Restart server to load updated code

## Maintenance

**When to Update UAT Tests**:
- ✅ New features with user acceptance criteria
- ✅ Changes to user-facing behavior
- ✅ New output modes or display formats
- ✅ Breaking changes to CLI interface

**When NOT to Update UAT Tests**:
- ❌ Internal refactoring (no user impact)
- ❌ Performance optimizations (use performance tests)
- ❌ Bug fixes (use regression tests)
