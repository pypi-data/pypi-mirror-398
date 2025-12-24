"""
PyAttackForge is free software: you can redistribute it and/or modify
it under the terms of the GNU Affero General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

PyAttackForge is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU Affero General Public License for more details.

You should have received a copy of the GNU Affero General Public License
along with this program.  If not, see <https://www.gnu.org/licenses/>.
"""

import requests
import logging
from datetime import datetime, timezone, timedelta
from typing import Any, Dict, Optional, Set, Tuple, List


logger = logging.getLogger("pyattackforge")


class PyAttackForgeClient:
    """
    Python client for interacting with the AttackForge API.

    Provides methods to manage assets, projects, and vulnerabilities.
    Supports dry-run mode for testing without making real API calls.
    """

    def __init__(self, api_key: str, base_url: str = "https://demo.attackforge.com", dry_run: bool = False):
        """
        Initialize the PyAttackForgeClient.

        Args:
            api_key (str): Your AttackForge API key.
            base_url (str, optional): The base URL for the AttackForge instance. Defaults to "https://demo.attackforge.com".
            dry_run (bool, optional): If True, no real API calls are made. Defaults to False.
        """
        self.base_url = base_url.rstrip("/")
        self.headers = {
            "X-SSAPI-KEY": api_key,
            "Content-Type": "application/json",
            "Connection": "close"
        }
        self.dry_run = dry_run
        self._asset_cache = None
        self._project_scope_cache = {}  # {project_id: set(asset_names)}

    def _request(
        self,
        method: str,
        endpoint: str,
        json_data: Optional[Dict[str, Any]] = None,
        params: Optional[Dict[str, Any]] = None
    ) -> Any:
        """
        Internal method to send an HTTP request to the AttackForge API.

        Args:
            method (str): HTTP method (get, post, put, etc.).
            endpoint (str): API endpoint path.
            json_data (dict, optional): JSON payload for the request.
            params (dict, optional): Query parameters.

        Returns:
            Response: The HTTP response object.
        """
        url = f"{self.base_url}{endpoint}"
        if self.dry_run:
            logger.info("[DRY RUN] %s %s", method.upper(), url)
            if json_data:
                logger.info("Payload: %s", json_data)
            if params:
                logger.info("Params: %s", params)
            return DummyResponse()
        return requests.request(method, url, headers=self.headers, json=json_data, params=params)

    def get_assets(self) -> Dict[str, Dict[str, Any]]:
        """
        Retrieve all assets from AttackForge.

        Returns:
            dict: Mapping of asset names to asset details.
        """
        if self._asset_cache is None:
            self._asset_cache = {}
            skip, limit = 0, 500
            while True:
                resp = self._request("get", "/api/ss/assets", params={"skip": skip, "limit": limit})
                data = resp.json()
                for asset in data.get("assets", []):
                    name = asset.get("asset")
                    if name:
                        self._asset_cache[name] = asset
                if skip + limit >= data.get("count", 0):
                    break
                skip += limit
        return self._asset_cache

    def get_asset_by_name(self, name: str) -> Optional[Dict[str, Any]]:
        """
        Retrieve an asset by its name.

        Args:
            name (str): The asset name.

        Returns:
            dict or None: Asset details if found, else None.
        """
        return self.get_assets().get(name)

    def create_asset(self, asset_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Create a new asset in AttackForge.

        Args:
            asset_data (dict): Asset details.

        Returns:
            dict: Created asset details.

        Raises:
            RuntimeError: If asset creation fails.
        """
        resp = self._request("post", "/api/ss/library/asset", json_data=asset_data)
        if resp.status_code in (200, 201):
            asset = resp.json()
            self._asset_cache = None  # Invalidate cache
            return asset
        if "Asset Already Exists" in resp.text:
            return self.get_asset_by_name(asset_data["name"])
        raise RuntimeError(f"Asset creation failed: {resp.text}")

    def get_project_by_name(self, name: str) -> Optional[Dict[str, Any]]:
        """
        Retrieve a project by its name.

        Args:
            name (str): The project name.

        Returns:
            dict or None: Project details if found, else None.
        """
        params = {
            "startDate": "2000-01-01T00:00:00.000Z",
            "endDate": "2100-01-01T00:00:00.000Z",
            "status": "All"
        }
        resp = self._request("get", "/api/ss/projects", params=params)
        for proj in resp.json().get("projects", []):
            if proj.get("project_name") == name:
                return proj
        return None

    def get_project_scope(self, project_id: str) -> Set[str]:
        """
        Retrieve the scope (assets) of a project.

        Args:
            project_id (str): The project ID.

        Returns:
            set: Set of asset names in the project scope.

        Raises:
            RuntimeError: If project retrieval fails.
        """
        if project_id in self._project_scope_cache:
            return self._project_scope_cache[project_id]

        resp = self._request("get", f"/api/ss/project/{project_id}")
        if resp.status_code != 200:
            raise RuntimeError(f"Failed to retrieve project: {resp.text}")

        scope = set(resp.json().get("scope", []))
        self._project_scope_cache[project_id] = scope
        return scope

    def update_project_scope(self, project_id: str, new_assets: List[str]) -> Dict[str, Any]:
        """
        Update the scope (assets) of a project.

        Args:
            project_id (str): The project ID.
            new_assets (iterable): Asset names to add to the scope.

        Returns:
            dict: Updated project details.

        Raises:
            RuntimeError: If update fails.
        """
        current_scope = self.get_project_scope(project_id)
        updated_scope = list(current_scope.union(new_assets))
        resp = self._request("put", f"/api/ss/project/{project_id}", json_data={"scope": updated_scope})
        if resp.status_code not in (200, 201):
            raise RuntimeError(f"Failed to update project scope: {resp.text}")
        self._project_scope_cache[project_id] = set(updated_scope)
        return resp.json()

    def create_project(self, name: str, **kwargs) -> Dict[str, Any]:
        """
        Create a new project in AttackForge.

        Args:
            name (str): Project name.
            **kwargs: Additional project fields.

        Returns:
            dict: Created project details.

        Raises:
            RuntimeError: If project creation fails.
        """
        start, end = get_default_dates()
        payload = {
            "name": name,
            "code": kwargs.get("code", "DEFAULT"),
            "groups": kwargs.get("groups", []),
            "startDate": kwargs.get("startDate", start),
            "endDate": kwargs.get("endDate", end),
            "scope": kwargs.get("scope", []),
            "testsuites": kwargs.get("testsuites", []),
            "organization_code": kwargs.get("organization_code", "ORG_DEFAULT"),
            "vulnerability_code": kwargs.get("vulnerability_code", "VULN_"),
            "scoringSystem": kwargs.get("scoringSystem", "CVSSv3.1"),
            "team_notifications": kwargs.get("team_notifications", []),
            "admin_notifications": kwargs.get("admin_notifications", []),
            "custom_fields": kwargs.get("custom_fields", []),
            "asset_library_ids": kwargs.get("asset_library_ids", []),
            "sla_activation": kwargs.get("sla_activation", "automatic")
        }
        resp = self._request("post", "/api/ss/project", json_data=payload)
        if resp.status_code in (200, 201):
            return resp.json()
        raise RuntimeError(f"Project creation failed: {resp.text}")

    def update_project(self, project_id: str, update_fields: Dict[str, Any]) -> Dict[str, Any]:
        """
        Update an existing project.

        Args:
            project_id (str): The project ID.
            update_fields (dict): Fields to update.

        Returns:
            dict: Updated project details.

        Raises:
            RuntimeError: If update fails.
        """
        resp = self._request("put", f"/api/ss/project/{project_id}", json_data=update_fields)
        if resp.status_code in (200, 201):
            return resp.json()
        raise RuntimeError(f"Project update failed: {resp.text}")

    def create_vulnerability(
        self,
        project_id: str,
        title: str,
        affected_asset_name: str,
        priority: str,
        likelihood_of_exploitation: int,
        description: str,
        attack_scenario: str,
        remediation_recommendation: str,
        steps_to_reproduce: str,
        tags: Optional[list] = None,
        notes: Optional[list] = None,
        is_zeroday: bool = False,
        is_visible: bool = True,
        import_to_library: Optional[str] = None,
        import_source: Optional[str] = None,
        import_source_id: Optional[str] = None,
        custom_fields: Optional[list] = None,
        linked_testcases: Optional[list] = None,
        custom_tags: Optional[list] = None,
    ) -> Dict[str, Any]:
        """
        Create a new security finding (vulnerability) in AttackForge.

        Args:
            project_id (str): The project ID.
            title (str): The title of the finding.
            affected_asset_name (str): The name of the affected asset.
            priority (str): The priority (e.g., "Critical").
            likelihood_of_exploitation (int): Likelihood of exploitation (e.g., 10).
            description (str): Description of the finding.
            attack_scenario (str): Attack scenario details.
            remediation_recommendation (str): Remediation recommendation.
            steps_to_reproduce (str): Steps to reproduce the finding.
            tags (list, optional): List of tags.
            notes (list, optional): List of notes.
            is_zeroday (bool, optional): Whether this is a zero-day finding.
            is_visible (bool, optional): Whether the finding is visible.
            import_to_library (str, optional): Library to import to.
            import_source (str, optional): Source of import.
            import_source_id (str, optional): Source ID for import.
            custom_fields (list, optional): List of custom fields.
            linked_testcases (list, optional): List of linked testcases.
            custom_tags (list, optional): List of custom tags.

        Returns:
            dict: Created vulnerability details.

        Raises:
            ValueError: If any required field is missing.
            RuntimeError: If vulnerability creation fails.
        """
        # Validate required fields
        required_fields = [
            ("project_id", project_id),
            ("title", title),
            ("affected_asset_name", affected_asset_name),
            ("priority", priority),
            ("likelihood_of_exploitation", likelihood_of_exploitation),
            ("description", description),
            ("attack_scenario", attack_scenario),
            ("remediation_recommendation", remediation_recommendation),
            ("steps_to_reproduce", steps_to_reproduce),
        ]
        for field_name, value in required_fields:
            if value is None:
                raise ValueError(f"Missing required field: {field_name}")

        payload = {
            "projectId": project_id,
            "title": title,
            "affected_asset_name": affected_asset_name,
            "priority": priority,
            "likelihood_of_exploitation": likelihood_of_exploitation,
            "description": description,
            "attack_scenario": attack_scenario,
            "remediation_recommendation": remediation_recommendation,
            "steps_to_reproduce": steps_to_reproduce,
            "tags": tags or [],
            "is_zeroday": is_zeroday,
            "is_visible": is_visible,
            "import_to_library": import_to_library,
            "import_source": import_source,
            "import_source_id": import_source_id,
            "custom_fields": custom_fields or [],
            "linked_testcases": linked_testcases or [],
            "custom_tags": custom_tags or [],
        }
        # Only include notes if it is a non-empty list
        if notes:
            payload["notes"] = notes

        # Remove None values (for optional fields)
        payload = {k: v for k, v in payload.items() if v is not None}

        resp = self._request("post", "/api/ss/vulnerability", json_data=payload)
        if resp.status_code in (200, 201):
            return resp.json()
        raise RuntimeError(f"Vulnerability creation failed: {resp.text}")


class DummyResponse:
    """
    Dummy response object for dry-run mode.
    """
    def __init__(self) -> None:
        self.status_code = 200
        self.text = "[DRY RUN] No real API call performed."

    def json(self) -> Dict[str, Any]:
        return {}


def get_default_dates() -> Tuple[str, str]:
    """
    Get default start and end dates for a project (now and 30 days from now, in ISO format).

    Returns:
        tuple: (start_date, end_date) as ISO 8601 strings.
    """
    now = datetime.now(timezone.utc)
    start = now.isoformat(timespec="milliseconds").replace("+00:00", "Z")
    end = (now + timedelta(days=30)).isoformat(timespec="milliseconds").replace("+00:00", "Z")
    return start, end
