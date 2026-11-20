import pandas as pd
import pytest

import data_collector


def test_save_results_refuses_to_shrink_existing_history(monkeypatch):
    existing = pd.DataFrame(
        [
            {"unique_id": "FOX5-1", "title": "First copy"},
            {"unique_id": "FOX5-1", "title": "Duplicate copy"},
        ]
    )
    upload_called = False

    monkeypatch.setattr(data_collector, "read_file_s3", lambda _key: existing)

    def record_upload(*_args, **_kwargs):
        nonlocal upload_called
        upload_called = True

    monkeypatch.setattr(data_collector, "upload_file_s3", record_upload)

    with pytest.raises(RuntimeError, match="result has fewer rows"):
        data_collector.save_results([])

    assert upload_called is False
