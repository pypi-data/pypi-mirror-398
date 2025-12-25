# Shell Completion

Enable tab completion for faster CLI usage.

## Automatic Installation

```bash
acto completion install
```

This automatically detects your shell and installs completion.

## Manual Installation

### Bash

```bash
# Generate completion script
acto completion bash > ~/.acto-completion.bash

# Add to ~/.bashrc
echo 'source ~/.acto-completion.bash' >> ~/.bashrc

# Reload
source ~/.bashrc
```

### Zsh

```bash
# Generate completion script
acto completion zsh > ~/.acto-completion.zsh

# Add to ~/.zshrc
echo 'source ~/.acto-completion.zsh' >> ~/.zshrc

# Reload
source ~/.zshrc
```

### Fish

```fish
# Generate completion script
acto completion fish > ~/.config/fish/completions/acto.fish

# Reload
source ~/.config/fish/completions/acto.fish
```

### PowerShell

```powershell
# Generate completion script
acto completion powershell > $HOME\.acto-completion.ps1

# Add to profile
Add-Content $PROFILE '. $HOME\.acto-completion.ps1'

# Reload
. $PROFILE
```

## Usage

After installation, press `Tab` to complete:

```bash
acto pr<TAB>        # → acto proof
acto proof cr<TAB>  # → acto proof create
acto proof create --ta<TAB>  # → acto proof create --task-id
```

## Troubleshooting

### Completion Not Working

1. Ensure the completion script is sourced
2. Check your shell configuration file
3. Restart your terminal

### Wrong Shell Detected

Specify shell explicitly:

```bash
acto completion install --shell bash
acto completion install --shell zsh
acto completion install --shell fish
acto completion install --shell powershell
```

