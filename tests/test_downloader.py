import tempfile
from pathlib import Path

from zig_fetch_py import downloader


def test_is_git_dependency_url():
    assert downloader.is_git_dependency_url("git+https://github.com/example/repo.git#abc123")
    assert not downloader.is_git_dependency_url("https://example.com/archive.tar.gz")


def test_split_git_dependency_url():
    repo_url, ref = downloader.split_git_dependency_url(
        "git+https://github.com/karlseguin/websocket.zig#97fefafa59cc78ce177cff540b8685cd7f699276"
    )
    assert repo_url == "https://github.com/karlseguin/websocket.zig"
    assert ref == "97fefafa59cc78ce177cff540b8685cd7f699276"


def test_build_git_env_propagates_proxy(monkeypatch):
    monkeypatch.setenv("HTTP_PROXY", "http://127.0.0.1:7890")
    monkeypatch.setenv("HTTPS_PROXY", "http://127.0.0.1:7890")
    monkeypatch.delenv("GIT_HTTP_PROXY", raising=False)
    monkeypatch.delenv("GIT_HTTPS_PROXY", raising=False)

    env = downloader._build_git_env()

    assert env["GIT_HTTP_PROXY"] == "http://127.0.0.1:7890"
    assert env["GIT_HTTPS_PROXY"] == "http://127.0.0.1:7890"


def test_process_dependency_git_commit(monkeypatch):
    with tempfile.TemporaryDirectory() as cache_temp:
        cache_dir = Path(cache_temp)
        dep_info = {
            "url": "git+https://github.com/karlseguin/websocket.zig#97fefafa59cc78ce177cff540b8685cd7f699276",
            "hash": "websocket-0.1.0-ZPISdRlzAwBB_Bz2UMMqxYqF6YEVTIBoFsbzwPUJTHIc",
        }

        calls = {}

        def fake_clone(repo_url: str, target_path: Path, ref: str | None = None):
            calls["repo_url"] = repo_url
            calls["target_path"] = target_path
            calls["ref"] = ref
            target_path.mkdir(parents=True, exist_ok=True)
            (target_path / "build.zig.zon").write_text('.{ .name = "dummy" }', encoding="utf-8")

        monkeypatch.setattr(downloader, "clone_git_dependency", fake_clone)

        result = downloader.process_dependency("websocket", dep_info, cache_dir)

        expected_target = cache_dir / dep_info["hash"]
        assert result == expected_target
        assert expected_target.exists()
        assert calls["repo_url"] == "https://github.com/karlseguin/websocket.zig"
        assert calls["ref"] == "97fefafa59cc78ce177cff540b8685cd7f699276"
