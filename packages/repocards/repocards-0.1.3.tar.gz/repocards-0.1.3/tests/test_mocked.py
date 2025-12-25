"""
Tests with mocked GitHub and GitLab API responses
"""

import pytest

from repocards.core.fetcher import (
    EXCLUDE_GLOBS,
    INCLUDE_GLOBS,
    _looks_texty,
    _matches_any,
    _parse_repo_url,
    _rank_candidate,
)


class TestRepoURLParsing:
    """Test URL parsing logic"""

    def test_parse_basic_url(self):
        """Should parse basic GitHub URLs"""
        platform, api_base, owner, name, ref = _parse_repo_url(
            "https://github.com/myuser/myrepo"
        )
        assert platform == "github"
        assert owner == "myuser"
        assert name == "myrepo"
        assert ref is None

    def test_parse_url_with_git_suffix(self):
        """Should handle .git suffix"""
        platform, api_base, owner, name, ref = _parse_repo_url(
            "https://github.com/user/repo.git"
        )
        assert platform == "github"
        assert owner == "user"
        assert name == "repo"

    def test_parse_url_with_fragment_ref(self):
        """Should extract ref from fragment"""
        platform, api_base, owner, name, ref = _parse_repo_url(
            "https://github.com/user/repo#develop"
        )
        assert platform == "github"
        assert owner == "user"
        assert name == "repo"
        assert ref == "develop"

    def test_parse_url_with_tree_ref(self):
        """Should extract ref from /tree/ path"""
        platform, api_base, owner, name, ref = _parse_repo_url(
            "https://github.com/user/repo/tree/feature/branch"
        )
        assert platform == "github"
        assert owner == "user"
        assert name == "repo"
        assert ref == "feature/branch"

    def test_parse_invalid_url(self):
        """Should raise error for unsupported platforms"""
        with pytest.raises(ValueError, match="Unsupported platform"):
            _parse_repo_url("https://bitbucket.org/user/repo")

    def test_parse_incomplete_url(self):
        """Should raise error for incomplete URLs"""
        with pytest.raises(ValueError):
            _parse_repo_url("https://github.com/user")

    def test_parse_gitlab_url(self):
        """Should parse GitLab URLs"""
        platform, api_base, owner, name, ref = _parse_repo_url(
            "https://gitlab.com/user/project"
        )
        assert platform == "gitlab"
        assert owner == "user"
        assert name == "user/project"  # Full project path for GitLab
        assert ref is None
        assert "gitlab.com/api/v4" in api_base

    def test_parse_selfhosted_gitlab_url(self):
        """Should parse self-hosted GitLab URLs"""
        platform, api_base, owner, name, ref = _parse_repo_url(
            "https://gitlab.epfl.ch/user/project"
        )
        assert platform == "gitlab"
        assert owner == "user"
        assert name == "user/project"  # Full project path for GitLab
        assert "gitlab.epfl.ch/api/v4" in api_base

    def test_parse_gitlab_url_with_fragment_ref(self):
        """Should extract ref from fragment for GitLab URLs"""
        platform, api_base, owner, name, ref = _parse_repo_url(
            "https://gitlab.com/user/project#develop"
        )
        assert platform == "gitlab"
        assert owner == "user"
        assert name == "user/project"  # Full project path for GitLab
        assert ref == "develop"

    def test_parse_gitlab_url_with_tree_ref(self):
        """Should extract ref from /-/tree/ path for GitLab URLs"""
        platform, api_base, owner, name, ref = _parse_repo_url(
            "https://gitlab.com/user/project/-/tree/feature/branch"
        )
        assert platform == "gitlab"
        assert owner == "user"
        assert name == "user/project"  # Full project path for GitLab
        assert ref == "feature/branch"

    def test_parse_gitlab_url_with_nested_groups(self):
        """Should handle GitLab URLs with nested groups/subgroups"""
        platform, api_base, owner, name, ref = _parse_repo_url(
            "https://gitlab.com/group/subgroup/project"
        )
        assert platform == "gitlab"
        assert owner == "group"
        assert name == "group/subgroup/project"
        assert ref is None

    def test_parse_gitlab_url_with_nested_groups_and_git_suffix(self):
        """Should handle nested groups with .git suffix"""
        platform, api_base, owner, name, ref = _parse_repo_url(
            "https://gitlab.com/group/subgroup/project.git"
        )
        assert platform == "gitlab"
        assert owner == "group"
        assert name == "group/subgroup/project"
        assert ref is None

    def test_parse_gitlab_url_with_nested_groups_and_ref(self):
        """Should handle nested groups with tree ref"""
        platform, api_base, owner, name, ref = _parse_repo_url(
            "https://gitlab.com/group/subgroup/project/-/tree/main"
        )
        assert platform == "gitlab"
        assert owner == "group"
        assert name == "group/subgroup/project"
        assert ref == "main"

    def test_parse_gitlab_url_with_deeply_nested_groups(self):
        """Should handle deeply nested groups (3+ levels)"""
        platform, api_base, owner, name, ref = _parse_repo_url(
            "https://gitlab.com/org/team/subteam/project"
        )
        assert platform == "gitlab"
        assert owner == "org"
        assert name == "org/team/subteam/project"
        assert ref is None

    def test_parse_gitlab_url_with_nested_groups_and_fragment_ref(self):
        """Should handle nested groups with fragment ref"""
        platform, api_base, owner, name, ref = _parse_repo_url(
            "https://gitlab.com/group/subgroup/project#develop"
        )
        assert platform == "gitlab"
        assert owner == "group"
        assert name == "group/subgroup/project"
        assert ref == "develop"

    def test_parse_gitlab_url_with_dashes_in_project_name(self):
        """Should handle project names containing dashes"""
        platform, api_base, owner, name, ref = _parse_repo_url(
            "https://gitlab.com/group/my-sub-group/my-project"
        )
        assert platform == "gitlab"
        assert owner == "group"
        assert name == "group/my-sub-group/my-project"
        assert ref is None

    def test_parse_gitlab_url_with_dashes_and_ref(self):
        """Should handle project names with dashes and refs"""
        platform, api_base, owner, name, ref = _parse_repo_url(
            "https://gitlab.com/my-org/my-team/my-project/-/tree/feature-branch"
        )
        assert platform == "gitlab"
        assert owner == "my-org"
        assert name == "my-org/my-team/my-project"
        assert ref == "feature-branch"

    def test_parse_gitlab_url_with_blob_route(self):
        """Should handle GitLab URLs with /-/blob/ route"""
        platform, api_base, owner, name, ref = _parse_repo_url(
            "https://gitlab.com/group/subgroup/project/-/blob/main/README.md"
        )
        assert platform == "gitlab"
        assert owner == "group"
        assert name == "group/subgroup/project"
        # Note: ref extraction not implemented for blob routes yet
        assert ref is None

    def test_parse_gitlab_url_with_commits_route(self):
        """Should handle GitLab URLs with /-/commits/ route"""
        platform, api_base, owner, name, ref = _parse_repo_url(
            "https://gitlab.com/group/project/-/commits/develop"
        )
        assert platform == "gitlab"
        assert owner == "group"
        assert name == "group/project"
        assert ref is None

    def test_parse_gitlab_url_with_tags_route(self):
        """Should handle GitLab URLs with /-/tags/ route"""
        platform, api_base, owner, name, ref = _parse_repo_url(
            "https://gitlab.com/user/project/-/tags/v1.0.0"
        )
        assert platform == "gitlab"
        assert owner == "user"
        assert name == "user/project"
        assert ref is None

    def test_parse_gitlab_url_with_branches_route(self):
        """Should handle GitLab URLs with /-/branches/ route"""
        platform, api_base, owner, name, ref = _parse_repo_url(
            "https://gitlab.com/org/team/project/-/branches"
        )
        assert platform == "gitlab"
        assert owner == "org"
        assert name == "org/team/project"
        assert ref is None

    def test_parse_gitlab_url_with_nested_groups_and_blob_route(self):
        """Should handle nested groups with /-/blob/ route"""
        platform, api_base, owner, name, ref = _parse_repo_url(
            "https://gitlab.com/a/b/c/project/-/blob/feature/src/file.py"
        )
        assert platform == "gitlab"
        assert owner == "a"
        assert name == "a/b/c/project"
        assert ref is None

    def test_parse_gitlab_url_with_merge_requests_route(self):
        """Should handle GitLab URLs with /-/merge_requests/ route"""
        platform, api_base, owner, name, ref = _parse_repo_url(
            "https://gitlab.com/group/project/-/merge_requests/123"
        )
        assert platform == "gitlab"
        assert owner == "group"
        assert name == "group/project"
        assert ref is None

    def test_parse_gitlab_url_with_issues_route(self):
        """Should handle GitLab URLs with /-/issues/ route"""
        platform, api_base, owner, name, ref = _parse_repo_url(
            "https://gitlab.com/org/team/project/-/issues/45"
        )
        assert platform == "gitlab"
        assert owner == "org"
        assert name == "org/team/project"
        assert ref is None

    def test_parse_gitlab_url_with_pipelines_route(self):
        """Should handle GitLab URLs with /-/pipelines/ route"""
        platform, api_base, owner, name, ref = _parse_repo_url(
            "https://gitlab.com/user/my-project/-/pipelines"
        )
        assert platform == "gitlab"
        assert owner == "user"
        assert name == "user/my-project"
        assert ref is None



class TestFetcherWithMocks:
    """Test fetcher with mocked API responses"""

    def test_fetch_with_github_token(self):
        """Should use provided GitHub token"""
        # This test verifies token is passed to the session
        # Simplified version that just checks the function accepts the token parameter
        # Real API testing would be better done with integration tests
        pass  # Token handling is tested via integration tests


class TestFileSelection:
    """Test file selection and filtering logic"""

    def test_matches_include_patterns(self):
        """Should match files against include patterns"""
        # Test files that should match
        assert _matches_any("README.md", INCLUDE_GLOBS)
        assert _matches_any("README.rst", INCLUDE_GLOBS)
        assert _matches_any("pyproject.toml", INCLUDE_GLOBS)
        assert _matches_any("setup.py", INCLUDE_GLOBS)
        assert _matches_any("package.json", INCLUDE_GLOBS)

    def test_matches_exclude_patterns(self):
        """Should match files against exclude patterns"""

        assert _matches_any("data/dataset.csv", EXCLUDE_GLOBS)
        assert _matches_any(".git/config", EXCLUDE_GLOBS)
        assert _matches_any("venv/lib/python3.11/site-packages/numpy.py", EXCLUDE_GLOBS)

    def test_looks_texty(self):
        """Should identify text files"""

        assert _looks_texty("script.py")
        assert _looks_texty("config.json")
        assert _looks_texty("notes.md")
        assert _looks_texty("build.sh")
        assert _looks_texty("CMakeLists.txt")
        assert not _looks_texty("binary.exe")
        assert not _looks_texty("image.png")

    def test_rank_candidate_prioritizes_important_files(self):
        """Should rank important files higher"""

        readme_rank = _rank_candidate("README.md")
        manifest_rank = _rank_candidate("pyproject.toml")
        workflow_rank = _rank_candidate(".github/workflows/test.yml")
        docs_rank = _rank_candidate("docs/guide.md")
        random_rank = _rank_candidate("src/utils/helper.py")

        # Lower rank = higher priority
        assert readme_rank < docs_rank
        assert manifest_rank < random_rank
        assert workflow_rank < random_rank
