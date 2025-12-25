from __future__ import annotations

import logging
import shutil
from typing import Optional, TYPE_CHECKING

from unicrm.services.red_alerts import send_red_alert

if TYPE_CHECKING:  # pragma: no cover - for type hints only
    from django.contrib.auth.models import AbstractBaseUser

logger = logging.getLogger(__name__)


def check_disk_usage_and_alert(
    path: str = "/",
    threshold_percent: float = 70.0,
    initiated_by: Optional["AbstractBaseUser"] = None,
) -> bool:
    """
    Check disk usage for ``path`` and send a red alert if usage exceeds ``threshold_percent``.

    Args:
        path: Filesystem path whose device usage will be inspected.
        threshold_percent: Percentage used at which an alert is raised.
        initiated_by: Optional Django user recorded on outgoing messages.

    Returns:
        True if at least one alert delivery succeeded, False otherwise.
    """
    total, used, free = shutil.disk_usage(path)
    percent_used = (used / total * 100) if total else 0.0
    summary = (
        f"Disk usage for {path}: {percent_used:.2f}% used "
        f"({format_bytes(used)} of {format_bytes(total)})."
    )
    print(summary)
    logger.info(summary)

    if percent_used < threshold_percent:
        logger.debug(
            "Disk usage below threshold (%.2f%% < %.2f%%); no alert sent.",
            percent_used,
            threshold_percent,
        )
        return False

    subject = f"Disk usage alert: {percent_used:.1f}% used on {path}"
    body = (
        f"The filesystem mounted at {path} is {percent_used:.1f}% full "
        f"({format_bytes(used)} used of {format_bytes(total)} total, {format_bytes(free)} free), "
        f"which is above the configured threshold of {threshold_percent:.1f}%."
    )

    deliveries = send_red_alert(subject=subject, body=body, initiated_by=initiated_by)
    success = any(delivery.status == "sent" for delivery in deliveries)

    if success:
        logger.info(
            "Disk usage alert sent for %s (%.2f%%).",
            path,
            percent_used,
        )
    else:
        logger.warning(
            "Disk usage threshold exceeded for %s (%.2f%%) but no alert deliveries succeeded.",
            path,
            percent_used,
        )
    return success


def format_bytes(num_bytes: int) -> str:
    """Return a human-friendly string for ``num_bytes``."""
    if num_bytes is None:
        return "0 B"

    units = ["B", "KB", "MB", "GB", "TB", "PB"]
    value = float(num_bytes)
    for unit in units:
        if value < 1024 or unit == units[-1]:
            return f"{value:.2f} {unit}"
        value /= 1024
    return f"{value:.2f} PB"
