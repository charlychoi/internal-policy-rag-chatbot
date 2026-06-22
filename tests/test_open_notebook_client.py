from pathlib import Path
import sys
sys.path.append(str(Path(__file__).resolve().parents[1] / "src"))
from open_notebook_client import OpenNotebookClient, OpenNotebookConfig


def test_client_builds_headers_without_password():
    client = OpenNotebookClient(OpenNotebookConfig(api_base="http://example.test/api", password=""))
    assert "Authorization" not in client.headers


def test_client_builds_headers_with_password():
    client = OpenNotebookClient(OpenNotebookConfig(api_base="http://example.test/api", password="secret"))
    assert client.headers["Authorization"] == "Bearer secret"
