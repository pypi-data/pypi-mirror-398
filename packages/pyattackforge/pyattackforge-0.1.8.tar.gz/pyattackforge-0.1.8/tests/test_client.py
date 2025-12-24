import os
import tempfile
import unittest
from pyattackforge import PyAttackForgeClient


class TestPyAttackForgeClient(unittest.TestCase):
    def setUp(self):
        # Use dummy values for dry-run mode
        self.client = PyAttackForgeClient(api_key="dummy", dry_run=True)
        # Patch create_asset to return a dummy dict
        self.client.create_asset = lambda asset_data: {
            "name": asset_data.get("name", "DummyAsset")
        }

    def test_get_assets_dry_run(self):
        assets = self.client.get_assets()
        self.assertIsInstance(assets, dict)

    def test_create_asset_dry_run(self):
        asset = self.client.create_asset({"name": "TestAsset"})
        self.assertIsInstance(asset, dict)

    def test_get_project_by_name_dry_run(self):
        project = self.client.get_project_by_name("TestProject")
        self.assertIsNone(project)

    def test_create_project_dry_run(self):
        project = self.client.create_project("TestProject")
        self.assertIsInstance(project, dict)

    def test_create_vulnerability_dry_run(self):
        # Patch get_all_writeups to return a matching writeup for this test
        self.client.get_all_writeups = (
            lambda force_refresh=False: [
                {
                    "title": "Test Vuln",
                    "belongs_to_library": "Main Vulnerabilities",
                    "reference_id": "dummy_writeup_id",
                }
            ]
        )
        self.client.create_writeup = lambda **kwargs: {"reference_id": "dummy_writeup_id"}
        vuln = self.client.create_vulnerability(
            project_id="dummy",
            title="Test Vuln",
            affected_assets=[{"name": "TestAsset"}],
            priority="High",
            likelihood_of_exploitation=5,
            description="Test description",
            attack_scenario="Test scenario",
            remediation_recommendation="Test remediation",
            steps_to_reproduce="Step 1"
        )
        self.assertIsInstance(vuln, dict)

    def test_create_vulnerability_with_import_source_and_writeup_custom_fields(self):
        # Patch get_all_writeups to return a matching writeup for this test
        self.client.get_all_writeups = (
            lambda force_refresh=False: [
                {
                    "title": "Test Vuln 2",
                    "belongs_to_library": "Main Vulnerabilities",
                    "reference_id": "dummy_writeup_id",
                }
            ]
        )
        self.client.create_writeup = lambda **kwargs: {"reference_id": "dummy_writeup_id"}
        vuln = self.client.create_vulnerability(
            project_id="dummy",
            title="Test Vuln 2",
            affected_assets=[
                {"name": "TestAsset2"},
                {"name": "TestAsset3"}
            ],
            priority="Medium",
            likelihood_of_exploitation=3,
            description="Another test description",
            attack_scenario="Another scenario",
            remediation_recommendation="Another remediation",
            steps_to_reproduce="Step A",
            import_source="UnitTestSource",
            writeup_custom_fields=[
                {"key": "extra_info", "value": "unit test"}
            ]
        )
        self.assertIsInstance(vuln, dict)

    def test_create_vulnerability_with_existing_writeup_id(self):
        # Ensure the client uses the provided writeup_id and does not attempt to create/search
        self.client.get_all_writeups = lambda force_refresh=False: []
        self.client.find_writeup_in_cache = lambda title, library="Main Vulnerabilities": None
        captured = {"endpoints": []}

        def fake_create_from_writeup(**kwargs):
            captured.update(kwargs)
            return {"created": True, "writeup_id": kwargs.get("writeup_id")}

        self.client.create_finding_from_writeup = fake_create_from_writeup
        vuln = self.client.create_vulnerability(
            project_id="dummy",
            title="Existing Writeup Vuln",
            affected_assets=[{"name": "AssetExisting"}],
            priority="High",
            likelihood_of_exploitation=5,
            description="desc",
            attack_scenario="scenario",
            remediation_recommendation="remed",
            steps_to_reproduce="steps",
            writeup_id="writeup-123"
        )
        self.assertEqual(vuln.get("writeup_id"), "writeup-123")
        self.assertEqual(captured.get("writeup_id"), "writeup-123")
        assets = captured.get("affected_assets", [])
        self.assertEqual(assets, [{"assetName": "AssetExisting"}])

    def test_create_vulnerability_old_dry_run(self):
        vuln = self.client.create_vulnerability_old(
            project_id="dummy",
            title="Legacy Vuln",
            affected_asset_name="LegacyAsset",
            priority="Low",
            likelihood_of_exploitation=1,
            description="Legacy description",
            attack_scenario="Legacy scenario",
            remediation_recommendation="Legacy remediation",
            steps_to_reproduce="Legacy step"
        )
        self.assertIsInstance(vuln, dict)

    def test_create_writeup_dry_run(self):
        writeup = self.client.create_writeup(
            title="SQL Injection",
            description="SQLi description",
            remediation_recommendation="Sanitize inputs",
            custom_fields=[
                {
                    "key": "references",
                    "value": "OWASP ASVS §5.3; CWE-89"
                }
            ]
        )
        self.assertIsInstance(writeup, dict)

    def test_create_finding_from_writeup_dry_run(self):
        finding = self.client.create_finding_from_writeup(
            project_id="dummy_project",
            writeup_id="dummy_writeup",
            priority="High",
            affected_assets=[
                {"name": "TestAsset4"},
                {"name": "TestAsset5"}
            ]
        )
        self.assertIsInstance(finding, dict)

    def test_get_findings_for_project_dry_run(self):
        findings = self.client.get_findings_for_project("dummy_project")
        self.assertIsInstance(findings, list)

    def test_get_findings_with_pagination(self):
        captured = {}

        class Resp:
            status_code = 200
            text = "OK"

            def json(self):
                return {"vulnerabilities": [{"id": i} for i in range(10)]}

        def fake_request(method, endpoint, json_data=None, params=None, files=None, data=None, headers_override=None):
            captured["params"] = params
            captured["endpoint"] = endpoint
            return Resp()

        self.client._request = fake_request
        findings = self.client.get_findings("proj1", page=2, limit=3, priority="High")
        self.assertEqual(len(findings), 3)
        self.assertEqual(findings[0]["id"], 3)
        self.assertEqual(captured["params"]["priority"], "High")
        self.assertEqual(captured["params"]["skip"], 3)
        self.assertEqual(captured["params"]["limit"], 3)
        self.assertEqual(captured["params"]["page"], 2)
        self.assertEqual(captured["endpoint"], "/api/ss/project/proj1/vulnerabilities")
        with self.assertRaises(ValueError):
            self.client.get_findings("proj1", page=0)

    def test_upsert_finding_for_project_create(self):
        # Simulate no existing findings (should create new)
        self.client.get_findings_for_project = lambda project_id: []
        # Patch get_all_writeups to return a matching writeup for this test
        self.client.get_all_writeups = (
            lambda force_refresh=False: [
                {
                    "title": "UnitTest Finding",
                    "belongs_to_library": "Main Vulnerabilities",
                    "reference_id": "dummy_writeup_id",
                }
            ]
        )
        self.client.create_writeup = lambda **kwargs: {"reference_id": "dummy_writeup_id"}
        result = self.client.upsert_finding_for_project(
            project_id="dummy_project",
            title="UnitTest Finding",
            affected_assets=[{"name": "AssetA"}],
            priority="High",
            likelihood_of_exploitation=7,
            description="Test finding description",
            attack_scenario="Test scenario",
            remediation_recommendation="Test remediation",
            steps_to_reproduce="Step 1",
            tags=["unit", "test"],
            notes=[
                {"note": "Initial note", "type": "PLAINTEXT"}
            ],
        )
        self.assertIsInstance(result, dict)
        self.assertEqual(result.get("action"), "create")

    def test_upsert_finding_for_project_update(self):
        # Simulate an existing finding with the same title and some assets/notes
        existing_finding = {
            "vulnerability_id": "123",
            "vulnerability_title": "UnitTest Finding",
            "vulnerability_affected_assets": [
                {"asset": {"name": "AssetA"}},
                {"asset": {"name": "AssetB"}}
            ],
            "vulnerability_notes": [{"note": "Existing note", "type": "PLAINTEXT"}]
        }
        self.client.get_findings_for_project = lambda project_id: [existing_finding]
        # Patch get_all_writeups to return a matching writeup for this test
        self.client.get_all_writeups = (
            lambda force_refresh=False: [
                {
                    "title": "UnitTest Finding",
                    "belongs_to_library": "Main Vulnerabilities",
                    "reference_id": "dummy_writeup_id",
                }
            ]
        )
        self.client.create_writeup = lambda **kwargs: {"reference_id": "dummy_writeup_id"}
        # Patch _request to simulate API update response

        class Resp:
            status_code = 200

            def json(self):
                return {"updated": True}
            text = "OK"
        self.client._request = (
            lambda method, endpoint, json_data=None, params=None: Resp()
        )
        result = self.client.upsert_finding_for_project(
            project_id="dummy_project",
            title="UnitTest Finding",
            affected_assets=[
                {"name": "AssetB"},
                {"name": "AssetC"}
            ],
            priority="High",
            likelihood_of_exploitation=7,
            description="Test finding description",
            attack_scenario="Test scenario",
            remediation_recommendation="Test remediation",
            steps_to_reproduce="Step 1",
            tags=["unit", "test"],
            notes=[
                {"note": "Existing note", "type": "PLAINTEXT"},
                {"note": "New note", "type": "PLAINTEXT"}
            ],
        )
        self.assertIsInstance(result, dict)
        self.assertEqual(result.get("action"), "update")
        # Check that assets are merged and deduplicated
        update_payload = result.get("update_payload", {})
        asset_names = {
            a["assetName"] for a in update_payload.get("affected_assets", [])
        }
        self.assertSetEqual(asset_names, {"AssetA", "AssetB", "AssetC"})
        # Check that notes are merged and deduplicated
        notes = update_payload.get("notes", [])
        note_texts = {n["note"] for n in notes}
        self.assertSetEqual(note_texts, {"Existing note", "New note"})

    def test_find_writeup_in_cache_dry_run(self):
        writeup_id = self.client.find_writeup_in_cache("SQL Injection")
        self.assertTrue(writeup_id is None or isinstance(writeup_id, str))

    def test_project_scope_management_dry_run(self):
        # Patch _request to simulate API responses
        def fake_request(method, endpoint, json_data=None, params=None):
            if method == "get" and endpoint == "/api/ss/project/dummy_project":

                class Resp:
                    status_code = 200

                    def json(self):
                        return {"scope": ["AssetA", "AssetB"]}

                return Resp()
            if method == "put" and endpoint == "/api/ss/project/dummy_project":

                class Resp:
                    status_code = 200

                    def json(self):
                        return {"scope": json_data.get("scope", [])}

                return Resp()
            raise RuntimeError("Unexpected API call")
        self.client._request = fake_request
        # Test get_project_scope
        scope = self.client.get_project_scope("dummy_project")
        self.assertSetEqual(scope, {"AssetA", "AssetB"})
        # Test update_project_scope (add AssetC)
        updated = self.client.update_project_scope("dummy_project", ["AssetC"])
        self.assertIn("scope", updated)
        self.assertIn("AssetC", updated["scope"])

    def test_create_writeup_missing_required_fields(self):
        # Should raise ValueError if required fields are missing
        # Do not patch create_writeup here so real validation is used
        with self.assertRaises(ValueError):
            self.client.create_writeup(
                title="",
                description="desc",
                remediation_recommendation="remed"
            )
        with self.assertRaises(ValueError):
            self.client.create_writeup(
                title="Title",
                description="",
                remediation_recommendation="remed"
            )
        with self.assertRaises(ValueError):
            self.client.create_writeup(
                title="Title",
                description="desc",
                remediation_recommendation=""
            )

    def test_dummy_response(self):
        from pyattackforge.client import DummyResponse
        resp = DummyResponse()
        self.assertEqual(resp.status_code, 200)
        self.assertIsInstance(resp.json(), dict)
        self.assertIn("[DRY RUN]", resp.text)

    def test_upload_finding_evidence_dry_run(self):
        with tempfile.NamedTemporaryFile(delete=False) as tmp:
            tmp.write(b"evidence")
            evidence_path = tmp.name
        try:
            resp = self.client.upload_finding_evidence("vuln123", evidence_path)
            self.assertIsInstance(resp, dict)
        finally:
            os.remove(evidence_path)

    def test_upload_testcase_evidence_dry_run(self):
        with tempfile.NamedTemporaryFile(delete=False) as tmp:
            tmp.write(b"evidence")
            evidence_path = tmp.name
        try:
            resp = self.client.upload_testcase_evidence("proj1", "tc1", evidence_path)
            self.assertIsInstance(resp, dict)
        finally:
            os.remove(evidence_path)

    def test_assign_findings_to_testcase_merges(self):
        captured = {"endpoints": []}

        def fake_update(project_id, testcase_id, update_fields):
            captured["payload"] = update_fields

            return {"updated": True, "project_id": project_id, "testcase_id": testcase_id}
        self.client.update_testcase = fake_update
        result = self.client.assign_findings_to_testcase(
            "proj1",
            "tc1",
            ["vulnA", "vulnB"],
            existing_linked_vulnerabilities=["vulnB", "vulnC"]
        )
        self.assertIsInstance(result, dict)
        linked = captured["payload"].get("linked_vulnerabilities", [])
        self.assertListEqual(linked, ["vulnB", "vulnC", "vulnA"])

    def test_add_note_to_finding_deduplicates(self):
        self.client.get_vulnerability = lambda vid: {
            "vulnerability_notes": [{"note": "Existing note", "type": "PLAINTEXT"}]
        }
        captured = {"endpoints": []}

        class Resp:
            status_code = 200
            text = "OK"

            def json(self):
                return {"ok": True}

        def fake_request(method, endpoint, json_data=None, params=None, files=None, data=None, headers_override=None):
            captured["json_data"] = json_data
            return Resp()
        self.client._request = fake_request
        result = self.client.add_note_to_finding("vuln123", "Existing note")
        self.assertIsInstance(result, dict)
        notes = captured["json_data"].get("notes", [])
        self.assertEqual(len(notes), 1)

    def test_update_finding(self):
        captured = {}

        class Resp:
            status_code = 200
            text = "OK"

            def json(self):
                return {"updated": True}

        def fake_request(method, endpoint, json_data=None, params=None, files=None, data=None, headers_override=None):
            captured["endpoint"] = endpoint
            captured["json_data"] = json_data
            return Resp()

        self.client._request = fake_request
        resp = self.client.update_finding(
            vulnerability_id="v-1",
            project_id="p-1",
            affected_assets=[{"name": "asset-a"}, {"assetName": "asset-b"}, "asset-c"],
            notes=[{"note": "n1", "type": "PLAINTEXT"}],
            custom="field",
        )
        self.assertIsInstance(resp, dict)
        payload = captured["json_data"]
        self.assertEqual(payload["project_id"], "p-1")
        self.assertEqual(
            payload["affected_assets"],
            [{"assetName": "asset-a"}, {"assetName": "asset-b"}, {"assetName": "asset-c"}],
        )
        self.assertEqual(payload["notes"], [{"note": "n1", "type": "PLAINTEXT"}])
        self.assertEqual(payload["custom"], "field")
        self.assertEqual(captured["endpoint"], "/api/ss/vulnerability/v-1")
        with self.assertRaises(ValueError):
            self.client.update_finding("", project_id="p-1")

    def test_get_testcases(self):
        # DummyResponse returns {}, so should yield an empty list without raising
        cases = self.client.get_testcases("proj1")
        self.assertIsInstance(cases, list)
        self.assertEqual(cases, [])

    def test_get_testcase(self):
        class Resp:
            def __init__(self, status_code, body):
                self.status_code = status_code
                self._body = body

            def json(self):
                return self._body
            text = "resp"

        calls = []

        def fake_request(method, endpoint, json_data=None, params=None, files=None, data=None, headers_override=None):
            calls.append(endpoint)
            if "tc-ok" in endpoint:
                return Resp(200, {"testcase": {"id": "tc-ok", "status": "Not Tested"}})
            return Resp(404, {})

        self.client._request = fake_request
        tc_none = self.client.get_testcase("proj", "tc-missing")
        self.assertIsNone(tc_none)
        tc = self.client.get_testcase("proj", "tc-ok")
        self.assertIsInstance(tc, dict)
        self.assertEqual(tc.get("id"), "tc-ok")

    def test_add_note_to_testcase(self):
        captured = {"endpoints": []}

        class Resp:
            status_code = 200

            def json(self):
                return {"status": "Testcase Note Created"}

        def fake_request(method, endpoint, json_data=None, params=None, files=None, data=None, headers_override=None):
            captured["endpoints"].append((endpoint, json_data))
            return Resp()

        self.client._request = fake_request
        resp = self.client.add_note_to_testcase("proj1", "tc1", "Note text", status="Tested")
        self.assertIsInstance(resp, dict)
        note_calls = [c for c in captured["endpoints"] if "/note" in c[0]]
        self.assertTrue(note_calls)
        self.assertEqual(note_calls[0][1]["note"], "Note text")
        self.assertEqual(note_calls[0][1]["note_type"], "PLAINTEXT")

    def test_link_vulnerability_to_testcases(self):
        captured = {}

        class Resp:
            status_code = 200
            text = "OK"

            def json(self):
                return {"linked": True}

        def fake_request(method, endpoint, json_data=None, params=None, files=None, data=None, headers_override=None):
            captured["method"] = method
            captured["endpoint"] = endpoint
            captured["json_data"] = json_data
            return Resp()

        self.client._request = fake_request
        resp = self.client.link_vulnerability_to_testcases("v1", ["tc1", "tc2"], project_id="proj1")
        self.assertIsInstance(resp, dict)
        self.assertEqual(captured["endpoint"], "/api/ss/vulnerability/v1")
        self.assertEqual(captured["json_data"]["linked_testcases"], ["tc1", "tc2"])
        self.assertEqual(captured["json_data"]["project_id"], "proj1")

    def test_add_findings_to_testcase(self):
        captured = {}
        # Simulate existing testcase with one linked vuln (as dict)
        self.client.get_testcases = lambda project_id: [
            {
                "id": "tc1",
                "linked_vulnerabilities": [{"id": "existing"}],
            }
        ]

        def fake_assign(project_id, testcase_id, vulnerability_ids, existing_linked_vulnerabilities=None, additional_fields=None):
            captured["project_id"] = project_id
            captured["testcase_id"] = testcase_id
            captured["vulnerability_ids"] = vulnerability_ids
            captured["existing_linked_vulnerabilities"] = existing_linked_vulnerabilities
            captured["additional_fields"] = additional_fields
            return {"assigned": True}

        self.client.assign_findings_to_testcase = fake_assign
        resp = self.client.add_findings_to_testcase(
            "proj1",
            "tc1",
            ["new1", "new2"],
            additional_fields={"status": "Tested"},
        )
        self.assertIsInstance(resp, dict)
        self.assertEqual(captured["existing_linked_vulnerabilities"], ["existing"])
        self.assertEqual(captured["vulnerability_ids"], ["new1", "new2"])
        self.assertEqual(captured["additional_fields"], {"status": "Tested"})


if __name__ == "__main__":
    unittest.main()
