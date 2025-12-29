# mypy: disable-error-code="no-untyped-call"
import os
import re

import bugsnag
from bugsnag.error import (
    Error,
)
from bugsnag.event import (
    Event,
)
from bugsnag.notification import (
    Notification,
)

from blends.utils.env import (
    guess_environment,
)

META: dict[str, str] = {}


def _remove_nix_hash(path: str) -> str:
    pattern = r"(\/nix\/store\/[a-z0-9]{32}-)"
    result = re.search(pattern, path)
    if not result:
        return path
    return path[result.end(0) :]


def bugsnag_remove_nix_hash(
    notification: Notification,
) -> None:
    notification.stacktrace = [
        {**trace, "file": _remove_nix_hash(trace["file"])} for trace in notification.stacktrace
    ]


def bugsnag_add_batch_metadata(
    notification: Notification,
) -> None:
    batch_job_info = {}
    if batch_job_id := os.environ.get("AWS_BATCH_JOB_ID"):
        batch_job_info["batch_job_id"] = batch_job_id
    if batch_job_info:
        notification.add_tab("batch_job_info", batch_job_info)


def add_bugsnag_data(**data: str) -> None:
    META.update(data)


def filter_local_host_errors(event: Event) -> None:
    fa_standard_hostname_len = 12
    hostname = event.hostname

    hostname_format_1 = hostname.endswith("ec2.internal")
    hostname_format_2 = hostname.startswith("runner-")
    hostname_format_3 = len(hostname) == fa_standard_hostname_len and hostname.isalnum()
    hostname_format_4 = "-casa-vm" in hostname

    suspicious_hostname = not any(
        {
            hostname_format_1,
            hostname_format_2,
            hostname_format_3,
            hostname_format_4,
        },
    )

    if suspicious_hostname and event.release_stage == "production":
        event.errors.insert(
            0,
            Error(
                error_class="LocalError",
                error_message=hostname,
                stacktrace=event.errors[0].stacktrace,
            ),
        )


def initialize_bugsnag() -> None:
    bugsnag.before_notify(bugsnag_add_batch_metadata)
    bugsnag.before_notify(bugsnag_remove_nix_hash)
    bugsnag.before_notify(filter_local_host_errors)
    bugsnag.configure(
        ignore_classes=[
            "SystemExit",
        ],
        release_stage=guess_environment(),
        notify_release_stages=["production"],
    )
    bugsnag.start_session()
