import os

# Disable browser-use telemetry by default to avoid SSL errors behind VPNs
# Users can override by setting ANONYMIZED_TELEMETRY=true
os.environ.setdefault('ANONYMIZED_TELEMETRY', 'false')

import click
import uvicorn


@click.command()
@click.option('--port', default=8080, help='Port to run server')
@click.option('--reload', is_flag=True, help='Enable auto-reload for development')
def main(port: int, reload: bool):
    """Start the Usefly server."""
    uvicorn.run(
        "src.server:app",
        host="0.0.0.0",
        port=port,
        reload=reload,
        reload_dirs=["src"] if reload else None
    )


if __name__ == "__main__":
    main()
