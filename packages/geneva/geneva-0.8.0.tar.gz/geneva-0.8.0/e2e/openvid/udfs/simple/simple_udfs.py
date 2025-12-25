# SPDX-License-Identifier: PROPRIETARY
# SPDX-FileCopyrightText: Copyright The Geneva Authors

"""
Simple CPU-only UDFs for OpenVid video dataset.

These UDFs check file existence and basic metadata validation.
"""

import os

import geneva


@geneva.udf(version="0.1", memory=256 * 1024**2, num_cpus=0.25)
class HasFile:
    """
    Check if a video file exists in GCS.

    Configures GCS bucket and path from environment variables:
    - VIDEO_BUCKET: GCS bucket name (e.g., 'jon-geneva-demo')
    - VIDEO_PATH: Path prefix within bucket (e.g., 'demo-data/openvid/videos')

    Alternatively, set VIDEO_BASE_PATH with full gs:// path (e.g., 'gs://bucket/path')
    which will be automatically parsed into bucket and path components.
    """

    def __init__(self):
        self._client = None
        self._bucket = None
        self._path_prefix = None

    def setup(self):
        """Initialize GCS client and bucket on first call."""
        from google.cloud import storage

        # Parse bucket and path from environment
        base_path = os.getenv("VIDEO_BASE_PATH", "gs://jon-geneva-demo/demo-data/openvid/videos/video")

        if base_path.startswith("gs://"):
            # Parse gs://bucket/path format
            parts = base_path[5:].split("/", 1)
            bucket_name = parts[0]
            self._path_prefix = parts[1] if len(parts) > 1 else ""
        else:
            # Use separate bucket and path
            bucket_name = os.getenv("VIDEO_BUCKET", "jon-geneva-demo")
            self._path_prefix = os.getenv("VIDEO_PATH", "demo-data/openvid/videos/video")

        self._client = storage.Client()
        self._bucket = self._client.bucket(bucket_name)

    def __call__(self, video: str) -> bool:
        """
        Check if video file exists in GCS.

        Args:
            video: Video filename (e.g., '0.mp4')

        Returns:
            True if file exists, False otherwise
        """
        if self._client is None:
            self.setup()

        try:
            blob_path = f"{self._path_prefix}/{video}" if self._path_prefix else video
            return self._bucket.blob(blob_path).exists()
        except Exception as e:
            # Log error and return False for any GCS errors
            print(f"Error checking {video}: {e}")
            return False
