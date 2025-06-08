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
import subprocess
import uuid

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
        c.execute("SELECT filename FROM images ORDER BY rowid DESC LIMIT ? OFFSET ?", (limit, offset))
        total = conn.execute("SELECT COUNT(*) FROM images").fetchone()[0]
    else:
        c.execute("SELECT filename FROM images WHERE status = ? ORDER BY rowid DESC LIMIT ? OFFSET ?", (status, limit, offset))
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
    conn = sqlite3.connect('images.db')
    c = conn.cursor()
    c.execute("SELECT hash FROM images WHERE hash IS NOT NULL")
    existing_hashes = [imagehash.hex_to_hash(row[0]) for row in c.fetchall()]
    conn.close()
    for existing_hash in existing_hashes:
        if new_hash - existing_hash < 5:
            return True
    return False

def handle_image_upload(local_path, filename):
    allowed_extensions = (".jpg", ".jpeg", ".png", ".webp")
    if not filename.lower().endswith(allowed_extensions):
        print(f"Skipping unsupported file: {filename}")
        return None

    try:
        with Image.open(local_path) as img:
            phash = imagehash.phash(img)
            duplicate = is_duplicate(phash)
    except Exception as e:
        print(f"Error hashing {filename}: {e}")
        return None

    blob = bucket.blob(f"original/{filename}")
    blob.upload_from_filename(local_path)

    insert_image_metadata(filename, duplicate, phash)

    return {
        "filename": filename,
        "url": f"https://storage.googleapis.com/{bucket_name}/original/{filename}",
        "duplicate": duplicate
    }

@app.route("/api/scrape", methods=["POST"])
def scrape():
    data = request.get_json()
    url = data.get("url")
    temp_dir = f"/tmp/{uuid.uuid4()}"
    os.makedirs(temp_dir, exist_ok=True)

    try:
        config_path = os.path.join(os.path.dirname(__file__), "gallery-dl.conf")
        result = subprocess.run(
            ["gallery-dl", "--config", config_path, "--dest", temp_dir, url],
            stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True
        )

        if result.returncode != 0:
            print("Gallery-dl failed:", result.stderr)
            return jsonify({"success": False, "error": result.stderr}), 500

        uploaded = []

        for root, _, files in os.walk(temp_dir):
            for file in files:
                if file.lower().endswith((".jpg", ".jpeg", ".png", ".webp")):
                    filepath = os.path.join(root, file)
                    filename = secure_filename(file)
                    print("Handling file:", filename)

                    try:
                        result = handle_image_upload(filepath, filename)
                        if result:
                            uploaded.append(result)
                    except Exception as e:
                        print(f"Error processing {filename}: {e}")

        if not uploaded:
            return jsonify({"success": False, "error": "No images were found in the scrape."}), 400

        return jsonify({
            "success": True,
            "downloaded": len(uploaded),
            "uploaded": uploaded
        })


    except Exception as e:
        print("Scrape route failed:", e)
        return jsonify({"success": False, "error": str(e)}), 500

    finally:
        subprocess.run(["rm", "-rf", temp_dir])

if __name__ == "__main__":
    app.run(debug=True)