# acto registry

Manage local proof registry.

## Commands

| Command | Description |
|---------|-------------|
| `acto registry list` | List proofs in local registry |
| `acto registry get` | Get a specific proof |
| `acto registry stats` | Show registry statistics |

## List Proofs

```bash
acto registry list [OPTIONS]
```

### Options

| Option | Description | Default |
|--------|-------------|---------|
| `--limit`, `-l` | Max results | 50 |
| `--robot-id`, `-r` | Filter by robot | - |
| `--task-id`, `-t` | Filter by task | - |

### Output

```
Local Registry Proofs:
┌────────────────────┬─────────────────────┬──────────────────┬─────────────────────┐
│ Proof ID           │ Task ID             │ Robot ID         │ Created             │
├────────────────────┼─────────────────────┼──────────────────┼─────────────────────┤
│ abc123...          │ pick-and-place      │ robot-001        │ 2025-01-15 10:30:00 │
│ def456...          │ inspection          │ robot-002        │ 2025-01-15 09:15:00 │
└────────────────────┴─────────────────────┴──────────────────┴─────────────────────┘
```

## Get Proof

```bash
acto registry get PROOF_ID
```

## Stats

```bash
acto registry stats
```

### Output

```
Registry Statistics:
  Total proofs: 150
  Unique robots: 5
  Unique tasks: 12
  First proof: 2025-01-01 00:00:00
  Last proof: 2025-01-15 10:30:00
```

