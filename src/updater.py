import sys
from helper import get_absolute_path
import subprocess
import os
import traceback
import logging
import time
import ctypes
from packaging import version

import json
import urllib.request
import re

log = logging.getLogger(__name__)

GITHUB_REPO = "Mage-Enderman/VRCTextboxSTT"
GITHUB_API_URL = f"https://api.github.com/repos/{GITHUB_REPO}"
REMOTE_GIT_URL = f"https://github.com/{GITHUB_REPO}.git"

class Update_Handler(object):
    """
    Class responsible for handling updates of the application.

    Args:
        git_path (str): The path to the Git executable.
        repo_path (str): The path to the repository.
        script_path (str): The path to the script file.
    """
    def __init__(self, git_path, repo_path: str = "..", script_path: str = __file__):
        self.script_path = script_path
        self.repo_path = repo_path
        self.git_path = git_path
        self.github_repo = GITHUB_REPO
        self.remote_url = REMOTE_GIT_URL
        if not os.path.isfile(self.git_path):
            log.error("Git not found, using default path")
            self.git_path = "git"
        self.startupinfo = subprocess.STARTUPINFO()
        self.startupinfo.dwFlags = subprocess.STARTF_USESHOWWINDOW
        self.startupinfo.wShowWindow = 0
        self.cache_folder = os.path.join(os.path.dirname(sys.executable), "cache")
        self.custom_env = {**os.environ, 'TMPDIR': self.cache_folder}

    def _get_latest_tag_from_github_api(self) -> str:
        """
        Queries the GitHub API for releases or tags on the fork.
        """
        # 1. Try releases/latest
        try:
            req = urllib.request.Request(
                f"{GITHUB_API_URL}/releases/latest",
                headers={"User-Agent": "TextboxSTT-Updater", "Accept": "application/vnd.github.v3+json"}
            )
            with urllib.request.urlopen(req, timeout=5) as resp:
                data = json.loads(resp.read().decode('utf-8'))
                tag = data.get("tag_name")
                if tag and not ("-" in tag):
                    return tag
        except Exception:
            pass

        # 2. Try tags list
        try:
            req = urllib.request.Request(
                f"{GITHUB_API_URL}/tags",
                headers={"User-Agent": "TextboxSTT-Updater", "Accept": "application/vnd.github.v3+json"}
            )
            with urllib.request.urlopen(req, timeout=5) as resp:
                tags_data = json.loads(resp.read().decode('utf-8'))
                highest_tag = None
                for item in tags_data:
                    tag = item.get("name", "")
                    if not tag or "-" in tag:
                        continue
                    try:
                        if highest_tag is None or version.parse(tag) > version.parse(highest_tag):
                            highest_tag = tag
                    except Exception:
                        continue
                if highest_tag:
                    return highest_tag
        except Exception:
            pass

        return None

    def _get_latest_tag_from_git(self) -> str:
        """
        Queries remote or local git tags as a fallback.
        """
        # Try git ls-remote first without needing a local clone
        try:
            result = subprocess.run(
                [self.git_path, "ls-remote", "--tags", self.remote_url],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                startupinfo=self.startupinfo,
                timeout=10
            )
            if result.returncode == 0:
                output = result.stdout.decode('utf-8', errors='ignore')
                highest_tag = None
                for line in output.splitlines():
                    match = re.search(r"refs/tags/([^\^\{\}\s]+)", line)
                    if match:
                        tag = match.group(1)
                        if "-" in tag:
                            continue
                        try:
                            if highest_tag is None or version.parse(tag) > version.parse(highest_tag):
                                highest_tag = tag
                        except Exception:
                            continue
                if highest_tag:
                    return highest_tag
        except Exception:
            pass

        # Try local repo git tag if available
        try:
            self.fetch()
            result = subprocess.run([self.git_path, "tag"], cwd=self.repo_path, stdout=subprocess.PIPE, startupinfo=self.startupinfo)
            tags = result.stdout.decode('utf-8', errors='ignore')
            highest_tag = None
            for tag in tags.splitlines():
                tag = tag.strip()
                if not tag or "-" in tag:
                    continue
                try:
                    if highest_tag is None or version.parse(tag) > version.parse(highest_tag):
                        highest_tag = tag
                except Exception:
                    continue
            return highest_tag
        except Exception:
            log.debug(traceback.format_exc())
            return None

    def get_latest_tag(self) -> str:
        """
        Gets the latest tag from the fork repository.

        Returns:
            str: The latest tag from the repository, or None if no tags exist.
        """
        tag = self._get_latest_tag_from_github_api()
        if tag:
            return tag
        return self._get_latest_tag_from_git()
    
    def check_for_updates(self, current_version: str = None) -> tuple:
        """
        Checks if an update is available on the fork.

        Args:
            current_version (str): The current version of the application.
        
        Returns:
            tuple: (is_update_available: bool, latest_tag: str or None)
        """
        if not current_version:
            return False, None

        latest_tag = self.get_latest_tag()
        log.debug("Latest Tag from fork: " + str(latest_tag))

        if not latest_tag:
            log.debug("No release tags found on fork")
            return False, None

        if "-" in latest_tag and "-" not in current_version:
            return False, None

        try:
            update_available = version.parse(latest_tag) > version.parse(current_version)
        except Exception as e:
            log.debug(f"Failed to parse version ({current_version} vs {latest_tag}): {e}")
            update_available = False

        if update_available:
            log.info(f"Update Available! {current_version} -> {latest_tag}")
        else:
            log.info(f"No Update Available (Current: {current_version}, Latest: {latest_tag})")

        return update_available, latest_tag

    def fetch(self) -> None:
        """
        Fetches the tags from the repository.
        """
        try:
            log.debug("Fetching Tags from fork")
            subprocess.run([self.git_path, "remote", "set-url", "origin", self.remote_url], cwd=self.repo_path, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, startupinfo=self.startupinfo)
            result = subprocess.run([self.git_path, "fetch", "--all", "--tags", "--force"], cwd=self.repo_path, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, startupinfo=self.startupinfo)
            result = result.stdout.decode('utf-8', errors='ignore')
            if result:
                log.debug(result)
        except Exception:
            log.debug(traceback.format_exc())

    def update(self, callback, ui_output) -> None:
        """
        Updates the application.

        Args:
            callback: The callback function to call after the update is finished.
            ui_output: The function to call to output messages to the UI.
        """
        path = get_absolute_path("force_update.bat", self.script_path)
        process = subprocess.Popen([path], creationflags=subprocess.CREATE_NEW_CONSOLE)
        while process.poll() is None:
            ui_output("Updating.")
            time.sleep(0.5)
            ui_output("Updating..")
            time.sleep(0.5)
            ui_output("Updating...")
            time.sleep(0.5)

        if process.returncode != 0:
            ctypes.windll.user32.MessageBoxW(0, "The Update process may have failed, please try again or run `force_update.bat` in the src folder as administator", f"TextboxSTT - Unexpected Error - {str(process.returncode)}", 0)
        else:
            ui_output("Update finished! Restarting...")
            time.sleep(1)
        callback()
