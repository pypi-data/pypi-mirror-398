# SPDX-License-Identifier: PROPRIETARY
# SPDX-FileCopyrightText: Copyright The Geneva Authors

"""
Stress test-specific fixtures.

Common fixtures are inherited from src/conftest.py, including:
- beefy_cluster: Large cluster with 14 CPU / 56GB memory workers
- standard_cluster: Standard cluster configuration
- All other common fixtures

This file is intentionally minimal as stress tests use shared fixtures.
"""

import logging

_LOG = logging.getLogger(__name__)
