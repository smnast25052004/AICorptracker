#!/usr/bin/env python3
"""
Grafana Provisioning Script — configures data source and imports dashboards.

Grafana is installed natively (apt) on server 192.168.31.179:3000
and exposed externally via port forwarding at 95.79.92.200:3000.
PostgreSQL runs in Docker on the same host (port 5432 mapped to host).

Usage from the server itself:
    python grafana/provision.py

Usage from external machine (through port forwarding):
    python grafana/provision.py --grafana-url http://95.79.92.200:3000

With custom PostgreSQL host:
    python grafana/provision.py --pg-host 192.168.31.179
"""
import argparse
import json
import sys
from pathlib import Path

import httpx

# Grafana is native (systemd service), accessed via port forwarding
DEFAULT_GRAFANA_URL = "http://192.168.31.179:3000"
DEFAULT_GRAFANA_USER = "admin"
DEFAULT_GRAFANA_PASS = "A7zv4F5C"

# PostgreSQL runs in Docker on the same host, port 5432 mapped to 0.0.0.0
DEFAULT_PG_HOST = "192.168.31.179"
DEFAULT_PG_PORT = 5432
DEFAULT_PG_DB = "corptracker"
DEFAULT_PG_USER = "corptracker"
DEFAULT_PG_PASS = "corptracker_secret"


class GrafanaProvisioner:

    def __init__(self, grafana_url: str, user: str, password: str):
        self.base_url = grafana_url.rstrip("/")
        self.auth = (user, password)
        self.client = httpx.Client(auth=self.auth, timeout=30.0)

    def check_connection(self) -> bool:
        try:
            resp = self.client.get(f"{self.base_url}/api/org")
            resp.raise_for_status()
            org = resp.json()
            print(f"[OK] Connected to Grafana: {org.get('name', 'unknown')}")
            return True
        except Exception as e:
            print(f"[ERROR] Cannot connect to Grafana: {e}")
            return False

    def _ensure_jsondata_database(
        self,
        ds_id: int,
        pg_db: str,
        pg_pass: str,
    ) -> None:
        """Grafana 12+ requires default database inside jsonData; heal existing datasources."""
        resp = self.client.get(f"{self.base_url}/api/datasources/{ds_id}")
        if resp.status_code != 200:
            return
        body = resp.json()
        jd = dict(body.get("jsonData") or {})
        if jd.get("database") == pg_db:
            return
        jd["database"] = pg_db
        body["jsonData"] = jd
        body["database"] = pg_db
        body["secureJsonData"] = {"password": pg_pass}
        put = self.client.put(f"{self.base_url}/api/datasources/{ds_id}", json=body)
        if put.status_code in (200, 201):
            print(f"[OK] Updated datasource jsonData.database -> {pg_db!r} (Grafana 12+)")
        elif put.status_code == 403 and "read-only" in (put.text or "").lower():
            print(
                "[WARN] Datasource is provisioned as read-only — edit "
                "grafana/provisioning/datasources/datasource.yml (jsonData.database) "
                "and restart the Grafana container / service."
            )
        else:
            print(f"[WARN] Could not patch jsonData.database: {put.status_code} {put.text}")

    def create_datasource(
        self,
        pg_host: str,
        pg_port: int,
        pg_db: str,
        pg_user: str,
        pg_pass: str,
        force_recreate: bool = False,
    ) -> int | None:
        existing = self.client.get(f"{self.base_url}/api/datasources").json()
        for ds in existing:
            if ds.get("name") == "CorpTracker PostgreSQL":
                if force_recreate:
                    resp = self.client.delete(f"{self.base_url}/api/datasources/uid/{ds.get('uid', ds['id'])}")
                    if resp.status_code in (200, 404):
                        print(f"[OK] Old datasource removed, creating new one...")
                    else:
                        print(f"[WARN] Could not remove old datasource: {resp.status_code}")
                else:
                    print(f"[OK] Datasource already exists (id={ds['id']})")
                    self._ensure_jsondata_database(ds["id"], pg_db, pg_pass)
                    return ds["id"]
                break

        payload = {
            "name": "CorpTracker PostgreSQL",
            "type": "postgres",
            "uid": "corptracker-pg",
            "url": f"{pg_host}:{pg_port}",
            "database": pg_db,
            "user": pg_user,
            "secureJsonData": {"password": pg_pass},
            "jsonData": {
                # Grafana 12+ (grafana-postgresql-datasource): requires default DB in jsonData
                "database": pg_db,
                "sslmode": "disable",
                "maxOpenConns": 10,
                "maxIdleConns": 5,
                "connMaxLifetime": 14400,
                "postgresVersion": 1600,
                "timescaledb": False,
            },
            "access": "proxy",
            "isDefault": True,
        }

        resp = self.client.post(f"{self.base_url}/api/datasources", json=payload)
        if resp.status_code in (200, 201):
            ds_id = resp.json().get("datasource", {}).get("id") or resp.json().get("id")
            print(f"[OK] Datasource created (id={ds_id})")
            return ds_id
        else:
            print(f"[ERROR] Failed to create datasource: {resp.status_code} {resp.text}")
            return None

    def create_folder(self, title: str, uid: str) -> str:
        existing = self.client.get(f"{self.base_url}/api/folders").json()
        for f in existing:
            if f.get("uid") == uid:
                print(f"[OK] Folder '{title}' already exists")
                return uid

        resp = self.client.post(
            f"{self.base_url}/api/folders",
            json={"uid": uid, "title": title},
        )
        if resp.status_code in (200, 201):
            print(f"[OK] Folder '{title}' created")
        else:
            print(f"[WARN] Folder creation: {resp.status_code} {resp.text}")
        return uid

    def import_dashboard(self, dashboard_json: dict, folder_uid: str) -> bool:
        payload = {
            "dashboard": dashboard_json,
            "overwrite": True,
            "folderUid": folder_uid,
        }
        resp = self.client.post(
            f"{self.base_url}/api/dashboards/db",
            json=payload,
        )
        title = dashboard_json.get("title", "unknown")
        if resp.status_code == 200:
            url = resp.json().get("url", "")
            print(f"[OK] Dashboard '{title}' imported -> {self.base_url}{url}")
            return True
        else:
            print(f"[ERROR] Dashboard '{title}' import failed: {resp.status_code} {resp.text}")
            return False

    def import_dashboards_from_dir(self, directory: str, folder_uid: str) -> int:
        dashboard_dir = Path(directory)
        if not dashboard_dir.exists():
            print(f"[ERROR] Directory not found: {directory}")
            return 0

        count = 0
        for json_file in sorted(dashboard_dir.glob("*.json")):
            print(f"\nImporting {json_file.name}...")
            with open(json_file) as f:
                dashboard = json.load(f)
            dashboard["id"] = None
            if self.import_dashboard(dashboard, folder_uid):
                count += 1
        return count


def main():
    parser = argparse.ArgumentParser(description="Provision Grafana for CorpTracker")
    parser.add_argument("--grafana-url", default=DEFAULT_GRAFANA_URL)
    parser.add_argument("--grafana-user", default=DEFAULT_GRAFANA_USER)
    parser.add_argument("--grafana-pass", default=DEFAULT_GRAFANA_PASS)
    parser.add_argument("--pg-host", default=DEFAULT_PG_HOST)
    parser.add_argument("--pg-port", type=int, default=DEFAULT_PG_PORT)
    parser.add_argument("--pg-db", default=DEFAULT_PG_DB)
    parser.add_argument("--pg-user", default=DEFAULT_PG_USER)
    parser.add_argument("--pg-pass", default=DEFAULT_PG_PASS)
    parser.add_argument("--recreate-datasource", action="store_true", help="Delete and recreate datasource (fixes connection issues)")
    args = parser.parse_args()

    provisioner = GrafanaProvisioner(args.grafana_url, args.grafana_user, args.grafana_pass)

    if not provisioner.check_connection():
        sys.exit(1)

    ds_id = provisioner.create_datasource(
        args.pg_host, args.pg_port, args.pg_db, args.pg_user, args.pg_pass,
        force_recreate=args.recreate_datasource,
    )
    if not ds_id:
        sys.exit(1)

    folder_uid = provisioner.create_folder("CorpTracker", "corptracker")

    script_dir = Path(__file__).parent
    dashboards_dir = script_dir / "dashboards"
    count = provisioner.import_dashboards_from_dir(str(dashboards_dir), folder_uid)

    print(f"\n{'='*50}")
    print(f"Provisioning complete: {count} dashboards imported")
    print(f"Open: {args.grafana_url}/dashboards/f/corptracker")


if __name__ == "__main__":
    main()
