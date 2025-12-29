# ESCALATION REQUIRED

<!--
Escalation Report Template
Used by: Behavior 8 - Escalation Criteria
Location: Output to console/log when escalation triggered

Use this template when stopping due to:
- Same error 3x consecutively
- Session stalled >20 minutes
- Obra breakpoint triggered
- Security-sensitive operation detected
- Data loss/corruption suspected
- Loop detected (same objective 3x without progress)
- Critical Obra exception
- Resource exhaustion
- Authentication permanently failed
- Breaking changes to production
-->

**Session**: {session_id}
**Timestamp**: {YYYY-MM-DDTHH:MM:SSZ}
**Reason**: {stop_reason}
**Category**: {CRITICAL | STALLED | SECURITY | LOOP | BREAKPOINT}

## Last Successful State

- **Checkpoint**: `.obra/checkpoints/{checkpoint_file}`
- **Completed**: {last_completed_milestone}
- **Progress**: {percentage}%

## Error Details

```
{error_message}
{stack_trace_if_available}
```

## Context

- **Files modified this session**: {file_count}
- **Last activity**: {time_since_last_activity}
- **Retry attempts**: {retry_count}

## Recommended Action

{suggestion based on error category}

<!--
Suggestions by category:
- CRITICAL: Review error, check data integrity, consider rollback
- STALLED: Check system resources, network, external services
- SECURITY: Verify authorization, review changes before proceeding
- LOOP: Analyze objective, check for conflicting requirements
- BREAKPOINT: Review Obra's request, provide required input
-->

## Resume Command

```
obra resume {session_id}
```

---

<!--
Escalation Categories:

| Category | When Used |
|----------|-----------|
| CRITICAL | Data loss, corruption, critical exception |
| STALLED | No progress for >20 minutes |
| SECURITY | Credentials, prod deploy, destructive action |
| LOOP | Same objective 3x without progress |
| BREAKPOINT | Obra explicitly requested human input |

Stop Immediately Triggers:
- Same error 3x consecutively (retry exhausted)
- Session stalled >20 minutes with no activity indicators
- Obra explicitly requests human input (breakpoint triggered)
- Security-sensitive operation detected
- Data loss or corruption detected or suspected
- Loop detected (same objective submitted 3x without progress)
- Critical exception in Obra itself
- Resource exhaustion (disk full, memory exhausted)
- Authentication permanently failed
- Breaking changes to production systems detected
-->
