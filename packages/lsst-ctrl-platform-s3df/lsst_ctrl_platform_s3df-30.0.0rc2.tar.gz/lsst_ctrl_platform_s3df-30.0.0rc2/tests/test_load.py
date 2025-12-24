import sys

import pytest
from lsst.ctrl.execute.allocationConfig import AllocationConfig
from lsst.ctrl.execute.condorConfig import CondorConfig
from lsst.ctrl.execute.findPackageFile import find_package_file


def test_exec_config():
    exec_config_name = find_package_file("execConfig.py", platform="s3df")

    configuration = CondorConfig()
    configuration.loadFromStream(exec_config_name)
    assert configuration.platform.scheduler == "slurm"


def test_allocation_config():
    slurm_config_name = find_package_file("slurmConfig.py", platform="s3df")

    configuration = AllocationConfig()
    configuration.loadFromStream(slurm_config_name)
    assert configuration.platform.queue == "$QUEUE"


if __name__ == "__main__":
    sys.exit(pytest.main())
