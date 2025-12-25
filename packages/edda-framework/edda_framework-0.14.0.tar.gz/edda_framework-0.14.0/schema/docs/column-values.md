# Database Column Values Reference

This document defines the standard values for database columns that must be consistent across all Durax framework implementations (Edda/Python, Romancy/Go, etc.).

## workflow_instances.status

| Value | Description |
|-------|-------------|
| `running` | Workflow is actively executing |
| `completed` | Workflow finished successfully |
| `failed` | Workflow failed with an error |
| `cancelled` | Workflow was cancelled by user |
| `waiting_for_event` | Workflow is waiting for an external event (via `wait_event`) |
| `waiting_for_timer` | Workflow is waiting for a timer to expire (via `sleep`/`sleep_until`) |
| `waiting_for_message` | Workflow is waiting for a channel message (via `receive`) |
| `recurred` | Workflow completed one iteration and is ready to restart (Erlang-style tail recursion) |
| `compensating` | Workflow is executing compensation handlers |

## workflow_history.event_type

All event types use **PascalCase** for cross-language consistency.

| Value | Description |
|-------|-------------|
| `ActivityCompleted` | An activity finished successfully |
| `ActivityFailed` | An activity failed with an error |
| `EventReceived` | An external event was received (via `wait_event`) |
| `TimerExpired` | A timer expired (via `sleep`/`sleep_until`) |
| `ChannelMessageReceived` | A channel message was received (via `receive`) |
| `MessageTimeout` | A channel message receive timed out |
| `CompensationExecuted` | A compensation handler executed successfully |
| `CompensationFailed` | A compensation handler failed |
| `WorkflowFailed` | The workflow failed (recorded before status update) |
| `WorkflowCancelled` | The workflow was cancelled |

## workflow_history.data_type

| Value | Description |
|-------|-------------|
| `json` | Event data is stored as JSON text in `event_data` column |
| `binary` | Event data is stored as raw bytes in `event_data_binary` column |

## channel_subscriptions.mode

| Value | Description |
|-------|-------------|
| `broadcast` | All subscribers receive a copy of each message |
| `competing` | Only one subscriber receives each message (work queue pattern) |

## channel_messages.data_type

| Value | Description |
|-------|-------------|
| `json` | Message data is stored as JSON text in `data` column |
| `binary` | Message data is stored as raw bytes in `data_binary` column |

## outbox_events.status

| Value | Description |
|-------|-------------|
| `pending` | Event is waiting to be published |
| `processing` | Event is currently being processed by the relayer |
| `published` | Event was successfully published |
| `failed` | Event publishing failed after all retries |
| `invalid` | Event is malformed and cannot be published |
| `expired` | Event expired before it could be published |

## workflow_instances.framework

| Value | Description |
|-------|-------------|
| `python` | Workflow is managed by Edda (Python) |
| `go` | Workflow is managed by Romancy (Go) |

This column enables cross-language interoperability: any framework can deliver messages to workflows managed by other frameworks, while each framework only processes (replays/resumes) its own workflows.

---

## Cross-Language Compatibility Notes

1. **Event type naming**: Always use PascalCase (e.g., `ActivityCompleted`, not `activity_completed`)

2. **Message delivery**: Any framework can deliver channel messages to any workflow, regardless of the target workflow's framework. The delivering framework:
   - Acquires a lock on the target workflow
   - Records the message in `workflow_history` with the correct `event_type`
   - Updates the workflow status to `running`
   - Releases the lock

3. **Workflow processing**: Each framework only processes workflows where `framework` matches its own identifier. This ensures correct replay behavior.

4. **Activity IDs**: Both frameworks use the format `{activity_name}:{counter}` for deterministic replay (e.g., `fetch_data:1`, `receive_orders:2`).
