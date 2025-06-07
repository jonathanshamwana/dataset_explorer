import os
import sqlite3
from flask import Flask, request, jsonify
from google.cloud import storage
from dotenv import load_dotenv
from werkzeug.utils import secure_filename
from db import init_db
from PIL import Image
import imagehash
import tempfile

load_dotenv()
app = Flask(__name__)

init_db()

# Google Cloud Storage setup
bucket_name = os.getenv("GCS_BUCKET_NAME")
gcs_client = storage.Client()
bucket = gcs_client.bucket(bucket_name)

# Insert image metadata into SQLite
def insert_image_metadata(filename, duplicate, hash_value):
    conn = sqlite3.connect('images.db')
    c = conn.cursor()
    c.execute('''
        INSERT INTO images (filename, duplicate, hash)
        VALUES (?, ?, ?)
        ON CONFLICT(filename) DO UPDATE SET
            duplicate=excluded.duplicate,
            hash=excluded.hash
    ''', (filename, int(duplicate), str(hash_value)))
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

        temp = tempfile.NamedTemporaryFile(delete=False)
        file.seek(0)
        temp.write(file.read())
        temp.close()

        with Image.open(temp.name) as img:
            phash = imagehash.phash(img)
            duplicate = is_duplicate(phash)

        os.unlink(temp.name)

        insert_image_metadata(filename, duplicate, phash)

        uploaded_files.append({
            "filename": filename,
            "url": f"https://storage.googleapis.com/{bucket_name}/original/{filename}",
            "duplicate": duplicate
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

@app.route("/api/stats", methods=["GET"])
def stats():
    conn = sqlite3.connect("images.db")
    c = conn.cursor()

    approved = c.execute("SELECT COUNT(*) FROM images WHERE status = 'approved'").fetchone()[0]
    total = c.execute("SELECT COUNT(*) FROM images").fetchone()[0]

    conn.close()
    return jsonify({"approved": approved, "total": total})

def is_duplicate(new_hash):
    print("Checking if duplicate...")
    conn = sqlite3.connect('images.db')
    c = conn.cursor()
    c.execute("SELECT hash FROM images WHERE hash IS NOT NULL")
    existing_hashes = [imagehash.hex_to_hash(row[0]) for row in c.fetchall()]
    conn.close()
    for existing_hash in existing_hashes:
        print("Checking a hash...")
        if new_hash - existing_hash < 5:
            print("DUPLICATE DUPLICATE")
            return True
    print("No matching hashes found...")
    return False
