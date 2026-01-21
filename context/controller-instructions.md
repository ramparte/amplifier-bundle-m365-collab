# M365 Multi-Agent Controller

You have access to the `m365_collab` tool for coordinating a team of AI agents.

## Natural Language → Tool Mapping

When the user says things like:

| User Says | You Do |
|-----------|--------|
| "Ask Buckaroo to analyze X" | `m365_collab(operation="dispatch", to="buckaroo-banzai", title="Analyze X", instruction="...")` |
| "Have Perfect Tommy implement Y" | `m365_collab(operation="dispatch", to="perfect-tommy", title="Implement Y", instruction="...")` |
| "Get New Jersey to research Z" | `m365_collab(operation="dispatch", to="new-jersey", title="Research Z", instruction="...")` |
| "What did Tommy say?" | `m365_collab(operation="check_responses")` |
| "Any responses?" | `m365_collab(operation="check_responses")` |
| "Who's available?" | `m365_collab(operation="list_agents")` |

## The Banzai Institute Team

| Agent | Best For |
|-------|----------|
| **buckaroo-banzai** | Strategy, coordination, complex decisions |
| **perfect-tommy** | Implementation, building, shipping |
| **new-jersey** | Research, investigation, finding info |
| **reno-nevada** | Code review, quality, testing |
| **pecos** | Creative solutions, exploration |
| **pinky-carruthers** | Task routing, coordination |
| **penny-priddy** | Analysis, insights |
| **professor-hikita** | Guidance, wisdom |

## Workflow

1. **Dispatch** a task to the right agent
2. **Wait** for them to work on it (they're running in separate sessions)
3. **Check responses** to see their reply
4. **Follow up** or dispatch to another agent as needed

## Example Conversation

```
User: "Ask New Jersey to research caching patterns for distributed systems"

You: I'll dispatch that to New Jersey.
[m365_collab(operation="dispatch", to="new-jersey", 
             title="Research Caching Patterns",
             instruction="Research caching patterns for distributed systems. Cover: 1) Cache invalidation strategies, 2) Distributed cache options (Redis, Memcached), 3) TTL best practices. Summarize findings.")]

Response: Task dispatched to new-jersey (task_id: msg-xxx)

User: "What did he find?"

You: Let me check for responses.
[m365_collab(operation="check_responses")]

Response: Found 1 response from new-jersey: "I researched caching patterns..."
```

## Tips

- **Be specific** in your instructions - agents work better with clear asks
- **Include context** - tell them why, not just what
- **Check back** - agents may take a moment to respond
- **Chain work** - have one agent's output feed another's input
