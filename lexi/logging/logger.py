import logging
import os
import platform
import subprocess
import sys

from lexi import enums, shared

log_dir = os.path.join(shared.cache_dir, "lexi", "logs")
log_filename = os.path.join(log_dir, "lexi.log")
prev_log_filename = os.path.join(log_dir, "lexi_prev.log")

os.makedirs(log_dir, exist_ok=True)

if os.path.exists(log_filename):
    os.rename(log_filename, prev_log_filename)

logging.basicConfig(
    level=(
        logging.DEBUG
        if shared.APP_ID.endswith(".Devel") or enums.Schema.USE_DEBUG_LOG()
        else logging.INFO
    ),
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler(log_filename, mode="a", encoding="utf-8"),
        logging.StreamHandler(),
    ],
)

logger = logging.getLogger("lexi")


def log_system_info() -> None:
    """Log system information."""
    open(log_filename, "a", encoding="utf-8").truncate(0)
    logger.info("Logging started")
    logger.info("Starting Lexi %s v%s", shared.PREFIX, shared.VERSION)
    logger.debug("Python version: %s", sys.version)
    if os.getenv("FLATPAK_ID") == shared.PREFIX:
        process = subprocess.run(
            ("flatpak-spawn", "--host", "flatpak", "--version"),
            capture_output=True,
            encoding="utf-8",
            check=False,
        )
        logger.debug("Flatpak version: %s", process.stdout.rstrip())
    logger.info("Platform: %s", platform.platform())
    logger.info("-" * 37)
