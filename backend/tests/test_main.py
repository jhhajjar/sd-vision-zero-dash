import pytest

import main


@pytest.fixture
def client():
    main.app.config.update(TESTING=True)
    return main.app.test_client()


@pytest.mark.parametrize(
    ("query", "message"),
    [
        ("page=0", "page must be at least 1"),
        ("page=-1", "page must be at least 1"),
        ("page=garbage", "page must be an integer"),
        ("pageSize=0", "pageSize must be at least 1"),
        ("pageSize=-1", "pageSize must be at least 1"),
        ("pageSize=garbage", "pageSize must be an integer"),
        ("pageSize=101", "pageSize must be at most 100"),
    ],
)
def test_incidents_rejects_invalid_pagination_before_loading_data(
    client, monkeypatch, query, message
):
    def fail_if_called(*_args, **_kwargs):
        raise AssertionError("incident data should not load for an invalid request")

    monkeypatch.setattr(main, "get_incidents_and_count", fail_if_called)

    response = client.get(f"/incidents?{query}")

    assert response.status_code == 400
    assert response.get_json() == {"error": message}


def test_pagination_defaults_and_limits():
    with main.app.test_request_context("/incidents"):
        assert main.parse_pagination_parameter("page", default=1) == 1
        assert (
            main.parse_pagination_parameter("pageSize", default=10, maximum=100) == 10
        )

    with main.app.test_request_context("/incidents?page=2&pageSize=100"):
        assert main.parse_pagination_parameter("page", default=1) == 2
        assert (
            main.parse_pagination_parameter("pageSize", default=10, maximum=100) == 100
        )


def test_incidents_returns_json_error_for_malformed_filter(client, monkeypatch):
    def fail_if_called(*_args, **_kwargs):
        raise AssertionError("incident data should not load for an invalid request")

    monkeypatch.setattr(main, "get_incidents_and_count", fail_if_called)

    response = client.get("/incidents", query_string={"filter": "not-json"})

    assert response.status_code == 400
    assert "error" in response.get_json()
