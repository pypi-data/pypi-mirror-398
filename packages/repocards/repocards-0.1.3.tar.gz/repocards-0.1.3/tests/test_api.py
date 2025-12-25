"""
Unit tests for the public API (api.py)
"""

import json
import tempfile
from pathlib import Path

import pytest

from repocards import get_repo_info
from repocards.schemas import RepoCard


class TestGetRepoInfo:
    """Test the public get_repo_info API function"""

    # Use a small, stable test repository
    TEST_REPO = "https://github.com/octocat/Hello-World"

    def test_markdown_mode_returns_string(self):
        """Mode 'markdown' should return a markdown string"""
        result = get_repo_info(self.TEST_REPO, mode="markdown", max_files=20)
        assert isinstance(result, str)
        assert len(result) > 0
        assert "## octocat/Hello-World" in result or "Hello-World" in result

    def test_json_mode_returns_valid_json_string(self):
        """Mode 'json' should return a valid JSON string"""
        result = get_repo_info(self.TEST_REPO, mode="json", max_files=20)
        assert isinstance(result, str)

        # Verify it's valid JSON
        parsed = json.loads(result)
        assert "repo_url" in parsed
        assert "title" in parsed
        assert "markdown" in parsed
        assert self.TEST_REPO in parsed["repo_url"]

    def test_pydantic_mode_returns_repocard_object(self):
        """Mode 'pydantic' should return a RepoCard object"""
        result = get_repo_info(self.TEST_REPO, mode="pydantic", max_files=20)
        assert isinstance(result, RepoCard)
        assert result.repo_url == self.TEST_REPO
        assert result.title
        assert result.markdown
        assert isinstance(result.meta, dict)
        assert isinstance(result.extras, dict)

    def test_markdown_file_mode_writes_file(self):
        """Mode 'markdown_file' should write a markdown file and return path"""
        with tempfile.TemporaryDirectory() as tmpdir:
            result = get_repo_info(
                self.TEST_REPO, mode="markdown_file", max_files=20, out_dir=tmpdir
            )

            assert isinstance(result, str)
            result_path = Path(result)
            assert result_path.exists()
            assert result_path.suffix == ".md"
            assert result_path.parent == Path(tmpdir)

            # Verify content
            content = result_path.read_text(encoding="utf-8")
            assert len(content) > 0
            assert "Hello-World" in content or "octocat" in content

    def test_json_file_mode_writes_file(self):
        """Mode 'json_file' should write a JSON file and return path"""
        with tempfile.TemporaryDirectory() as tmpdir:
            result = get_repo_info(
                self.TEST_REPO, mode="json_file", max_files=20, out_dir=tmpdir
            )

            assert isinstance(result, str)
            result_path = Path(result)
            assert result_path.exists()
            assert result_path.suffix == ".json"
            assert result_path.parent == Path(tmpdir)

            # Verify content is valid JSON
            content = result_path.read_text(encoding="utf-8")
            parsed = json.loads(content)
            assert "repo_url" in parsed
            assert self.TEST_REPO in parsed["repo_url"]

    def test_default_mode_is_markdown(self):
        """When mode is not specified, it should default to markdown"""
        result = get_repo_info(self.TEST_REPO, max_files=20)
        assert isinstance(result, str)
        assert "## " in result or "#" in result  # Should contain markdown headers

    def test_invalid_mode_raises_value_error(self):
        """Invalid mode should raise ValueError"""
        with pytest.raises(ValueError, match="Invalid mode"):
            get_repo_info(self.TEST_REPO, mode="invalid_mode")

    def test_markdown_file_without_out_dir_raises_error(self):
        """markdown_file mode without out_dir should raise ValueError"""
        with pytest.raises(ValueError, match="out_dir is required"):
            get_repo_info(self.TEST_REPO, mode="markdown_file")

    def test_json_file_without_out_dir_raises_error(self):
        """json_file mode without out_dir should raise ValueError"""
        with pytest.raises(ValueError, match="out_dir is required"):
            get_repo_info(self.TEST_REPO, mode="json_file")

    def test_max_files_parameter_is_respected(self):
        """max_files parameter should be passed through to fetcher"""
        # Just verify it doesn't crash with different max_files values
        result = get_repo_info(self.TEST_REPO, mode="markdown", max_files=10)
        assert isinstance(result, str)

        result = get_repo_info(self.TEST_REPO, mode="markdown", max_files=50)
        assert isinstance(result, str)

    def test_file_modes_create_directory_if_not_exists(self):
        """File modes should create the output directory if it doesn't exist"""
        with tempfile.TemporaryDirectory() as tmpdir:
            nested_dir = Path(tmpdir) / "nested" / "output"

            result = get_repo_info(
                self.TEST_REPO,
                mode="markdown_file",
                max_files=20,
                out_dir=str(nested_dir),
            )

            assert Path(result).exists()
            assert Path(result).parent == nested_dir

    def test_all_modes_produce_consistent_content(self):
        """All modes should produce consistent underlying data"""
        # Get data in different modes
        md_result = get_repo_info(self.TEST_REPO, mode="markdown", max_files=20)
        json_result = get_repo_info(self.TEST_REPO, mode="json", max_files=20)
        pydantic_result = get_repo_info(self.TEST_REPO, mode="pydantic", max_files=20)

        # Parse JSON
        json_data = json.loads(json_result)

        # Compare content consistency
        assert md_result == json_data["markdown"]
        assert md_result == pydantic_result.markdown
        assert json_data["repo_url"] == pydantic_result.repo_url
        assert json_data["title"] == pydantic_result.title

    def test_pydantic_result_has_expected_structure(self):
        """Pydantic result should have all expected fields"""
        result = get_repo_info(self.TEST_REPO, mode="pydantic", max_files=20)

        # Check required fields
        assert hasattr(result, "repo_url")
        assert hasattr(result, "ref")
        assert hasattr(result, "title")
        assert hasattr(result, "meta")
        assert hasattr(result, "markdown")
        assert hasattr(result, "extras")

        # Check extras structure
        assert "ecosystems" in result.extras
        assert "capabilities" in result.extras
        assert "quickstart" in result.extras
        assert "imaging" in result.extras

        # Check meta structure
        assert "license" in result.meta
        assert "topics" in result.meta
        assert "languages" in result.meta
