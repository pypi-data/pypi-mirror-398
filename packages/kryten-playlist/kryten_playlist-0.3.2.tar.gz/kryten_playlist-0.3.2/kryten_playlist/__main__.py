"""Main entry point for kryten-playlist service."""

import argparse
import asyncio
import logging
import signal
import sys
from pathlib import Path

from kryten_playlist.service import PlaylistService


def setup_logging(level: str = "INFO") -> None:
    """Configure logging for the service."""
    logging.basicConfig(
        level=getattr(logging, level.upper()),
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        handlers=[logging.StreamHandler(sys.stdout)],
    )


def parse_args() -> argparse.Namespace:
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(description="Kryten Playlist Service")
    parser.add_argument(
        "--config",
        type=Path,
        default=Path("/etc/kryten/playlist/config.json"),
        help="Path to configuration file (default: /etc/kryten/playlist/config.json)",
    )
    parser.add_argument(
        "--log-level",
        choices=["DEBUG", "INFO", "WARNING", "ERROR"],
        default="INFO",
        help="Logging level (default: INFO)",
    )
    parser.add_argument(
        "--web",
        action="store_true",
        help="Run FastAPI web UI/API alongside the NATS service",
    )
    return parser.parse_args()


async def main_async() -> None:
    """Main async entry point."""
    args = parse_args()
    setup_logging(args.log_level)

    logger = logging.getLogger(__name__)
    logger.info("Starting Kryten Playlist Service")

    service = PlaylistService(config_path=args.config, enable_web=args.web)

    # Setup signal handlers (Unix only - Windows uses KeyboardInterrupt)
    loop = asyncio.get_event_loop()

    def signal_handler(sig: int) -> None:
        logger.info("Received signal %s, shutting down...", sig)
        asyncio.create_task(service.stop())

    if sys.platform != "win32":
        for sig in (signal.SIGTERM, signal.SIGINT):
            loop.add_signal_handler(sig, lambda s=sig: signal_handler(s))

    try:
        await service.start()
        await service.wait_for_shutdown()
    except KeyboardInterrupt:
        logger.info("Keyboard interrupt received")
    except Exception as e:
        logger.error("Service error: %s", e, exc_info=True)
        sys.exit(1)
    finally:
        await service.stop()


def main() -> None:
    """Main entry point."""
    try:
        asyncio.run(main_async())
    except KeyboardInterrupt:
        pass


if __name__ == "__main__":
    main()
