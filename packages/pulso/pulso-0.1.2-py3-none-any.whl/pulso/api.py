"""HTTP API server for Pulso."""

from typing import Optional

from flask import Flask, jsonify, request

from .core import fetch, get_metadata, has_changed, snapshot
from .fetcher import FetchError


def _get_url(payload: Optional[dict]) -> Optional[str]:
    if payload and isinstance(payload, dict):
        url = payload.get("url")
        if url:
            return url
    return request.args.get("url")


def create_app() -> Flask:
    app = Flask(__name__)

    @app.get("/health")
    def health() -> tuple:
        return jsonify({"status": "ok"}), 200

    @app.post("/fetch")
    def fetch_endpoint() -> tuple:
        payload = request.get_json(silent=True) or {}
        url = _get_url(payload)
        force = bool(payload.get("force", False))
        if url is None:
            return jsonify({"error": "Missing 'url'"}), 400

        try:
            html = fetch(url, force=force)
        except FetchError as exc:
            return jsonify({"error": str(exc), "url": url}), 502

        return jsonify({"url": url, "html": html}), 200

    @app.get("/metadata")
    def metadata_endpoint() -> tuple:
        url = _get_url(None)
        if url is None:
            return jsonify({"error": "Missing 'url'"}), 400

        metadata = get_metadata(url)
        if metadata is None:
            return jsonify({"error": "Not cached", "url": url}), 404

        return jsonify(metadata), 200

    @app.get("/has_changed")
    def has_changed_endpoint() -> tuple:
        url = _get_url(None)
        if url is None:
            return jsonify({"error": "Missing 'url'"}), 400

        try:
            changed = has_changed(url)
        except FetchError as exc:
            return jsonify({"error": str(exc), "url": url}), 502

        return jsonify({"url": url, "changed": changed}), 200

    @app.post("/snapshot")
    def snapshot_endpoint() -> tuple:
        payload = request.get_json(silent=True) or {}
        url = _get_url(payload)
        if url is None:
            return jsonify({"error": "Missing 'url'"}), 400

        path = snapshot(url)
        if path is None:
            return jsonify({"error": "Not cached", "url": url}), 404

        return jsonify({"url": url, "snapshot_path": str(path)}), 200

    return app
