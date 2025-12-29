# Session Handoff: {session_id}

<!--
Handoff Template
Used by: Behavior 10 - Clean Handoff
Location: .obra/handoffs/{session_id}_handoff.md

ALWAYS produce a handoff when session ends, whether success, failure, or abort.
This document should give the human everything needed to understand session outcome.
-->

**Status**: {COMPLETED | FAILED | ABORTED | ESCALATED}
**Duration**: {start_time} to {end_time} ({duration})
**Verification**: {VERIFIED | UNVERIFIED}

## Summary

{One paragraph summary of what happened during this session. Include key accomplishments, any problems encountered, and overall outcome.}

## Accomplished

- [ ] {Story/task 1 - status}
- [ ] {Story/task 2 - status}
- [ ] {Story/task 3 - status}

## Files Changed

**Created**:
- {path/to/new/file1.py}
- {path/to/new/file2.py}

**Modified**:
- {path/to/existing/file.py} - {brief description of changes}

**Deleted**:
- {path/to/removed/file.py} - {reason for deletion}

## Open Issues

- {Any known problems, limitations, or incomplete work}
- {Edge cases not handled}
- {Technical debt introduced}

## Next Steps

<!-- Include appropriate next steps based on session outcome -->

### If Incomplete:
- {What remains to be done}
- {Priority order for remaining work}

### If Failed:
- {Suggested remediation steps}
- {Root cause if known}

### If Complete:
- {Suggested follow-up improvements}
- {Optional enhancements to consider}

## Resume

- **Command**: `obra resume {session_id}`
- **Checkpoint**: `.obra/checkpoints/{latest_checkpoint_file}`
- **Continuation prompt**: `.obra/prompts/_active/{work_id}_continuation/`

---

<!--
Status Values:
- COMPLETED: All objectives achieved
- FAILED: Session ended with unrecoverable error
- ABORTED: Session stopped before completion (context exhaustion, user interrupt)
- ESCALATED: Session stopped due to escalation criteria

Verification Levels:
- VERIFIED: Deliverables exist AND smoke test passed
- UNVERIFIED: Deliverables exist but no smoke test OR test failed
-->
