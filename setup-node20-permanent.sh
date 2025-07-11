#!/bin/bash
# Add Node.js 20 to your shell profile for permanent use

NODE20_PATH="/usr/local/Cellar/node@20/20.19.3/bin"

# Function to add to profile
add_to_profile() {
    local profile_file="$1"
    local profile_name="$2"
    
    if [ -f "$profile_file" ]; then
        if ! grep -q "node@20" "$profile_file"; then
            echo "" >> "$profile_file"
            echo "# Add Node.js 20 for cline-for-writing development" >> "$profile_file"
            echo "export PATH=\"$NODE20_PATH:\$PATH\"" >> "$profile_file"
            echo "✅ Added Node.js 20 to $profile_name"
        else
            echo "ℹ️  Node.js 20 already configured in $profile_name"
        fi
    fi
}

echo "🔧 Setting up Node.js 20 for permanent use..."
echo "Current Node.js version: $(node --version)"
echo "Target Node.js 20 path: $NODE20_PATH"

# Check common shell profiles
add_to_profile "$HOME/.bash_profile" ".bash_profile"
add_to_profile "$HOME/.bashrc" ".bashrc"
add_to_profile "$HOME/.zshrc" ".zshrc"

echo ""
echo "🎉 Setup complete!"
echo "💡 To use Node.js 20 immediately, run:"
echo "   source ~/.zshrc    # if using zsh"
echo "   source ~/.bash_profile    # if using bash"
echo ""
echo "🔄 Or restart your terminal"
