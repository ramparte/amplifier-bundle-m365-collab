# M365 Agent Collaboration Bundle

Multi-agent orchestration via Microsoft 365 SharePoint. Enables multiple Amplifier sessions to collaborate through a shared message board.

## Features

- **Agent Personas** - Define specialized agents (researcher, implementer, reviewer, coordinator)
- **Task Dispatch** - Send tasks to specific agents or broadcast to all
- **Message Board** - SharePoint-based persistent communication
- **Session Binding** - Link local Amplifier sessions to agent identities
- **Message Polling** - Route incoming messages to active sessions

## Quick Start

### 1. Set Up Credentials

```bash
# Create config directory
mkdir -p ~/.m365-tenant
chmod 700 ~/.m365-tenant

# Copy and edit templates
cp templates/credentials.template.json ~/.m365-tenant/credentials.json
cp templates/config.template.yaml ~/.m365-tenant/config.yaml

# Edit with your tenant details
nano ~/.m365-tenant/credentials.json
chmod 600 ~/.m365-tenant/credentials.json
```

### 2. Install the CLI

```bash
# Link orchestrator scripts
mkdir -p ~/bin
ln -sf ~/.m365-tenant/m365 ~/bin/m365

# Copy scripts to config dir
cp orchestrator/* ~/.m365-tenant/

# Add to PATH (add to ~/.bashrc)
export PATH=$HOME/bin:$PATH
```

### 3. Azure App Registration

Create an app registration in Azure AD with these **Application Permissions**:

| Permission | Purpose |
|------------|---------|
| `Files.ReadWrite.All` | Read/write SharePoint files |
| `Sites.ReadWrite.All` | Access SharePoint sites |
| `User.Read.All` | List users (optional, for user management) |
| `User.ReadWrite.All` | Create users (optional) |

Don't forget to **Grant admin consent** after adding permissions.

## Usage

```bash
# Check system status
m365 status

# Dispatch a task to an agent
m365 dispatch agent-alpha "Research caching patterns"

# Broadcast to all agents
m365 broadcast "New project starting"

# View recent messages
m365 messages -v

# Start an agent session
m365 start agent-alpha

# Run message poller
m365 poll
```

## Architecture

See [orchestrator/ARCHITECTURE.md](orchestrator/ARCHITECTURE.md) for the full system design.

```
┌─────────────────────────────────────────────────────────┐
│  CONTROLLER (your main session)                         │
│  - Dispatches tasks to agents                           │
│  - Monitors progress                                    │
└─────────────────────────┬───────────────────────────────┘
                          │
                          ▼
┌─────────────────────────────────────────────────────────┐
│  M365 TENANT (SharePoint)                               │
│  └── AgentMessages/                                     │
│      ├── msg-001.json  (task for agent-alpha)          │
│      ├── msg-002.json  (status from agent-beta)        │
│      └── ...                                            │
└─────────────────────────┬───────────────────────────────┘
                          │
        ┌─────────────────┼─────────────────┐
        ▼                 ▼                 ▼
┌───────────────┐ ┌───────────────┐ ┌───────────────┐
│ agent-alpha   │ │ agent-beta    │ │ agent-gamma   │
│ (researcher)  │ │ (implementer) │ │ (reviewer)    │
│ Local session │ │ Local session │ │ Local session │
└───────────────┘ └───────────────┘ └───────────────┘
```

## Agent Roles

| Agent | Role | Description |
|-------|------|-------------|
| agent-alpha | researcher | Investigates problems, gathers information |
| agent-beta | implementer | Builds solutions from specifications |
| agent-gamma | reviewer | Reviews code, ensures quality |
| agent-delta | coordinator | Plans work, assigns tasks |

## Files

```
~/.m365-tenant/
├── credentials.json     # Your tenant secrets (PRIVATE)
├── config.yaml          # Agent definitions
├── m365-orchestrator    # Main CLI
├── start-agent-session  # Agent launcher
├── message-poller       # Message router
├── m365                 # Convenience wrapper
├── sessions/            # Session state
├── personas/            # Agent context files
└── logs/                # Activity logs
```

## License

MIT
