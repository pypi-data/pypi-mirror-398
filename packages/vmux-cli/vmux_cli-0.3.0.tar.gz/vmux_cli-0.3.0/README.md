# vmux

Run any command in the cloud. Like tmux, but virtual.

## Install

```bash
uv tool install vmux
```

## Usage

```bash
# Login with GitHub
vmux login

# Run a command (streams output)
vmux run python train.py

# Run in background
vmux run --detach python long_job.py

# Attach to running job
vmux attach <job_id>

# View logs
vmux logs <job_id>
```

## Features

- **Cloud execution**: Run Python scripts on Cloudflare containers
- **Automatic dependencies**: Uses `uv` for instant package installs
- **Interactive terminal**: Attach to running jobs via tmux
- **Background jobs**: Detach and reattach anytime

## License

MIT
