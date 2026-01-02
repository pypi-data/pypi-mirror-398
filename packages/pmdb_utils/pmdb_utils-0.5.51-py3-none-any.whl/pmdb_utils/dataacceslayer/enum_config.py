from enum import Enum
from datetime import datetime, timezone


try:
    from enum import StrEnum as _StrEnum
except ImportError:  # Python < 3.11

    class _StrEnum(str, Enum):
        """Enum with string values for Python 3.9+."""

        def __str__(self) -> str:
            return self.value


class _DynamicDateTime:
    def __get__(self, instance, owner) -> datetime:
        return datetime.now(timezone.utc)


class TablePathBasic(_StrEnum):
    """Basic table paths used across the platform."""

    bucket_name = "lakehouse"
    base_path = f"s3://{bucket_name}"
    landing_path = f"{base_path}/landing"
    postlanding_path = f"{base_path}/postlanding"
    archive_path = f"{base_path}/archive"
    snapshot_path = f"{base_path}/snapshot"
    metadata_path = f"{base_path}/metadata"
    log_path = f"{base_path}/log"


class TablePathArchive(_StrEnum):
    """Archive table paths used across the platform."""

    boliga_houselistings = TablePathBasic.archive_path + "/boliga/houselistings"
    eloverblik_meterdata = TablePathBasic.archive_path + "/eloverblik/meterdata"
    garmin_daily_sleep = TablePathBasic.archive_path + "/garmin/daily_sleep"
    garmin_daily_stress = TablePathBasic.archive_path + "/garmin/daily_stress"
    jobindex_job_categories = TablePathBasic.archive_path + "/jobindex/job_categories"
    minio_objects = TablePathBasic.archive_path + "/minio/objects"
    pull_push_reddit_submissions = (
        TablePathBasic.archive_path + "/pull_push/reddit_submissions"
    )
    shelly_device_status = TablePathBasic.archive_path + "/shelly/device_status"
    strava_activities = TablePathBasic.archive_path + "/strava/activities"
    wiki_sp500 = TablePathBasic.archive_path + "/wiki/sp500"
