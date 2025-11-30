---
name: tdd
description: Implement features using Test-Driven Development with disciplined red-green-refactor workflow and quality gates
---

<role>
You are implementing features using Test-Driven Development (TDD). This is a disciplined, gated workflow that ensures quality through behavioral testing and systematic verification.
</role>

<context>
TDD follows a gated workflow where each gate must complete successfully before proceeding. Tests become contracts that define expected behavior.

Project: FastAPI + LangGraph + LangChain AI workflow system
Stack: Python 3.11+, pytest, ruff, Pydantic
Patterns: Async-first, dependency injection, structured error handling
See CLAUDE.md for project conventions.
</context>

<critical_notes>
- Gates are sequential checkpoints - complete each before proceeding
- Tests are behavioral contracts - test what the system does, not how it does it
- Gate 3 commits failing tests as IMMUTABLE contract - no test changes after this
- Behavioral over implementation - tests should survive refactoring
- Clean workspace - organize temporary files in .claude/workspace/
- MVP mindset - duplication over wrong abstraction, YAGNI, simple solutions
</critical_notes>

<workflow>
## Phase 0: Test Strategy Planning

<instructions>
Before writing any code or tests, plan your testing approach:
- What test levels are needed? (Unit for logic, Integration for API/LangGraph flows)
- What are the critical behaviors to validate?
- What edge cases and error scenarios matter?
- What external dependencies need mocking (API clients, LLM calls)?
- Is test data realistic and minimal?
</instructions>

<thinking>
Test strategy considerations:
1. Is this pure logic (unit tests) or does it involve LangGraph/API calls (integration tests)?
2. What are the invariants that must hold true?
3. What external dependencies need mocking (Anthropic API, Ticketmaster, Yelp, Weather)?
4. For LangGraph workflows: test node behaviors independently or full graph flow?
5. What error conditions matter (API failures, invalid input, LLM errors)?
6. What would constitute comprehensive coverage for this feature?
</thinking>

## Phase 1: Understanding

<instructions>
Explore and understand what needs to be built. Consider:
- How does this feature fit the existing architecture (LangGraph workflow, tools, FastAPI)?
- Which modules and patterns should I follow (see CLAUDE.md)?
- What are different implementation approaches?
- What's the most maintainable design for an MVP?
- Which existing code can serve as reference?
</instructions>

<thinking>
I need to understand this feature deeply before writing tests:
1. What existing code patterns in this codebase should I follow?
2. Which modules will this feature interact with (agent.py, tools/, main.py)?
3. What are the user's actual needs beyond the stated requirements?
4. Are there similar features I can reference for consistency?
5. What's the simplest, most maintainable approach (avoid over-engineering)?
6. What are the critical behaviors vs nice-to-have features?
</thinking>

## Phase 2: Gated Implementation

### Gate 1 — Write Failing Tests

<instructions>
Create comprehensive behavioral tests that define the contract.

**Test file organization:**
- Unit tests: `tests/unit/test_*.py` - Pure logic, no I/O, fully mocked
- Integration tests: `tests/integration/test_*.py` - API clients, LangGraph flows, database

**Write tests covering:**
- Happy path: Main success scenario
- Edge cases: Boundary conditions, empty inputs, unusual but valid data
- Error conditions: API failures, invalid input, resource exhaustion

**Test quality requirements:**
- Behavioral focus: Test WHAT the system does, not HOW it does it
- Arrange-Act-Assert structure: Setup, execute, verify
- Single concept per test: One behavior tested per test function
- Realistic test data: Use realistic examples, not "foo"/"bar"
- Proper mocking: Mock external dependencies (httpx for API calls, LLM responses)

**Expected outcome:** All new tests FAIL with meaningful error messages.
</instructions>

<thinking>
I'm writing behavioral tests that will define the contract:
1. What behaviors should users observe when this feature works?
2. What edge cases and error conditions must be handled?
3. Which existing test files show patterns I should follow?
4. How can I make tests resilient to implementation changes?
5. Am I testing user outcomes, not internal implementation details?
6. For tools: Am I testing ToolResult structure (success, data, error_type, error_detail, user_message)?
7. For LangGraph: Am I testing node outputs and state transitions, not internal LLM prompts?
</thinking>

### Gate 2 — Verify Tests Fail Correctly

<instructions>
Confirm tests fail appropriately before proceeding.

Run: `pytest tests/unit/test_[feature].py -xvs` (or integration path)

Verify:
- All new tests FAIL with meaningful error messages
- Failures indicate missing functionality (not test bugs or syntax errors)
- Error messages guide what needs implementing
- Existing tests remain PASSING (no regression)

If tests pass when they should fail, or fail for wrong reasons (syntax, imports), fix tests before proceeding.
</instructions>

<thinking>
Before proceeding, I must verify test failures are correct:
1. Are all new tests failing with clear, meaningful errors?
2. Do errors indicate missing functionality (ImportError, AttributeError, assertion failures)?
3. Are existing tests still passing (no regression)?
4. Do the failures guide me toward what needs implementing?
5. Are failure messages descriptive enough to debug if implementation goes wrong?
</thinking>

### Gate 3 — Commit Failing Tests (Lock Contract)

<instructions>
Lock in the test contract with git commit.

**This is a critical checkpoint:** Tests become IMMUTABLE after this commit.

Run:
```bash
git add tests/unit/test_[feature].py  # or tests/integration/
git commit -m "test: add failing tests for [feature] (TDD Gate 3)

- Test happy path: [brief description]
- Test edge cases: [what scenarios]
- Test error handling: [what failures]
"
```

After this commit, you MUST NOT modify these tests unless they are incorrect (test bug, not implementation bug).
</instructions>

<thinking>
I'm committing the test contract:
1. Have I included all necessary test cases (happy path, edges, errors)?
2. Are the tests clear enough to guide implementation?
3. Is my commit message descriptive of what behavior is being tested?
4. Am I ready to treat these tests as immutable requirements?
5. Did I follow project patterns (async tests with pytest-asyncio, proper mocking)?
</thinking>

### Gate 4 — Make Tests Pass (Green)

<instructions>
Implement minimal solution that satisfies all tests.

**Implementation requirements:**
- Write minimal code to pass tests (not production-perfect, just working)
- Keep tests unchanged (they're the immutable contract from Gate 3)
- Follow CLAUDE.md patterns: dependency injection, ToolResult errors, async/await
- Ensure NEW code has 100% test coverage (not overall, just new lines)

**Verification steps:**
1. Run tests: `pytest tests/unit/test_[feature].py -xvs`
2. Check coverage of NEW code: `pytest tests/unit/test_[feature].py --cov=app/[module] --cov-report=term-missing`
3. Verify all new lines are covered (look for missing line numbers)
4. Launch overfit-verifier agent to ensure generalization

**Expected outcome:**
- All tests pass (green)
- New code has 100% coverage
- Implementation is general, not hardcoded to test values
</instructions>

<thinking>
Now I'll implement the solution:
1. What's the minimal code needed to pass these tests?
2. Am I solving the general problem, not just making specific test cases pass?
3. Does my implementation follow CLAUDE.md patterns (dependency injection, async/await, ToolResult)?
4. Is every line of new code executed by at least one test?
5. Will this pass the overfit-verifier's scrutiny (no hardcoded test values)?
6. Is this implementation clear and maintainable for an MVP?
7. Am I avoiding premature abstraction (Rule of Three: extract on 3rd occurrence)?
</thinking>

### Gate 5 — Refactor (If Needed)

<instructions>
Improve code quality while keeping tests green.

**When to refactor:**
- Code duplication appeared (but wait for 3rd occurrence before extracting)
- Function is too long (> 50 lines) or does multiple things
- Naming is unclear or inconsistent
- Unnecessary complexity or nesting

**When NOT to refactor:**
- Tests aren't green yet (fix tests first)
- Code works and is clear enough for MVP
- Only one or two occurrences of pattern (wait for third)

**Refactoring rules:**
- Run tests after EVERY refactoring step
- Keep tests green throughout (if test breaks, revert refactoring)
- Refactor production code AND test code for clarity
- No new functionality during refactoring

**Verification:**
Run: `pytest tests/ -xvs` (full suite after each refactor)
</instructions>

<thinking>
Should I refactor or is code good enough for MVP?
1. Is there duplication? How many times? (Need 3+ to extract)
2. Are functions clear and focused (Single Responsibility)?
3. Is naming consistent and descriptive?
4. Would refactoring make code significantly clearer or is it premature optimization?
5. If refactoring, what's the smallest safe step I can take?
6. After refactoring, do ALL tests still pass?
</thinking>

### Gate 6 — Document Changes

<instructions>
Use doc-drafter agent to update documentation.

The agent will update:
- CHANGELOG.md (always)
- README.md (if user-facing feature)
- docs/API.md (if API endpoints or tools changed)
- Docstrings (for new/modified functions)

Launch agent with context about what changed and why.
</instructions>

<thinking>
Documentation needs:
1. What user-facing changes occurred (for README, CHANGELOG)?
2. What technical changes occurred (for API.md, ARCHITECTURE.md)?
3. Are docstrings clear and following Google-style format?
4. Should examples be updated to show new feature?
</thinking>

### Gate 7 — Final Review

<instructions>
Run comprehensive quality checks before committing implementation.

**Run in parallel:**
1. Code review: Launch code-reviewer agent for architectural and security review
2. Linting: `ruff check . && ruff format .`
3. Full test suite: `pytest tests/ --cov=app --cov-report=term-missing`
4. Coverage check: Verify overall coverage > 80%, new code coverage = 100%

**Review checklist:**
- Architecture: Does code follow CLAUDE.md patterns?
- Security: No hardcoded secrets, proper input validation?
- Performance: Async/await used correctly, no blocking I/O?
- AI/LLM patterns: Structured outputs, proper ToolResult errors?
- Test quality: Behavioral tests that survive refactoring?

**Expected outcome:** All checks pass, code-reviewer gives "READY TO COMMIT" verdict.
</instructions>

<thinking>
Final quality checks:
1. Will the code pass the reviewer agent's standards (architecture, security, AI patterns)?
2. Are there any linting or formatting issues?
3. Does test coverage meet requirements (>80% overall, 100% for new code)?
4. Have I cleaned up temporary files in .claude/workspace/?
5. Is the implementation ready for production use (or at least MVP quality)?
6. Are there any TODOs or FIXMEs that should be addressed now?
</thinking>

### Gate 8 — Commit Implementation

<instructions>
Commit the implementation with clear commit message.

```bash
git add app/[files] tests/[files]
git commit -m "feat: implement [feature]

Implementation:
- [What was implemented]
- [Key architectural decisions]

Testing:
- [Coverage metrics]
- [Test types: unit/integration]

Follows TDD workflow (Gates 1-7 complete)
"
```

If ROADMAP.md tracks this feature, mark it complete: `- [x] Feature name`
</instructions>

<thinking>
Committing implementation:
1. Are all changed files staged (app/, tests/, docs/)?
2. Is my commit message descriptive of what was implemented and why?
3. Did I reference related issues or design docs?
4. Is ROADMAP.md updated if this completes a planned feature?
</thinking>
</workflow>

<completion_checklist>
Before marking TDD workflow complete, verify ALL of the following:

**Process compliance:**
- [ ] All 8 gates completed in sequence
- [ ] Gate 3 committed failing tests as immutable contract
- [ ] No test modifications after Gate 3 (unless test bugs found)
- [ ] Tests remained green throughout Gates 5-8

**Test quality:**
- [ ] Tests are behavioral (test what system does, not how)
- [ ] Tests cover happy path, edge cases, and error conditions
- [ ] Test pyramid balanced (majority unit tests, fewer integration)
- [ ] New code has 100% test coverage
- [ ] Overall project coverage > 80%

**Implementation quality:**
- [ ] Implementation is general, not overfitted to test cases
- [ ] Follows CLAUDE.md patterns (async/await, dependency injection, ToolResult)
- [ ] No hardcoded secrets or security vulnerabilities
- [ ] Proper error handling (tools return errors, don't raise)
- [ ] Code passes ruff linting and formatting

**Documentation:**
- [ ] CHANGELOG.md updated
- [ ] README.md or docs/ updated if user-facing changes
- [ ] Docstrings follow Google-style format
- [ ] ROADMAP.md updated if feature complete

**Cleanup:**
- [ ] Temporary files removed from .claude/workspace/
- [ ] No commented-out code or debug prints
- [ ] All TODOs either resolved or tracked in issues

**Git history:**
- [ ] Two commits: (1) failing tests (Gate 3), (2) implementation (Gate 8)
- [ ] Commit messages descriptive and follow conventional commits
- [ ] Code-reviewer approved with "READY TO COMMIT" verdict
</completion_checklist>

<anti_patterns>
Common TDD anti-patterns to AVOID:

**Test-After Development:**
- ❌ Writing implementation before tests
- ✅ Always write failing test first (Gates 1-2 before Gate 4)

**Testing Implementation Details:**
- ❌ Tests that break when refactoring (coupled to internals)
- ✅ Behavioral tests that verify outcomes, not implementation

**Modifying Tests to Pass:**
- ❌ Changing tests after Gate 3 to make implementation easier
- ✅ Tests are immutable contract - fix implementation to pass tests

**Over-Mocking:**
- ❌ Mocking everything including internal functions
- ✅ Mock external dependencies only (API clients, LLM, database)

**Premature Abstraction:**
- ❌ Extracting helpers/base classes on first duplication
- ✅ Wait for 3rd occurrence before extracting (Rule of Three)

**Skipping Gates:**
- ❌ Jumping straight to implementation without failing tests
- ✅ Complete all gates in sequence, verify at each checkpoint

**Large Test Batches:**
- ❌ Writing 20 tests before running any
- ✅ RED-GREEN cycle: one test at a time, verify failure, implement, verify pass

**Ignoring Coverage Gaps:**
- ❌ Accepting < 100% coverage for new code
- ✅ Every new line must be tested before Gate 7 passes
</anti_patterns>

<task>
Implement the following feature using the TDD workflow described above:

$ARGUMENTS

Remember: Test FIRST, implement SECOND, refactor THIRD. Each gate must complete successfully before proceeding to the next.
</task>
