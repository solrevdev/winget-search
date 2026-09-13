"""Exercise the Pages helper against local remotes and guard the build contract."""
import datetime
import os
from pathlib import Path
import subprocess
import tempfile
import unittest

import yaml

ROOT = Path(__file__).resolve().parents[1]
HELPER = ROOT / "force_pages_update.sh"


class PagesHelperTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix="winget-helper-test-")
        self.addCleanup(self.temp.cleanup)
        self.base = Path(self.temp.name)
        self.env = dict(os.environ, GIT_CONFIG_GLOBAL=os.devnull,
                        GIT_CONFIG_NOSYSTEM="1", GIT_TERMINAL_PROMPT="0",
                        TMPDIR=str(self.base))
        self.remote = self.base / "remote.git"
        self.repo = self.base / "source"
        self.git(self.base, "init", "--bare", str(self.remote))
        self.git(self.base, "init", "-b", "topic/work", str(self.repo))
        self.git(self.repo, "config", "user.name", "Test")
        self.git(self.repo, "config", "user.email", "test@example.invalid")
        (self.repo / "source.txt").write_text("source\n")
        self.git(self.repo, "add", "source.txt")
        self.git(self.repo, "commit", "-m", "test: create source")
        self.git(self.repo, "remote", "add", "origin", str(self.remote))
        self.git(self.repo, "switch", "--orphan", "gh-pages")
        (self.repo / "index.html").write_text("<!DOCTYPE html><title>Test</title>\n")
        (self.repo / "catalog.json").write_text("{}\n")
        self.git(self.repo, "add", ".")
        self.git(self.repo, "commit", "-m", "test: create site")
        self.git(self.repo, "push", "origin", "gh-pages")
        self.pages_before = self.git(self.remote, "rev-parse", "gh-pages")
        self.git(self.repo, "switch", "topic/work")
        self.source_before = self.git(self.repo, "rev-parse", "HEAD")

    def git(self, cwd, *args):
        return subprocess.run(["git", *args], cwd=cwd, env=self.env, check=True,
                              text=True, stdout=subprocess.PIPE,
                              stderr=subprocess.PIPE).stdout.strip()

    def hook(self, repo, name, body):
        hooks = repo / ("hooks" if repo == self.remote else ".git/hooks")
        path = hooks / name
        path.write_text("#!/bin/bash\nset -eu\n" + body + "\n")
        path.chmod(0o755)

    def run_helper(self, success, cwd=None):
        branch = self.git(self.repo, "symbolic-ref", "--short", "HEAD")
        head = self.git(self.repo, "rev-parse", "HEAD")
        status = self.git(self.repo, "status", "--porcelain", "--untracked-files=all")
        result = subprocess.run(["bash", str(HELPER)], cwd=cwd or self.repo,
                                env=self.env, text=True, capture_output=True)
        self.assertEqual(result.returncode == 0, success, result.stdout + result.stderr)
        self.assertEqual(self.git(self.repo, "symbolic-ref", "--short", "HEAD"), branch)
        self.assertEqual(self.git(self.repo, "rev-parse", "HEAD"), head)
        self.assertEqual(self.git(self.repo, "status", "--porcelain", "--untracked-files=all"), status)
        return result

    def assert_remote_unchanged(self):
        self.assertEqual(self.git(self.remote, "rev-parse", "gh-pages"), self.pages_before)

    def test_success_preserves_source_and_pushes_only_intended_files(self):
        self.run_helper(True)
        self.assertEqual(self.git(self.remote, "rev-parse", "gh-pages^"), self.pages_before)
        files = self.git(self.remote, "diff-tree", "--no-commit-id", "--name-only", "-r", "gh-pages")
        self.assertEqual(set(files.splitlines()), {".nojekyll", "index.html"})
        self.assertEqual(len(self.git(self.repo, "worktree", "list", "--porcelain").split("worktree ")) - 1, 1)
        self.assertEqual(list(self.base.glob("winget-pages-update.*")), [])

    def test_success_from_gh_pages_preserves_its_head(self):
        self.git(self.repo, "switch", "gh-pages")
        self.run_helper(True)

    def test_success_from_subdirectory_with_remote_only_pages_branch(self):
        self.git(self.repo, "branch", "-D", "gh-pages")
        subdir = self.repo / "subdir"
        subdir.mkdir()
        self.run_helper(True, cwd=subdir)

    def test_rejects_staged_unstaged_and_untracked_changes(self):
        for kind in ("staged", "unstaged", "untracked"):
            with self.subTest(kind=kind):
                path = self.repo / ("extra.txt" if kind == "untracked" else "source.txt")
                path.write_text("keep this\n")
                if kind == "staged":
                    self.git(self.repo, "add", "source.txt")
                self.run_helper(False)
                self.assertEqual(path.read_text(), "keep this\n")
                self.assert_remote_unchanged()
                if kind != "untracked":
                    self.git(self.repo, "restore", "--staged", "--worktree", "source.txt")
        self.assertEqual(list(self.base.glob("winget-pages-update.*")), [])

    def test_rejects_detached_head_without_changes(self):
        self.git(self.repo, "switch", "--detach")
        result = subprocess.run(["bash", str(HELPER)], cwd=self.repo,
                                env=self.env, text=True, capture_output=True)
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("detached HEAD", result.stderr)
        self.assertEqual(self.git(self.repo, "rev-parse", "HEAD"), self.source_before)
        self.assertEqual(self.git(self.repo, "status", "--porcelain"), "")
        self.assert_remote_unchanged()

    def test_fetch_failure_preserves_starting_branch(self):
        self.git(self.repo, "remote", "set-url", "origin", str(self.base / "missing.git"))
        self.run_helper(False)
        self.assert_remote_unchanged()

    def test_commit_failure_retains_work_for_inspection(self):
        self.hook(self.repo, "pre-commit", "exit 1")
        result = self.run_helper(False)
        self.assertIn("Inspect retained work", result.stderr)
        self.assert_remote_unchanged()
        self.assertEqual(len(list(self.base.glob("winget-pages-update.*/site/index.html"))), 1)

    def test_push_failure_retains_committed_work(self):
        self.hook(self.remote, "pre-receive", "exit 1")
        self.run_helper(False)
        self.assert_remote_unchanged()
        worktree = next(self.base.glob("winget-pages-update.*/site"))
        self.assertEqual(self.git(worktree, "log", "-1", "--format=%s"), "chore: trigger Pages publication")
        self.assertEqual(self.git(worktree, "status", "--porcelain"), "")

    def test_missing_index_stops_before_commit(self):
        self.git(self.repo, "switch", "gh-pages")
        self.git(self.repo, "mv", "index.html", "other.html")
        self.git(self.repo, "commit", "-m", "test: remove index")
        self.git(self.repo, "push", "origin", "gh-pages")
        self.pages_before = self.git(self.remote, "rev-parse", "gh-pages")
        self.git(self.repo, "switch", "topic/work")
        self.run_helper(False)
        self.assert_remote_unchanged()

    def test_unrelated_staged_file_is_not_published_or_deleted(self):
        self.hook(self.repo, "post-checkout", 'echo keep > unrelated.txt\ngit add unrelated.txt')
        result = self.run_helper(False)
        self.assertIn("cleanup failed", result.stderr)
        files = self.git(self.remote, "ls-tree", "--name-only", "gh-pages").splitlines()
        self.assertNotIn("unrelated.txt", files)
        worktree = next(self.base.glob("winget-pages-update.*/site"))
        self.assertEqual((worktree / "unrelated.txt").read_text(), "keep\n")

    def test_concurrent_orphan_publication_rejects_non_fast_forward_pull(self):
        # Deployments replace gh-pages history, so a race must stop rather than merge.
        self.hook(self.repo, "post-checkout", '\n'.join([
            'tree=$(git rev-parse HEAD^{tree})',
            'replacement=$(echo "test: concurrent deployment" | git commit-tree "$tree")',
            'git push --force origin "$replacement:refs/heads/gh-pages"',
        ]))
        self.run_helper(False)
        self.assertEqual(self.git(self.remote, "log", "-1", "--format=%s", "gh-pages"),
                         "test: concurrent deployment")
        worktree = next(self.base.glob("winget-pages-update.*/site"))
        self.assertEqual(self.git(worktree, "rev-parse", "HEAD"), self.pages_before)

    def test_concurrent_fast_forward_publication_is_preserved(self):
        self.hook(self.repo, "post-checkout", '\n'.join([
            'tree=$(git rev-parse HEAD^{tree})',
            'next=$(echo "test: concurrent update" | git commit-tree "$tree" -p HEAD)',
            'git push origin "$next:refs/heads/gh-pages"',
        ]))
        self.run_helper(True)
        self.assertEqual(self.git(self.remote, "rev-parse", "gh-pages^^"), self.pages_before)
        self.assertEqual(self.git(self.remote, "log", "-1", "--format=%s", "gh-pages^"),
                         "test: concurrent update")


class BuildWorkflowTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.workflow = yaml.safe_load((ROOT / ".github/workflows/github_workflows_build.yml").read_text())
        cls.steps = cls.workflow["jobs"]["build"]["steps"]

    def test_cache_date_is_utc_across_runner_timezones(self):
        step = next(step for step in self.steps if step.get("id") == "cache-date")
        for timezone in ("Pacific/Kiritimati", "Pacific/Honolulu"):
            with self.subTest(timezone=timezone), tempfile.TemporaryDirectory() as directory:
                output = Path(directory) / "output"
                subprocess.run(["bash", "-eu", "-c", step["run"]], check=True,
                               env=dict(os.environ, TZ=timezone, GITHUB_OUTPUT=str(output)))
                today = datetime.datetime.now(datetime.timezone.utc).date().isoformat()
                self.assertEqual(output.read_text(), f"date={today}\n")

    def test_cache_reuses_daily_keys_and_versioned_prefix(self):
        cache = next(step for step in self.steps if step.get("id") == "cache-winget")
        settings = cache["with"]
        self.assertIn("steps.cache-date.outputs.date", settings["key"])
        self.assertNotIn("github.run_id", settings["key"])
        prefix = settings["restore-keys"].strip()
        self.assertRegex(prefix, r"winget-pkgs-v\d+-")
        self.assertTrue(settings["key"].startswith(prefix))

    def test_all_cache_outcomes_refresh_upstream_default_branch_before_extraction(self):
        upstream = next(step for step in self.steps
                        if step.get("with", {}).get("repository") == "microsoft/winget-pkgs")
        cache = next(step for step in self.steps if step.get("id") == "cache-winget")
        extract = next(step for step in self.steps if "extract_packages.py" in step.get("run", ""))
        self.assertNotIn("if", upstream, "Misses, prefix restores and exact hits must all refresh")
        self.assertEqual(upstream["uses"], "actions/checkout@v4")
        self.assertNotIn("ref", upstream["with"], "Checkout must resolve the current upstream default")
        self.assertFalse(upstream["with"]["persist-credentials"])
        self.assertEqual(upstream["with"]["path"], cache["with"]["path"])
        self.assertLess(self.steps.index(cache), self.steps.index(upstream))
        self.assertLess(self.steps.index(upstream), self.steps.index(extract))
        self.assertNotIn("origin/master", str(self.steps))


if __name__ == "__main__":
    unittest.main()
