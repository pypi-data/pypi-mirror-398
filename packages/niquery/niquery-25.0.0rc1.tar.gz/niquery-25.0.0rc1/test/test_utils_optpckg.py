# emacs: -*- mode: python; py-indent-offset: 4; indent-tabs-mode: nil -*-
# vi: set ft=python sts=4 ts=4 sw=4 et:
#
# Copyright The NiPreps Developers <nipreps@gmail.com>
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#
# We support and encourage derived works from this project, please read
# about our expectations at
#
#     https://www.nipreps.org/community/licensing/
#

import pytest

from niquery.utils.optpckg import have_datalad


def fake_which(executable):
    if executable in ("git", "git-annex"):
        return None
    return f"/usr/bin/{executable}"


def test_have_datalad_missing_cli_tools(monkeypatch):
    monkeypatch.setattr("shutil.which", fake_which)
    assert have_datalad() is False


@pytest.mark.skipif(not have_datalad(), reason="Missing DataLad or system dependencies")
def test_have_datalad(tmp_path):
    # If we reach here, all dependencies are present.
    from datalad.api import Dataset  # type: ignore[import-untyped]

    ds = Dataset(str(tmp_path / "datalad_test_dataset"))
    assert ds is not None
