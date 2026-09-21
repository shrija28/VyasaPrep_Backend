"""Frontend route compatibility layer.

The active application is the React + Vite app in frontend-react. This
blueprint keeps the legacy Flask routes from crashing and serves the SPA
for browser navigation paths that are not actual static files.
"""

from __future__ import annotations

from pathlib import Path

from flask import Blueprint, redirect, send_file, send_from_directory, request

router = Blueprint("routes_pages", __name__)

_PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent.parent
_DIST_DIR = _PROJECT_ROOT / "frontend-react" / "dist"
_LEGACY_HTML_DIR = _PROJECT_ROOT / "frontend" / "html"


def _send_spa():
    """Serve the production React build when available; otherwise fall back to dev mode info."""
    index_path = _DIST_DIR / "index.html"
    if index_path.exists():
        return send_from_directory(str(_DIST_DIR), "index.html")

    fallback = _LEGACY_HTML_DIR / "landing.html"
    if fallback.exists():
        return send_file(str(fallback), mimetype="text/html")

    return (
        "<html><head><title>VyasaPrep Backend</title></head><body style='font-family:sans-serif;padding:2.5rem;line-height:1.6;'>"
        "<h2 style='color:#1e293b;'>VyasaPrep Backend API Server is Running!</h2>"
        "<p style='color:#475569;'>You are accessing the <b>Flask Backend API</b> (Port 8000).</p>"
        "<p style='color:#475569;'>To use the VyasaPrep App, please open the React Frontend in your browser at: <br/>"
        "<a href='http://localhost:5173' style='font-size:1.25rem;color:#4f46e5;font-weight:bold;'>http://localhost:5173</a></p>"
        "</body></html>",
        200
    )


@router.route("/", methods=["GET"])
@router.route("/index.html", methods=["GET"])
def root_page():
    return _send_spa()


@router.route("/login", methods=["GET"])
@router.route("/register", methods=["GET"])
@router.route("/dashboard", methods=["GET"])
@router.route("/admin", methods=["GET"])
@router.route("/admin/dashboard", methods=["GET"])
@router.route("/institution", methods=["GET"])
@router.route("/institution/dashboard", methods=["GET"])
@router.route("/student/institution/dashboard", methods=["GET"])
@router.route("/contact-us", methods=["GET"])
@router.route("/syllabus", methods=["GET"])
def spa_compat_routes():
    return _send_spa()


@router.route("/favicon.ico", methods=["GET"])
def favicon():
    candidates = [
        _DIST_DIR / "favicon.svg",
        _PROJECT_ROOT / "frontend-react" / "public" / "favicon.svg",
        _PROJECT_ROOT / "frontend" / "favicon.svg",
    ]
    for candidate in candidates:
        if candidate.exists():
            return send_file(str(candidate), mimetype="image/svg+xml")
    return redirect("/", code=302)


@router.route("/<path:filename>", methods=["GET"])
def catch_all(filename):
    """Serve any built asset or fall back to the React app for client-side routes."""
    if filename.startswith("api/"):
        return "Not Found", 404

    asset_path = _DIST_DIR / filename
    if asset_path.exists() and asset_path.is_file():
        return send_from_directory(str(_DIST_DIR), filename)

    if request.path.startswith("/assets/"):
        return "Not Found", 404

    return _send_spa()


__all__ = ["router"]
