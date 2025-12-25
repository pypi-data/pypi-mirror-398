"""Unit tests for the Specklia Client."""

import json
import struct
from datetime import datetime
from typing import Dict, List
from unittest.mock import patch

import geopandas as gpd
import pandas as pd
import pytest
import responses
from shapely import Polygon, to_geojson
from shapely.geometry import mapping

from specklia import Specklia, chunked_transfer

_QUERY_DATASET_DICT = {
    "dataset_id": "sheffield",
    "epsg4326_polygon": Polygon(((0, 0), (0, 1), (1, 1), (0, 0))),
    "min_timestamp": datetime(2000, 1, 1),
    "max_timestamp": datetime(2000, 1, 2),
    "columns_to_return": ["croissant"],
    "additional_filters": [
        {"column": "cheese", "operator": "<", "threshold": 6.57},
        {"column": "wine", "operator": ">=", "threshold": -23},
    ],
}


@pytest.fixture
def example_geodataframe() -> gpd.GeoDataFrame:
    return gpd.GeoDataFrame(
        {"geometry": gpd.points_from_xy([1, 2, 3, 4, 5], [0, 1, 2, 3, 4]), "timestamp": [2, 3, 4, 5, 6]},
        crs="EPSG:4326",
    )


@pytest.fixture
def example_datasets_dataframe() -> pd.DataFrame:
    return pd.DataFrame(
        [
            {
                "columns": {
                    "description": "hobbit height in cm",
                    "max_value": "150",
                    "min_value": "0",
                    "name": "height",
                    "type": "int",
                    "unit": "centimetres",
                },
                "created_timestamp": "Sat, 1 Jan 2000 15:44:24",
                "dataset_id": "sauron",
                "dataset_name": "hobbit_height",
                "description": "The height of some hobbits",
                "epsg4326_coverage": mapping(Polygon(((0, 1), (1, 1), (1, 0)))),
                "last_modified_timestamp": "Sun, 2 Jan 2000 15:44:24",
                "last_queried_timestamp": "Sun, 2 Jan 2000 12:14:44",
                "max_timestamp": "Wed, 1 Dec 1999 12:10:54",
                "min_timestamp": "Mon, 1 Nov 1999 00:41:25",
                "owning_group_id": "pippin",
                "owning_group_name": "merry",
                "size_rows": 4,
                "size_uncompressed_bytes": 726,
            }
        ]
    )


@pytest.fixture
def example_usage_report() -> List[Dict]:
    return [
        {
            "total_billable_bytes_processed": 10,
            "total_increase_in_bytes_stored": 20,
            "user_id": "example_user",
            "year": 2023,
            "month": 11,
        }
    ]


@pytest.fixture
def test_client(token: str) -> Specklia:
    with patch.object(Specklia, "_fetch_user_id"):
        return Specklia(auth_token=token, url="https://localhost")


def test_create_client(test_client: Specklia) -> None:
    assert test_client is not None


@responses.activate(assert_all_requests_are_fired=True)
def test_user_id(test_client: Specklia, token_matcher: responses.matchers.header_matcher) -> None:
    responses.add(responses.POST, "https://localhost/users", json="fake_user_id", match=[token_matcher])
    test_client._fetch_user_id()
    assert test_client.user_id == "fake_user_id"


@responses.activate(assert_all_requests_are_fired=True)
def test_list_users(test_client: Specklia, token_matcher: responses.matchers.header_matcher) -> None:
    responses.add(
        responses.GET,
        "https://localhost/users",
        json=[{"name": "fred", "email": "fred@fred.fred"}],
        match=[token_matcher],
    )
    test_client.list_users(group_id="hazbin")


@responses.activate(assert_all_requests_are_fired=True)
def test_add_points_to_dataset(
    test_client: Specklia, example_geodataframe: gpd.GeoDataFrame, token_matcher: responses.matchers.header_matcher
) -> None:
    responses.add(
        responses.POST,
        "https://localhost/ingest",
        json={"chunk_set_uuid": "brian"},
        match=[
            token_matcher,
            responses.matchers.json_params_matcher(
                {
                    "dataset_id": "dummy_dataset",
                    "new_points": [{"source": {"reference": "cheese"}, "chunk_set_uuid": "brian", "num_chunks": 1}],
                    "duplicate_source_behaviour": "error",
                },
            ),
        ],
    )
    responses.add(
        responses.POST,
        "https://localhost/chunk/upload/1-of-1",
        json={"chunk_set_uuid": "brian"},
    )
    test_client.add_points_to_dataset(
        dataset_id="dummy_dataset", new_points=[{"source": {"reference": "cheese"}, "gdf": example_geodataframe}]
    )


@responses.activate(assert_all_requests_are_fired=True)
def test_query_dataset(
    test_client: Specklia, example_geodataframe: gpd.GeoDataFrame, token_matcher: responses.matchers.header_matcher
) -> None:
    responses.add(
        responses.POST,
        "https://localhost/query",
        json={
            "chunk_set_uuid": "brian",
            "num_chunks": 1,
            "sources": [
                {
                    "geospatial_coverage": mapping(Polygon()),
                    "min_time": datetime.now().isoformat(),
                    "max_time": datetime.now().isoformat(),
                }
            ],
        },
        match=[
            token_matcher,
            responses.matchers.json_params_matcher(
                {
                    "dataset_id": "dummy_dataset",
                    "epsg4326_search_area": json.loads(to_geojson(Polygon(((0, 0), (0, 1), (1, 1), (0, 0))))),
                    "min_timestamp": 1588719600,
                    "max_timestamp": 1589065200,
                    "columns_to_return": ["lat", "lon"],
                    "additional_filters": [
                        {"column": "cheese", "operator": "<", "threshold": 6.57},
                        {"column": "wine", "operator": ">=", "threshold": -23},
                    ],
                    "source_information_only": False,
                }
            ),
        ],
    )

    responses.add(
        responses.GET,
        "https://localhost/chunk/download/brian/1",
        body=struct.pack("i", 1) + chunked_transfer.serialise_dataframe(example_geodataframe),
    )
    responses.add(responses.DELETE, "https://localhost/chunk/delete/brian")

    response = test_client.query_dataset(
        dataset_id="dummy_dataset",
        epsg4326_polygon=Polygon(((0, 0), (0, 1), (1, 1), (0, 0))),
        min_datetime=datetime(2020, 5, 6),
        max_datetime=datetime(2020, 5, 10),
        columns_to_return=["lat", "lon"],
        additional_filters=[
            {"column": "cheese", "operator": "<", "threshold": 6.57},
            {"column": "wine", "operator": ">=", "threshold": -23},
        ],
    )

    pd.testing.assert_frame_equal(response[0], example_geodataframe)


@pytest.mark.parametrize(
    ("invalid_json", "expected_exception", "expected_match"),
    # invalid espg4326_search_area type
    [
        (dict(_QUERY_DATASET_DICT, epsg4326_polygon="my back garden"), TypeError, "provide only Geometry objects"),
        # invalid min_datetime type
        (
            dict(_QUERY_DATASET_DICT, min_timestamp="a long time ago"),
            AttributeError,
            "object has no attribute 'timestamp'",
        ),
        # invalid max_datetime type
        (
            dict(_QUERY_DATASET_DICT, max_timestamp="the year 3000"),
            AttributeError,
            "object has no attribute 'timestamp'",
        ),
    ],
)
def test_query_dataset_invalid_request(
    test_client: Specklia, invalid_json: dict, expected_exception: type[Exception], expected_match: str
) -> None:
    with pytest.raises(expected_exception, match=expected_match):
        test_client.query_dataset(
            dataset_id=invalid_json["dataset_id"],
            epsg4326_polygon=invalid_json["epsg4326_polygon"],
            min_datetime=invalid_json["min_timestamp"],
            max_datetime=invalid_json["max_timestamp"],
            columns_to_return=invalid_json["columns_to_return"],
            additional_filters=invalid_json["additional_filters"],
        )


@responses.activate(assert_all_requests_are_fired=True)
def test_list_all_groups(test_client: Specklia, token_matcher: responses.matchers.header_matcher) -> None:
    responses.add(responses.GET, "https://localhost/groups", json=["ducks"], match=[token_matcher])
    test_client.internal_admin.list_all_groups()


@responses.activate(assert_all_requests_are_fired=True)
def test_create_group(test_client: Specklia, token_matcher: responses.matchers.header_matcher) -> None:
    responses.add(
        responses.POST,
        "https://localhost/groups",
        json={},
        match=[
            token_matcher,
            responses.matchers.json_params_matcher({"group_name": "ducks"}),
        ],
    )
    test_client.create_group("ducks")


@responses.activate(assert_all_requests_are_fired=True)
def test_update_group_name(test_client: Specklia, token_matcher: responses.matchers.header_matcher) -> None:
    responses.add(
        responses.PUT,
        "https://localhost/groups",
        json={},
        match=[
            token_matcher,
            responses.matchers.json_params_matcher({"group_id": "ducks", "new_group_name": "pigeons"}),
        ],
    )
    test_client.update_group_name(group_id="ducks", new_group_name="pigeons")


@responses.activate(assert_all_requests_are_fired=True)
def test_delete_group(test_client: Specklia, token_matcher: responses.matchers.header_matcher) -> None:
    responses.add(
        responses.DELETE,
        "https://localhost/groups",
        json={},
        match=[
            token_matcher,
            responses.matchers.query_param_matcher({"group_id": "ducks"}),
        ],
    )
    test_client.delete_group(group_id="ducks")


@responses.activate(assert_all_requests_are_fired=True)
def test_list_groups(test_client: Specklia, token_matcher: responses.matchers.header_matcher) -> None:
    responses.add(responses.GET, "https://localhost/groupmembership", json=["ducks"], match=[token_matcher])
    test_client.list_groups()


@responses.activate(assert_all_requests_are_fired=True)
def test_add_user_to_group(test_client: Specklia, token_matcher: responses.matchers.header_matcher) -> None:
    responses.add(
        responses.POST,
        "https://localhost/groupmembership",
        json={},
        match=[
            token_matcher,
            responses.matchers.json_params_matcher({"group_id": "ducks", "user_to_add_id": "donald"}),
        ],
    )
    test_client.add_user_to_group(group_id="ducks", user_to_add_id="donald")


@responses.activate(assert_all_requests_are_fired=True)
def test_update_user_privileges(test_client: Specklia, token_matcher: responses.matchers.header_matcher) -> None:
    responses.add(
        responses.PUT,
        "https://localhost/groupmembership",
        json={},
        match=[
            token_matcher,
            responses.matchers.json_params_matcher(
                {"group_id": "ducks", "user_to_update_id": "donald", "new_privileges": "ADMIN"}
            ),
        ],
    )
    test_client.update_user_privileges(group_id="ducks", user_to_update_id="donald", new_privileges="ADMIN")


@responses.activate(assert_all_requests_are_fired=True)
def test_delete_user_from_group(test_client: Specklia, token_matcher: responses.matchers.header_matcher) -> None:
    responses.add(
        responses.DELETE,
        "https://localhost/groupmembership",
        json={},
        match=[
            token_matcher,
            responses.matchers.query_param_matcher({"group_id": "ducks", "user_to_delete_id": "donald"}),
        ],
    )
    test_client.delete_user_from_group(group_id="ducks", user_to_delete_id="donald")


@responses.activate(assert_all_requests_are_fired=True)
def test_generate_api_key(test_client: Specklia, token_matcher: responses.matchers.header_matcher) -> None:
    user_dict = {"user_id": "user_1233", "token": "specklia_token_123"}
    responses.add(
        responses.PUT,
        "https://localhost/generate_user_api_key/user_1233",
        json=user_dict,
        match=[token_matcher],
    )
    response = test_client.internal_admin.generate_user_api_key(user_id="user_1233")
    assert response == user_dict


@responses.activate(assert_all_requests_are_fired=True)
def test_list_datasets(
    test_client: Specklia, token_matcher: responses.matchers.header_matcher, example_datasets_dataframe: pd.DataFrame
) -> None:
    responses.add(
        responses.GET,
        "https://localhost/metadata",
        json=example_datasets_dataframe.to_dict(orient="records"),
        match=[token_matcher],
    )
    datasets = test_client.list_datasets()
    assert type(datasets["epsg4326_coverage"][0]) is Polygon
    for column in datasets.columns:
        if "timestamp" in column:
            assert type(datasets[column][0]) is pd.Timestamp


@responses.activate(assert_all_requests_are_fired=True)
def test_create_dataset(test_client: Specklia, token_matcher: responses.matchers.header_matcher) -> None:
    responses.add(
        responses.POST,
        "https://localhost/metadata",
        json={},
        match=[
            token_matcher,
            responses.matchers.json_params_matcher(
                {
                    "dataset_name": "am",
                    "description": "wibble",
                    "columns": [
                        {"name": "hobbits", "type": "halflings", "description": "concerning hobbits"},
                        {"name": "cats", "type": "pets", "description": "concerning cats"},
                    ],
                    "storage_technology": "OLAP",
                }
            ),
        ],
    )
    test_client.create_dataset(
        dataset_name="am",
        description="wibble",
        columns=[
            {"name": "hobbits", "type": "halflings", "description": "concerning hobbits"},
            {"name": "cats", "type": "pets", "description": "concerning cats"},
        ],
    )


@responses.activate(assert_all_requests_are_fired=True)
def test_update_dataset_ownership(test_client: Specklia, token_matcher: responses.matchers.header_matcher) -> None:
    responses.add(
        responses.PUT,
        "https://localhost/metadata",
        json={},
        match=[
            token_matcher,
            responses.matchers.json_params_matcher({"dataset_id": "bside", "new_owning_group_id": "arctic monkeys"}),
        ],
    )
    test_client.update_dataset_ownership(dataset_id="bside", new_owning_group_id="arctic monkeys")


@responses.activate(assert_all_requests_are_fired=True)
def test_delete_dataset(test_client: Specklia, token_matcher: responses.matchers.header_matcher) -> None:
    responses.add(
        responses.DELETE,
        "https://localhost/metadata",
        json={},
        match=[
            token_matcher,
            responses.matchers.query_param_matcher({"dataset_id": "bside"}),
        ],
    )
    test_client.delete_dataset(dataset_id="bside")


@responses.activate(assert_all_requests_are_fired=True)
def test_report_usage(
    test_client: Specklia, token_matcher: responses.matchers.header_matcher, example_usage_report: List[Dict]
) -> None:
    responses.add(
        responses.GET,
        "https://localhost/usage",
        json=example_usage_report,
        match=[
            token_matcher,
            responses.matchers.query_param_matcher({"group_id": "beatles"}),
        ],
    )
    group_id = "beatles"
    results = test_client.report_usage(group_id=group_id)
    assert len(results) == 1
    assert results[0]["user_id"] == "example_user"
