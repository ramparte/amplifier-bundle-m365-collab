# M365 Multi-Agent Orchestration System

## Overview

This system enables multiple AI agent sessions running on your laptop to collaborate
through an M365 tenant, with you as the controller.

```
┌─────────────────────────────────────────────────────────────────────┐
│  CONTROLLER (your main Amplifier session)                           │
│  - Manages tenant users                                             │
│  - Dispatches tasks to agents                                       │
│  - Monitors progress via SharePoint/webhooks                        │
└──────────────────────────────┬──────────────────────────────────────┘
                               │
                               ▼
┌─────────────────────────────────────────────────────────────────────┐
│                     M365 TENANT                                      │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐                  │
│  │ agent-alpha │  │ agent-beta  │  │ agent-gamma │  ... more        │
│  │ (researcher)│  │(implementer)│  │ (reviewer)  │                  │
│  └──────┬──────┘  └──────┬──────┘  └──────┬──────┘                  │
│         │                │                │                          │
│         └────────────────┼────────────────┘                          │
│                          ▼                                           │
│  ┌──────────────────────────────────────────────────────────────┐   │
│  │  SharePoint: /AgentMessages/                                  │   │
│  │  - Tasks posted by controller                                 │   │
│  │  - Status updates from agents                                 │   │
│  │  - Inter-agent messages                                       │   │
│  └──────────────────────────────────────────────────────────────┘   │
│                          │                                           │
│                          ▼                                           │
│  ┌──────────────────────────────────────────────────────────────┐   │
│  │  Webhooks (Azure subscription on SharePoint changes)          │   │
│  │  → Notifies local webhook receiver when messages change       │   │
│  └──────────────────────────────────────────────────────────────┘   │
└──────────────────────────────┬──────────────────────────────────────┘
                               │ webhook callbacks
                               ▼
┌─────────────────────────────────────────────────────────────────────┐
│  LOCAL AGENT SESSIONS                                                │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐                  │
│  │ Session for │  │ Session for │  │ Session for │                  │
│  │ agent-alpha │  │ agent-beta  │  │ agent-gamma │                  │
│  │ (port 8766) │  │ (port 8767) │  │ (port 8768) │                  │
│  └─────────────┘  └─────────────┘  └─────────────┘                  │
│                                                                      │
│  Each session:                                                       │
│  - Runs as that agent's "persona"                                   │
│  - Polls or receives webhooks for tasks                             │
│  - Posts results back to SharePoint                                 │
│  - Can message other agents                                         │
└─────────────────────────────────────────────────────────────────────┘
```

## Components

### 1. Credentials Store (`~/.m365-tenant/credentials.json`)
- Tenant ID, client ID, client secret
- Admin credentials for user management
- PRIVATE - never commit to git

### 2. Configuration (`~/.m365-tenant/config.yaml`)
- Agent definitions (names, roles)
- Channel configuration
- Session bindings (which local session = which agent)

### 3. Agent Users
Created in the M365 tenant via Graph API:
- `agent-alpha@M365x72159956.onmicrosoft.com`
- `agent-beta@M365x72159956.onmicrosoft.com`
- etc.

### 4. SharePoint Message Board
`/Shared Documents/AgentMessages/`
- Messages are JSON files
- Types: task, status, message, handoff
- Each message has: id, from, to, type, content, status

### 5. Webhook Receiver
Local HTTP server that receives notifications when SharePoint changes:
- Runs on localhost:8765
- Routes messages to appropriate agent sessions
- Can use ngrok for public URL if needed

### 6. Session Manager
Scripts to:
- Start a new Amplifier session bound to an agent
- List running agent sessions
- Send instructions to specific agents
- Monitor all agent activity

## Workflows

### Controller dispatches task to specific agent:
1. Controller posts task to SharePoint with `to: agent-alpha`
2. Webhook fires, notifies local receiver
3. Receiver forwards to agent-alpha's session
4. Agent-alpha works on task, posts result
5. Webhook notifies controller

### Agent-to-agent collaboration:
1. agent-alpha posts task with `to: agent-beta`
2. agent-beta receives, works, responds
3. Both can see conversation in SharePoint

### Broadcast to all agents:
1. Controller posts with `to: all`
2. All agent sessions receive notification
3. Agents coordinate among themselves

## Files

```
~/.m365-tenant/
├── credentials.json     # Secrets (600 permissions)
├── config.yaml          # Configuration
├── sessions/            # Session state
│   ├── alpha.json       # agent-alpha session info
│   ├── beta.json        # agent-beta session info
│   └── ...
├── logs/                # Activity logs
└── ARCHITECTURE.md      # This file
```

## CLI Commands

```bash
# Manage agents
m365-orchestrator users list
m365-orchestrator users create agent-alpha
m365-orchestrator users create-all

# Manage sessions  
m365-orchestrator session start agent-alpha
m365-orchestrator session list
m365-orchestrator session stop agent-alpha

# Send instructions
m365-orchestrator dispatch agent-alpha "Research the caching patterns"
m365-orchestrator broadcast "Stand by for new project"

# Monitor
m365-orchestrator status
m365-orchestrator messages --follow

# Webhooks
m365-orchestrator webhook start
m365-orchestrator webhook status
```
