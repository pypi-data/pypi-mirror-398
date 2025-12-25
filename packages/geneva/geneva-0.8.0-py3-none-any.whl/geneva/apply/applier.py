# SPDX-License-Identifier: PROPRIETARY
# SPDX-FileCopyrightText: Copyright The Geneva Authors

import abc

import pyarrow as pa

from geneva.apply.task import MapTask, ReadTask
from geneva.debug.logger import ErrorLogger


class BatchApplier(abc.ABC):
    """Interface class for all appliers"""

    @abc.abstractmethod
    def run(
        self,
        read_task: ReadTask,
        map_task: MapTask,
        error_logger: ErrorLogger,
    ) -> pa.RecordBatch:
        """Run the map task on the data from the read task and return the result

        return a record batch, which contains the result of the map task"""
