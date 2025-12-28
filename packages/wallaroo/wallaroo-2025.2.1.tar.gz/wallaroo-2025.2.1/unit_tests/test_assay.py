import httpx
import pytest
import respx

import wallaroo
from wallaroo.assay import Assay, AssayAnalysis, AssayAnalysisList, edge_df, meta_df

from . import testutil

assay_result = {
    "assay_id": None,
    "name": "Test Assay",
    "created_at": 1643145081787,
    "elapsed_millis": 47,
    "pipeline_id": 1,
    "pipeline_name": "mypipeline",
    "iopath": "output 0 0",
    "baseline_summary": {
        "count": 19451,
        "min": 11.621197700500488,
        "max": 15.81431484222412,
        "mean": 12.94923653910751,
        "median": 12.91372299194336,
        "std": 0.444395950550726,
        "edges": [
            11.621197700500488,
            12.57109260559082,
            12.815332412719728,
            13.018439292907717,
            13.300100326538086,
            15.81431484222412,
            1.7976931348623157e308,
        ],
        "edge_names": [
            "left_outlier",
            "q_20",
            "q_40",
            "q_60",
            "q_80",
            "q_100",
            "right_outlier",
        ],
        "aggregated_values": [
            0.0,
            0.19998971775230065,
            0.19998971775230065,
            0.2000411289907974,
            0.19998971775230065,
            0.19998971775230065,
            0.0,
        ],
        "aggregation": "Density",
        "start": None,
        "end": None,
    },
    "window_summary": {
        "count": 2162,
        "min": 11.798182487487791,
        "max": 14.873453140258787,
        "mean": 12.950320512028782,
        "median": 12.913423538208008,
        "std": 0.4514067181228918,
        "edges": [
            11.621197700500488,
            12.57109260559082,
            12.815332412719728,
            13.018439292907717,
            13.300100326538086,
            15.81431484222412,
            1.7976931348623157e308,
        ],
        "edge_names": [
            "e_1.16e1",
            "e_1.26e1",
            "e_1.28e1",
            "e_1.30e1",
            "e_1.33e1",
            "e_1.58e1",
            "e_1.80e308",
        ],
        "aggregated_values": [
            0.0,
            0.20259019426456984,
            0.20444033302497688,
            0.19241443108233117,
            0.18732654949121183,
            0.21322849213691028,
            0.0,
        ],
        "aggregation": "Density",
        "start": "2021-01-02T00:00:00Z",
        "end": "2021-01-03T00:00:00Z",
    },
    "score": 0.04057973233911011,
    "scores": [
        0.0,
        0.0026004765122691897,
        0.004450615272676234,
        0.0076266979084662345,
        0.01266316826108882,
        0.01323877438460963,
        0.0,
    ],
    "index": None,
    "summarizer": {
        "type": "UnivariateContinuous",
        "bin_mode": "Quantile",
        "aggregation": "Density",
        "metric": "SumDiff",
        "num_bins": 5,
        "bin_weights": None,
        "provided_edges": None,
    },
    "alert_threshold": 0.5,
    "warning_threshold": None,
    "status": "Ok",
}


def test_assay(client):
    data = {"id": 0}
    assay = Assay(client, data)
    assert assay

    # _fetch_attributes should be an integration test


@pytest.mark.respx(assert_all_mocked=True)
def test_turn_on_off(respx_mock):
    gql_client = testutil.new_gql_client(endpoint="http://api-lb:8080/v1/graphql")
    client = wallaroo.Client(
        gql_client=gql_client,
        auth_type="test_auth",
        api_endpoint="http://api-lb:8080",
        config={"default_arch": "x86"},
    )

    turn_on_payload = {"id": 0, "active": True}
    turn_off_payload = {"id": 0, "active": False}

    respx_mock.post(
        f"{client.api_endpoint}/v1/api/assays/set_active", json=turn_on_payload
    ).mock(return_value=httpx.Response(200, json=turn_on_payload))

    respx_mock.post(f"{client.api_endpoint}/v1/api/assays/set_active").mock(
        return_value=httpx.Response(200, json=turn_off_payload)
    )

    data = {"id": 0, "active": True}
    assay = Assay(client, data)
    assert assay._active
    data = assay.turn_off()
    assert not assay._active
    data = assay.turn_on()
    assert assay._active


@respx.mock(assert_all_mocked=False)
def test_set_thresholds(respx_mock):
    respx_mock.post(
        "http://api-lb:8080/v1/graphql",
    ).mock(
        return_value=httpx.Response(
            200,
            json={"data": {"update_assay_by_pk": [{"id": 0, "active": "false"}]}},
        )
    )

    gql_client = testutil.new_gql_client(endpoint="http://api-lb:8080/v1/graphql")
    client = wallaroo.Client(
        gql_client=gql_client,
        auth_type="test_auth",
        api_endpoint="http://api-lb:8080",
        config={"default_arch": "x86"},
    )
    data = {"id": 0, "alert_threshold": 0.5, "warning_threshold": None}
    assay = Assay(client, data)
    assert assay._alert_threshold == 0.5
    assert assay._warning_threshold is None
    assay.set_alert_threshold(0.75)
    assay.set_warning_threshold(0.50)
    assert assay._alert_threshold == 0.75
    assert assay._warning_threshold == 0.50


def test_meta_df():
    df = meta_df(assay_result, "Baseline")
    assert df.shape == (1, 16)


def test_edge_df():
    df = edge_df(assay_result["baseline_summary"])
    assert df.shape == (7, 4)


def test_assay_analysis(client):
    aa = AssayAnalysis(raw=assay_result, client=client)
    assert aa

    df = aa.compare_basic_stats()
    assert df.shape == (8, 4)

    df = aa.compare_bins()
    assert df.shape == (7, 9)

    # TODO: chart has side effects we don't want in a unit test
    # And was only meant to be called in a notebook.
    # Whats the best way to address this?
    # aa.chart()


def test_assay_analysis_list(client):
    aal = AssayAnalysisList([AssayAnalysis(raw=assay_result, client=client)])
    assert aal[0], "Could not get first item"
    df = aal.to_dataframe()
    assert df.shape == (1, 18)

    print(df.iloc[0]["warning_threshold"])
    print(df.iloc[0]["alert_threshold"])
    assert df.iloc[0]["warning_threshold"] is None
    assert df.iloc[0]["alert_threshold"] == 0.5

    # TODO: These all have unwanted side effects.
    # And were only meant to be called in a notebook.
    # chart_df

    assert aal._AssayAnalysisList__status_color("Ok") == "green"  # type: ignore
    assert aal._AssayAnalysisList__status_color("Warning") == "orange"  # type: ignore
    assert aal._AssayAnalysisList__status_color("foobar") == "red"  # type: ignore


def test_chart_scores_throws():
    aal = AssayAnalysisList([])
    with pytest.raises(ValueError):
        aal.chart_scores()


def test_chart_iopaths_throws():
    aal = AssayAnalysisList([])
    with pytest.raises(ValueError):
        aal.chart_iopaths()
