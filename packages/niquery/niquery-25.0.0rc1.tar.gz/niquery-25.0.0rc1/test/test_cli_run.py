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

from pathlib import Path
from click.testing import CliRunner
import pandas as pd
import json

import niquery.cli.run as runmod


def test_index_command_writes_csv(tmp_path, monkeypatch):
    runner = CliRunner()
    out_file = tmp_path / "edges.tsv"

    # Prevent filesystem / logging side-effects
    monkeypatch.setattr(runmod, "verify_output_path", lambda *args, **kwargs: None)
    monkeypatch.setattr(runmod, "configure_logging", lambda *args, **kwargs: None)

    # Provide deterministic fake API calls
    monkeypatch.setattr(runmod, "get_cursors", lambda remote: ["c1", "c2"])
    monkeypatch.setattr(
        runmod,
        "fetch_pages",
        lambda cursors, max_workers=None: [{"id": "ds1", "remote": "r"}, {"id": "ds2", "remote": "r"}],
    )
    monkeypatch.setattr(
        runmod,
        "edges_to_dataframe",
        lambda edges: pd.DataFrame({"id": [e["id"] for e in edges], "remote": [e["remote"] for e in edges]}),
    )

    result = runner.invoke(runmod.cli, ["index", "dummy_remote", str(out_file)])
    assert result.exit_code == 0, result.output

    # Check file was created and contains expected columns/rows
    assert out_file.exists()
    df = pd.read_csv(out_file, sep=runmod.DSV_SEPARATOR)
    assert "id" in df.columns
    assert set(df["id"].tolist()) == {"ds1", "ds2"}


def test_collect_command_calls_writers(tmp_path, monkeypatch):
    runner = CliRunner()
    # Build a simple input CSV with dataset entries
    in_file = tmp_path / "datasets.tsv"
    df_in = pd.DataFrame(
        {
            "remote": ["r1", "r2"],
            "id": ["ds000001", "ds000002"],
            "tag": ["", ""],
            "modalities": ["bold", "bold"],
        }
    )
    df_in.to_csv(in_file, sep=runmod.DSV_SEPARATOR, index=False)

    out_dir = tmp_path / "out"
    out_dir.mkdir()

    # Avoid logging / filesystem checks
    monkeypatch.setattr(runmod, "verify_output_path", lambda *args, **kwargs: None)
    monkeypatch.setattr(runmod, "configure_logging", lambda *args, **kwargs: None)

    # Filter should be called and return a filtered dataframe (we mimic no filtering)
    monkeypatch.setattr(runmod, "filter_nonrelevant_datasets", lambda df, species, modality: df)

    # Make query_datasets return predictable success/failure lists
    fake_success = [{"remote": "r1", "id": "ds000001", "files": []}]
    fake_failure = [{"remote": "r2", "id": "ds000002", "error": "not found"}]
    monkeypatch.setattr(runmod, "query_datasets", lambda df, max_workers=None: (fake_success, fake_failure))

    called = {"write_lists": False, "write_tags": False}

    def fake_write_dataset_file_lists(success_results, out_dirname, sep):
        called["write_lists"] = True
        # write a sentinel file so we can assert the CLI attempted to write output
        Path(out_dirname).joinpath("written_file_lists.txt").write_text(json.dumps(success_results))

    def fake_write_dataset_tags(failure_results, fname, sep):
        called["write_tags"] = True
        Path(fname).write_text(json.dumps(failure_results))

    monkeypatch.setattr(runmod, "write_dataset_file_lists", fake_write_dataset_file_lists)
    monkeypatch.setattr(runmod, "write_dataset_tags", fake_write_dataset_tags)

    # Run the CLI. Species and modality are required and accept multiple values.
    result = runner.invoke(
        runmod.cli,
        [
            "collect",
            str(in_file),
            str(out_dir),
            "--species",
            "human",
            "--modality",
            "bold",
        ],
    )
    assert result.exit_code == 0, result.output

    # Ensure our writer mocks were invoked
    assert called["write_lists"] is True
    assert called["write_tags"] is True

    # And the sentinel files exist
    assert (out_dir / "written_file_lists.txt").exists()


def test_analyze_command_calls_feature_extraction(tmp_path, monkeypatch):
    runner = CliRunner()

    # Create a fake input directory (content not used because we will mock
    # filter_non_conforming_ds)
    in_dir = tmp_path / "indir"
    in_dir.mkdir()
    out_dir = tmp_path / "outdir"
    out_dir.mkdir()

    # Avoid logging / FS checks
    monkeypatch.setattr(runmod, "verify_output_path", lambda *args, **kwargs: None)
    monkeypatch.setattr(runmod, "configure_logging", lambda *args, **kwargs: None)

    # Mock filter_non_conforming_ds to return a list of dataset "files"
    fake_datasets = {"ds000001": "ds000001.tsv", "ds000002": "ds000002.tsv"}
    monkeypatch.setattr(runmod, "filter_non_conforming_ds", lambda path: fake_datasets)

    # Mock identify_modality_files to return a mapping of dataset->list-of-files
    fake_files = {"ds000001": [{"path": "f1.nii.gz"}], "ds000002": [{"path": "f2.nii.gz"}]}
    monkeypatch.setattr(runmod, "identify_modality_files", lambda datasets, sep, suffix, max_workers=None: fake_files)

    # Mock extract_volume_features to return (success_results, failure_results)
    fake_success_results = {"ds000001": [{"path": "f1.nii.gz", "n_vols": 120}]}
    fake_failure_results = [{"dataset": "ds000002", "file": "f2.nii.gz", "error": "bad"}]
    monkeypatch.setattr(runmod, "extract_volume_features", lambda files: (fake_success_results, fake_failure_results))

    called = {"write_lists": False, "write_paths": False}

    def fake_write_dataset_file_lists(success_results, out_dirname, sep):
        called["write_lists"] = True
        Path(out_dirname).joinpath("file_lists_written.txt").write_text(json.dumps(success_results))

    def fake_write_dataset_paths(failure_results, fname, sep):
        called["write_paths"] = True
        Path(fname).write_text(json.dumps(failure_results))

    monkeypatch.setattr(runmod, "write_dataset_file_lists", fake_write_dataset_file_lists)
    monkeypatch.setattr(runmod, "write_dataset_paths", fake_write_dataset_paths)

    # Run the analyze command. `--suffix` is required (multiple allowed)
    result = runner.invoke(
        runmod.cli,
        ["analyze", str(in_dir), str(out_dir), "--suffix", ".nii.gz"],
    )
    assert result.exit_code == 0, result.output

    assert called["write_lists"] is True
    assert called["write_paths"] is True
    assert (out_dir / "file_lists_written.txt").exists()


def test_select_command_writes_selection(tmp_path, monkeypatch):
    runner = CliRunner()

    # Create a fake dataset TSV that would be returned by filter_non_conforming_ds
    ds_file = tmp_path / "ds000001.tsv"
    sample_df = pd.DataFrame(
        {
            runmod.DATASETID: ["ds000001", "ds000001"],
            runmod.FILENAME: ["f1.nii.gz", "f2.nii.gz"],
            "n_volumes": [200, 250],
        }
    )
    sample_df.to_csv(ds_file, sep=runmod.DSV_SEPARATOR, index=False)

    # We'll mock filter_non_conforming_ds to return our file path
    monkeypatch.setattr(runmod, "filter_non_conforming_ds", lambda path: {"ds000001": str(ds_file)})

    # Mock identify_relevant_runs to pick some rows from the concatenated dataframe
    # We simply return the dataframe read back with identical content for simplicity.
    def fake_identify_relevant_runs(df, contrib_thr, min_timepoints, max_timepoints, seed):
        # simulate filtering by timepoints by using the provided thresholds
        sel = df[(df["n_volumes"] >= min_timepoints) & (df["n_volumes"] <= max_timepoints)]
        return sel

    monkeypatch.setattr(runmod, "identify_relevant_runs", fake_identify_relevant_runs)

    out_file = tmp_path / "selected.tsv"

    # Avoid logging / FS checks
    monkeypatch.setattr(runmod, "verify_output_path", lambda *args, **kwargs: None)
    monkeypatch.setattr(runmod, "configure_logging", lambda *args, **kwargs: None)

    # Run the select command (seed is required positional arg)
    result = runner.invoke(
        runmod.cli,
        [
            "select",
            str(tmp_path),  # in_dirname (our monkeypatch ignores actual path)
            str(out_file),
            "20250101",  # seed
            "--total-runs",
            "10",
            "--contr-fraction",
            "0.05",
            "--min-timepoints",
            "100",
            "--max-timepoints",
            "300",
        ],
    )
    assert result.exit_code == 0, result.output

    # Check output written
    assert out_file.exists()
    df_out = pd.read_csv(out_file, sep=runmod.DSV_SEPARATOR)
    # The fake_identify_relevant_runs should have returned rows within the requested timepoint range
    assert df_out["n_volumes"].min() >= 100
    assert df_out["n_volumes"].max() <= 300
