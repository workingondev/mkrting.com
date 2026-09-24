"""Private local editorial dashboard. Bind only to the loopback interface."""

from __future__ import annotations

import argparse
import json
import re
import secrets
import threading
import time
import uuid
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qs, urlparse

from collect_cycle import cycle as collect_cycle
from auto_draft import create_selected_draft
from create_pr import create_pr
from editor_lock import editorial_lock
from engine import LOCAL, add_item, draft_cluster, get_cluster, init_db, primary_url_specific, research_cluster, shortlist
from publish_pr import publish_draft

PAGE = (Path(__file__).parent / "editor_ui.html").read_text(encoding="utf-8")
TOKEN = secrets.token_urlsafe(32)
JOBS: dict[str, dict] = {}
JOBS_LOCK = threading.Lock()
POOL = ThreadPoolExecutor(max_workers=1)
DRAFT_NAME = re.compile(r"[a-z0-9]+(?:-[a-z0-9]+)*\.json\Z")


def safe_draft(name: str) -> Path:
    if not DRAFT_NAME.fullmatch(name):
        raise ValueError("Invalid draft name")
    path = LOCAL / "drafts" / name
    if not path.is_file():
        raise ValueError("Draft not found")
    return path


def state() -> dict:
    connection = init_db()
    try:
        leads = shortlist(connection, 120)
        for lead in leads:
            _, items = get_cluster(connection, lead["id"])
            lead["items"] = [{key: item[key] for key in ("title", "url", "source_name", "summary", "is_primary", "published_at")} for item in items]
            cache = connection.execute("SELECT research_json,researched_at FROM research_cache WHERE cluster_id=?", (lead["id"],)).fetchone()
            lead["research"] = json.loads(cache["research_json"]) if cache else None
            lead["researched_at"] = cache["researched_at"] if cache else None
        drafts = []
        for path in sorted((LOCAL / "drafts").glob("*.json")):
            try:
                payload = json.loads(path.read_text(encoding="utf-8"))
                drafts.append({"name": path.name, "cluster_id": payload["cluster_id"], "title": payload["article"]["title"], "status": payload.get("review_status", "needs_human_review"), "pr_url": payload.get("pr_url"), "merged_at": payload.get("merged_at")})
            except (KeyError, ValueError, OSError):
                continue
        last = LOCAL / "last_collect.json"
        try:
            last_collect = json.loads(last.read_text(encoding="utf-8")) if last.exists() else None
        except (OSError, ValueError):
            last_collect = None
        feeds = json.loads((Path(__file__).resolve().parents[1] / "data/feeds.json").read_text())
        return {"leads": leads, "drafts": drafts, "last_collect": last_collect,
                "active_feeds": sum(bool(feed.get("enabled")) for feed in feeds),
                "stats": {"new": sum(lead["status"] == "new" for lead in leads),
                          "ready": sum(lead["status"] == "new" and lead["ready_for_draft"] for lead in leads),
                          "researched": sum(bool(lead["research"]) for lead in leads),
                          "drafts": len(drafts)}}
    finally:
        connection.close()


def run_action(kind: str, data: dict, progress) -> object:
    if kind == "collect":
        progress("Collecting feeds and researching selected leads")
        return collect_cycle()
    with editorial_lock():
        connection = init_db()
        try:
            if kind in {"research", "draft", "auto_draft", "dismiss", "restore", "add_source"}:
                cluster_id = int(data.get("cluster_id", 0))
                get_cluster(connection, cluster_id)
            if kind == "research":
                progress("Reading sources and building the claim ledger")
                research, model, _, _, _ = research_cluster(connection, cluster_id)
                return {"cluster_id": cluster_id, "model": model, "research": research}
            if kind == "draft":
                progress("Writing and validating the article draft")
                return {"draft": draft_cluster(connection, cluster_id).name}
            if kind == "auto_draft":
                return {"draft": create_selected_draft(connection, cluster_id, progress).name}
            if kind == "dismiss":
                connection.execute("UPDATE clusters SET status='dismissed' WHERE id=?", (cluster_id,))
                connection.commit()
                return {"dismissed": cluster_id}
            if kind == "restore":
                connection.execute("UPDATE clusters SET status='new' WHERE id=? AND status='dismissed'", (cluster_id,))
                connection.commit()
                return {"restored": cluster_id}
            if kind == "add_source":
                url = str(data.get("url", "")).strip()
                primary = bool(data.get("primary"))
                if primary and not primary_url_specific(url):
                    raise RuntimeError("Use the exact official campaign page or post, not a home/profile page")
                _, created = add_item(connection, cluster_id=cluster_id, url=url,
                                      title=str(data.get("title", "")).strip(),
                                      summary=str(data.get("summary", "")).strip(),
                                      source_name=str(data.get("source_name", "")).strip(),
                                      source_type="primary" if primary else "manual",
                                      region=str(data.get("region", "Global")), is_primary=primary)
                return {"cluster_id": cluster_id, "created": created}
            if kind in {"pr", "publish"}:
                path = safe_draft(str(data.get("draft", "")))
                if kind == "pr":
                    progress("Creating the draft PR")
                    return {"pr_url": create_pr(path)}
                if data.get("review_confirmed") is not True:
                    raise RuntimeError("Read the article and confirm your review before publishing")
                progress("Checking the reviewed draft and GitHub PR")
                return {"pr_url": publish_draft(path, progress)}
            raise ValueError("Unknown action")
        finally:
            connection.close()


def submit_action(kind: str, data: dict) -> str:
    job_id = uuid.uuid4().hex
    with JOBS_LOCK:
        if any(job["status"] in {"queued", "running"} for job in JOBS.values()):
            raise RuntimeError("Another action is running; wait for it to finish")
        JOBS[job_id] = {"status": "queued", "message": "Waiting to start", "result": None, "created_at": datetime.now(timezone.utc).isoformat(timespec="seconds")}
        if len(JOBS) > 40:
            for old in list(JOBS)[:-40]:
                JOBS.pop(old, None)

    def worker():
        def progress(message):
            with JOBS_LOCK:
                JOBS[job_id]["message"] = message
        with JOBS_LOCK:
            JOBS[job_id]["status"] = "running"
        try:
            result = run_action(kind, data, progress)
            with JOBS_LOCK:
                JOBS[job_id].update(status="done", message="Done", result=result)
        except Exception as error:
            with JOBS_LOCK:
                JOBS[job_id].update(status="error", message=f"{type(error).__name__}: {str(error)[:500]}")

    POOL.submit(worker)
    return job_id


def collection_scheduler() -> None:
    """Keep lead discovery active while this local desk process is running."""
    last_attempt = 0.0
    while True:
        try:
            marker = LOCAL / "last_collect.json"
            now = time.time()
            due = (not marker.exists() or now - marker.stat().st_mtime >= 2 * 60 * 60) and now - last_attempt >= 2 * 60 * 60
            if due:
                try:
                    submit_action("collect", {})
                    last_attempt = now
                except RuntimeError:
                    pass
        except OSError:
            pass
        time.sleep(60)


class Handler(BaseHTTPRequestHandler):
    def log_message(self, format, *args):
        return

    def reply(self, status: int, data: object, content_type: str = "application/json"):
        body = (json.dumps(data, ensure_ascii=False) if content_type == "application/json" else str(data)).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", content_type + "; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        self.send_header("X-Content-Type-Options", "nosniff")
        self.send_header("Content-Security-Policy", "default-src 'self'; script-src 'self' 'unsafe-inline'; style-src 'self' 'unsafe-inline'; connect-src 'self'; frame-src 'self'; base-uri 'none'; frame-ancestors 'none'")
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self):
        if self.headers.get("Host") not in {"127.0.0.1:8766", "localhost:8766", f"127.0.0.1:{self.server.server_port}", f"localhost:{self.server.server_port}"}:
            return self.reply(403, {"error": "Local access only"})
        path = urlparse(self.path)
        try:
            if path.path == "/":
                self.reply(200, PAGE.replace("__DASHBOARD_TOKEN__", TOKEN), "text/html")
            elif path.path == "/api/state":
                self.reply(200, state())
            elif path.path == "/api/draft":
                name = parse_qs(path.query).get("name", [""])[0]
                self.reply(200, json.loads(safe_draft(name).read_text(encoding="utf-8")))
            elif path.path == "/api/job":
                job_id = parse_qs(path.query).get("id", [""])[0]
                with JOBS_LOCK:
                    job = JOBS.get(job_id)
                    self.reply(200 if job else 404, job or {"error": "Job not found"})
            else:
                self.reply(404, {"error": "Not found"})
        except (ValueError, OSError) as error:
            self.reply(400, {"error": str(error)})

    def do_POST(self):
        if self.path != "/api/action":
            return self.reply(404, {"error": "Not found"})
        origin = self.headers.get("Origin", "")
        expected = f"http://{self.headers.get('Host', '')}"
        allowed_hosts = {f"127.0.0.1:{self.server.server_port}", f"localhost:{self.server.server_port}"}
        if self.headers.get("Host") not in allowed_hosts or origin != expected or self.headers.get("X-Editor-Token") != TOKEN:
            return self.reply(403, {"error": "Dashboard security check failed"})
        try:
            length = int(self.headers.get("Content-Length", "0"))
            if length <= 0 or length > 16384:
                raise ValueError("Invalid request size")
            body = json.loads(self.rfile.read(length))
            if not isinstance(body, dict):
                raise ValueError("Invalid request")
            job_id = submit_action(str(body.get("action", "")), body)
            self.reply(202, {"job_id": job_id})
        except (ValueError, RuntimeError) as error:
            self.reply(400, {"error": str(error)})


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--port", type=int, default=8766)
    args = parser.parse_args()
    server = ThreadingHTTPServer(("127.0.0.1", args.port), Handler)
    threading.Thread(target=collection_scheduler, daemon=True).start()
    print(f"Private editorial dashboard: http://127.0.0.1:{args.port}/", flush=True)
    server.serve_forever()


if __name__ == "__main__":
    main()
