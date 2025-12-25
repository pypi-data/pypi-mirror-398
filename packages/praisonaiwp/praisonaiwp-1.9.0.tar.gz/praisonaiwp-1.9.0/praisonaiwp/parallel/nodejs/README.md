# PraisonAIWP Parallel Executor (Node.js)

This module provides parallel execution capabilities for PraisonAIWP using Node.js's async/await and event loop.

## Installation

```bash
cd praisonaiwp/parallel/nodejs
npm install
```

## Dependencies

- `ssh2` - SSH client for Node.js
- `p-limit` - Concurrency limiter for parallel operations

## How It Works

1. Python passes operation data to Node.js via stdin (JSON)
2. Node.js spawns multiple SSH connections (up to `workers` limit)
3. Operations execute concurrently
4. Results are returned to Python via stdout (JSON)

## Performance

- **Sequential (Python)**: ~0.5s per post = 50s for 100 posts
- **Parallel (Node.js)**: ~5-8s for 100 posts (10 workers)
- **Speedup**: ~10x faster for bulk operations

## Usage

This module is called automatically by PraisonAIWP when:
- Creating 10+ posts from a file
- Bulk update operations
- Any operation where parallel execution is beneficial

## Manual Testing

```bash
# Test with sample data
echo '{"operation":"create","data":[{"post_title":"Test","post_content":"Content"}],"server":{"hostname":"example.com","username":"user","key_file":"~/.ssh/id_rsa","wp_path":"/var/www/html","php_bin":"php","wp_cli":"wp"},"workers":10}' | node index.js
```

## Architecture

```
Python (Main Process)
    ↓
ParallelExecutor.execute_parallel()
    ↓
subprocess.run(['node', 'index.js'])
    ↓
Node.js (Child Process)
    ↓
p-limit (Concurrency Control)
    ↓
Multiple SSH Connections (Parallel)
    ↓
WordPress Servers
```

## Error Handling

- Connection errors are caught per-operation
- Failed operations return `{success: false, error: "..."}`
- Successful operations return `{success: true, post_id: 123}`
- Overall process fails only if Node.js crashes

## Limitations

- Maximum 5 minute timeout per batch
- SSH key authentication only (no password support)
- Requires Node.js 14+ installed on system
