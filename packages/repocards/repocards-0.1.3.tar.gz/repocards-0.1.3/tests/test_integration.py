"""
Integration tests for CLI and end-to-end workflows
"""

import json
import tempfile
from pathlib import Path
from unittest.mock import patch

from typer.testing import CliRunner

from repocards.cli import app
from repocards.schemas import FetchedFile, RepoSnapshot

runner = CliRunner()


class TestCLI:
    """Test CLI commands"""

    def test_version_command(self):
        """Should display version"""
        result = runner.invoke(app, ["version"])
        assert result.exit_code == 0
        assert "0.1.0" in result.stdout

    @patch("repocards.cli.fetch_repo_snapshot_via_api")
    def test_summarize_stdout(self, mock_fetch):
        """Should output markdown to stdout when no output path specified"""
        # Mock the API response
        mock_fetch.return_value = RepoSnapshot(
            owner="testuser",
            name="testproject",
            ref="main",
            description="Test project",
            license_spdx="MIT",
            topics=["python"],
            files=[
                FetchedFile(
                    path="README.md",
                    content="# Test Project\n\nThis is a test.\n\n```bash\npip install test\n```",
                ),
                FetchedFile(path="pyproject.toml", content="[project]\nname = 'test'"),
            ],
            languages={"Python": 10000},
        )

        result = runner.invoke(
            app, ["summarize", "https://github.com/testuser/testproject"]
        )

        assert result.exit_code == 0
        assert "testuser/testproject" in result.stdout
        assert "MIT" in result.stdout

    @patch("repocards.cli.fetch_repo_snapshot_via_api")
    def test_summarize_with_output_dir(self, mock_fetch):
        """Should write files to specified output directory"""
        mock_fetch.return_value = RepoSnapshot(
            owner="testuser",
            name="testproject",
            ref="main",
            description="Test project",
            files=[
                FetchedFile(path="README.md", content="# Test\nTest project"),
                FetchedFile(path="pyproject.toml", content="[project]\nname='test'"),
            ],
            languages={"Python": 5000},
        )

        with tempfile.TemporaryDirectory() as tmpdir:
            result = runner.invoke(
                app,
                [
                    "summarize",
                    "https://github.com/testuser/testproject",
                    "--out-dir",
                    tmpdir,
                ],
            )

            assert result.exit_code == 0

            # Check files were created
            md_path = Path(tmpdir) / "card.md"
            json_path = Path(tmpdir) / "card.json"

            assert md_path.exists()
            assert json_path.exists()

            # Verify content
            md_content = md_path.read_text()
            assert "testuser/testproject" in md_content

            json_content = json.loads(json_path.read_text())
            assert json_content["title"] == "testuser/testproject"
            assert "extras" in json_content

    @patch("repocards.cli.fetch_repo_snapshot_via_api")
    def test_summarize_with_custom_stem(self, mock_fetch):
        """Should use custom filename stem"""
        mock_fetch.return_value = RepoSnapshot(
            owner="user",
            name="repo",
            ref="main",
            files=[FetchedFile(path="README.md", content="# Test")],
            languages={"Python": 1000},
        )

        with tempfile.TemporaryDirectory() as tmpdir:
            result = runner.invoke(
                app,
                [
                    "summarize",
                    "https://github.com/user/repo",
                    "--out-dir",
                    tmpdir,
                    "--out-stem",
                    "myproject",
                ],
            )

            assert result.exit_code == 0
            assert (Path(tmpdir) / "myproject.md").exists()
            assert (Path(tmpdir) / "myproject.json").exists()

    @patch("repocards.cli.fetch_repo_snapshot_via_api")
    def test_summarize_with_exact_paths(self, mock_fetch):
        """Should write to exact specified paths"""
        mock_fetch.return_value = RepoSnapshot(
            owner="user",
            name="repo",
            ref="main",
            files=[FetchedFile(path="README.md", content="# Test")],
            languages={},
        )

        with tempfile.TemporaryDirectory() as tmpdir:
            md_path = str(Path(tmpdir) / "custom.md")
            json_path = str(Path(tmpdir) / "custom.json")

            result = runner.invoke(
                app,
                [
                    "summarize",
                    "https://github.com/user/repo",
                    "--out-md",
                    md_path,
                    "--out-json",
                    json_path,
                ],
            )

            assert result.exit_code == 0
            assert Path(md_path).exists()
            assert Path(json_path).exists()


class TestEndToEnd:
    """Test complete workflows"""

    @patch("repocards.cli.fetch_repo_snapshot_via_api")
    def test_complete_python_project_analysis(self, mock_fetch):
        """Should analyze a Python project with all features"""
        mock_fetch.return_value = RepoSnapshot(
            owner="myorg",
            name="myproject",
            ref="main",
            description="A Python data processing library",
            license_spdx="Apache-2.0",
            topics=["python", "data", "analytics"],
            files=[
                FetchedFile(
                    path="README.md",
                    content="""# MyProject

A powerful data processing library.

## Installation
```bash
pip install myproject
```

## Usage
```python
import myproject
result = myproject.process(data)
```

## Building
```bash
python -m build
pytest tests/
```
""",
                ),
                FetchedFile(
                    path="pyproject.toml",
                    content="""[project]
name = "myproject"
version = "1.0.0"

[project.scripts]
myproject = "myproject.cli:main"
""",
                ),
                FetchedFile(
                    path=".github/workflows/test.yml",
                    content="""
name: Test
jobs:
  test:
    steps:
      - run: pip install -e .
      - run: pytest tests/ --cov
""",
                ),
                FetchedFile(path="Dockerfile", content="FROM python:3.11\nCOPY . /app"),
                FetchedFile(
                    path="docs/api.md",
                    content="Documentation: https://myproject.readthedocs.io",
                ),
            ],
            languages={"Python": 50000, "Shell": 2000},
        )

        with tempfile.TemporaryDirectory() as tmpdir:
            result = runner.invoke(
                app,
                [
                    "summarize",
                    "https://github.com/myorg/myproject",
                    "--out-dir",
                    tmpdir,
                    "--out-stem",
                    "analysis",
                ],
            )

            assert result.exit_code == 0

            # Read generated JSON
            json_path = Path(tmpdir) / "analysis.json"
            card_data = json.loads(json_path.read_text())

            # Verify structure
            assert card_data["repo_url"] == "https://github.com/myorg/myproject"
            assert card_data["title"] == "myorg/myproject"
            assert card_data["meta"]["license"] == "Apache-2.0"

            # Verify extras
            extras = card_data["extras"]
            assert "python" in extras["ecosystems"]

            caps = extras["capabilities"]
            # Check basic capabilities that should be present
            assert caps["provides_api"] is True
            assert caps["dockerfile_present"] is True
            assert len(caps["package_names"]) > 0

            # Verify commands were extracted
            assert "buckets_by_os" in caps
            assert "install" in caps["buckets_by_os"]

            # Verify quickstart
            assert "quickstart" in extras
            assert len(extras["quickstart"].get("linux", [])) > 0

    @patch("repocards.cli.fetch_repo_snapshot_via_api")
    def test_cmake_project_analysis(self, mock_fetch):
        """Should analyze a CMake-based C++ project"""
        mock_fetch.return_value = RepoSnapshot(
            owner="org",
            name="cpp-lib",
            ref="main",
            license_spdx="BSD-3-Clause",
            files=[
                FetchedFile(
                    path="README.md",
                    content="""# C++ Library

## Build
```bash
cmake -B build
cmake --build build
ctest --test-dir build
```
""",
                ),
                FetchedFile(
                    path="CMakeLists.txt",
                    content="cmake_minimum_required(VERSION 3.14)\nproject(mylib)",
                ),
            ],
            languages={"C++": 80000, "CMake": 5000},
        )

        with tempfile.TemporaryDirectory() as tmpdir:
            result = runner.invoke(
                app,
                ["summarize", "https://github.com/org/cpp-lib", "--out-dir", tmpdir],
            )

            assert result.exit_code == 0

            json_path = Path(tmpdir) / "card.json"
            card_data = json.loads(json_path.read_text())

            # Should detect CMake ecosystem
            assert "cmake" in card_data["extras"]["ecosystems"]

            # Should categorize cmake commands as build
            caps = card_data["extras"]["capabilities"]
            buckets = caps["buckets_by_os"]
            assert "build" in buckets

            # Quickstart should prioritize cmake commands
            quickstart = card_data["extras"]["quickstart"]
            has_cmake = any(
                "cmake" in step.get("cmd", "").lower()
                for os_steps in quickstart.values()
                for step in os_steps
            )
            assert has_cmake


class TestOutputResolvers:
    """Test output path resolution logic"""

    def test_resolve_outputs_exact_paths(self):
        """Exact paths should take precedence"""
        from repocards.cli import _resolve_outputs

        md, js = _resolve_outputs(
            out_dir=None,
            out_md="/custom/path.md",
            out_json="/other/data.json",
            out_stem=None,
        )
        assert md == "/custom/path.md"
        assert js == "/other/data.json"

    def test_resolve_outputs_dir_and_stem(self):
        """Should combine directory and stem"""
        import tempfile

        from repocards.cli import _resolve_outputs

        with tempfile.TemporaryDirectory() as tmpdir:
            md, js = _resolve_outputs(
                out_dir=tmpdir, out_md=None, out_json=None, out_stem="myfile"
            )
            assert tmpdir in md
            assert "myfile.md" in md
            assert tmpdir in js
            assert "myfile.json" in js

    def test_resolve_outputs_default_to_stdout(self):
        """Should return None for stdout output"""
        from repocards.cli import _resolve_outputs

        md, js = _resolve_outputs(
            out_dir=None, out_md=None, out_json=None, out_stem=None
        )
        assert md is None
        assert js is None
