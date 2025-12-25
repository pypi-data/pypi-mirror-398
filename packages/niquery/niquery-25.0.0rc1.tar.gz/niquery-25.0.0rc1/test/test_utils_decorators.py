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

import click
import pytest
from click.testing import CliRunner

from niquery.utils.decorators import _datalad_req_msg, require_datalad, require_datalad_click


def test_require_datalad_runs_when_available(monkeypatch):
    # Patch have_datalad to return True
    monkeypatch.setattr("niquery.utils.decorators.have_datalad", lambda: True)

    @require_datalad
    def foo(x):
        return x + 1

    assert foo(1) == 2


def test_require_datalad_raises_when_missing(monkeypatch):
    # Patch have_datalad to return False
    monkeypatch.setattr("niquery.utils.decorators.have_datalad", lambda: False)

    @require_datalad
    def foo(x):
        return x + 1

    with pytest.raises(RuntimeError, match=_datalad_req_msg):
        foo(1)


def test_require_datalad_click_runs_when_available(monkeypatch):
    monkeypatch.setattr("niquery.utils.decorators.have_datalad", lambda: True)

    @click.command()
    @require_datalad_click
    def cli():
        click.echo("Success")

    runner = CliRunner()
    result = runner.invoke(cli)
    assert result.exit_code == 0
    assert "Success" in result.output


def test_require_datalad_click_raises_click_exception(monkeypatch):
    monkeypatch.setattr("niquery.utils.decorators.have_datalad", lambda: False)

    @click.command()
    @require_datalad_click
    def cli():
        click.echo("Should not get here")

    runner = CliRunner()
    result = runner.invoke(cli)
    assert result.exit_code != 0
    assert _datalad_req_msg in result.output
