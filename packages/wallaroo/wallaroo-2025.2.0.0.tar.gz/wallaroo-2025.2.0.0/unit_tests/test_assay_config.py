import json
import os
from datetime import datetime, timezone

import httpx
import pytest
import respx

import wallaroo
from wallaroo.assay_config import *
from wallaroo.pipeline import Pipeline

from . import testutil
from .reusable_responders import (
    add_default_workspace_responder,
)


class TestAssayConfig:
    def setup_method(self):
        self.gql_client = testutil.new_gql_client(
            endpoint="http://api-lb:8080/v1/graphql"
        )
        self.test_client = wallaroo.Client(
            gql_client=self.gql_client,
            auth_type="test_auth",
            api_endpoint="http://api-lb:8080",
            config={"default_arch": "x86"},
            request_timeout=2,  # this field used only by deployment.wait_for_running() tests
        )

        os.environ["ASSAYS_V2_ENABLED"] = "false"

    def test_calc_bins(self):
        assert calc_bins(100_000, "auto") == "auto"
        assert calc_bins(100_000, None) == 50
        assert calc_bins(650, None) == 25
        assert calc_bins(660, None) == 25

    def test_fixed_baseline(self):
        pipeline_name = "mypipeline"
        model_name = "mymodel"
        bl = FixedBaseline(
            pipeline_name,
            model_name,
            datetime.now(timezone.utc).replace(tzinfo=None),
            datetime.now(),
        )
        json_dict = json.loads(bl.to_json())
        fixed = json_dict["calculated"]["fixed_window"]
        assert fixed["pipeline"] == pipeline_name
        assert fixed["model"] == model_name

    @respx.mock(assert_all_mocked=False)
    def test_fixed_baseline_builder(self, respx_mock):
        pipeline_name = "mypipeline"
        model_name = "mymodel"

        # Mock the HTTP client response
        mock_response = httpx.Response(
            200,
            json={
                "count": 188,
                "min": 11.986584663391112,
                "max": 14.29722023010254,
                "mean": 13.031112508570894,
                "median": 12.956134796142578,
                "std": 0.4770556767131347,
                "edges": [
                    11.986584663391112,
                    12.622478485107422,
                    12.854415893554688,
                    13.064453125,
                    13.440485000610352,
                    14.29722023010254,
                    None,
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
                    0.20212765957446807,
                    0.19680851063829788,
                    0.20212765957446807,
                    0.19680851063829788,
                    0.20212765957446807,
                    0.0,
                ],
                "aggregation": "Density",
                "start": "2023-01-01T00:00:00+00:00",
                "end": "2023-01-02T00:00:00+00:00",
            },
        )

        respx_mock.post("http://api-lb:8080/v1/api/assays/summarize").mock(
            return_value=mock_response
        )

        fbb = FixedWindowBaselineBuilder(
            client=self.test_client,
            pipeline_name=pipeline_name,
            pipeline_id=1,
            workspace_name="test",
            alert_threshold=0.5,
            warning_threshold=0.5,
        ).add_workspace_id(1)
        fbb.add_window(
            WindowConfig(
                pipeline_name=pipeline_name,
                model_name=model_name,
                width="3 hour",
                path="out variable 0",
            )
        )
        sc = UnivariateContinousSummarizerConfig(
            BinMode.QUANTILE,
            Aggregation.DENSITY,
            Metric.SUMDIFF,
            10,
            None,
            None,
            None,
            True,
        )
        fbb = fbb.add_summarizer(sc)

        # Test the builder configuration
        assert fbb.pipeline_name == pipeline_name
        assert fbb.model_name is None
        assert fbb.start is None
        assert fbb.end is None

        # Add required fields
        fbb.add_model_name(model_name)
        fbb.add_start(datetime.now())
        fbb.add_end(datetime.now())

        # Build the baseline
        fb = fbb.build()
        assert fb is not None
        assert isinstance(fb, StaticBaseline)
        assert fb.static["count"] == 188

    def test_summarizer_config(self):
        ts = SummarizerConfig()
        assert ts is not None

    def test_uc_summarizer_config(self):
        num_bins = 10
        ucs = UnivariateContinousSummarizerConfig(
            BinMode.QUANTILE,
            Aggregation.DENSITY,
            Metric.SUMDIFF,
            num_bins,
            None,
            None,
            None,
            True,
        )
        assert ucs is not None
        ucs_dict = json.loads(ucs.to_json())
        assert ucs_dict["num_bins"] == num_bins

    def test_uc_sum_builder(self):
        ucsb = UnivariateContinousSummarizerBuilder()
        assert ucsb is not None

        ucsb.add_aggregation(Aggregation.EDGES)
        ucsb.add_metric(Metric.MAXDIFF)

        sum_config = ucsb.build()
        sum = json.loads(sum_config.to_json())
        assert sum["num_bins"] == 5
        assert sum["type"] == "UnivariateContinuous"
        assert sum["aggregation"] == "Edges"
        assert sum["metric"] == "MaxDiff"

    def test_window_config(self):
        wc = WindowConfig(
            pipeline_name="pipeline_name", model_name="model_name", width="3 hour"
        )
        wd = json.loads(wc.to_json())
        assert wd["model_name"] == "model_name"

    def test_window_builder(self):
        pipeline_name = "mypipeline"
        model_name = "mymodel"
        wb = WindowBuilder(pipeline_name)
        wb.add_model_name(model_name)
        wb.add_width(hours=3)
        assert wb is not None
        window_dict = json.loads(wb.build().to_json())
        assert window_dict["model_name"] == model_name
        assert window_dict["width"] == "3 hours"

    def test_config_encoder(self):
        d = datetime.now()
        o = {"date": d}
        with pytest.raises(Exception):
            s = json.dumps(o)

        s = json.dumps(o, default=ConfigEncoder)
        assert s is not None

    def test_assay_config(self):
        bl = FixedBaseline(
            "pipeline_name",
            "model_name",
            datetime.now(timezone.utc).replace(tzinfo=None),
            datetime.now(),
        )
        wc = WindowConfig("pipeline_name", "model_name", "3 hour")
        sc = UnivariateContinousSummarizerConfig(
            BinMode.QUANTILE,
            Aggregation.DENSITY,
            Metric.SUMDIFF,
            10,
            None,
            None,
            None,
            True,
        )

        ac = AssayConfig(
            None,
            "test",
            0,
            "test",
            True,
            "test",
            bl,
            wc,
            sc,
            None,
            0.5,
            datetime.now(),
            None,
            None,
        )
        ad = json.loads(ac.to_json())
        print(ac.to_json())
        assert ad["name"] == "test"

    @respx.mock(assert_all_mocked=True)
    def test_assay_builder(self, respx_mock):
        add_default_workspace_responder(respx_mock)
        resp = respx_mock.post(
            f"{self.test_client.api_endpoint}/v1/api/assays/summarize",
        ).mock(
            return_value=httpx.Response(
                200,
                json={
                    "count": 188,
                    "min": 11.986584663391112,
                    "max": 14.29722023010254,
                    "mean": 13.031112508570894,
                    "median": 12.956134796142578,
                    "std": 0.4770556767131347,
                    "edges": [
                        11.986584663391112,
                        12.622478485107422,
                        12.854415893554688,
                        13.064453125,
                        13.440485000610352,
                        14.29722023010254,
                        None,
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
                        0.20212765957446807,
                        0.19680851063829788,
                        0.20212765957446807,
                        0.19680851063829788,
                        0.20212765957446807,
                        0.0,
                    ],
                    "aggregation": "Density",
                    "start": "2023-01-01T00:00:00+00:00",
                    "end": "2023-01-02T00:00:00+00:00",
                },
            )
        )
        ab = AssayBuilder(
            client=self.test_client,
            name="n",
            pipeline_id=0,
            pipeline_name="test",
            model_name="test",
            baseline_start=datetime.now(),
            baseline_end=datetime.now(),
            iopath="inputs 0 0",
        )
        assert ab.name == "n"
        ab.add_name("ab")

        with pytest.raises(Exception):
            ab.add_iopath("foo")

        ab.add_iopath(" inputs 0 0 ")

        ad = ab.build()
        assert ad.name == "ab"
        assert isinstance(ad.baseline, StaticBaseline)
        assert ad.baseline.static["count"] == 188

    @respx.mock(assert_all_mocked=True)
    def test_assay_builder_window_width(self, respx_mock):
        add_default_workspace_responder(respx_mock)
        resp = respx_mock.post(
            f"{self.test_client.api_endpoint}/v1/api/assays/summarize",
        ).mock(
            return_value=httpx.Response(
                200,
                json={
                    "count": 188,
                    "min": 11.986584663391112,
                    "max": 14.29722023010254,
                    "mean": 13.031112508570894,
                    "median": 12.956134796142578,
                    "std": 0.4770556767131347,
                    "edges": [
                        11.986584663391112,
                        12.622478485107422,
                        12.854415893554688,
                        13.064453125,
                        13.440485000610352,
                        14.29722023010254,
                        None,
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
                        0.20212765957446807,
                        0.19680851063829788,
                        0.20212765957446807,
                        0.19680851063829788,
                        0.20212765957446807,
                        0.0,
                    ],
                    "aggregation": "Density",
                    "start": "2023-01-01T00:00:00+00:00",
                    "end": "2023-01-02T00:00:00+00:00",
                },
            )
        )
        assay_builder = AssayBuilder(
            client=self.test_client,
            name="n",
            pipeline_id=0,
            pipeline_name="test",
            model_name="test",
            baseline_start=datetime.now(),
            baseline_end=datetime.now(),
            iopath="inputs 0 0",
        )
        assay_builder.window_builder().add_width(hours=12)

        acd = assay_builder.build()
        assert acd.window.width == "12 hours"
        assert acd.window.start is None
        assert acd.window.interval is None

        assay_builder.window_builder().add_interval(hours=4)
        window_start_date = datetime.now()
        assay_builder.window_builder().add_start(window_start_date)
        acd = assay_builder.build()
        assert acd.window.width == "12 hours"
        assert acd.window.interval == "4 hours"
        assert acd.window.start == window_start_date.astimezone(tz=timezone.utc)

        # Invalid interval type
        with pytest.raises(Exception):
            assay_builder.window_builder().add_interval(fortnights=2)

        # Multiple intervals invalid
        with pytest.raises(Exception):
            assay_builder.window_builder().add_interval(weeks=1, hours=4)

    @respx.mock(assert_all_mocked=True)
    def test_assay_builder_bin_settings(self, respx_mock):
        add_default_workspace_responder(respx_mock)
        weights = [1.0] * 7
        resp = respx_mock.post(
            f"{self.test_client.api_endpoint}/v1/api/assays/summarize",
        ).mock(
            return_value=httpx.Response(
                200,
                json={
                    "count": 188,
                    "min": 11.986584663391112,
                    "max": 14.29722023010254,
                    "mean": 13.031112508570894,
                    "median": 12.956134796142578,
                    "std": 0.4770556767131347,
                    "edges": [
                        11.986584663391112,
                        12.622478485107422,
                        12.854415893554688,
                        13.064453125,
                        13.440485000610352,
                        14.29722023010254,
                        None,
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
                        0.20212765957446807,
                        0.19680851063829788,
                        0.20212765957446807,
                        0.19680851063829788,
                        0.20212765957446807,
                        0.0,
                    ],
                    "aggregation": "Density",
                    "start": "2023-01-01T00:00:00+00:00",
                    "end": "2023-01-02T00:00:00+00:00",
                },
            )
        )
        ab = AssayBuilder(
            client=self.test_client,
            name="n",
            pipeline_id=0,
            pipeline_name="test",
            model_name="test",
            baseline_start=datetime.now(),
            baseline_end=datetime.now(),
            iopath="inputs 0 0",
        )
        with pytest.raises(Exception):
            ab.summarizer_builder.add_bin_weights([1])

        ab.summarizer_builder.add_bin_weights(weights)

        ad = ab.build()
        assert ad.summarizer.bin_weights == weights

        with pytest.raises(Exception):
            ab.summarizer_builder.add_num_bins(7)

        ab.summarizer_builder.add_bin_weights(None)
        ab.summarizer_builder.add_num_bins(7)

        ad = ab.build()
        assert ad.summarizer.bin_weights is None
        assert ad.summarizer.num_bins == 7

    @respx.mock(assert_all_mocked=True)
    def test_assay_builder_add_edges(self, respx_mock):
        add_default_workspace_responder(respx_mock)
        edges = [1.0] * 6
        resp = respx_mock.post(
            f"{self.test_client.api_endpoint}/v1/api/assays/summarize",
        ).mock(
            return_value=httpx.Response(
                200,
                json={
                    "count": 188,
                    "min": 11.986584663391112,
                    "max": 14.29722023010254,
                    "mean": 13.031112508570894,
                    "median": 12.956134796142578,
                    "std": 0.4770556767131347,
                    "edges": [
                        11.986584663391112,
                        12.622478485107422,
                        12.854415893554688,
                        13.064453125,
                        13.440485000610352,
                        14.29722023010254,
                        None,
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
                        0.20212765957446807,
                        0.19680851063829788,
                        0.20212765957446807,
                        0.19680851063829788,
                        0.20212765957446807,
                        0.0,
                    ],
                    "aggregation": "Density",
                    "start": "2023-01-01T00:00:00+00:00",
                    "end": "2023-01-02T00:00:00+00:00",
                },
            )
        )
        ab = AssayBuilder(
            client=self.test_client,
            name="n",
            pipeline_id=0,
            pipeline_name="test",
            model_name="test",
            baseline_start=datetime.now(),
            baseline_end=datetime.now(),
            iopath="inputs 0 0",
        )
        # too few edges
        with pytest.raises(Exception):
            ab.summarizer_builder.add_bin_edges([1])

        # edges == to number of bins
        ab.summarizer_builder.add_bin_edges(edges[1:])
        # edges specifying left outlier
        ab.summarizer_builder.add_bin_edges(edges)

        # too many edges
        with pytest.raises(Exception):
            ab.summarizer_builder.add_bin_edges([1.0] * 8)

        # check that that we can't build with the wrong bin mode
        with pytest.raises(Exception):
            ad = json.loads(ab.build().to_json())

        # check that the edges get into the json and back
        ab.summarizer_builder.add_bin_mode(BinMode.PROVIDED, edges)
        ad = ab.build()
        assert ad.summarizer.provided_edges == edges

        # try to change num bins
        moar_bins = 10
        with pytest.raises(Exception):
            ab.summarizer_builder.add_num_bins(moar_bins)

        # clear out the edges and add more bins
        ab.summarizer_builder.add_bin_mode(BinMode.EQUAL)
        ab.summarizer_builder.add_num_bins(moar_bins)

        ad = ab.build()
        assert ad.summarizer.provided_edges is None
        assert ad.summarizer.num_bins == moar_bins

        ab.summarizer_builder.add_bin_mode(BinMode.PROVIDED, [1.0] * moar_bins)
        ad = ab.build()
        assert len(ad.summarizer.provided_edges) == moar_bins

    @respx.mock(assert_all_mocked=True)
    def test_assay_builder_with_baseline_data(self, respx_mock):
        add_default_workspace_responder(respx_mock)
        baseline_data = np.array([1, 2, 3, 4, 5, 6, 7, 8, 9])
        ab = AssayBuilder(
            client=self.test_client,
            name="n",
            pipeline_id=0,
            pipeline_name="test",
            model_name="test",
            iopath="output 2 0",
            baseline_data=baseline_data,
        )
        assert isinstance(ab.baseline_builder, VectorBaselineBuilder)
        df = ab.baseline_dataframe()
        assert isinstance(df, pd.DataFrame)
        assert df.columns == ["output_2_0"]

    @respx.mock(assert_all_mocked=True)
    def test_build_assay_with_static_baseline_data(self, respx_mock):
        add_default_workspace_responder(respx_mock)
        respx_mock.post(
            f"{self.test_client.api_endpoint}/v1/api/assays/summarize",
        ).mock(
            return_value=httpx.Response(
                200,
                json={
                    "count": 188,
                    "min": 11.986584663391112,
                    "max": 14.29722023010254,
                    "mean": 13.031112508570894,
                    "median": 12.956134796142578,
                    "std": 0.4770556767131347,
                    "edges": [
                        11.986584663391112,
                        12.622478485107422,
                        12.854415893554688,
                        13.064453125,
                        13.440485000610352,
                        14.29722023010254,
                        None,
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
                        0.20212765957446807,
                        0.19680851063829788,
                        0.20212765957446807,
                        0.19680851063829788,
                        0.20212765957446807,
                        0.0,
                    ],
                    "aggregation": "Density",
                    "start": "2023-01-01T00:00:00+00:00",
                    "end": "2023-01-02T00:00:00+00:00",
                },
            )
        )
        pipeline = Pipeline(
            client=self.test_client,
            data={
                "id": 1,
                "pipeline_id": "x",
                "created_at": datetime.now().isoformat(),
                "updated_at": datetime.now().isoformat(),
                "pipeline_versions": [{"id": 1}],
                "visibility": "pUbLIC",
            },
        )
        window_builder = (
            WindowBuilder("test").add_model_name("model_name").add_start(datetime.now())
        )

        baseline_data = np.array([1, 2, 3, 4, 5, 6, 7, 8, 9])
        a = self.test_client.build_assay(
            assay_name="test",
            pipeline=cast(Pipeline, pipeline),
            model_name="model_name",
            iopath="output 0 0",
            baseline_data=baseline_data,
        )
        a.window_builder_ = window_builder
        test_baseline_assay_config = a.build()
        assert isinstance(test_baseline_assay_config.baseline, StaticBaseline)
        assert test_baseline_assay_config.baseline.static is not None
        assert test_baseline_assay_config.baseline.static["count"] == 188
        assert test_baseline_assay_config.window.start is not None
