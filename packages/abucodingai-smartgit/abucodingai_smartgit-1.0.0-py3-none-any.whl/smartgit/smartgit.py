"""SmartGit core implementation"""

import os
import json
import subprocess
from pathlib import Path
from datetime import datetime
from typing import Optional, List, Dict, Any


class SmartGit:
    """Main SmartGit class for Git automation"""

    def __init__(self, path: Optional[str] = None):
        self.cwd = path or os.getcwd()
        self.metadata_file = ".smartgit.json"

    def all(self, no_version: bool = False, no_deploy: bool = False) -> None:
        """Complete workflow: create repo, deploy, version"""
        try:
            project_name = self._detect_project_name()
            if not project_name:
                print("Deploy/Repo Creation Failed")
                return

            # Create repo
            self._create_repo(project_name)

            # Deploy if not disabled
            if not no_deploy:
                self._deploy(project_name)

            # Version if not disabled
            if not no_version:
                version_number = self._get_version_from_env() or "v1.0.0"
                self._create_version(project_name, version_number)

            print("Repo Live")
            print(f"Deploy live at https://abucodingai.github.io/{project_name}")
        except Exception as e:
            print("Deploy/Repo Creation Failed")

    def repo(self, project_name: str) -> None:
        """Create a new repository"""
        try:
            self._create_repo(project_name)
            print("Repo Live")
        except Exception as e:
            print("Repo Creation Failed")

    def ignore(self, files: List[str]) -> None:
        """Add files to .gitignore"""
        try:
            gitignore_path = os.path.join(self.cwd, ".gitignore")
            content = ""

            if os.path.exists(gitignore_path):
                with open(gitignore_path, "r") as f:
                    content = f.read()

            files_to_ignore = "\n".join(files)
            content += ("\n" if content else "") + files_to_ignore

            with open(gitignore_path, "w") as f:
                f.write(content)

            print("✅ Files ignored")
        except Exception as e:
            print("Ignore Failed")

    def include(self, files: List[str]) -> None:
        """Remove files from .gitignore"""
        try:
            gitignore_path = os.path.join(self.cwd, ".gitignore")

            if not os.path.exists(gitignore_path):
                print("✅ Files included")
                return

            with open(gitignore_path, "r") as f:
                content = f.read()

            for file in files:
                lines = content.split("\n")
                lines = [line for line in lines if line.strip() != file.strip()]
                content = "\n".join(lines)

            with open(gitignore_path, "w") as f:
                f.write(content)

            print("✅ Files included")
        except Exception as e:
            print("Include Failed")

    def version(
        self, project_name: str, version_name: str, files: Optional[List[str]] = None
    ) -> None:
        """Create a version"""
        try:
            self._create_version(project_name, version_name, files)
            print(f"✅ Version {version_name} created")
        except Exception as e:
            print("Version Creation Failed")

    def addfile(
        self, project_name: str, version_name: str, files: List[str]
    ) -> None:
        """Add files to existing version"""
        try:
            project_path = os.path.join(self.cwd, project_name)
            metadata = self._load_metadata(project_path)

            version = next(
                (v for v in metadata.get("versions", []) if v["version"] == version_name),
                None,
            )

            if not version:
                print("Version not found")
                return

            new_files = [f.strip() for f in files]
            version["files"] = list(set(version["files"] + new_files))

            self._save_metadata(metadata, project_path)
            print(f"✅ Files added to {version_name}")
        except Exception as e:
            print("Add File Failed")

    def lab(self, project_name: Optional[str] = None) -> None:
        """Activate GitLab mode"""
        try:
            project_path = os.path.join(self.cwd, project_name) if project_name else self.cwd
            metadata = self._load_metadata(project_path)
            metadata["gitLabMode"] = True
            self._save_metadata(metadata, project_path)
            print("✅ GitLab mode activated")
        except Exception as e:
            print("GitLab Activation Failed")

    def shortcut(self, shortcut_name: str, command: str) -> None:
        """Create a shortcut"""
        try:
            metadata = self._load_metadata()
            metadata["shortcuts"][shortcut_name] = command
            self._save_metadata(metadata)

            # Create batch file for Windows
            batch_path = os.path.join(self.cwd, f"{shortcut_name}.bat")
            with open(batch_path, "w") as f:
                f.write(f"@echo off\nsmartgit {command} %*")

            print(f"✅ Shortcut created: {shortcut_name}")
        except Exception as e:
            print("Shortcut Creation Failed")

    def _create_repo(self, project_name: str) -> None:
        """Create a git repository"""
        project_path = os.path.join(self.cwd, project_name)

        if os.path.exists(project_path):
            raise Exception(f"Repository already exists: {project_path}")

        os.makedirs(project_path, exist_ok=True)

        # Initialize git
        subprocess.run(["git", "init"], cwd=project_path, check=True, capture_output=True)

        # Create metadata file
        metadata = {
            "name": project_name,
            "versions": [],
            "gitLabMode": False,
            "shortcuts": {},
        }

        metadata_path = os.path.join(project_path, self.metadata_file)
        with open(metadata_path, "w") as f:
            json.dump(metadata, f, indent=2)

        # Create initial commit
        subprocess.run(
            ["git", "add", "-A"], cwd=project_path, check=True, capture_output=True
        )
        subprocess.run(
            ["git", "commit", "-m", "Initial commit"],
            cwd=project_path,
            check=True,
            capture_output=True,
        )

    def _deploy(self, project_name: str) -> None:
        """Deploy to GitHub Pages"""
        project_path = os.path.join(self.cwd, project_name)

        if not os.path.exists(project_path):
            raise Exception(f"Project not found: {project_path}")

        try:
            # Check if gh-pages branch exists
            result = subprocess.run(
                ["git", "rev-parse", "--verify", "gh-pages"],
                cwd=project_path,
                capture_output=True,
            )

            if result.returncode == 0:
                subprocess.run(
                    ["git", "checkout", "gh-pages"],
                    cwd=project_path,
                    check=True,
                    capture_output=True,
                )
            else:
                # Create orphan branch
                subprocess.run(
                    ["git", "checkout", "--orphan", "gh-pages"],
                    cwd=project_path,
                    check=True,
                    capture_output=True,
                )
                try:
                    subprocess.run(
                        ["git", "rm", "-rf", "."],
                        cwd=project_path,
                        check=True,
                        capture_output=True,
                    )
                except:
                    pass

            # Add all files
            subprocess.run(
                ["git", "add", "-A"], cwd=project_path, check=True, capture_output=True
            )

            # Commit
            message = f"Deploy: {datetime.now().isoformat()}"
            try:
                subprocess.run(
                    ["git", "commit", "-m", message],
                    cwd=project_path,
                    check=True,
                    capture_output=True,
                )
            except:
                pass

            # Push
            subprocess.run(
                ["git", "push", "-u", "origin", "gh-pages", "--force"],
                cwd=project_path,
                check=True,
                capture_output=True,
            )
        except Exception as e:
            raise Exception(f"Deployment failed: {e}")

    def _create_version(
        self,
        project_name: str,
        version_name: str,
        files: Optional[List[str]] = None,
    ) -> None:
        """Create a version"""
        project_path = os.path.join(self.cwd, project_name)
        metadata = self._load_metadata(project_path)

        version_info = {
            "version": version_name,
            "files": files or ["all"],
            "createdAt": datetime.now().isoformat(),
        }

        metadata["versions"].append(version_info)
        self._save_metadata(metadata, project_path)

    def _detect_project_name(self) -> Optional[str]:
        """Detect project name from main HTML file"""
        files = os.listdir(self.cwd)
        html_files = [f for f in files if f.endswith(".html")]

        if not html_files:
            return None

        if "index.html" in html_files:
            return "index"

        return html_files[0].replace(".html", "")

    def _get_version_from_env(self) -> Optional[str]:
        """Get version from .env or package.json"""
        try:
            # Check .env file
            env_path = os.path.join(self.cwd, ".env")
            if os.path.exists(env_path):
                with open(env_path, "r") as f:
                    for line in f:
                        if line.startswith("VERSION="):
                            return line.split("=")[1].strip()

            # Check package.json
            package_path = os.path.join(self.cwd, "package.json")
            if os.path.exists(package_path):
                with open(package_path, "r") as f:
                    package = json.load(f)
                    if "version" in package:
                        return f"v{package['version']}"

            return None
        except:
            return None

    def _load_metadata(self, project_path: Optional[str] = None) -> Dict[str, Any]:
        """Load metadata"""
        path = project_path or self.cwd
        metadata_path = os.path.join(path, self.metadata_file)

        if not os.path.exists(metadata_path):
            return {
                "name": "project",
                "versions": [],
                "gitLabMode": False,
                "shortcuts": {},
            }

        with open(metadata_path, "r") as f:
            return json.load(f)

    def _save_metadata(
        self, metadata: Dict[str, Any], project_path: Optional[str] = None
    ) -> None:
        """Save metadata"""
        path = project_path or self.cwd
        metadata_path = os.path.join(path, self.metadata_file)

        with open(metadata_path, "w") as f:
            json.dump(metadata, f, indent=2)
