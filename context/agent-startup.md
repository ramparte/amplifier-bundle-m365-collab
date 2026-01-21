# Agent Startup Protocol

**FIRST THING**: Check for pending tasks assigned to you:

```
m365_collab(operation="my_tasks", status="pending")
```

If you have tasks:
1. Work on the highest priority one first
2. **ALWAYS respond when done** using `m365_collab(operation="respond", ...)`

If no tasks, let the controller know you're ready:
```
m365_collab(operation="post_status", title="Online", message="Ready for tasks")
```
