import os
from unittest.mock import MagicMock, patch

import pytest

from bilby.core.sampler import get_implemented_samplers
from bilby_pipe.job_creation.nodes.analysis_node import touch_checkpoint_files


@pytest.mark.parametrize(
    "sampler",
    get_implemented_samplers(),
)
def test_touch_checkpoint_files(tmp_path, sampler):
    directory = tmp_path / "test_dir"
    label = "test"
    filenames = touch_checkpoint_files(
        directory,
        label,
        sampler,
    )

    for filename in filenames:
        assert os.path.exists(filename)


def test_non_pickle_checkpoint_file(tmp_path):
    directory = tmp_path / "test_dir"
    label = "test"
    mock_sampler_class = MagicMock()
    filename = "chain.dat"
    mock_sampler_class.get_expected_outputs = MagicMock(
        return_value=([os.path.join(directory, filename)], []),
    )
    with patch(
        "bilby.core.sampler.get_sampler_class",
        return_value=mock_sampler_class,
    ):
        filenames = touch_checkpoint_files(
            directory,
            label,
            "no_a_sampler",
        )
    assert os.path.split(filenames[1])[1] == filename
    assert os.path.exists(os.path.join(directory, filename))

    # Make sure the file can be opened
    with open(os.path.join(directory, filename), "r") as f:
        f.readlines()
