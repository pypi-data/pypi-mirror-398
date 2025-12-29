# Continuation Prompt

<!--
Continuation Prompt Template
Used by: Behavior 9 - Context Budget Management
Location: .obra/prompts/_active/{work_id}_continuation/CONTINUE.md

Create this prompt when context usage reaches 80% (red zone).
Include all context needed for a fresh session to continue seamlessly.
-->

## Previous Session

- **Session ID**: {session_id}
- **Work ID**: {work_id}
- **Completed**: {list of completed stories}
- **In Progress**: {current_story} ({percentage}%)

## Resume Instructions

1. Read checkpoint: `.obra/checkpoints/{latest_checkpoint_file}`
2. Run: `obra resume {session_id}`
3. Continue with: "{next_objective}"

## Key Context (Summary)

<!--
Include only the essential context needed to continue.
Summarize key decisions, architecture choices, and important state.
-->

{relevant_context_summary}

## Files Modified

<!--
List all files modified in the previous session.
Include brief notes about significant changes.
-->

- `{path/to/file1.py}` - {brief description}
- `{path/to/file2.py}` - {brief description}

## Notes for Continuation

<!--
Any important notes for the next session:
- Decisions made and rationale
- Blockers encountered
- Technical context
- Things to watch out for
-->

{handoff_notes}

---

<!--
Example Continuation Prompt:

# Continuation Prompt

## Previous Session
- Session ID: abc123
- Work ID: FEAT-AUTH-001
- Completed: Stories 1-2 (Setup, JWT Implementation)
- In Progress: Story 3 (Password Reset) - 40%

## Resume Instructions
1. Read checkpoint: .obra/checkpoints/abc123_2025-12-20T16-00-00Z.yaml
2. Run: obra resume abc123
3. Continue with: "Complete password reset email verification flow"

## Key Context (Summary)
- JWT auth implemented with RS256 signing
- Access tokens: 15 min expiry, Refresh tokens: 7 days with rotation
- User model has email, password_hash, refresh_token fields
- Password reset requires: token generation, email sending, verification endpoint

## Files Modified
- `src/auth/jwt.py` - JWT generation and validation
- `src/auth/middleware.py` - Auth middleware for protected routes
- `src/models/user.py` - Added refresh_token field

## Notes for Continuation
- Using SendGrid for email (API key in .env)
- Password reset tokens expire in 1 hour
- Started implementing token generation, need to add email sending
-->
