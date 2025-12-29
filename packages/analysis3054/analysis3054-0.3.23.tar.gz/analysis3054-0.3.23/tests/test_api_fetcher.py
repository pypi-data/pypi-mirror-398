import asyncio
import json
import threading
import time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

import pandas as pd
import pytest

from analysis3054.api_fetcher import fetch_apis_to_dataframe


class _TestHandler(BaseHTTPRequestHandler):
    last_success_ts = 0.0

    def do_GET(self):
        if self.path.startswith("/json"):
            payload = [
                {"id": 1, "value": 10, "source": "json"},
                {"id": 2, "value": 20, "source": "json"},
            ]
            data = json.dumps(payload).encode("utf-8")
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(data)))
            self.end_headers()
            self.wfile.write(data)
            return

        if self.path.startswith("/csv"):
            csv_content = "id,value,source\n3,30,csv\n4,40,csv\n"
            data = csv_content.encode("utf-8")
            self.send_response(200)
            self.send_header("Content-Type", "text/csv")
            self.send_header("Content-Length", str(len(data)))
            self.end_headers()
            self.wfile.write(data)
            return

        if self.path.startswith("/ndjson"):
            ndjson_content = """
{"id": 6, "value": 60, "source": "ndjson"}
{"id": 7, "value": 70, "source": "ndjson"}
""".strip().encode("utf-8")
            self.send_response(200)
            self.send_header("Content-Type", "application/x-ndjson")
            self.send_header("Content-Length", str(len(ndjson_content)))
            self.end_headers()
            self.wfile.write(ndjson_content)
            return

        if self.path.startswith("/slow"):
            # First attempt should time out for small client deadlines; subsequent retries grow the timeout
            time.sleep(0.18)
            payload = {"id": 5, "value": 50, "source": "slow"}
            data = json.dumps(payload).encode("utf-8")
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(data)))
            self.end_headers()
            self.wfile.write(data)
            return

        if self.path.startswith("/throttle"):
            now = time.perf_counter()
            if now - self.__class__.last_success_ts < 0.12:
                payload = {"error": "too many requests"}
                data = json.dumps(payload).encode("utf-8")
                self.send_response(429)
                self.send_header("Content-Type", "application/json")
                self.send_header("Retry-After", "0.25")
                self.send_header("Content-Length", str(len(data)))
                self.end_headers()
                self.wfile.write(data)
                return

            self.__class__.last_success_ts = now
            payload = {"id": int(now * 1000) % 1000, "value": 99, "source": "throttled"}
            data = json.dumps(payload).encode("utf-8")
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(data)))
            self.end_headers()
            self.wfile.write(data)
            return

        self.send_response(404)
        self.end_headers()

    def log_message(self, format, *args):  # pragma: no cover - silence server logs
        return


def _start_server():
    server = ThreadingHTTPServer(("localhost", 0), _TestHandler)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    return server, thread


def test_fetch_apis_to_dataframe_concurrent(tmp_path):
    server, thread = _start_server()
    base_url = f"http://{server.server_address[0]}:{server.server_address[1]}"

    endpoints = [
        {"url": f"{base_url}/json", "params": {"page": 1}},
        f"{base_url}/csv",
    ]

    output_dir = tmp_path / "exports"
    try:
        df = fetch_apis_to_dataframe(
            endpoints,
            max_workers=4,
            output_dir=output_dir,
            file_name="fast_export",
            sort_by="id",
        )
    finally:
        server.shutdown()
        thread.join(timeout=2)

    assert isinstance(df, pd.DataFrame)
    assert len(df) == 4
    assert set(df["source"]) == {"json", "csv"}

    output_path = Path(output_dir) / "fast_export.csv"
    assert output_path.exists()
    written = pd.read_csv(output_path)
    assert len(written) == len(df)


def test_fetch_apis_to_dataframe_adapts_timeout():
    server, thread = _start_server()
    base_url = f"http://{server.server_address[0]}:{server.server_address[1]}"

    endpoints = [f"{base_url}/slow"]

    try:
        df = fetch_apis_to_dataframe(
            endpoints,
            timeout=0.05,  # intentionally small to trigger adaptive growth
            retries=3,
            max_workers=2,
        )
    finally:
        server.shutdown()
        thread.join(timeout=2)

    assert len(df) == 1
    assert df.loc[0, "source"] == "slow"


def test_fetch_apis_to_dataframe_applies_transform():
    server, thread = _start_server()
    base_url = f"http://{server.server_address[0]}:{server.server_address[1]}"

    endpoints = [
        f"{base_url}/json",
        f"{base_url}/csv",
    ]

    try:
        df = fetch_apis_to_dataframe(
            endpoints,
            sort_by="id",
            transform=lambda frame: frame.assign(value_scaled=frame["value"] * 2),
        )
    finally:
        server.shutdown()
        thread.join(timeout=2)

    assert "value_scaled" in df.columns
    assert df.loc[df["id"] == 1, "value_scaled"].item() == 20


def test_fetch_apis_to_dataframe_parses_ndjson():
    server, thread = _start_server()
    base_url = f"http://{server.server_address[0]}:{server.server_address[1]}"

    endpoints = [f"{base_url}/ndjson"]

    try:
        df = fetch_apis_to_dataframe(endpoints, sort_by="id")
    finally:
        server.shutdown()
        thread.join(timeout=2)

    assert len(df) == 2
    assert set(df["source"]) == {"ndjson"}
    assert df.iloc[0]["id"] == 6


def test_fetch_apis_to_dataframe_allows_async_transform():
    server, thread = _start_server()
    base_url = f"http://{server.server_address[0]}:{server.server_address[1]}"

    endpoints = [f"{base_url}/json"]

    async def _async_transform(frame: pd.DataFrame) -> pd.DataFrame:
        await asyncio.sleep(0)
        return frame.assign(source=frame["source"].str.upper())

    try:
        df = fetch_apis_to_dataframe(
            endpoints,
            transform=_async_transform,
        )
    finally:
        server.shutdown()
        thread.join(timeout=2)

    assert df.loc[0, "source"] == "JSON"


def test_fetch_apis_to_dataframe_rejects_non_dataframe_transform():
    server, thread = _start_server()
    base_url = f"http://{server.server_address[0]}:{server.server_address[1]}"

    endpoints = [f"{base_url}/json"]

    try:
        with pytest.raises(TypeError, match="must return a pandas DataFrame; got int"):
            fetch_apis_to_dataframe(
                endpoints,
                transform=lambda frame: 42,
            )
    finally:
        server.shutdown()
        thread.join(timeout=2)


def test_fetch_apis_to_dataframe_slowdowns_on_backpressure():
    _TestHandler.last_success_ts = 0.0
    server, thread = _start_server()
    base_url = f"http://{server.server_address[0]}:{server.server_address[1]}"

    endpoints = [
        f"{base_url}/throttle",
        f"{base_url}/throttle",
        f"{base_url}/throttle",
    ]

    start = time.perf_counter()
    try:
        df = fetch_apis_to_dataframe(
            endpoints,
            retries=2,
            max_workers=3,
            sort_by="value",
        )
    finally:
        server.shutdown()
        thread.join(timeout=2)

    elapsed = time.perf_counter() - start
    assert len(df) == 3
    # Adaptive throttle should inject extra delay after the first 429s, extending runtime
    assert elapsed >= 0.35


def test_fetch_apis_to_dataframe_background_future():
    server, thread = _start_server()
    base_url = f"http://{server.server_address[0]}:{server.server_address[1]}"

    endpoints = [f"{base_url}/json", f"{base_url}/csv"]

    start = time.perf_counter()
    try:
        future = fetch_apis_to_dataframe(
            endpoints,
            run_in_background=True,
            sort_by="id",
        )
        non_blocking_elapsed = time.perf_counter() - start
        assert non_blocking_elapsed < 0.05
        df = future.result(timeout=2)
    finally:
        server.shutdown()
        thread.join(timeout=2)

    assert isinstance(df, pd.DataFrame)
    assert len(df) == 4
