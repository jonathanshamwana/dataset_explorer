import os
import sqlite3
from flask import Flask, request, jsonify
from google.cloud import storage
from dotenv import load_dotenv
from werkzeug.utils import secure_filename
from db import init_db

load_dotenv()
app = Flask(__name__)
init_db()

# Google Cloud Storage setup
bucket_name = os.getenv("GCS_BUCKET_NAME")
gcs_client = storage.Client()
bucket = gcs_client.bucket(bucket_name)

# Insert image metadata into SQLite
def insert_image_metadata(filename):
    conn = sqlite3.connect('images.db')
    c = conn.cursor()
    c.execute('INSERT OR IGNORE INTO images (filename) VALUES (?)', (filename,))
    conn.commit()
    conn.close()

@app.route("/api/upload", methods=["POST"])
def upload():
    files = request.files.getlist("files")
    uploaded_files = []

    for file in files:
        filename = secure_filename(file.filename)
        blob = bucket.blob(f"original/{filename}")
        blob.upload_from_file(file, content_type=file.content_type)

        # Save metadata to SQLite
        insert_image_metadata(filename)

        uploaded_files.append({
            "filename": filename,
            "url": f"https://storage.googleapis.com/{bucket_name}/original/{filename}"
        })

    return jsonify(uploaded_files)

@app.route("/api/images", methods=["GET"])
def list_images():
    status = request.args.get("status", "all")
    limit = int(request.args.get("limit", 100))
    offset = int(request.args.get("offset", 0))

    conn = sqlite3.connect('images.db')
    c = conn.cursor()

    if status == "all":
        c.execute("SELECT filename FROM images LIMIT ? OFFSET ?", (limit, offset))
        total = conn.execute("SELECT COUNT(*) FROM images").fetchone()[0]
    else:
        c.execute("SELECT filename FROM images WHERE status = ? LIMIT ? OFFSET ?", (status, limit, offset))
        total = conn.execute("SELECT COUNT(*) FROM images WHERE status = ?", (status,)).fetchone()[0]

    filenames = [row[0] for row in c.fetchall()]
    conn.close()

    images = [{
        "filename": f,
        "url": f"https://storage.googleapis.com/{bucket_name}/original/{f}"
    } for f in filenames]

    return jsonify({"images": images, "total": total})

@app.route("/api/action", methods=["POST"])
def action():
    data = request.get_json()
    image_id = data.get("imageId")
    action = data.get("action")

    status_map = {"approve": "approved", "delete": "deleted"}
    new_status = status_map.get(action, "all")

    conn = sqlite3.connect('images.db')
    c = conn.cursor()
    c.execute("UPDATE images SET status = ? WHERE filename = ?", (new_status, image_id))
    conn.commit()
    conn.close()

    return jsonify({"success": True})
