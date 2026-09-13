"""Run actions/checkout against local Git data and a stub default-branch API.

Usage: python tests/checkout-cache-smoke.py /path/to/checkout/dist/index.js
The action bundle is unmodified; Git transport uses only temporary local remotes.
"""
import http.server
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import threading


def main(action):
    with tempfile.TemporaryDirectory(prefix="winget-checkout-smoke-") as directory:
        root = Path(directory)
        env = {key: value for key, value in os.environ.items()
               if not key.startswith(("INPUT_", "GITHUB_", "STATE_")) and key != "GH_TOKEN"}
        env.update(GIT_CONFIG_GLOBAL=str(root / "gitconfig"), GIT_CONFIG_NOSYSTEM="1",
                   GIT_TERMINAL_PROMPT="0")

        def git(cwd, *args):
            return subprocess.run(["git", *args], cwd=cwd, env=env, check=True,
                                  capture_output=True, text=True).stdout.strip()

        upstream = root / "upstream"
        git(root, "init", "-b", "main", str(upstream))
        git(upstream, "config", "user.name", "Test")
        git(upstream, "config", "user.email", "test@example.invalid")

        def commit(text):
            (upstream / "manifest.txt").write_text(text)
            git(upstream, "add", "manifest.txt")
            git(upstream, "commit", "-m", f"test: {text}")
            return git(upstream, "rev-parse", "HEAD")

        default_branch = "main"
        requests = []

        class Api(http.server.BaseHTTPRequestHandler):
            def do_GET(self):
                requests.append(self.path)
                if self.path != "/api/v3/repos/test/upstream":
                    self.send_error(404)
                    return
                body = json.dumps({"default_branch": default_branch}).encode()
                self.send_response(200)
                self.send_header("Content-Type", "application/json")
                self.send_header("Content-Length", str(len(body)))
                self.end_headers()
                self.wfile.write(body)

            def log_message(self, *_args):
                pass

        server = http.server.ThreadingHTTPServer(("127.0.0.1", 0), Api)
        thread = threading.Thread(target=server.serve_forever, daemon=True)
        thread.start()
        url = f"http://127.0.0.1:{server.server_port}"
        print(f"Checkout smoke: PID {os.getpid()}, API {url}, files {root}", flush=True)
        try:
            git(root, "config", "--global", f"url.{upstream.as_uri()}.insteadOf", f"{url}/test/upstream")
            workspace = root / "workspace"
            workspace.mkdir()
            runner_temp = root / "runner"
            runner_temp.mkdir()
            env.update({
                "GITHUB_WORKSPACE": str(workspace), "GITHUB_REPOSITORY": "test/source",
                "GITHUB_EVENT_NAME": "workflow_dispatch", "GITHUB_SERVER_URL": url,
                "RUNNER_TEMP": str(runner_temp), "INPUT_REPOSITORY": "test/upstream",
                "INPUT_PATH": "winget-pkgs", "INPUT_TOKEN": "local-test-only",
                "INPUT_FETCH-DEPTH": "1", "INPUT_CLEAN": "true",
                "INPUT_PERSIST-CREDENTIALS": "false", "INPUT_SET-SAFE-DIRECTORY": "false",
                "INPUT_GITHUB-SERVER-URL": url,
            })
            checkout = workspace / "winget-pkgs"

            def refresh(expected, label):
                result = subprocess.run(["node", str(action)], env=env, cwd=workspace,
                                        capture_output=True, text=True, timeout=60)
                if result.returncode:
                    raise AssertionError(result.stdout + result.stderr)
                assert git(checkout, "rev-parse", "HEAD") == expected, label
                assert git(checkout, "branch", "--show-current") == default_branch, label
                assert "extraheader" not in (checkout / ".git/config").read_text().lower()
                print(f"PASS: {label}", flush=True)

            refresh(commit("cold cache"), "cache miss uses main")
            sentinel = checkout / ".git/cache-reuse-proof"
            sentinel.write_text("keep Git directory")
            snapshot = root / "saved-cache"
            shutil.copytree(checkout, snapshot)
            refresh(commit("same day update"), "exact hit fetches new commit")
            assert sentinel.read_text() == "keep Git directory"
            # Restore the older snapshot at another workspace path, as a later runner does.
            next_workspace = root / "next-workspace"
            next_workspace.mkdir()
            checkout = next_workspace / "winget-pkgs"
            shutil.copytree(snapshot, checkout)
            env["GITHUB_WORKSPACE"] = str(next_workspace)
            git(upstream, "branch", "-m", "release/current")
            default_branch = "release/current"
            refresh(commit("renamed default"), "prefix restore follows changed default branch")
            assert (checkout / ".git/cache-reuse-proof").read_text() == "keep Git directory"
            assert len(requests) == 3, requests
            print("PASS: both restored Git directories reused; credentials removed", flush=True)
        finally:
            server.shutdown()
            server.server_close()
            thread.join()
            print("Checkout smoke API stopped; temporary files will be removed", flush=True)


if __name__ == "__main__":
    main(Path(sys.argv[1]).resolve())
