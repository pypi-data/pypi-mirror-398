#!/bin/bash

# Nia MCP Server Universal Installer for macOS
# This script automatically installs dependencies and configures Nia MCP Server
#
# Usage:
#   Interactive (no API key):  curl -fsSL https://app.trynia.ai/cli | sh
#   With API key:              curl -fsSL https://app.trynia.ai/api/setup-script | bash -s -- API_KEY IDE_NAME [--remote|--local]

set -e  # Exit on error

# Color codes for output
RED='\033[0;31m'
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
BOLD='\033[1m'
NC='\033[0m' # No Color

# Remote MCP URL
REMOTE_MCP_URL="https://apigcp.trynia.ai/mcp"
NIA_API_URL="https://apigcp.trynia.ai/"
APP_URL="${NIA_APP_URL:-https://app.trynia.ai}"
BACKEND_URL="${NIA_BACKEND_URL:-https://apigcp.trynia.ai}"

# Print functions
print_header() {
    echo -e "\n${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo -e "${BLUE}  $1${NC}"
    echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}\n"
}

print_success() {
    echo -e "${GREEN}✓${NC} $1"
}

print_error() {
    echo -e "${RED}✗${NC} $1"
}

print_info() {
    echo -e "${BLUE}ℹ${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}⚠${NC} $1"
}

# ============================================================================
# Device Authorization Flow Functions
# ============================================================================

# Start a device authorization session
# Returns: Sets DEVICE_SESSION_ID, DEVICE_USER_CODE, DEVICE_VERIFICATION_URL
start_device_session() {
    print_info "Starting device authorization..."
    
    # Call the backend to start a device session
    local response
    response=$(curl -s --fail --max-time 30 -X POST "${BACKEND_URL}/public/mcp-device/start" \
        -H "Content-Type: application/json" \
        2>&1)
    
    if [ $? -ne 0 ]; then
        print_error "Failed to connect to Nia servers."
        print_info "Please check your internet connection and try again."
        return 1
    fi
    
    # Parse response (extract fields from JSON)
    DEVICE_SESSION_ID=$(echo "$response" | grep -o '"authorization_session_id":"[^"]*"' | cut -d'"' -f4)
    DEVICE_USER_CODE=$(echo "$response" | grep -o '"user_code":"[^"]*"' | cut -d'"' -f4)
    DEVICE_VERIFICATION_URL=$(echo "$response" | grep -o '"verification_url":"[^"]*"' | cut -d'"' -f4)
    
    if [ -z "$DEVICE_SESSION_ID" ] || [ -z "$DEVICE_USER_CODE" ]; then
        print_error "Failed to start device session."
        print_info "Server response: $response"
        return 1
    fi
    
    return 0
}

# Exchange device session for API key
# Args: $1 = session_id, $2 = user_code
# Returns: Sets DEVICE_API_KEY
exchange_for_api_key() {
    local session_id=$1
    local user_code=$2
    
    print_info "Exchanging code for API key..."
    
    local response
    response=$(curl -s --fail --max-time 30 -X POST "${BACKEND_URL}/public/mcp-device/exchange" \
        -H "Content-Type: application/json" \
        -d "{\"authorization_session_id\":\"$session_id\",\"user_code\":\"$user_code\"}" \
        2>&1)
    
    if [ $? -ne 0 ]; then
        print_error "Failed to connect to Nia servers."
        return 1
    fi
    
    # Check for errors
    local error_detail
    error_detail=$(echo "$response" | grep -o '"detail":"[^"]*"' | cut -d'"' -f4)
    if [ -n "$error_detail" ]; then
        print_error "$error_detail"
        return 1
    fi
    
    # Extract API key
    DEVICE_API_KEY=$(echo "$response" | grep -o '"api_key":"[^"]*"' | cut -d'"' -f4)
    
    if [ -z "$DEVICE_API_KEY" ]; then
        print_error "Failed to get API key from server."
        print_info "Server response: $response"
        return 1
    fi
    
    return 0
}

# Open browser on macOS
open_browser() {
    local url=$1
    if command -v open &> /dev/null; then
        open "$url" 2>/dev/null || true
    fi
}

# Interactive IDE selection
select_ide_interactive() {
    echo ""
    echo -e "${CYAN}Select your coding agent:${NC}"
    echo ""
    echo "  1) Cursor"
    echo "  2) Claude Code"
    echo "  3) VS Code"
    echo "  4) Windsurf"
    echo "  5) Cline"
    echo "  6) Continue.dev"
    echo "  7) JetBrains"
    echo "  8) Claude Desktop"
    echo "  9) Other (show all)"
    echo ""
    
    local choice
    read -p "Enter number [1]: " choice </dev/tty
    choice=${choice:-1}
    
    case "$choice" in
        1) SELECTED_IDE="cursor" ;;
        2) SELECTED_IDE="claude-code" ;;
        3) SELECTED_IDE="vscode" ;;
        4) SELECTED_IDE="windsurf" ;;
        5) SELECTED_IDE="cline" ;;
        6) SELECTED_IDE="continue" ;;
        7) SELECTED_IDE="jetbrains" ;;
        8) SELECTED_IDE="claude-desktop" ;;
        9)
            echo ""
            print_supported_ides
            echo ""
            read -p "Enter IDE name: " SELECTED_IDE </dev/tty
            ;;
        *)
            SELECTED_IDE="cursor"
            ;;
    esac
    
    print_success "Selected: $SELECTED_IDE"
}

# Interactive mode selection
select_mode_interactive() {
    local ide=$1
    
    local can_remote=false
    local can_local=false
    
    supports_remote "$ide" && can_remote=true
    supports_local "$ide" && can_local=true
    
    # If only one mode is supported, use it
    if [ "$can_remote" = true ] && [ "$can_local" = false ]; then
        SELECTED_MODE="remote"
        print_info "Using remote mode (only mode supported for $ide)"
        return
    fi
    if [ "$can_local" = true ] && [ "$can_remote" = false ]; then
        SELECTED_MODE="local"
        print_info "Using local mode (only mode supported for $ide)"
        return
    fi
    
    # Both modes supported - ask user
    echo ""
    echo -e "${CYAN}Select installation method:${NC}"
    echo ""
    echo "  1) Local  - Runs on your machine. More stable. Requires Python & pipx. (recommended)"
    echo "  2) Remote - Connects to Nia cloud. No installation required. (unstable)"
    echo ""
    
    local choice
    read -p "Enter number [1]: " choice </dev/tty
    choice=${choice:-1}
    
    case "$choice" in
        2) SELECTED_MODE="remote" ;;
        *) SELECTED_MODE="local" ;;
    esac
    
    print_success "Selected: $SELECTED_MODE mode"
}

# Run the interactive device flow setup
run_interactive_setup() {
    print_header "Nia MCP Server Interactive Setup"
    
    echo -e "${BLUE}"
    cat << "EOF"
    ███╗   ██╗██╗ █████╗
    ████╗  ██║██║██╔══██╗
    ██╔██╗ ██║██║███████║
    ██║╚██╗██║██║██╔══██║
    ██║ ╚████║██║██║  ██║
    ╚═╝  ╚═══╝╚═╝╚═╝  ╚═╝
EOF
    echo -e "${NC}"
    
    echo "Welcome to Nia! Let's set up your MCP server."
    echo "This will configure Nia to work with your coding agent."
    echo ""
    
    # Check prerequisites
    check_macos
    
    # Ensure curl is available (install Xcode tools if needed)
    if ! check_curl; then
        if ! install_xcode_tools; then
            print_error "Cannot proceed without curl."
            exit 1
        fi
    fi
    
    # Step 1: Select IDE
    select_ide_interactive
    local ide="$SELECTED_IDE"
    
    # Step 2: Select mode
    select_mode_interactive "$ide"
    local mode="$SELECTED_MODE"
    
    # Step 3: Start device authorization
    echo ""
    print_header "Browser Authorization"
    
    if ! start_device_session; then
        print_error "Failed to start authorization. Please try again."
        exit 1
    fi
    
    # Display the code prominently
    echo ""
    echo -e "${BOLD}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo ""
    echo -e "  Your authorization code is:"
    echo ""
    echo -e "  ${BOLD}${GREEN}    $DEVICE_USER_CODE${NC}"
    echo ""
    echo -e "${BOLD}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo ""
    
    # Try to open browser
    print_info "Opening browser for sign-in..."
    open_browser "$DEVICE_VERIFICATION_URL"
    
    echo ""
    echo "If the browser didn't open, go to:"
    echo -e "  ${CYAN}$DEVICE_VERIFICATION_URL${NC}"
    echo ""
    echo -e "${YELLOW}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo -e "${YELLOW}  Complete the setup in your browser${NC}"
    echo -e "${YELLOW}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo ""
    echo "  1. Sign in or create an account"
    echo "  2. Create your organization"
    echo "  3. Connect GitHub"
    echo "  4. Wait until you see 'Waiting for Terminal'"
    echo "  5. Come back here and press Enter"
    echo ""
    
    # Wait for user to complete browser onboarding
    echo -e "${CYAN}Complete the browser setup, then press Enter here${NC}"
    echo ""
    read -p "Press Enter to continue..." </dev/tty
    
    # Step 4: Exchange for API key
    echo ""
    print_info "Checking authorization status..."
    
    # Try exchange - keep retrying until user completes browser setup or cancels
    while ! exchange_for_api_key "$DEVICE_SESSION_ID" "$DEVICE_USER_CODE"; do
        echo ""
        print_warning "Browser setup not complete yet."
        echo ""
        echo "Make sure you've completed these steps in your browser:"
        echo "  1. Signed in to Nia"
        echo "  2. Created your organization"
        echo "  3. You should see 'Waiting for Terminal' screen"
        echo ""
        read -p "Press Enter to try again (or Ctrl+C to cancel)..." </dev/tty
        echo ""
    done
    
    print_success "API key obtained successfully!"
    
    # Step 5: Continue with regular setup using the obtained API key
    local api_key="$DEVICE_API_KEY"
    
    # Run the appropriate setup based on mode
    if [ "$mode" = "remote" ]; then
        print_info "Setting up Remote MCP..."
        
        if ! run_remote_setup "$api_key" "$ide"; then
            print_error "Remote setup failed."
            exit 1
        fi
        
        print_next_steps "$ide" "remote"
    else
        # Local mode: Full installation flow
        
        # Ensure Homebrew is installed
        if ! check_homebrew; then
            if ! install_homebrew; then
                print_error "Cannot proceed without Homebrew."
                exit 1
            fi
        fi
        
        # Ensure pipx is installed
        if ! check_pipx; then
            if ! install_pipx; then
                print_error "Cannot proceed without pipx."
                exit 1
            fi
            export PATH="$HOME/.local/bin:$PATH"
        fi
        
        # Install nia-mcp-server
        if ! install_nia_mcp_server; then
            exit 1
        fi
        
        # Run the setup
        if ! run_setup "$api_key" "$ide"; then
            print_error "Setup failed."
            exit 1
        fi
        
        print_next_steps "$ide" "local"
    fi
    
    echo ""
    print_success "Setup complete! You can close this terminal."
}

# Check if running on macOS
check_macos() {
    if [[ "$OSTYPE" != "darwin"* ]]; then
        print_error "This installer is designed for macOS only."
        print_info "For other platforms, please visit: https://docs.trynia.ai"
        exit 1
    fi
}

# Check if curl is available
check_curl() {
    if command -v curl &> /dev/null; then
        return 0
    fi
    
    print_warning "curl is not installed"
    return 1
}

# Install Xcode Command Line Tools (provides curl, git, etc.)
install_xcode_tools() {
    print_header "Installing Xcode Command Line Tools"
    print_info "This provides curl, git, and other essential tools..."
    
    # Check if already installed
    if xcode-select -p &> /dev/null; then
        print_success "Xcode Command Line Tools already installed"
        return 0
    fi
    
    print_info "A popup may appear asking to install. Please click 'Install'."
    xcode-select --install 2>/dev/null || true
    
    # Wait for installation
    print_info "Waiting for installation to complete..."
    until xcode-select -p &> /dev/null; do
        sleep 5
    done
    
    print_success "Xcode Command Line Tools installed successfully"
    return 0
}

# Check if Python3 is available
check_python3() {
    if command -v python3 &> /dev/null; then
        return 0
    else
        return 1
    fi
}

# Install Python3 via Homebrew
install_python3() {
    print_header "Installing Python3"
    
    if ! command -v brew &> /dev/null; then
        print_error "Homebrew is required to install Python3"
        return 1
    fi
    
    if brew install python3; then
        print_success "Python3 installed successfully"
        return 0
    else
        print_error "Failed to install Python3"
        return 1
    fi
}

# Install jq for better JSON merging (optional)
install_jq() {
    if command -v jq &> /dev/null; then
        return 0
    fi
    
    if command -v brew &> /dev/null; then
        print_info "Installing jq for better config merging..."
        if brew install jq &> /dev/null; then
            print_success "jq installed"
            return 0
        fi
    fi
    return 1
}

# Ensure pip is available
ensure_pip() {
    if python3 -m pip --version &> /dev/null; then
        return 0
    fi
    
    print_info "Bootstrapping pip..."
    if python3 -m ensurepip --upgrade &> /dev/null; then
        print_success "pip bootstrapped successfully"
        return 0
    else
        print_warning "Could not bootstrap pip"
        return 1
    fi
}

# Check if Homebrew is installed
check_homebrew() {
    # First check if brew is in PATH
    if command -v brew &> /dev/null; then
        print_success "Homebrew is already installed"
        return 0
    fi
    
    # On Apple Silicon, brew might be installed but not in PATH
    if [[ -f "/opt/homebrew/bin/brew" ]]; then
        print_info "Homebrew found at /opt/homebrew, adding to PATH..."
        eval "$(/opt/homebrew/bin/brew shellenv)"
        print_success "Homebrew is already installed (Apple Silicon)"
        return 0
    fi
    
    # On Intel Macs, check /usr/local
    if [[ -f "/usr/local/bin/brew" ]]; then
        print_info "Homebrew found at /usr/local, adding to PATH..."
        eval "$(/usr/local/bin/brew shellenv)"
        print_success "Homebrew is already installed (Intel)"
        return 0
    fi
    
    print_warning "Homebrew is not installed"
    return 1
}

# Install Homebrew
install_homebrew() {
    print_header "Installing Homebrew"
    print_info "Homebrew is required to install pipx. This may take a few minutes..."

    if /bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"; then
        # Add Homebrew to PATH for Apple Silicon Macs
        if [[ -f "/opt/homebrew/bin/brew" ]]; then
            eval "$(/opt/homebrew/bin/brew shellenv)"
        fi
        print_success "Homebrew installed successfully"
        return 0
    else
        print_error "Failed to install Homebrew"
        return 1
    fi
}

# Check if pipx is installed
check_pipx() {
    if command -v pipx &> /dev/null; then
        print_success "pipx is already installed"
        return 0
    else
        print_warning "pipx is not installed"
        return 1
    fi
}

# Install pipx
install_pipx() {
    print_header "Installing pipx"

    # Try installing with brew first (preferred)
    if command -v brew &> /dev/null; then
        if brew install pipx; then
            pipx ensurepath
            print_success "pipx installed successfully via Homebrew"
            return 0
        fi
        print_warning "Homebrew install failed, trying pip fallback..."
    fi

    # Fallback to pip - ensure Python3 is available
    if ! check_python3; then
        print_warning "Python3 not found, attempting to install..."
        if command -v brew &> /dev/null; then
            if ! install_python3; then
                print_error "Cannot proceed without Python3."
                return 1
            fi
        else
            print_error "Python3 is required but not found and Homebrew is not available to install it."
            print_info "Please install Python3 from https://python.org"
            return 1
        fi
    fi
    
    # Ensure pip is available (bootstrap if needed)
    if ! ensure_pip; then
        print_error "pip is not available and could not be bootstrapped."
        return 1
    fi
    
    print_info "Attempting to install pipx via pip..."
    if python3 -m pip install --user pipx; then
        python3 -m pipx ensurepath
        print_success "pipx installed successfully via pip"
        return 0
    else
        print_error "Failed to install pipx"
        return 1
    fi
}

# Install nia-mcp-server
install_nia_mcp_server() {
    print_header "Installing Nia MCP Server"

    # Check if already installed
    if pipx list | grep -q "nia-mcp-server"; then
        print_info "Nia MCP Server is already installed. Upgrading to latest version..."
        if pipx upgrade nia-mcp-server; then
            print_success "Nia MCP Server upgraded successfully"
            return 0
        else
            print_warning "Upgrade failed, but existing installation should still work"
            return 0
        fi
    else
        print_info "Installing Nia MCP Server package..."
        if pipx install nia-mcp-server; then
            print_success "Nia MCP Server installed successfully"
            return 0
        else
            print_error "Failed to install Nia MCP Server"
            return 1
        fi
    fi
}

# Validate inputs
validate_inputs() {
    if [ -z "$1" ]; then
        print_error "API key is required"
        echo ""
        echo "Usage options:"
        echo ""
        echo "  Interactive (recommended):"
        echo "    curl -fsSL https://app.trynia.ai/cli | sh"
        echo ""
        echo "  With API key:"
        echo "    curl -fsSL https://app.trynia.ai/api/setup-script | bash -s -- API_KEY IDE_NAME [--remote|--local]"
        echo ""
        print_supported_ides
        exit 1
    fi

    if [ -z "$2" ]; then
        print_error "IDE name is required"
        echo ""
        echo "Usage options:"
        echo ""
        echo "  Interactive (recommended):"
        echo "    curl -fsSL https://app.trynia.ai/cli | sh"
        echo ""
        echo "  With API key:"
        echo "    curl -fsSL https://app.trynia.ai/api/setup-script | bash -s -- API_KEY IDE_NAME [--remote|--local]"
        echo ""
        print_supported_ides
        exit 1
    fi

    # Validate API key format
    if [[ ! "$1" =~ ^nk_ ]]; then
        print_error "Invalid API key format. API key should start with 'nk_'"
        echo ""
        echo "For interactive setup without an API key, run:"
        echo "  curl -fsSL https://app.trynia.ai/cli | sh"
        exit 1
    fi

    # Validate IDE name
    local supported_ides=(
        "cursor" "claude-code" "claude-desktop" "vscode" "windsurf" "continue" "cline" 
        "codex" "antigravity" "trae" "amp" "zed" "augment" "roo-code" "kilo-code"
        "gemini-cli" "opencode" "jetbrains" "kiro" "lm-studio" "visual-studio"
        "crush" "bolt-ai" "rovo-dev" "zencoder" "qodo-gen" "qwen-coder"
        "perplexity" "warp" "copilot-agent" "copilot-cli" "amazon-q" "factory" "vibe"
    )
    local ide_valid=false
    for supported_ide in "${supported_ides[@]}"; do
        if [ "$2" = "$supported_ide" ]; then
            ide_valid=true
            break
        fi
    done

    if [ "$ide_valid" = false ]; then
        print_error "Unsupported IDE: $2"
        echo ""
        print_supported_ides
        exit 1
    fi
}

print_supported_ides() {
    echo -e "${CYAN}Supported IDEs:${NC}"
    echo ""
    echo -e "  ${GREEN}Remote + Local:${NC}"
    echo "    cursor, vscode, windsurf, cline, antigravity, trae, continue"
    echo "    roo-code, kilo-code, gemini-cli, opencode, qodo-gen, qwen-coder"
    echo "    visual-studio, crush, copilot-agent, copilot-cli, factory, rovo-dev"
    echo ""
    echo -e "  ${GREEN}Remote only:${NC}"
    echo "    claude-code (via CLI), amp (via CLI), vibe"
    echo ""
    echo -e "  ${GREEN}Local only:${NC}"
    echo "    codex, zed, augment, jetbrains, kiro, lm-studio, bolt-ai"
    echo "    zencoder, perplexity, warp, amazon-q, claude-desktop"
    echo ""
    echo -e "${CYAN}Options:${NC}"
    echo "  --remote    Configure remote MCP (no local installation required)"
    echo "  --local     Configure local MCP (default, requires pipx)"
}

# Get the MCP config file path for each IDE
get_mcp_config_path() {
    local ide=$1
    case "$ide" in
        cursor)
            echo "$HOME/.cursor/mcp.json"
            ;;
        vscode)
            echo "$HOME/.vscode/mcp.json"
            ;;
        windsurf)
            echo "$HOME/.codeium/windsurf/mcp_config.json"
            ;;
        cline)
            echo "$HOME/.cline/mcp_settings.json"
            ;;
        continue)
            echo "$HOME/.continue/config.json"
            ;;
        antigravity)
            echo "$HOME/.gemini/antigravity/mcp_config.json"
            ;;
        trae)
            echo "$HOME/Library/Application Support/Trae/User/mcp.json"
            ;;
        gemini-cli)
            echo "$HOME/.gemini/settings.json"
            ;;
        claude-desktop)
            echo "$HOME/Library/Application Support/Claude/claude_desktop_config.json"
            ;;
        opencode)
            echo "$HOME/.opencode/config.json"
            ;;
        roo-code)
            echo "$HOME/.roo-code/mcp.json"
            ;;
        kilo-code)
            echo "$HOME/.kilocode/mcp.json"
            ;;
        jetbrains)
            echo "$HOME/.jetbrains/mcp.json"
            ;;
        kiro)
            echo "$HOME/.kiro/mcp.json"
            ;;
        lm-studio)
            echo "$HOME/.lmstudio/mcp.json"
            ;;
        visual-studio)
            echo "$HOME/.vs/mcp.json"
            ;;
        crush)
            echo "$HOME/.crush/config.json"
            ;;
        bolt-ai)
            echo "$HOME/Library/Application Support/BoltAI/mcp.json"
            ;;
        qodo-gen)
            echo "$HOME/.qodo/mcp.json"
            ;;
        qwen-coder)
            echo "$HOME/.qwen/settings.json"
            ;;
        perplexity)
            echo "$HOME/Library/Application Support/Perplexity/mcp.json"
            ;;
        warp)
            echo "$HOME/.warp/mcp.json"
            ;;
        copilot-agent)
            echo ".github/copilot-mcp.json"
            ;;
        copilot-cli)
            echo "$HOME/.copilot/mcp-config.json"
            ;;
        amazon-q)
            echo "$HOME/.aws/amazonq/mcp.json"
            ;;
        vibe)
            echo "$HOME/.vibe/config.toml"
            ;;
        *)
            echo ""
            ;;
    esac
}

# Check if IDE supports remote mode
supports_remote() {
    local ide=$1
    case "$ide" in
        cursor|vscode|windsurf|cline|antigravity|trae|continue|roo-code|kilo-code|\
        gemini-cli|opencode|qodo-gen|qwen-coder|visual-studio|crush|copilot-agent|\
        copilot-cli|factory|rovo-dev|claude-code|amp|vibe)
            return 0
            ;;
        *)
            return 1
            ;;
    esac
}

# Check if IDE supports local mode
supports_local() {
    local ide=$1
    case "$ide" in
        cursor|vscode|windsurf|cline|antigravity|trae|continue|roo-code|kilo-code|\
        gemini-cli|opencode|qodo-gen|qwen-coder|visual-studio|crush|copilot-agent|\
        copilot-cli|factory|rovo-dev|codex|zed|augment|jetbrains|kiro|lm-studio|\
        bolt-ai|zencoder|perplexity|warp|amazon-q|claude-desktop|claude-code)
            return 0
            ;;
        *)
            return 1
            ;;
    esac
}

# Run the setup for local mode (file-based IDEs)
run_local_file_setup() {
    local api_key=$1
    local ide=$2
    local config_path=$3

    # Create config directory if it doesn't exist
    local config_dir=$(dirname "$config_path")
    mkdir -p "$config_dir"

    # Generate local config based on IDE
    local local_config=""
    case "$ide" in
        cursor|antigravity|trae|roo-code|kilo-code|bolt-ai|kiro|lm-studio|perplexity|warp|amazon-q)
            local_config=$(cat <<EOF
{
  "mcpServers": {
    "nia": {
      "command": "pipx",
      "args": ["run", "--no-cache", "nia-mcp-server"],
      "env": {
        "NIA_API_KEY": "$api_key",
        "NIA_API_URL": "$NIA_API_URL"
      }
    }
  }
}
EOF
)
            ;;
        vscode|visual-studio)
            local_config=$(cat <<EOF
{
  "servers": {
    "nia": {
      "type": "stdio",
      "command": "pipx",
      "args": ["run", "--no-cache", "nia-mcp-server"],
      "env": {
        "NIA_API_KEY": "$api_key",
        "NIA_API_URL": "$NIA_API_URL"
      }
    }
  }
}
EOF
)
            ;;
        windsurf)
            local_config=$(cat <<EOF
{
  "mcpServers": {
    "nia": {
      "command": "pipx",
      "args": ["run", "--no-cache", "nia-mcp-server"],
      "env": {
        "NIA_API_KEY": "$api_key",
        "NIA_API_URL": "$NIA_API_URL"
      }
    }
  }
}
EOF
)
            ;;
        cline)
            local_config=$(cat <<EOF
{
  "mcpServers": {
    "nia": {
      "command": "pipx",
      "args": ["run", "--no-cache", "nia-mcp-server"],
      "env": {
        "NIA_API_KEY": "$api_key",
        "NIA_API_URL": "$NIA_API_URL"
      },
      "alwaysAllow": [
        "index", "search", "manage_resource", "regex_search",
        "get_github_file_tree", "nia_web_search", "nia_deep_research_agent",
        "read_source_content", "doc_tree", "doc_ls", "doc_read", "doc_grep", "context"
      ],
      "disabled": false
    }
  }
}
EOF
)
            ;;
        continue)
            local_config=$(cat <<EOF
{
  "experimental": {
    "modelContextProtocolServer": {
      "transport": {
        "type": "stdio",
        "command": "pipx",
        "args": ["run", "--no-cache", "nia-mcp-server"],
        "env": {
          "NIA_API_KEY": "$api_key",
          "NIA_API_URL": "$NIA_API_URL"
        }
      }
    }
  }
}
EOF
)
            ;;
        gemini-cli|qwen-coder)
            local_config=$(cat <<EOF
{
  "mcpServers": {
    "nia": {
      "command": "pipx",
      "args": ["run", "--no-cache", "nia-mcp-server"],
      "env": {
        "NIA_API_KEY": "$api_key",
        "NIA_API_URL": "$NIA_API_URL"
      }
    }
  }
}
EOF
)
            ;;
        claude-desktop)
            local_config=$(cat <<EOF
{
  "mcpServers": {
    "nia": {
      "command": "pipx",
      "args": ["run", "--no-cache", "nia-mcp-server"],
      "env": {
        "NIA_API_KEY": "$api_key",
        "NIA_API_URL": "$NIA_API_URL"
      }
    }
  }
}
EOF
)
            ;;
        opencode)
            local_config=$(cat <<EOF
{
  "mcp": {
    "nia": {
      "type": "local",
      "command": ["pipx", "run", "--no-cache", "nia-mcp-server"],
      "env": {
        "NIA_API_KEY": "$api_key",
        "NIA_API_URL": "$NIA_API_URL"
      },
      "enabled": true
    }
  }
}
EOF
)
            ;;
        jetbrains)
            local_config=$(cat <<EOF
{
  "mcpServers": {
    "nia": {
      "command": "pipx",
      "args": ["run", "--no-cache", "nia-mcp-server"],
      "env": {
        "NIA_API_KEY": "$api_key",
        "NIA_API_URL": "$NIA_API_URL"
      }
    }
  }
}
EOF
)
            ;;
        zed)
            local_config=$(cat <<EOF
{
  "context_servers": {
    "Nia": {
      "source": "custom",
      "command": "pipx",
      "args": ["run", "--no-cache", "nia-mcp-server"],
      "env": {
        "NIA_API_KEY": "$api_key",
        "NIA_API_URL": "$NIA_API_URL"
      }
    }
  }
}
EOF
)
            ;;
        augment)
            local_config=$(cat <<EOF
{
  "augment.advanced": {
    "mcpServers": [
      {
        "name": "nia",
        "command": "pipx",
        "args": ["run", "--no-cache", "nia-mcp-server"],
        "env": {
          "NIA_API_KEY": "$api_key",
          "NIA_API_URL": "$NIA_API_URL"
        }
      }
    ]
  }
}
EOF
)
            ;;
        crush)
            local_config=$(cat <<EOF
{
  "\$schema": "https://charm.land/crush.json",
  "mcp": {
    "nia": {
      "type": "stdio",
      "command": "pipx",
      "args": ["run", "--no-cache", "nia-mcp-server"],
      "env": {
        "NIA_API_KEY": "$api_key",
        "NIA_API_URL": "$NIA_API_URL"
      }
    }
  }
}
EOF
)
            ;;
        qodo-gen)
            local_config=$(cat <<EOF
{
  "mcpServers": {
    "nia": {
      "command": "pipx",
      "args": ["run", "--no-cache", "nia-mcp-server"],
      "env": {
        "NIA_API_KEY": "$api_key",
        "NIA_API_URL": "$NIA_API_URL"
      }
    }
  }
}
EOF
)
            ;;
        copilot-cli)
            local_config=$(cat <<EOF
{
  "mcpServers": {
    "nia": {
      "type": "local",
      "command": "pipx",
      "args": ["run", "--no-cache", "nia-mcp-server"],
      "env": {
        "NIA_API_KEY": "$api_key",
        "NIA_API_URL": "$NIA_API_URL"
      },
      "tools": ["index", "search", "manage_resource", "nia_web_search", "nia_deep_research_agent"]
    }
  }
}
EOF
)
            ;;
        copilot-agent)
            local_config=$(cat <<EOF
{
  "mcpServers": {
    "nia": {
      "type": "stdio",
      "command": "pipx",
      "args": ["run", "--no-cache", "nia-mcp-server"],
      "env": {
        "NIA_API_KEY": "$api_key",
        "NIA_API_URL": "$NIA_API_URL"
      },
      "tools": ["index", "search", "manage_resource", "nia_web_search", "nia_deep_research_agent"]
    }
  }
}
EOF
)
            ;;
        *)
            print_error "Local config not available for $ide"
            return 1
            ;;
    esac

    # Write or merge config
    write_or_merge_config "$config_path" "$local_config"
}

# Run remote setup - configure remote MCP without local installation
run_remote_setup() {
    local api_key=$1
    local ide=$2

    print_header "Configuring $ide (Remote Mode)"

    # Handle CLI-based IDEs
    case "$ide" in
        claude-code)
            print_info "Running Claude Code remote MCP setup..."
            if output=$(claude mcp add --transport http nia "$REMOTE_MCP_URL" --header "Authorization: Bearer $api_key" 2>&1); then
                print_success "Remote MCP configured successfully!"
                return 0
            else
                print_error "Setup failed. Make sure Claude Code CLI is installed."
                print_info "Install from: https://www.claude.ai/download"
                echo "$output"
                return 1
            fi
            ;;
        amp)
            print_info "Running Amp remote MCP setup..."
            if output=$(amp mcp add nia --header "Authorization=Bearer $api_key" "$REMOTE_MCP_URL" 2>&1); then
                print_success "Remote MCP configured successfully!"
                return 0
            else
                print_error "Setup failed. Make sure Amp CLI is installed."
                echo "$output"
                return 1
            fi
            ;;
        factory)
            print_info "Running Factory droid remote MCP setup..."
            if output=$(droid mcp add nia "$REMOTE_MCP_URL" --type http --header "Authorization: Bearer $api_key" 2>&1); then
                print_success "Remote MCP configured successfully!"
                return 0
            else
                print_error "Setup failed. Make sure Factory droid CLI is installed."
                echo "$output"
                return 1
            fi
            ;;
        rovo-dev)
            print_info "Opening Rovo Dev MCP config..."
            acli rovodev mcp 2>/dev/null || true
            print_info "Please add the following config manually:"
            echo ""
            print_remote_config_json "$api_key" "$ide"
            return 0
            ;;
        vibe)
            print_info "Configuring Mistral Vibe CLI..."
            local config_path="$HOME/.vibe/config.toml"
            
            if [ ! -f "$config_path" ]; then
                print_error "Vibe CLI config not found at $config_path"
                print_info "Please make sure Mistral Vibe CLI is installed."
                print_info "Visit: https://docs.mistral.ai/capabilities/vibe/"
                return 1
            fi
            
            # Check if nia MCP is already configured
            if grep -q 'name = "nia"' "$config_path" 2>/dev/null; then
                print_warning "Nia MCP server already configured in Vibe CLI"
                return 0
            fi
            
            # Create backup
            cp "$config_path" "${config_path}.backup"
            print_info "Backup created: ${config_path}.backup"
            
            # Remove the old inline array syntax if it exists
            if grep -q '^mcp_servers = \[\]' "$config_path"; then
                # Use sed to remove the line
                sed -i.tmp '/^mcp_servers = \[\]/d' "$config_path"
                rm -f "${config_path}.tmp"
            fi
            
            # Append Nia MCP configuration at the end
            cat >> "$config_path" <<EOF

[[mcp_servers]]
name = "nia"
transport = "streamable-http"
url = "$REMOTE_MCP_URL"

[mcp_servers.headers]
Authorization = "Bearer $api_key"
EOF
            
            print_success "Nia MCP configured in Vibe CLI!"
            print_info "Config file: $config_path"
            print_info "Restart Vibe CLI to apply changes"
            return 0
            ;;
    esac

    # Handle file-based IDEs
    local config_path=$(get_mcp_config_path "$ide")
    if [ -z "$config_path" ]; then
        print_error "Unknown IDE config path for: $ide"
        return 1
    fi

    # Create config directory if it doesn't exist
    local config_dir=$(dirname "$config_path")
    mkdir -p "$config_dir"

    # Generate remote config based on IDE
    local remote_config=""
    case "$ide" in
        cursor|antigravity|trae|roo-code|kilo-code|qodo-gen)
            remote_config=$(cat <<EOF
{
  "mcpServers": {
    "nia": {
      "url": "$REMOTE_MCP_URL",
      "headers": {
        "Authorization": "Bearer $api_key"
      }
    }
  }
}
EOF
)
            ;;
        vscode|visual-studio)
            remote_config=$(cat <<EOF
{
  "servers": {
    "nia": {
      "type": "http",
      "url": "$REMOTE_MCP_URL",
      "headers": {
        "Authorization": "Bearer $api_key"
      }
    }
  }
}
EOF
)
            ;;
        windsurf)
            remote_config=$(cat <<EOF
{
  "mcpServers": {
    "nia": {
      "serverUrl": "$REMOTE_MCP_URL",
      "headers": {
        "Authorization": "Bearer $api_key"
      }
    }
  }
}
EOF
)
            ;;
        cline)
            remote_config=$(cat <<EOF
{
  "mcpServers": {
    "nia": {
      "url": "$REMOTE_MCP_URL",
      "type": "streamableHttp",
      "headers": {
        "Authorization": "Bearer $api_key"
      },
      "alwaysAllow": [
        "index", "search", "manage_resource", "regex_search",
        "get_github_file_tree", "nia_web_search", "nia_deep_research_agent",
        "read_source_content", "doc_tree", "doc_ls", "doc_read", "doc_grep", "context"
      ],
      "disabled": false
    }
  }
}
EOF
)
            ;;
        continue)
            remote_config=$(cat <<EOF
{
  "experimental": {
    "modelContextProtocolServer": {
      "transport": {
        "type": "http",
        "url": "$REMOTE_MCP_URL",
        "headers": {
          "Authorization": "Bearer $api_key"
        }
      }
    }
  }
}
EOF
)
            ;;
        gemini-cli|qwen-coder)
            remote_config=$(cat <<EOF
{
  "mcpServers": {
    "nia": {
      "httpUrl": "$REMOTE_MCP_URL",
      "headers": {
        "Authorization": "Bearer $api_key",
        "Accept": "application/json, text/event-stream"
      }
    }
  }
}
EOF
)
            ;;
        opencode)
            remote_config=$(cat <<EOF
{
  "mcp": {
    "nia": {
      "type": "remote",
      "url": "$REMOTE_MCP_URL",
      "headers": {
        "Authorization": "Bearer $api_key"
      },
      "enabled": true
    }
  }
}
EOF
)
            ;;
        crush)
            remote_config=$(cat <<EOF
{
  "\$schema": "https://charm.land/crush.json",
  "mcp": {
    "nia": {
      "type": "http",
      "url": "$REMOTE_MCP_URL",
      "headers": {
        "Authorization": "Bearer $api_key"
      }
    }
  }
}
EOF
)
            ;;
        copilot-agent)
            remote_config=$(cat <<EOF
{
  "mcpServers": {
    "nia": {
      "type": "http",
      "url": "$REMOTE_MCP_URL",
      "headers": {
        "Authorization": "Bearer $api_key"
      },
      "tools": ["index", "search", "manage_resource", "nia_web_search", "nia_deep_research_agent"]
    }
  }
}
EOF
)
            ;;
        copilot-cli)
            remote_config=$(cat <<EOF
{
  "mcpServers": {
    "nia": {
      "type": "http",
      "url": "$REMOTE_MCP_URL",
      "headers": {
        "Authorization": "Bearer $api_key"
      },
      "tools": ["index", "search", "manage_resource", "nia_web_search", "nia_deep_research_agent"]
    }
  }
}
EOF
)
            ;;
        *)
            print_error "Remote config not available for $ide"
            return 1
            ;;
    esac

    # Write or merge config
    write_or_merge_config "$config_path" "$remote_config"
    
    print_success "Remote MCP configuration written to: $config_path"
    print_info "Connected to: $REMOTE_MCP_URL"
    return 0
}

# Helper to print remote config JSON for manual setup
print_remote_config_json() {
    local api_key=$1
    local ide=$2
    
    echo -e "${BLUE}{"
    echo '  "mcpServers": {'
    echo '    "nia": {'
    echo "      \"url\": \"$REMOTE_MCP_URL\","
    echo '      "headers": {'
    echo "        \"Authorization\": \"Bearer $api_key\""
    echo '      }'
    echo '    }'
    echo '  }'
    echo -e "}${NC}"
}

# Write or merge config file
write_or_merge_config() {
    local config_path=$1
    local new_config=$2

    # Check if config file exists and has content
    if [ -f "$config_path" ] && [ -s "$config_path" ]; then
        print_warning "Existing config found at: $config_path"
        print_info "Backing up to: ${config_path}.backup"
        cp "$config_path" "${config_path}.backup"
        
        # Try to merge with existing config (if it's valid JSON)
        print_info "Attempting to merge with existing config..."
        
        # Try to install jq if not available (for better merging)
        install_jq
        
        # Prefer jq for JSON merging if available
        if command -v jq &> /dev/null; then
            local tmp_new_config
            tmp_new_config=$(mktemp)
            echo "$new_config" > "$tmp_new_config"
            if jq -s '.[0] * .[1]' "$config_path" "$tmp_new_config" > "${config_path}.tmp" 2>/dev/null; then
                mv "${config_path}.tmp" "$config_path"
                rm -f "$tmp_new_config"
                print_success "Configuration merged successfully!"
                return 0
            fi
            rm -f "$tmp_new_config" "${config_path}.tmp"
            print_warning "jq merge failed, trying Python..."
        fi
        
        # Fall back to Python
        if command -v python3 &> /dev/null; then
            local tmp_new_config
            tmp_new_config=$(mktemp)
            echo "$new_config" > "$tmp_new_config"
            if python3 - "$config_path" "$tmp_new_config" <<'PYEOF' 2>/dev/null
import json, sys
try:
    with open(sys.argv[1]) as f: existing = json.load(f)
    with open(sys.argv[2]) as f: new = json.load(f)
    def merge(a, b):
        for k, v in b.items():
            a[k] = merge(a.get(k, {}), v) if isinstance(a.get(k), dict) and isinstance(v, dict) else v
        return a
    with open(sys.argv[1], 'w') as f: json.dump(merge(existing, new), f, indent=2)
except Exception as e: sys.exit(1)
PYEOF
            then
                rm -f "$tmp_new_config"
                print_success "Configuration merged successfully!"
                return 0
            fi
            rm -f "$tmp_new_config"
            print_warning "Merge failed, writing new config..."
        else
            print_warning "Neither jq nor Python3 available for JSON merge, overwriting config..."
        fi
    fi

    # Write new config
    echo "$new_config" > "$config_path"
    print_success "Configuration written to: $config_path"
    return 0
}

# Run the setup for local mode
run_setup() {
    local api_key=$1
    local ide=$2

    print_header "Configuring $ide (Local Mode)"

    # Ensure pipx is in PATH
    export PATH="$HOME/.local/bin:$PATH"

    # Handle CLI-based IDEs differently
    case "$ide" in
        claude-code)
        print_info "Running Claude Code MCP setup (global scope)..."
            if output=$(claude mcp add nia --scope user -e "NIA_API_KEY=$api_key" -e "NIA_API_URL=$NIA_API_URL" -- pipx run --no-cache nia-mcp-server 2>&1); then
            print_success "Setup completed successfully!"
            print_info "Nia MCP server is now available across all your projects!"
            return 0
        else
            print_error "Setup failed. Make sure Claude Code CLI is installed."
            print_info "Install from: https://www.claude.ai/download"
                echo "$output"
            return 1
        fi
            ;;
        codex)
        print_info "Running Codex MCP setup..."
            if output=$(codex mcp add nia --env "NIA_API_KEY=$api_key" --env "NIA_API_URL=$NIA_API_URL" -- pipx run --no-cache nia-mcp-server 2>&1); then
            print_success "Setup completed successfully!"
            return 0
        else
            print_error "Setup failed. Make sure Codex CLI is installed."
                echo "$output"
            return 1
        fi
            ;;
        factory)
            print_info "Running Factory droid MCP setup..."
            if output=$(droid mcp add nia "pipx run --no-cache nia-mcp-server" --env "NIA_API_KEY=$api_key" --env "NIA_API_URL=$NIA_API_URL" 2>&1); then
                print_success "Setup completed successfully!"
                return 0
            else
                print_error "Setup failed. Make sure Factory droid CLI is installed."
                echo "$output"
                return 1
            fi
            ;;
        zencoder)
            print_info "Zencoder requires manual setup via UI."
            print_info "Go to: Zencoder menu (…) → Agent tools → Add custom MCP"
            echo ""
            echo -e "${CYAN}Add this configuration:${NC}"
            echo '{'
            echo '  "command": "pipx",'
            echo '  "args": ["run", "--no-cache", "nia-mcp-server"],'
            echo '  "env": {'
            echo "    \"NIA_API_KEY\": \"$api_key\","
            echo "    \"NIA_API_URL\": \"$NIA_API_URL\""
            echo '  }'
            echo '}'
            return 0
            ;;
    esac

    # For file-based IDEs
    local config_path=$(get_mcp_config_path "$ide")
    if [ -z "$config_path" ]; then
        # Try using nia-mcp-server setup command
        print_info "Running nia-mcp-server setup..."
        if output=$(pipx run nia-mcp-server setup "$api_key" --ide "$ide" 2>&1); then
            print_success "Setup completed successfully!"
            return 0
        else
            print_error "Setup failed"
            echo "$output"
            return 1
        fi
    fi

    run_local_file_setup "$api_key" "$ide" "$config_path"
}

# Print next steps
print_next_steps() {
    local ide=$1
    local mode=${2:-"local"}

    print_header "Setup Complete!"

    # ASCII art
    echo -e "${BLUE}"
    cat << "EOF"
    ███╗   ██╗██╗ █████╗
    ████╗  ██║██║██╔══██╗
    ██╔██╗ ██║██║███████║
    ██║╚██╗██║██║██╔══██║
    ██║ ╚████║██║██║  ██║
    ╚═╝  ╚═══╝╚═╝╚═╝  ╚═╝
EOF
    echo -e "${NC}"

    if [ "$mode" = "remote" ]; then
        echo -e "${GREEN}✓ Nia Remote MCP is now configured!${NC}\n"
        echo -e "${BLUE}Mode: Remote (Cloud)${NC} - No local installation required"
    else
    echo -e "${GREEN}✓ Nia MCP Server is now configured!${NC}\n"
        echo -e "${BLUE}Mode: Local${NC} - Running on your machine"
    fi

    echo ""
    echo "Next steps:"
    echo "  1. Restart your coding agent to load Nia"
    echo "  2. Try these commands in your agent:"
    echo ""
    echo -e "     ${YELLOW}\"Index the Turborepo documentation\"${NC}"
    echo "     index turborepo.com/docs"
    echo ""
    echo -e "     ${YELLOW}\"What is the difference between LayoutNG and the legacy layout engine in Chromium?\"${NC}"
    echo "     (Nia will search through Chromium's source code)"
    echo ""
    echo -e "     ${YELLOW}\"Index https://www.arxiv.org/abs/2512.07829 and tell me why is the rFID so much worse than VA-VAE in that research paper?\"${NC}"
    echo "     index https://www.arxiv.org/abs/2512.07829"
    echo ""
    echo "Learn more:"
    echo "  📚 Documentation: https://docs.trynia.ai"
    echo "  💬 Discord: https://discord.gg/BBSwUMrrfn"
    echo ""
}

# Main installation flow
main() {
    local api_key=$1
    local ide=$2
    local mode="local"  # default

    # Check for --remote or --local flag
    local has_remote=false
    local has_local=false
    for arg in "$@"; do
        [ "$arg" = "--remote" ] && has_remote=true
        [ "$arg" = "--local" ] && has_local=true
    done

    if [ "$has_remote" = true ] && [ "$has_local" = true ]; then
        print_error "Conflicting flags: cannot specify both --remote and --local"
        exit 1
    fi
    [ "$has_remote" = true ] && mode="remote"

    # If no API key provided, run interactive setup with device flow
    if [ -z "$api_key" ] || [[ ! "$api_key" =~ ^nk_ ]]; then
        # Check if first arg looks like a flag (not an API key)
        if [ -z "$1" ] || [[ "$1" == --* ]]; then
            run_interactive_setup
            exit 0
        fi
    fi

    if [ "$mode" = "remote" ]; then
        print_header "Nia Remote MCP Installer"
    else
        print_header "Nia MCP Server Installer"
    fi

    # Validate inputs
    validate_inputs "$api_key" "$ide"

    # Check prerequisites
    check_macos
    
    # Ensure curl is available
    if ! check_curl; then
        if ! install_xcode_tools; then
            print_error "Cannot proceed without curl."
            exit 1
        fi
    fi

    # Check mode compatibility
    if [ "$mode" = "remote" ]; then
        if ! supports_remote "$ide"; then
            print_error "$ide does not support remote MCP mode."
            print_info "Please use --local instead."
            exit 1
        fi
    else
        if ! supports_local "$ide"; then
            print_error "$ide does not support local MCP mode."
            print_info "Please use --remote instead."
            exit 1
        fi
    fi

    # Remote mode: Skip local installation, just configure
    if [ "$mode" = "remote" ]; then
        print_info "Setting up Remote MCP (no local installation required)..."
        
        if ! run_remote_setup "$api_key" "$ide"; then
            print_error "Remote setup failed. Please check the error messages above."
            print_info "For manual setup instructions, visit: https://docs.trynia.ai"
            exit 1
        fi
        
        print_next_steps "$ide" "remote"
        exit 0
    fi

    # Local mode: Full installation flow

    # Step 1: Ensure Homebrew is installed
    if ! check_homebrew; then
        if ! install_homebrew; then
            print_error "Cannot proceed without Homebrew. Please install it manually from https://brew.sh"
            exit 1
        fi
    fi

    # Step 2: Ensure pipx is installed
    if ! check_pipx; then
        if ! install_pipx; then
            print_error "Cannot proceed without pipx. Please install it manually."
            exit 1
        fi

        # Refresh PATH to pick up newly installed pipx
        export PATH="$HOME/.local/bin:$PATH"

        # Verify pipx is now available
        if ! command -v pipx &> /dev/null; then
            print_warning "pipx was installed but not found in PATH. You may need to restart your terminal."
            print_info "Try running this in a new terminal:"
            echo ""
            echo "  pipx run nia-mcp-server setup $api_key --ide $ide"
            echo ""
            exit 1
        fi
    fi

    # Step 3: Install/upgrade nia-mcp-server
    if ! install_nia_mcp_server; then
        exit 1
    fi

    # Step 4: Run the setup
    if ! run_setup "$api_key" "$ide"; then
        print_error "Setup failed. Please check the error messages above."
        print_info "For manual setup instructions, visit: https://docs.trynia.ai"
        exit 1
    fi

    # Step 5: Print next steps
    print_next_steps "$ide" "local"
}

# Run main with all arguments
main "$@"
