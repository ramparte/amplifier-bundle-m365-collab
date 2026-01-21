#!/bin/bash
# M365 Agent Orchestrator Setup Script

set -e

CONFIG_DIR="$HOME/.m365-tenant"
BIN_DIR="$HOME/bin"

echo "M365 Agent Orchestrator Setup"
echo "=============================="

# Create directories
mkdir -p "$CONFIG_DIR"
chmod 700 "$CONFIG_DIR"
mkdir -p "$CONFIG_DIR/sessions"
mkdir -p "$CONFIG_DIR/personas"
mkdir -p "$CONFIG_DIR/logs"
mkdir -p "$BIN_DIR"

# Copy orchestrator scripts
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)/orchestrator"
cp "$SCRIPT_DIR/m365-orchestrator" "$CONFIG_DIR/"
cp "$SCRIPT_DIR/start-agent-session" "$CONFIG_DIR/"
cp "$SCRIPT_DIR/message-poller" "$CONFIG_DIR/"
cp "$SCRIPT_DIR/m365" "$CONFIG_DIR/"
cp "$SCRIPT_DIR/ARCHITECTURE.md" "$CONFIG_DIR/"
chmod +x "$CONFIG_DIR/m365-orchestrator"
chmod +x "$CONFIG_DIR/start-agent-session"
chmod +x "$CONFIG_DIR/message-poller"
chmod +x "$CONFIG_DIR/m365"

# Link convenience command
ln -sf "$CONFIG_DIR/m365" "$BIN_DIR/m365"

# Copy templates if config doesn't exist
if [ ! -f "$CONFIG_DIR/credentials.json" ]; then
    cp "$(dirname "$0")/templates/credentials.template.json" "$CONFIG_DIR/credentials.json"
    chmod 600 "$CONFIG_DIR/credentials.json"
    echo ""
    echo "⚠️  Edit your credentials:"
    echo "   nano $CONFIG_DIR/credentials.json"
fi

if [ ! -f "$CONFIG_DIR/config.yaml" ]; then
    cp "$(dirname "$0")/templates/config.template.yaml" "$CONFIG_DIR/config.yaml"
    chmod 600 "$CONFIG_DIR/config.yaml"
    echo ""
    echo "⚠️  Edit your config:"
    echo "   nano $CONFIG_DIR/config.yaml"
fi

echo ""
echo "✓ Setup complete!"
echo ""
echo "Add to your ~/.bashrc:"
echo "  export PATH=\$HOME/bin:\$PATH"
echo ""
echo "Then run:"
echo "  source ~/.bashrc"
echo "  m365 status"
