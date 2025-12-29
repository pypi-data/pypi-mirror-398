import asyncio
from .agent import agent

async def main():
    try:
        await agent.to_cli(prog_name="Dockerfile-assistant")
    except KeyboardInterrupt:
        return
    except SystemExit:
        raise
    except Exception as exception:
        raise SystemExit(f"Fatal error running CLI: {exception}")
def cli():
    """Synchronous entry point for console script."""
    asyncio.run(main())


if __name__ == "__main__":
    cli()
