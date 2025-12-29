# src/xenfra/mcp_client.py

import json
import subprocess
import os
import tempfile
import base64
from pathlib import Path

class MCPClient:
    """
    A client for communicating with a local github-mcp-server process.

    This client starts the MCP server as a subprocess and interacts with it
    over stdin and stdout to download a full repository to a temporary directory.
    """

    def __init__(self, mcp_server_path="github-mcp-server"):
        """
        Initializes the MCPClient.

        Args:
            mcp_server_path (str): The path to the github-mcp-server executable.
                                   Assumes it's in the system's PATH by default.
        """
        self.mcp_server_path = mcp_server_path
        self.process = None

    def _start_server(self):
        """Starts the github-mcp-server subprocess."""
        if self.process and self.process.poll() is None:
            return
        try:
            self.process = subprocess.Popen(
                [self.mcp_server_path],
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                env=os.environ
            )
        except FileNotFoundError:
            raise RuntimeError(f"'{self.mcp_server_path}' not found. Ensure github-mcp-server is installed and in your PATH.")
        except Exception as e:
            raise RuntimeError(f"Failed to start MCP server: {e}")

    def _stop_server(self):
        """Stops the MCP server process."""
        if self.process:
            self.process.terminate()
            self.process.wait()
            self.process = None

    def _send_request(self, method: str, params: dict) -> dict:
        """Sends a JSON-RPC request and returns the response."""
        if not self.process or self.process.poll() is not None:
            self._start_server()

        request = {"jsonrpc": "2.0", "id": os.urandom(4).hex(), "method": method, "params": params}
        
        try:
            self.process.stdin.write(json.dumps(request) + '\n')
            self.process.stdin.flush()
            response_line = self.process.stdout.readline()
            if not response_line:
                error_output = self.process.stderr.read()
                raise RuntimeError(f"MCP server closed stream unexpectedly. Error: {error_output}")
            
            response = json.loads(response_line)
            if "error" in response:
                raise RuntimeError(f"MCP server returned an error: {response['error']}")
            return response.get("result", {})
        except (BrokenPipeError, json.JSONDecodeError) as e:
            raise RuntimeError(f"Failed to communicate with MCP server: {e}")

    def download_repo_to_tempdir(self, repo_url: str, commit_sha: str = "HEAD") -> str:
        """
        Downloads an entire repository at a specific commit to a local temporary directory.

        Args:
            repo_url (str): The full URL of the GitHub repository.
            commit_sha (str): The commit SHA to download. Defaults to "HEAD".

        Returns:
            The path to the temporary directory containing the downloaded code.
        """
        try:
            parts = repo_url.strip('/').split('/')
            owner = parts[-2]
            repo_name = parts[-1].replace('.git', '')
        except IndexError:
            raise ValueError("Invalid repository URL format. Expected format: https://github.com/owner/repo")

        print(f"   [MCP] Fetching file tree for {owner}/{repo_name} at {commit_sha}...")
        tree_result = self._send_request(
            method="git.get_repository_tree",
            params={"owner": owner, "repo": repo_name, "tree_sha": commit_sha, "recursive": True}
        )

        tree = tree_result.get("tree", [])
        if not tree:
            raise RuntimeError("Could not retrieve repository file tree.")

        temp_dir = tempfile.mkdtemp(prefix=f"xenfra_{repo_name}_")
        print(f"   [MCP] Downloading to temporary directory: {temp_dir}")

        for item in tree:
            item_path = item.get("path")
            item_type = item.get("type")

            if not item_path or item_type != "blob":  # Only handle files
                continue
            
            # For downloading content, we can use the commit_sha in the 'ref' parameter
            # to ensure we get the content from the correct version.
            content_result = self._send_request(
                method="repos.get_file_contents",
                params={"owner": owner, "repo": repo_name, "path": item_path, "ref": commit_sha}
            )

            content_b64 = content_result.get("content")
            if content_b64 is None:
                print(f"   [MCP] [Warning] Could not get content for {item_path}")
                continue

            try:
                # Content is base64 encoded, with newlines.
                decoded_content = base64.b64decode(content_b64.replace('\n', ''))
            except (base64.binascii.Error, TypeError):
                print(f"   [MCP] [Warning] Could not decode content for {item_path}")
                continue

            # Create file and parent directories in the temp location
            local_file_path = Path(temp_dir) / item_path
            local_file_path.parent.mkdir(parents=True, exist_ok=True)
            
            # Write the file content
            with open(local_file_path, "wb") as f:
                f.write(decoded_content)

        print("   [MCP] ✅ Repository download complete.")
        return temp_dir

    def __enter__(self):
        self._start_server()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self._stop_server()