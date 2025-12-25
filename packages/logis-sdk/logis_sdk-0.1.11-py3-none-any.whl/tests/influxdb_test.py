from datetime import datetime, timezone
from pathlib import Path
from random import randint
from typing import Literal

from influxdb_client.client.influxdb_client import InfluxDBClient
from influxdb_client.client.influxdb_client_async import InfluxDBClientAsync
from influxdb_client_3 import InfluxDBClient3, Point

from logis.metric.influxdb import InfluxCommand, InfluxRestClient

database = "test"
test_url = f"http://localhost:8181"
admin_token_file = Path(__file__)
token = "apiv3_9RtOrHrNRybmP8s-VnjxFU5nb89Ly_Xu5iWDN4vFUnPlK4-M0gbE0ODsLh4OGYvUyBGHsBwOm1RpDqQ-ZUqsyg"


def get_client(
    url=test_url,
    token=token,
    mode: Literal["sync", "async"] = "sync",
    database=database,
):
    return InfluxDBClient3(host=url, token=token, database=database)


def test_insert():
    client: InfluxDBClient3 = get_client(mode="sync")
    for i in range(10):
        client.write(
            record=Point("andy.temperature")
            .field("value", randint(36, 40) + 0.5)
            .tag("id", str(i))
            .tag("source", "体温计")
            .time(datetime.now()),
        )
    client.close()


def test_query():
    client: InfluxDBClient3 = get_client(mode="sync")
    result = client.query(
        'select * from "andy.temperature" where id>5 order by time desc'
    )
    print(result.to_pandas())
    client.close()


def test_command():
    bin_dir = Path("D:\\app\\influxdb3-core-3.5.0-windows_amd64")
    command = InfluxCommand(bin_dir)
    token = command.generate_admin_token(
        offline=False, path=bin_dir / "admin_token.json"
    )
    print("Process exited with code:", token)

    token = command.generate_admin_token(
        offline=True, path=bin_dir / "admin_token.json"
    )
    print("Process exited with code:", token)


def test_serve():
    bin_dir = Path("D:\\app\\influxdb3-core-3.5.0-windows_amd64")
    command = InfluxCommand(bin_dir)
    p = command.serve(
        data_dir=bin_dir / "data",
        object_store="file",
    )
    print(p)


def test_rest_client():
    tmp_db = "xxxxxx"
    client = InfluxRestClient("http://127.0.0.1:8181", token=token)
    x = client.create_database(tmp_db)
    assert x.success or x.error.code == 409, x
    x = client.delete_database(tmp_db)
    assert x.success, x
