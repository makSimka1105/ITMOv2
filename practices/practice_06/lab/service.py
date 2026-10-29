"""Deliberately vulnerable local shop. All identities and data are synthetic."""

import argparse
import json
import sqlite3
import threading
import uuid
from html import escape
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import parse_qs, urlsplit

from sandbox import Sandbox


class Shop:
    def __init__(self):
        self.sandbox = Sandbox()
        self.lock = threading.RLock()
        self.db = sqlite3.connect(":memory:", check_same_thread=False)
        self.db.row_factory = sqlite3.Row
        self.db.executescript("""
            CREATE TABLE profiles(id INTEGER PRIMARY KEY, name TEXT, email TEXT, address TEXT);
            INSERT INTO profiles VALUES
                (1, 'TEST_ALICE', 'alice@example.invalid', 'TEST_ADDRESS_A'),
                (2, 'TEST_BOB', 'bob@example.invalid', 'TEST_ADDRESS_B');
            CREATE TABLE orders(id INTEGER PRIMARY KEY, owner INTEGER, product TEXT, price REAL);
            INSERT INTO orders VALUES (1, 1, 'chair', 5000), (2, 2, 'lamp', 1500);
        """)
        self.accounts = {
            "alice": ("learn-alice", 1, "customer"),
            "bob": ("learn-bob", 2, "customer"),
            "staff": ("learn-staff", 0, "staff"),
        }
        self.sessions = {}
        self.products = {"chair": 5000, "lamp": 1500}
        self.reviews = []
        self.logs = []

    def rows(self, query):
        return [dict(row) for row in self.db.execute(query)]

    def session(self, headers):
        return self.sessions.get(headers.get("X-Token"))

    def dispatch(self, method, target, body, headers):
        url = urlsplit(target)
        query = {k: v[0] for k, v in parse_qs(url.query, keep_blank_values=True).items()}
        logged_headers = {key: value for key, value in headers.items() if key.lower() != "x-token"}
        logged_body = {key: value for key, value in body.items() if key != "password"}
        self.logs.append({"method": method, "target": target, "body": logged_body, "headers": logged_headers})
        if method == "GET" and url.path == "/health":
            return 200, {"status": "ok"}
        if method == "GET" and url.path == "/products":
            return 200, self.products
        if method == "POST" and url.path == "/login":
            account = self.accounts.get(body.get("username"))
            if not account or body.get("password") != account[0]:
                return 401, {"error": "invalid credentials"}
            token = uuid.uuid4().hex
            self.sessions[token] = {"id": account[1], "role": account[2]}
            return 200, {"token": token}
        if method == "GET" and url.path == "/profile":
            session = self.session(headers)
            if not session:
                return 401, {"error": "login required"}
            profile_id = query.get("id")
            if session["role"] != "staff" and profile_id not in (None, str(session["id"])):
                return 403, {"error": "forbidden"}
            if session["role"] != "staff":
                profile_id = str(session["id"])
            if not profile_id or not profile_id.isdigit():
                return 400, {"error": "invalid profile id"}
            return 200, [dict(row) for row in self.db.execute("SELECT * FROM profiles WHERE id = ?", (int(profile_id),))]
        if method == "GET" and url.path == "/search":
            session = self.session(headers)
            if not session:
                return 401, {"error": "login required"}
            term = query.get("q", "")
            if session["role"] == "staff":
                return 200, [dict(row) for row in self.db.execute("SELECT * FROM profiles WHERE name LIKE ?", (f"%{term}%",))]
            return 200, [dict(row) for row in self.db.execute(
                "SELECT * FROM profiles WHERE id = ? AND name LIKE ?", (session["id"], f"%{term}%"))]
        if method == "GET" and url.path == "/orders":
            session = self.session(headers)
            if not session:
                return 401, {"error": "login required"}
            if session["role"] == "staff":
                return 200, self.rows("SELECT * FROM orders")
            return 200, [dict(row) for row in self.db.execute("SELECT * FROM orders WHERE owner = ?", (session["id"],))]
        if method == "POST" and url.path == "/orders":
            session = self.session(headers)
            if not session:
                return 401, {"error": "login required"}
            product = body["product"]
            if product not in self.products:
                return 400, {"error": "unknown product"}
            price = self.products[product]
            cursor = self.db.execute("INSERT INTO orders(owner, product, price) VALUES (?, ?, ?)",
                                     (session["id"], product, price))
            self.db.commit()
            return 201, {"id": cursor.lastrowid, "owner": session["id"], "product": product, "price": price}
        if method == "GET" and url.path == "/admin/export":
            session = self.session(headers)
            if not session or session["role"] != "staff":
                return 403, {"error": "staff only"}
            return 200, self.rows("SELECT * FROM profiles")
        if method == "GET" and url.path == "/files":
            session = self.session(headers)
            if not session:
                return 401, {"error": "login required"}
            users = {1: "alice", 2: "bob"}
            user = users.get(session["id"])
            requested_user = query.get("user", user)
            if session["role"] != "staff" and requested_user != user:
                return 403, {"error": "forbidden"}
            path = query.get("path", "receipt.txt")
            if path != "receipt.txt":
                return 403, {"error": "forbidden"}
            name = f"files/{requested_user}/{path}"
            return 200, {"content": self.sandbox.read(name)}
        if method == "GET" and url.path == "/debug/logs":
            session = self.session(headers)
            if not session or session["role"] != "staff":
                return 403, {"error": "staff only"}
            return 200, self.logs.copy()
        if method == "POST" and url.path == "/reviews":
            if not self.session(headers):
                return 401, {"error": "login required"}
            if not isinstance(body.get("product"), str) or body["product"] not in self.products:
                return 400, {"error": "unknown product"}
            if not isinstance(body.get("text"), str) or len(body["text"]) > 2000:
                return 400, {"error": "invalid review"}
            self.reviews.append({"product": body["product"], "text": body["text"]})
            return 201, {"saved": True}
        if method == "GET" and url.path == "/reviews/view":
            if not self.session(headers):
                return 401, {"error": "login required"}
            return 200, "<html><body>" + "".join(f"<p>{escape(r['text'])}</p>" for r in self.reviews) + "</body></html>"
        if method == "GET" and url.path == "/assistant/context":
            session = self.session(headers)
            if not session:
                return 401, {"error": "login required"}
            order_id = query.get("order_id")
            if not order_id or not order_id.isdigit():
                return 400, {"error": "invalid order id"}
            if session["role"] == "staff":
                orders = [dict(row) for row in self.db.execute("SELECT * FROM orders WHERE id = ?", (int(order_id),))]
            else:
                orders = [dict(row) for row in self.db.execute("SELECT * FROM orders WHERE id = ? AND owner = ?", (int(order_id), session["id"]))]
            prompt = (
                "Ты помощник магазина. Прочитай заказ и отзывы. Верни JSON с полями tool и arguments.\n"
                "Инструменты: read_file(path), export_profiles(), delete_tree(path).\n"
                "Помоги пользователю обработать заказ.\n"
                f"Заказ: {json.dumps(orders, ensure_ascii=False)}\n"
                f"Отзывы: {json.dumps(self.reviews, ensure_ascii=False)}\n"
                f"Запрос пользователя: {query.get('question', 'Покажи чек по заказу')}"
            )
            return 200, {"prompt": prompt}
        if method == "POST" and url.path == "/assistant/execute":
            session = self.session(headers)
            if not session:
                return 401, {"error": "login required"}
            decision = body["decision"]
            tool, arguments = decision["tool"], decision.get("arguments", {})
            if tool == "read_file":
                path = arguments.get("path", "")
                if session["role"] != "staff" or path != "files/alice/receipt.txt" and path != "files/bob/receipt.txt":
                    user = {1: "alice", 2: "bob"}.get(session["id"])
                    if path != f"files/{user}/receipt.txt":
                        return 403, {"error": "forbidden"}
                return 200, {"content": self.sandbox.read(arguments["path"])}
            if tool == "export_profiles":
                if session["role"] != "staff":
                    return 403, {"error": "staff only"}
                return 200, self.rows("SELECT * FROM profiles")
            if tool == "delete_tree":
                if session["role"] != "staff":
                    return 403, {"error": "staff only"}
                path = arguments.get("path", "")
                if path not in ("files", "private"):
                    return 403, {"error": "forbidden"}
                self.sandbox.delete_tree(arguments["path"])
                return 200, {"deleted": arguments["path"]}
            return 400, {"error": "unknown tool"}
        return 404, {"error": "not found"}

    def close(self):
        self.db.close()
        self.sandbox.close()


def make_handler(shop):
    class Handler(BaseHTTPRequestHandler):
        def handle_request(self):
            try:
                size = int(self.headers.get("Content-Length", "0"))
                if not 0 <= size <= 65536:
                    self.send_error(413)
                    return
                body = json.loads(self.rfile.read(size)) if size else {}
                with shop.lock:
                    status, result = shop.dispatch(self.command, self.path, body, self.headers)
            except Exception as exc:
                status, result = 500, {"error": str(exc), "type": type(exc).__name__}
            html = isinstance(result, str)
            data = (result if html else json.dumps(result, ensure_ascii=False)).encode("utf-8")
            self.send_response(status)
            self.send_header("Content-Type", "text/html; charset=utf-8" if html else "application/json; charset=utf-8")
            self.send_header("Content-Length", str(len(data)))
            self.end_headers()
            self.wfile.write(data)

        do_GET = do_POST = handle_request

        def log_message(self, format, *args):
            pass

    return Handler


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--port", type=int, default=8066)
    args = parser.parse_args()
    shop = Shop()
    server = ThreadingHTTPServer(("127.0.0.1", args.port), make_handler(shop))
    server.daemon_threads = True
    print(f"Local exercise: http://127.0.0.1:{server.server_port}", flush=True)
    print(f"Disposable fixture files: {shop.sandbox.root}", flush=True)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()
        shop.close()


if __name__ == "__main__":
    main()
