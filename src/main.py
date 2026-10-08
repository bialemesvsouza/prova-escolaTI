from __future__ import annotations

import json
import os
import sqlite3
import threading
from datetime import datetime, timedelta, timezone
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any
from urllib.parse import unquote, urlparse


PROJECT_ROOT = Path(__file__).resolve().parent.parent
TIMEZONE = timezone(timedelta(hours=-3))
DEFAULT_PREFIX = "D"
DEFAULT_PREFERRED_RATIO = 3
DEFAULT_PORT = 8080


def now() -> datetime:
    return datetime.now(TIMEZONE)


def load_variant() -> tuple[str, int]:
    prefix = os.getenv("PREFIXO")
    ratio_raw = os.getenv("RAZAO_PREFERENCIAL")

    candidates = (
        PROJECT_ROOT / "variante" / "params.json",
        Path.cwd() / "variante" / "params.json",
        Path("/app/variante/params.json"),
    )
    for candidate in candidates:
        if prefix and ratio_raw:
            break
        try:
            data = json.loads(candidate.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            continue
        prefix = prefix or data.get("PREFIXO")
        ratio_raw = ratio_raw or str(data.get("RAZAO_PREFERENCIAL", ""))

    prefix = (prefix or DEFAULT_PREFIX).strip().upper()
    try:
        ratio = int(ratio_raw or DEFAULT_PREFERRED_RATIO)
    except ValueError:
        ratio = DEFAULT_PREFERRED_RATIO

    if len(prefix) != 1 or not prefix.isalpha() or not prefix.isupper():
        raise ValueError("PREFIXO deve ser uma letra maiuscula")
    if ratio < 1:
        raise ValueError("RAZAO_PREFERENCIAL deve ser maior que zero")
    return prefix, ratio


def select_database_path() -> Path:
    configured = os.getenv("DATA_DIR")
    candidates = [Path(configured)] if configured else [Path("/data")]
    candidates.append(PROJECT_ROOT / ".data")

    for directory in candidates:
        try:
            directory.mkdir(parents=True, exist_ok=True)
            probe = directory / ".write-test"
            probe.write_text("ok", encoding="utf-8")
            probe.unlink()
            return directory / "fila.db"
        except OSError:
            continue
    raise RuntimeError("nao foi possivel encontrar um diretorio gravavel")


class QueueStore:
    def __init__(self, database_path: Path, prefix: str, preferred_ratio: int):
        self.database_path = database_path
        self.prefix = prefix
        self.preferred_ratio = preferred_ratio
        self._schema_lock = threading.Lock()
        self._initialize()

    def _connect(self) -> sqlite3.Connection:
        connection = sqlite3.connect(
            self.database_path,
            timeout=30,
            isolation_level=None,
        )
        connection.row_factory = sqlite3.Row
        connection.execute("PRAGMA busy_timeout = 30000")
        return connection

    def _initialize(self) -> None:
        with self._schema_lock, self._connect() as connection:
            connection.execute("PRAGMA journal_mode = WAL")
            connection.execute("PRAGMA synchronous = FULL")
            connection.executescript(
                """
                CREATE TABLE IF NOT EXISTS tickets (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    business_date TEXT NOT NULL,
                    sequence INTEGER NOT NULL,
                    code TEXT NOT NULL,
                    kind TEXT NOT NULL CHECK(kind IN ('normal', 'preferencial')),
                    issued_at TEXT NOT NULL,
                    status TEXT NOT NULL CHECK(status IN ('aguardando', 'chamada', 'concluida', 'cancelada')),
                    called_at TEXT,
                    panel_order INTEGER,
                    UNIQUE(business_date, sequence),
                    UNIQUE(business_date, code)
                );

                CREATE TABLE IF NOT EXISTS state (
                    key TEXT PRIMARY KEY,
                    value INTEGER NOT NULL
                );

                INSERT OR IGNORE INTO state(key, value)
                VALUES ('preferred_streak', 0), ('panel_counter', 0);

                CREATE INDEX IF NOT EXISTS idx_tickets_waiting
                ON tickets(status, kind, id);

                CREATE INDEX IF NOT EXISTS idx_tickets_panel
                ON tickets(panel_order DESC);
                """
            )

    @staticmethod
    def _ticket(row: sqlite3.Row) -> dict[str, Any]:
        result: dict[str, Any] = {
            "codigo": row["code"],
            "tipo": row["kind"],
            "emissao": row["issued_at"],
            "status": row["status"],
        }
        if row["called_at"] is not None:
            result["chamada_em"] = row["called_at"]
        return result

    def issue(self, kind: str) -> dict[str, Any]:
        moment = now()
        business_date = moment.date().isoformat()
        issued_at = moment.isoformat(timespec="seconds")

        with self._connect() as connection:
            connection.execute("BEGIN IMMEDIATE")
            row = connection.execute(
                "SELECT COALESCE(MAX(sequence), 0) + 1 AS next_sequence "
                "FROM tickets WHERE business_date = ?",
                (business_date,),
            ).fetchone()
            sequence = int(row["next_sequence"])
            if sequence > 999:
                connection.rollback()
                raise OverflowError("limite_diario_atingido")
            code = f"{self.prefix}{sequence:03d}"
            cursor = connection.execute(
                """
                INSERT INTO tickets(
                    business_date, sequence, code, kind, issued_at, status
                ) VALUES (?, ?, ?, ?, ?, 'aguardando')
                """,
                (business_date, sequence, code, kind, issued_at),
            )
            ticket_id = cursor.lastrowid
            connection.commit()
            stored = connection.execute(
                "SELECT * FROM tickets WHERE id = ?", (ticket_id,)
            ).fetchone()
        return self._ticket(stored)

    def call_next(self) -> dict[str, Any] | None:
        called_at = now().isoformat(timespec="seconds")
        with self._connect() as connection:
            connection.execute("BEGIN IMMEDIATE")
            streak = int(
                connection.execute(
                    "SELECT value FROM state WHERE key = 'preferred_streak'"
                ).fetchone()["value"]
            )
            normal = connection.execute(
                "SELECT * FROM tickets WHERE status = 'aguardando' AND kind = 'normal' "
                "ORDER BY id LIMIT 1"
            ).fetchone()
            preferred = connection.execute(
                "SELECT * FROM tickets WHERE status = 'aguardando' AND kind = 'preferencial' "
                "ORDER BY id LIMIT 1"
            ).fetchone()

            chosen: sqlite3.Row | None
            if preferred is not None and (normal is None or streak < self.preferred_ratio):
                chosen = preferred
                new_streak = min(streak + 1, self.preferred_ratio)
            elif normal is not None:
                chosen = normal
                new_streak = 0
            else:
                chosen = preferred
                new_streak = min(streak + 1, self.preferred_ratio)

            if chosen is None:
                connection.rollback()
                return None

            panel_order = self._next_panel_order(connection)
            connection.execute(
                "UPDATE tickets SET status = 'chamada', called_at = ?, panel_order = ? "
                "WHERE id = ?",
                (called_at, panel_order, chosen["id"]),
            )
            connection.execute(
                "UPDATE state SET value = ? WHERE key = 'preferred_streak'",
                (new_streak,),
            )
            connection.commit()
            updated = connection.execute(
                "SELECT * FROM tickets WHERE id = ?", (chosen["id"],)
            ).fetchone()
        return self._ticket(updated)

    @staticmethod
    def _next_panel_order(connection: sqlite3.Connection) -> int:
        connection.execute(
            "UPDATE state SET value = value + 1 WHERE key = 'panel_counter'"
        )
        return int(
            connection.execute(
                "SELECT value FROM state WHERE key = 'panel_counter'"
            ).fetchone()["value"]
        )

    @staticmethod
    def _find_latest(connection: sqlite3.Connection, code: str) -> sqlite3.Row | None:
        return connection.execute(
            "SELECT * FROM tickets WHERE code = ? ORDER BY id DESC LIMIT 1", (code,)
        ).fetchone()

    def conclude(self, code: str) -> tuple[str, dict[str, Any] | None]:
        return self._transition(code, "chamada", "concluida")

    def cancel(self, code: str) -> tuple[str, dict[str, Any] | None]:
        return self._transition(code, "aguardando", "cancelada")

    def _transition(
        self, code: str, expected_status: str, target_status: str
    ) -> tuple[str, dict[str, Any] | None]:
        with self._connect() as connection:
            connection.execute("BEGIN IMMEDIATE")
            row = self._find_latest(connection, code)
            if row is None:
                connection.rollback()
                return "not_found", None
            if row["status"] != expected_status:
                connection.rollback()
                return "conflict", None
            connection.execute(
                "UPDATE tickets SET status = ? WHERE id = ?", (target_status, row["id"])
            )
            connection.commit()
            updated = connection.execute(
                "SELECT * FROM tickets WHERE id = ?", (row["id"],)
            ).fetchone()
        return "ok", self._ticket(updated)

    def recall(self, code: str) -> tuple[str, dict[str, Any] | None]:
        called_at = now().isoformat(timespec="seconds")
        with self._connect() as connection:
            connection.execute("BEGIN IMMEDIATE")
            row = self._find_latest(connection, code)
            if row is None:
                connection.rollback()
                return "not_found", None
            if row["status"] != "chamada":
                connection.rollback()
                return "conflict", None
            panel_order = self._next_panel_order(connection)
            connection.execute(
                "UPDATE tickets SET called_at = ?, panel_order = ? WHERE id = ?",
                (called_at, panel_order, row["id"]),
            )
            connection.commit()
            updated = connection.execute(
                "SELECT * FROM tickets WHERE id = ?", (row["id"],)
            ).fetchone()
        return "ok", self._ticket(updated)

    def panel(self) -> list[dict[str, Any]]:
        with self._connect() as connection:
            rows = connection.execute(
                "SELECT * FROM tickets WHERE panel_order IS NOT NULL "
                "ORDER BY panel_order DESC LIMIT 5"
            ).fetchall()
        return [self._ticket(row) for row in rows]


PREFIX, PREFERRED_RATIO = load_variant()
STORE = QueueStore(select_database_path(), PREFIX, PREFERRED_RATIO)
STATIC_FILE = Path(__file__).resolve().parent / "static" / "index.html"


class RequestHandler(BaseHTTPRequestHandler):
    server_version = "FilaAtendimento/1.0"

    def do_GET(self) -> None:  # noqa: N802
        path = urlparse(self.path).path
        if path == "/":
            self._send_html(STATIC_FILE.read_text(encoding="utf-8"))
            return
        if path == "/healthz":
            self._send_json(HTTPStatus.OK, {"status": "ok"})
            return
        if path == "/senhas/proxima":
            ticket = STORE.call_next()
            if ticket is None:
                self._send_json(HTTPStatus.NOT_FOUND, {"erro": "fila_vazia"})
            else:
                self._send_json(HTTPStatus.OK, ticket)
            return
        if path == "/painel":
            self._send_json(HTTPStatus.OK, {"chamadas": STORE.panel()})
            return
        self._send_json(HTTPStatus.NOT_FOUND, {"erro": "rota_nao_encontrada"})

    def do_POST(self) -> None:  # noqa: N802
        path = unquote(urlparse(self.path).path)
        if path == "/senhas":
            body = self._read_json()
            if not isinstance(body, dict) or body.get("tipo") not in {
                "normal",
                "preferencial",
            }:
                self._send_json(HTTPStatus.UNPROCESSABLE_ENTITY, {"erro": "tipo_invalido"})
                return
            try:
                ticket = STORE.issue(body["tipo"])
            except OverflowError:
                self._send_json(
                    HTTPStatus.CONFLICT, {"erro": "limite_diario_atingido"}
                )
                return
            self._send_json(HTTPStatus.CREATED, ticket)
            return

        parts = [part for part in path.split("/") if part]
        if len(parts) == 3 and parts[0] == "senhas":
            code, action = parts[1].upper(), parts[2]
            if action == "concluir":
                outcome, ticket = STORE.conclude(code)
                self._send_transition(outcome, ticket, "senha_nao_chamada")
                return
            if action == "rechamar":
                outcome, ticket = STORE.recall(code)
                self._send_transition(outcome, ticket, "senha_nao_chamada")
                return
            if action == "cancelar":
                outcome, ticket = STORE.cancel(code)
                self._send_transition(outcome, ticket, "senha_nao_aguardando")
                return

        self._send_json(HTTPStatus.NOT_FOUND, {"erro": "rota_nao_encontrada"})

    def do_OPTIONS(self) -> None:  # noqa: N802
        self.send_response(HTTPStatus.NO_CONTENT)
        self._common_headers("application/json; charset=utf-8", 0)
        self.end_headers()

    def _read_json(self) -> Any:
        try:
            content_length = int(self.headers.get("Content-Length", "0"))
            if content_length <= 0:
                return None
            return json.loads(self.rfile.read(content_length).decode("utf-8"))
        except (ValueError, UnicodeDecodeError, json.JSONDecodeError):
            return None

    def _send_transition(
        self,
        outcome: str,
        ticket: dict[str, Any] | None,
        conflict_error: str,
    ) -> None:
        if outcome == "not_found":
            self._send_json(HTTPStatus.NOT_FOUND, {"erro": "senha_nao_encontrada"})
        elif outcome == "conflict":
            self._send_json(HTTPStatus.CONFLICT, {"erro": conflict_error})
        else:
            self._send_json(HTTPStatus.OK, ticket or {})

    def _common_headers(self, content_type: str, length: int) -> None:
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(length))
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Cache-Control", "no-store")

    def _send_json(self, status: HTTPStatus, payload: Any) -> None:
        body = json.dumps(payload, ensure_ascii=False, separators=(",", ":")).encode(
            "utf-8"
        )
        self.send_response(status)
        self._common_headers("application/json; charset=utf-8", len(body))
        self.end_headers()
        self.wfile.write(body)

    def _send_html(self, html: str) -> None:
        body = html.encode("utf-8")
        self.send_response(HTTPStatus.OK)
        self._common_headers("text/html; charset=utf-8", len(body))
        self.end_headers()
        self.wfile.write(body)

    def log_message(self, format: str, *args: Any) -> None:
        print(f"{self.address_string()} - {format % args}")


class ReusableThreadingHTTPServer(ThreadingHTTPServer):
    allow_reuse_address = True
    daemon_threads = True


def run() -> None:
    port = int(os.getenv("PORT", str(DEFAULT_PORT)))
    server = ReusableThreadingHTTPServer(("0.0.0.0", port), RequestHandler)
    print(
        f"Fila de atendimento em http://localhost:{port} "
        f"(prefixo={PREFIX}, razao={PREFERRED_RATIO}, banco={STORE.database_path})",
        flush=True,
    )
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()


if __name__ == "__main__":
    run()
