import json
import logging
import platform
import re
import subprocess
from pathlib import Path
from typing import Optional, Union

import requests
from influxdb_client_3 import Point as _Point
from pydantic import BaseModel

from logis.data_type import DEFAULT_PYDANTIC_MODEL_CONFIG, ApiResponse


class Point(_Point):
    """
    继承自 influxdb_client_3.Point，避免用法上的错误
    """

    def tag(self, key: str, value: Optional[str] = None):
        """
        避免value为None，确保value一定是字符串类型
        """
        if value is not None:
            super().tag(key, str(value))
        return self


class InfluxQuery(BaseModel):
    model_config = DEFAULT_PYDANTIC_MODEL_CONFIG
    query: str
    language: str = "sql"
    mode: str = "all"
    database: Optional[str] = None


class InfluxCommand:

    def __init__(self, binary_dir: Path, version="v3", token: Optional[str] = None):
        self._binary_dir = binary_dir
        self.version = version
        self._token = token

    @property
    def token(self):
        return self._token

    @property
    def binary(self):
        p = self._binary_dir / "influxdb3.exe"
        assert p.exists(), f"InfluxDB 3 binary not found: {p}"
        return p

    def serve(
        self,
        data_dir: Union[Path, str],
        token_file: Optional[Path] = None,
        node_id: Optional[str] = platform.node(),
        object_store: str = "file",
        host: str = "127.0.0.1",
        port: int = 8181,
        start_new_session: bool = False,
        creationflags=subprocess.CREATE_NO_WINDOW,
        **kwargs,
    ):
        """
        启动 InfluxDB 服务。
        """
        p = subprocess.Popen(
            list(
                filter(
                    lambda x: x,
                    [
                        str(self.binary),
                        "serve",
                        f"--http-bind={host}:{port}",
                        f"--node-id={node_id}" if node_id else "",
                        f"--object-store={object_store}" if object_store else "",
                        f"--data-dir={data_dir}" if data_dir else "",
                        f"--admin-token-file={token_file}" if token_file else "",
                    ],
                )
            ),
            stdout=subprocess.PIPE,  # 捕获标准输出
            stderr=subprocess.PIPE,  # 捕获标准错误
            text=True,
            start_new_session=start_new_session,
            creationflags=creationflags,
            **kwargs,
        )
        return p

    def generate_admin_token(
        self,
        name: Optional[str] = None,
        offline: bool = True,
        path: Optional[Path] = None,
        expiry: Optional[str] = None,  # "100y",
        creationflags=subprocess.CREATE_NO_WINDOW,
    ):
        if offline:
            assert (
                path is not None
            ), "Path must be provided for offline token generation"

        with subprocess.Popen(
            list(
                filter(
                    lambda x: x,
                    [
                        str(self.binary),
                        "create",
                        "token",
                        "--admin",
                        f"--name={name}" if name else "",
                        "--offline" if offline else "",
                        f"--expiry={expiry}" if expiry else "",
                        f"--output-file={path}" if offline else "",
                    ],
                )
            ),
            stdout=subprocess.PIPE,  # 捕获标准输出
            stderr=subprocess.PIPE,  # 捕获标准错误
            text=True,
            creationflags=creationflags,
        ) as p:
            stdout, stderr = p.communicate()
        if p.returncode != 0:
            return None
        stdout = re.sub(r"\x1b\[\d+m", "", stdout)
        lines = stdout.split("\n")
        prefix = "Token: "
        for line in lines:
            if line.startswith(prefix):
                return line.split(prefix)[1].strip()
        return None

    def execute(self, cmd: str, token: Optional[str] = None, **kwargs):
        """
        执行 InfluxDB 命令。
        """
        with subprocess.Popen(
            list(
                filter(
                    lambda x: x,
                    [
                        str(self.binary),
                        *cmd.split(" "),
                        f"--token={token}" if token else "",
                    ],
                )
            ),
            stdout=subprocess.PIPE,  # 捕获标准输出
            stderr=subprocess.PIPE,  # 捕获标准错误
            text=True,
            creationflags=subprocess.CREATE_NO_WINDOW | subprocess.DETACHED_PROCESS,
        ) as p:
            stdout, stderr = p.communicate()
        p.wait()
        if p.returncode != 0:
            raise RuntimeError(f"Command failed: {cmd}\n{stderr}")
        return stdout

    def create_database(
        self, database: str, token: str, retention_period: Optional[str] = None
    ):
        """
        创建一个新的数据库。
        """
        rp = f"--retention-period {retention_period}" if retention_period else ""
        return self.execute(
            f"CREATE DATABASE {database} {rp}",
            token=token,
        )

    def list_database(self, token: str):
        """
        列出所有数据库。
        """
        items = json.loads(self.execute("show databases --format json", token=token))

        for item in items:
            item["name"] = item.pop("iox::database")

        return items

class InfluxRestClient:
    """
    官方SDK提供的接口太少了，这里暂且自己封装下
    """

    def __init__(self, base_url: str, token: str, version="v3", **kwargs):
        self._url = base_url.strip().rstrip("/") + "/api/" + version
        self._token = token

    def _get_default_headers(self):
        return dict(Authorization=f"Bearer {self._token}")

    def create_database(self, database: str, strict: bool = True):
        r = requests.post(
            f"{self._url}/configure/database",
            json=dict(db=database),
            headers=self._get_default_headers(),
        )
        r = ApiResponse.from_http_response(r)
        if not strict and r.error and r.error == 409:
            logging.warning(f"Database {database} already exists")
            r.success = True
        return r

    def delete_database(self, database: str, hard_delete_at: Optional[str] = None):
        r = requests.delete(
            f"{self._url}/configure/database",
            params=dict(db=database, hard_delete_at=hard_delete_at),
            headers=self._get_default_headers(),
        )
        return ApiResponse.from_http_response(r, content_type="json")

    def delete_table(
        self,
        database: str,
        table: str,
        hard_delete_at: Optional[str] = None,
        strict: bool = True,
    ):
        """
        Args:
            database: 数据库名称
            table: 表名称
            hard_delete_at: 强制删除时间，格式为RFC3339
            strict: 是否严格模式，默认True, 若设置为False, 则当表不存在时不会报错
        """
        tmp = requests.delete(
            f"{self._url}/configure/table",
            params=dict(db=database, table=table, hard_delete_at=hard_delete_at),
            headers=self._get_default_headers(),
        )
        r = ApiResponse.from_http_response(tmp, content_type="json")
        if not strict and r.error and r.error.code == 404:
            r.error = None
            r.success = True
        return r
