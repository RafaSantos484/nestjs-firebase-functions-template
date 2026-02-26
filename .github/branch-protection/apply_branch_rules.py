#!/usr/bin/env python3
"""
GitHub Branch Protection Rules Applicator

This script applies branch protection rules from JSON files to a GitHub repository.
It supports both legacy branch protection settings and new repository rules.

Usage:
    python3 apply_branch_rules.py --owner YOUR_OWNER --repo YOUR_REPO

Environment:
    GITHUB_TOKEN: GitHub personal access token (required)
    - Scope: 'repo' for private repos, 'public_repo' for public ones
    - Generate at: https://github.com/settings/tokens

Examples:
    # Apply all rules in current directory
    ./apply_branch_rules.py --owner RafaSantos484 --repo nestjs-firebase-functions-template

    # Dry run (preview without applying)
    ./apply_branch_rules.py --owner RafaSantos484 --repo nestjs-firebase-functions-template --dry-run

    # Verbose output
    ./apply_branch_rules.py --owner RafaSantos484 --repo nestjs-firebase-functions-template -v
"""

import json
import os
import sys
import argparse
import requests
from pathlib import Path
from typing import Dict, Any, Optional, List
from dataclasses import dataclass
from datetime import datetime


@dataclass
class Config:
    """Configuration for script execution"""
    owner: str
    repo: str
    github_token: str
    dry_run: bool = False
    verbose: bool = False
    rules_dir: Path = Path(__file__).parent
    api_base: str = "https://api.github.com"
    api_version: str = "2022-11-28"


class GitHubAPI:
    """Wrapper around GitHub REST API"""

    def __init__(self, config: Config):
        self.config = config
        self.session = requests.Session()
        self.session.headers.update({
            "Authorization": f"token {config.github_token}",
            "X-GitHub-Api-Version": config.api_version,
            "Accept": "application/vnd.github+json",
        })

    def _log(self, message: str, level: str = "INFO"):
        """Log message if verbose mode enabled"""
        if self.config.verbose:
            timestamp = datetime.now().strftime("%HH:%MM:%SS")
            print(f"[{timestamp}] [{level}] {message}")

    def _request(
        self,
        method: str,
        endpoint: str,
        json_data: Optional[Dict] = None,
        params: Optional[Dict] = None,
    ) -> requests.Response:
        """Make HTTP request to GitHub API"""
        url = f"{self.config.api_base}/{endpoint}"
        kwargs = {"params": params} if params else {}

        if json_data:
            kwargs["json"] = json_data

        self._log(f"{method} {endpoint}", "API")

        response = self.session.request(method, url, **kwargs)
        response.raise_for_status()
        return response

    def get_repository_rules(self) -> List[Dict[str, Any]]:
        """Get all repository rules"""
        endpoint = f"repos/{self.config.owner}/{self.config.repo}/rules"
        response = self._request("GET", endpoint)
        return response.json()

    def get_repository_rule(self, rule_id: int) -> Dict[str, Any]:
        """Get a specific repository rule by ID"""
        endpoint = f"repos/{self.config.owner}/{self.config.repo}/rules/{rule_id}"
        response = self._request("GET", endpoint)
        return response.json()

    def create_repository_rule(self, rule_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create a new repository rule"""
        endpoint = f"repos/{self.config.owner}/{self.config.repo}/rules"

        # Remove auto-generated fields
        payload = {k: v for k, v in rule_data.items() if k not in ["id"]}

        if self.config.dry_run:
            self._log(f"DRY RUN: Would create rule '{payload.get('name')}'", "WARN")
            return {**payload, "id": 0}

        response = self._request("POST", endpoint, json_data=payload)
        self._log(f"✅ Created rule: {payload.get('name')}", "SUCCESS")
        return response.json()

    def update_repository_rule(self, rule_id: int, rule_data: Dict[str, Any]) -> Dict[str, Any]:
        """Update an existing repository rule"""
        endpoint = f"repos/{self.config.owner}/{self.config.repo}/rules/{rule_id}"

        # Remove auto-generated fields
        payload = {k: v for k, v in rule_data.items() if k not in ["id"]}

        if self.config.dry_run:
            self._log(f"DRY RUN: Would update rule '{payload.get('name')}'", "WARN")
            return {**payload, "id": rule_id}

        response = self._request("PATCH", endpoint, json_data=payload)
        self._log(f"✅ Updated rule: {payload.get('name')}", "SUCCESS")
        return response.json()

    def delete_repository_rule(self, rule_id: int, rule_name: str = ""):
        """Delete a repository rule"""
        endpoint = f"repos/{self.config.owner}/{self.config.repo}/rules/{rule_id}"

        if self.config.dry_run:
            self._log(f"DRY RUN: Would delete rule '{rule_name}'", "WARN")
            return

        self._request("DELETE", endpoint)
        self._log(f"✅ Deleted rule: {rule_name}", "SUCCESS")


class BranchRulesManager:
    """Manages branch protection rules"""

    def __init__(self, config: Config):
        self.config = config
        self.api = GitHubAPI(config)

    def _find_rule_by_name(self, rules: List[Dict], name: str) -> Optional[Dict]:
        """Find rule by name"""
        for rule in rules:
            if rule.get("name") == name:
                return rule
        return None

    def _rules_are_equal(self, rule1: Dict, rule2: Dict) -> bool:
        """Check if two rule definitions are equal (ignoring ID and timestamps)"""
        compare_keys = {"name", "description", "conditions", "rules", "enforcement"}
        for key in compare_keys:
            if rule1.get(key) != rule2.get(key):
                return False
        return True

    def load_rule_file(self, file_path: Path) -> Dict[str, Any]:
        """Load and parse a rule JSON file"""
        self.api._log(f"Loading rule file: {file_path}")

        with open(file_path, "r") as f:
            rule = json.load(f)

        # Validate required fields
        required_fields = ["name", "target", "conditions", "rules"]
        for field in required_fields:
            if field not in rule:
                raise ValueError(f"Missing required field in {file_path}: {field}")

        return rule

    def apply_rules_from_directory(self) -> None:
        """Apply all .json files from rules directory"""
        json_files = sorted(self.config.rules_dir.glob("*.json"))

        if not json_files:
            print(f"⚠️  No JSON files found in {self.config.rules_dir}")
            return

        print(f"\n📋 Found {len(json_files)} rule file(s):")
        for f in json_files:
            print(f"   - {f.name}")

        print(f"\n🔄 Fetching existing rules from GitHub...")
        try:
            existing_rules = self.api.get_repository_rules()
            print(f"✅ Found {len(existing_rules)} existing rule(s)")
        except requests.exceptions.RequestException as e:
            print(f"❌ Error fetching existing rules: {e}")
            return

        print(f"\n📝 Processing rules...\n")

        for json_file in json_files:
            self._apply_single_rule(json_file, existing_rules)

    def _apply_single_rule(self, file_path: Path, existing_rules: List[Dict]) -> None:
        """Apply a single rule file"""
        try:
            rule_data = self.load_rule_file(file_path)
            rule_name = rule_data.get("name")

            print(f"📌 Processing: {file_path.name}")
            self.api._log(f"Rule: {rule_name}", "INFO")

            # Check if rule already exists
            existing_rule = self._find_rule_by_name(existing_rules, rule_name)

            if existing_rule:
                # Check if rules are different
                if self._rules_are_equal(rule_data, existing_rule):
                    print(f"   ✅ Rule '{rule_name}' already up-to-date")
                    self.api._log(f"Rule unchanged, skipping update", "INFO")
                else:
                    print(f"   🔄 Updating existing rule '{rule_name}'...")
                    self.api.update_repository_rule(existing_rule["id"], rule_data)
                    print(f"   ✅ Rule updated successfully")
            else:
                print(f"   ➕ Creating new rule '{rule_name}'...")
                self.api.create_repository_rule(rule_data)
                print(f"   ✅ Rule created successfully")

        except json.JSONDecodeError as e:
            print(f"   ❌ Invalid JSON in {file_path.name}: {e}")
        except ValueError as e:
            print(f"   ❌ Validation error in {file_path.name}: {e}")
        except requests.exceptions.RequestException as e:
            print(f"   ❌ API error: {e}")
        except Exception as e:
            print(f"   ❌ Unexpected error: {e}")

        print()


def validate_token(token: str) -> bool:
    """Validate GitHub token by making a test request"""
    headers = {
        "Authorization": f"token {token}",
        "Accept": "application/vnd.github+json",
    }

    try:
        response = requests.get(
            "https://api.github.com/user",
            headers=headers,
            timeout=5
        )
        return response.status_code == 200
    except requests.exceptions.RequestException:
        return False


def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(
        description="Apply GitHub branch protection rules from JSON files",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )

    parser.add_argument(
        "--owner",
        required=True,
        help="GitHub repository owner/organization",
    )
    parser.add_argument(
        "--repo",
        required=True,
        help="GitHub repository name",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Preview changes without applying them",
    )
    parser.add_argument(
        "-v", "--verbose",
        action="store_true",
        help="Enable verbose output",
    )
    parser.add_argument(
        "--rules-dir",
        type=Path,
        default=Path(__file__).parent,
        help="Directory containing JSON rule files (default: script directory)",
    )

    args = parser.parse_args()

    # Get token from environment
    token = os.getenv("GITHUB_TOKEN")
    if not token:
        print("❌ Error: GITHUB_TOKEN environment variable not set")
        print("   Generate a token at: https://github.com/settings/tokens")
        sys.exit(1)

    # Validate token
    print("🔐 Validating GitHub token...")
    if not validate_token(token):
        print("❌ Error: Invalid GitHub token")
        sys.exit(1)
    print("✅ Token valid")

    # Create config and manager
    config = Config(
        owner=args.owner,
        repo=args.repo,
        github_token=token,
        dry_run=args.dry_run,
        verbose=args.verbose,
        rules_dir=args.rules_dir,
    )

    print(f"\n📦 Repository: {config.owner}/{config.repo}")
    if config.dry_run:
        print("   Mode: DRY-RUN (no changes will be made)")
    print()

    # Apply rules
    manager = BranchRulesManager(config)
    try:
        manager.apply_rules_from_directory()
        print("✨ Done!")
    except KeyboardInterrupt:
        print("\n⚠️  Interrupted by user")
        sys.exit(130)
    except Exception as e:
        print(f"❌ Fatal error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
