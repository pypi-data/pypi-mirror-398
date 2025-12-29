import hashlib
import json
import os
import tempfile
import threading
import time
from datetime import datetime, timedelta
from pathlib import Path

from flask import Flask, jsonify, request, send_file

app = Flask(__name__)

STORAGE_DIR = os.environ.get("SFT_STORAGE_DIR", "/data/sft")
METADATA_FILE = os.path.join(STORAGE_DIR, "metadata.json")
CLEANUP_INTERVAL = 60


class FileStorage:
    def __init__(self, storage_dir):
        self.storage_dir = Path(storage_dir)
        self.storage_dir.mkdir(parents=True, exist_ok=True)
        self.metadata_file = self.storage_dir / "metadata.json"
        self.metadata = self._load_metadata()
        self.lock = threading.Lock()

    def _load_metadata(self):
        if self.metadata_file.exists():
            try:
                with open(self.metadata_file, "r") as f:
                    return json.load(f)
            except:
                return {}
        return {}

    def _save_metadata(self):
        with open(self.metadata_file, "w") as f:
            json.dump(self.metadata, f, indent=2)

    def _generate_file_id(self):
        import random

        while True:
            file_id = str(random.randint(100000, 999999))
            if file_id not in self.metadata:
                return file_id

    def _calculate_sha256(self, filepath):
        sha256_hash = hashlib.sha256()
        with open(filepath, "rb") as f:
            for byte_block in iter(lambda: f.read(4096), b""):
                sha256_hash.update(byte_block)
        return sha256_hash.hexdigest()

    def store_file(self, file_obj, filename, expiry_seconds, custom_file_id=None):
        with self.lock:
            if custom_file_id:
                if custom_file_id in self.metadata:
                    raise ValueError(f"File ID '{custom_file_id}' already exists")
                file_id = custom_file_id
            else:
                file_id = self._generate_file_id()
            file_path = self.storage_dir / file_id

            file_obj.save(str(file_path))

            file_size = file_path.stat().st_size
            sha256 = self._calculate_sha256(file_path)
            expiry_time = datetime.now() + timedelta(seconds=expiry_seconds)

            self.metadata[file_id] = {
                "filename": filename,
                "size": file_size,
                "sha256": sha256,
                "expiry": expiry_time.isoformat(),
                "uploaded": datetime.now().isoformat(),
            }
            self._save_metadata()

            return {
                "file_id": file_id,
                "filename": filename,
                "size": file_size,
                "sha256": sha256,
                "expiry": expiry_time.isoformat(),
            }

    def get_file(self, file_id):
        with self.lock:
            if file_id not in self.metadata:
                return None

            metadata = self.metadata[file_id]
            expiry = datetime.fromisoformat(metadata["expiry"])

            if datetime.now() > expiry:
                self._delete_file(file_id)
                return None

            file_path = self.storage_dir / file_id
            if not file_path.exists():
                return None

            return {"path": str(file_path), "metadata": metadata}

    def _delete_file(self, file_id):
        file_path = self.storage_dir / file_id
        if file_path.exists():
            file_path.unlink()
        if file_id in self.metadata:
            del self.metadata[file_id]
            self._save_metadata()

    def cleanup_expired(self):
        with self.lock:
            now = datetime.now()
            expired_ids = []

            for file_id, metadata in self.metadata.items():
                expiry = datetime.fromisoformat(metadata["expiry"])
                if now > expiry:
                    expired_ids.append(file_id)

            for file_id in expired_ids:
                self._delete_file(file_id)

            if expired_ids:
                print(f"Cleaned up {len(expired_ids)} expired files")


storage = FileStorage(STORAGE_DIR)


def cleanup_worker():
    while True:
        time.sleep(CLEANUP_INTERVAL)
        try:
            storage.cleanup_expired()
        except Exception as e:
            print(f"Error during cleanup: {e}")


@app.route("/health", methods=["GET"])
def health():
    return jsonify({"status": "ok"})


@app.route("/upload", methods=["POST"])
def upload():
    if "file" not in request.files:
        return jsonify({"error": "No file provided"}), 400

    file = request.files["file"]
    if file.filename == "":
        return jsonify({"error": "No file selected"}), 400

    expiry_seconds = int(request.form.get("expiry", 3600))
    custom_file_id = request.form.get("file_id")

    try:
        result = storage.store_file(file, file.filename, expiry_seconds, custom_file_id)
        return jsonify(result)
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/download/<file_id>", methods=["GET"])
def download(file_id):
    file_info = storage.get_file(file_id)

    if not file_info:
        return jsonify({"error": "File not found or expired"}), 404

    return send_file(
        file_info["path"],
        as_attachment=True,
        download_name=file_info["metadata"]["filename"],
    )


@app.route("/info/<file_id>", methods=["GET"])
def info(file_id):
    file_info = storage.get_file(file_id)

    if not file_info:
        return jsonify({"error": "File not found or expired"}), 404

    return jsonify(file_info["metadata"])


def run_server(host="0.0.0.0", port=12345):
    cleanup_thread = threading.Thread(target=cleanup_worker, daemon=True)
    cleanup_thread.start()

    print(f"Starting Simple File Transfer Server on {host}:{port}")
    print(f"Storage directory: {STORAGE_DIR}")

    app.run(host=host, port=port, threaded=True)


if __name__ == "__main__":
    run_server()
