#!/usr/bin/env python3
"""
JobTread Pave API Client
========================
Interact with JobTread via their Pave query language API.
Endpoint: POST https://api.jobtread.com/pave
Auth: Grant key (passed as grantKey in $ block)

Usage:
  python jobtread_pave.py org                    # Get organization ID
  python jobtread_pave.py projects               # List projects
  python jobtread_pave.py project <id>           # Get project details
  python jobtread_pave.py tasks <project_id>    # List tasks for a project
  python jobtread_pave.py create-task <project_id> --name "Task" --description "..."
  python jobtread_pave.py accounts               # List accounts (customers/vendors)
  python jobtread_pave.py files <project_id>     # List files on a project
  python jobtread_pave.py upload-file <project_id> <file_path> [--name "display.pdf"]
  python jobtread_pave.py raw <pave_query_file>  # Run raw Pave query from file

Requires: requests (pip install requests)
Config: Set JOBTREAD_GRANT_KEY env var
"""

import sys
import json
import os
import argparse
from pathlib import Path

try:
    import requests
except ImportError:
    print("ERROR: requests not installed. Run: pip install requests")
    sys.exit(1)

# ── Config ──────────────────────────────────────────────────
API_URL = "https://api.jobtread.com/pave"
GRANT_KEY = os.environ.get("JOBTREAD_GRANT_KEY", "")
ORG_ID = os.environ.get("JOBTREAD_ORG_ID", "")


def pave_query(query: dict) -> dict:
    """Execute a Pave API query. Returns parsed JSON response."""
    if not GRANT_KEY:
        print("ERROR: JOBTREAD_GRANT_KEY not set in environment")
        sys.exit(1)

    # Pave queries wrap inputs in a $ block with the grant key
    if "$" not in query:
        query = {**query, "$": {"grantKey": GRANT_KEY}}
    else:
        query["$"]["grantKey"] = GRANT_KEY

    resp = requests.post(API_URL, json={"query": query}, timeout=30)

    if resp.status_code != 200:
        print(f"API Error {resp.status_code}: {resp.text[:500]}")
        sys.exit(1)

    data = resp.json()

    # Pave returns the query results as top-level keys matching the query
    return data


def format_output(data, indent=0):
    """Pretty-print Pave response, handling nested objects and lists."""
    if isinstance(data, dict):
        for k, v in data.items():
            if k == "$":
                continue
            if isinstance(v, (dict, list)):
                print(f"{'  ' * indent}{k}:")
                format_output(v, indent + 1)
            else:
                print(f"{'  ' * indent}{k}: {v}")
    elif isinstance(data, list):
        for i, item in enumerate(data):
            if isinstance(item, (dict, list)):
                print(f"{'  ' * indent}[{i}]")
                format_output(item, indent + 1)
            else:
                print(f"{'  ' * indent}- {item}")
    else:
        print(f"{'  ' * indent}{data}")


# ── Commands ────────────────────────────────────────────────

def cmd_org(args):
    """Get organization ID (needed for most other queries)."""
    result = pave_query({
        "currentGrant": {
            "user": {
                "id": {},
                "name": {},
                "memberships": {
                    "nodes": {
                        "id": {},
                        "organization": {
                            "id": {},
                            "name": {},
                        }
                    }
                }
            }
        }
    })
    print("Organization info:")
    format_output(result.get("currentGrant", {}))


def cmd_projects(args):
    """List all projects in the organization."""
    if not ORG_ID:
        print("ERROR: JOBTREAD_ORG_ID not set. Run 'org' command first to find it.")
        sys.exit(1)

    result = pave_query({
        "organization": {
            "$": {"id": ORG_ID},
            "projects": {
                "nodes": {
                    "id": {},
                    "name": {},
                    "status": {},
                    "startDate": {},
                    "endDate": {},
                }
            }
        }
    })
    projects = result.get("organization", {}).get("projects", {}).get("nodes", [])
    if not projects:
        print("No projects found.")
        return
    print(f"\n📋 Projects ({len(projects)}):\n")
    for i, p in enumerate(projects, 1):
        print(f"  {i}. {p.get('name', 'Unnamed')} (ID: {p.get('id')})")
        print(f"     Status: {p.get('status', 'N/A')} | Start: {p.get('startDate', 'N/A')} | End: {p.get('endDate', 'N/A')}")
        print()


def cmd_project(args):
    """Get details for a specific project."""
    result = pave_query({
        "project": {
            "$": {"id": args.project_id},
            "id": {},
            "name": {},
            "status": {},
            "startDate": {},
            "endDate": {},
            "description": {},
            "account": {
                "id": {},
                "name": {},
                "type": {},
            }
        }
    })
    format_output(result.get("project", {}))


def cmd_tasks(args):
    """List tasks for a project."""
    result = pave_query({
        "project": {
            "$": {"id": args.project_id},
            "tasks": {
                "nodes": {
                    "id": {},
                    "name": {},
                    "status": {},
                    "dueDate": {},
                    "assignedTo": {
                        "id": {},
                        "name": {},
                    }
                }
            }
        }
    })
    tasks = result.get("project", {}).get("tasks", {}).get("nodes", [])
    if not tasks:
        print("No tasks found for this project.")
        return
    print(f"\n📝 Tasks ({len(tasks)}):\n")
    for i, t in enumerate(tasks, 1):
        assignee = t.get("assignedTo", {})
        assignee_name = assignee.get("name", "Unassigned") if assignee else "Unassigned"
        print(f"  {i}. {t.get('name', 'Unnamed')} (ID: {t.get('id')})")
        print(f"     Status: {t.get('status', 'N/A')} | Due: {t.get('dueDate', 'N/A')} | Assigned: {assignee_name}")
        print()


def cmd_create_task(args):
    """Create a task on a project."""
    query = {
        "createTask": {
            "$": {
                "projectId": args.project_id,
                "name": args.name,
            },
            "createdTask": {
                "id": {},
                "name": {},
                "status": {},
            }
        }
    }
    if args.description:
        query["createTask"]["$"]["description"] = args.description
    if args.due_date:
        query["createTask"]["$"]["dueDate"] = args.due_date

    result = pave_query(query)
    print("✅ Task created:")
    format_output(result.get("createTask", {}))


def cmd_accounts(args):
    """List accounts (customers and vendors)."""
    if not ORG_ID:
        print("ERROR: JOBTREAD_ORG_ID not set. Run 'org' command first.")
        sys.exit(1)

    result = pave_query({
        "organization": {
            "$": {"id": ORG_ID},
            "accounts": {
                "nodes": {
                    "id": {},
                    "name": {},
                    "type": {},
                    "createdAt": {},
                }
            }
        }
    })
    accounts = result.get("organization", {}).get("accounts", {}).get("nodes", [])
    if not accounts:
        print("No accounts found.")
        return
    print(f"\n👥 Accounts ({len(accounts)}):\n")
    for a in accounts:
        print(f"  {a.get('name', 'Unnamed')} ({a.get('type', 'N/A')}) — ID: {a.get('id')}")


def cmd_files(args):
    """List files on a project."""
    result = pave_query({
        "project": {
            "$": {"id": args.project_id},
            "files": {
                "nodes": {
                    "id": {},
                    "name": {},
                    "mimeType": {},
                    "createdAt": {},
                }
            }
        }
    })
    files = result.get("project", {}).get("files", {}).get("nodes", [])
    if not files:
        print("No files found for this project.")
        return
    print(f"\n📎 Files ({len(files)}):\n")
    for f in files:
        print(f"  {f.get('name', 'Unnamed')} ({f.get('mimeType', 'N/A')}) — ID: {f.get('id')}")


def cmd_upload_file(args):
    """
    Upload a file to a JobTread project.
    NOTE: File uploads may require a two-step process:
      1. Request upload URL from Pave API
      2. Upload file to the provided URL
    The exact Pave mutation for file uploads needs to be verified
    against the JobTread API schema. This is a starting point.
    """
    file_path = Path(args.file_path)
    if not file_path.exists():
        print(f"ERROR: File not found: {file_path}")
        sys.exit(1)

    display_name = args.name or file_path.name
    file_size = file_path.stat().st_size

    print(f"Preparing to upload: {display_name} ({file_size:,} bytes)")
    print(f"  Project: {args.project_id}")
    print(f"  Source: {file_path}")
    print()
    print("NOTE: JobTread file upload via Pave API may require a pre-signed URL flow.")
    print("Check the API explorer at https://app.jobtread.com/docs for the exact mutation.")
    print()
    print("Attempting upload mutation...")

    # Try the likely mutation structure (may need adjustment based on API schema)
    result = pave_query({
        "createFile": {
            "$": {
                "projectId": args.project_id,
                "name": display_name,
            },
            "createdFile": {
                "id": {},
                "name": {},
            }
        }
    })
    print("Upload result:")
    format_output(result.get("createFile", {}))


def cmd_raw(args):
    """Run a raw Pave query from a JSON/YAML file."""
    query_file = Path(args.query_file)
    if not query_file.exists():
        print(f"ERROR: Query file not found: {query_file}")
        sys.exit(1)

    with open(query_file) as f:
        content = f.read()

    # Try JSON first, fall back to YAML
    try:
        query = json.loads(content)
    except json.JSONDecodeError:
        try:
            import yaml
            query = yaml.safe_load(content)
        except ImportError:
            print("ERROR: File is not valid JSON and PyYAML not installed")
            sys.exit(1)

    print("Running Pave query:")
    print(json.dumps(query, indent=2))
    print()
    result = pave_query(query)
    format_output(result)


# ── CLI ─────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(description="JobTread Pave API Client")
    sub = parser.add_subparsers(dest="command")

    sub.add_parser("org", help="Get organization ID")

    sub.add_parser("projects", help="List all projects")

    p = sub.add_parser("project", help="Get project details")
    p.add_argument("project_id")

    p = sub.add_parser("tasks", help="List tasks for a project")
    p.add_argument("project_id")

    p = sub.add_parser("create-task", help="Create a task")
    p.add_argument("project_id")
    p.add_argument("--name", required=True)
    p.add_argument("--description", default="")
    p.add_argument("--due-date", default="")

    sub.add_parser("accounts", help="List accounts (customers/vendors)")

    p = sub.add_parser("files", help="List files on a project")
    p.add_argument("project_id")

    p = sub.add_parser("upload-file", help="Upload file to a project")
    p.add_argument("project_id")
    p.add_argument("file_path")
    p.add_argument("--name", default="")

    p = sub.add_parser("raw", help="Run raw Pave query from file")
    p.add_argument("query_file")

    args = parser.parse_args()
    if not args.command:
        parser.print_help()
        return

    cmds = {
        "org": cmd_org,
        "projects": cmd_projects,
        "project": cmd_project,
        "tasks": cmd_tasks,
        "create-task": cmd_create_task,
        "accounts": cmd_accounts,
        "files": cmd_files,
        "upload-file": cmd_upload_file,
        "raw": cmd_raw,
    }
    cmds[args.command](args)


if __name__ == "__main__":
    main()