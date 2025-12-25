# CLI Installation

The ACTO CLI is included with the SDK.

## Installation

```bash
pip install actobotics
```

Verify installation:

```bash
acto --version
```

## Shell Completion

Enable tab completion for your shell.

### Bash

```bash
# Add to ~/.bashrc
eval "$(_ACTO_COMPLETE=bash_source acto)"

# Or generate completion script
_ACTO_COMPLETE=bash_source acto > ~/.acto-complete.bash
echo "source ~/.acto-complete.bash" >> ~/.bashrc
```

### Zsh

```bash
# Add to ~/.zshrc
eval "$(_ACTO_COMPLETE=zsh_source acto)"
```

### Fish

```fish
# Add to ~/.config/fish/completions/acto.fish
_ACTO_COMPLETE=fish_source acto > ~/.config/fish/completions/acto.fish
```

### PowerShell

```powershell
# Add to your PowerShell profile
$scriptblock = {
    param($wordToComplete, $commandAst, $cursorPosition)
    $env:_ACTO_COMPLETE = "powershell_source"
    acto | ForEach-Object { $_ }
}
Register-ArgumentCompleter -Native -CommandName acto -ScriptBlock $scriptblock
```

## Using the CLI

### Generate Help

```bash
acto --help
acto keys --help
acto proof create --help
```

### Common Commands

```bash
# Generate keypair
acto keys generate

# Create proof
acto proof create --task-id task-001 --source telemetry.jsonl

# Interactive mode
acto interactive

# Check access
acto access check --owner WALLET --mint MINT --minimum 50000
```

