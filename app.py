# import section
from flask import Flask, request, jsonify, render_template, send_file
from apscheduler.schedulers.background import BackgroundScheduler

from flask_cors import CORS
from downloadImage import image_downloader
import os
import shutil
import uuid
import zipfile
import io
import time
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__, template_folder="Template", static_folder="static")
CORS(app) # Allow requests from the web browser

# Track cleanup status globally
cleanup_log = {
    "folders_deleted": 0,
    "zips_deleted": 0,
    "last_run": None,
    "triggered_by_scheduler": False
}

@app.route('/')
def home():
    return render_template("index.html")

@app.route("/download-images", methods=["POST"])
def download_images():
    data = request.get_json()
    queries = data.get("queries")
    limit = data.get("limit", 10)

    # debugg Attribute
    logger.debug(f'Received queries is : {queries}')

    if not queries:
        return jsonify({"error": "No queries provided"}), 400

    session_id = str(uuid.uuid4())
    base_dir = os.path.join("static", "downloads", session_id)
    os.makedirs(base_dir, exist_ok=True)

    try:
        # Download images
        image_downloader(queries, base_dir=base_dir, limit=limit)
        # Create ZIP
        zip_path = os.path.join("static", "zips", f"{session_id}.zip")
        os.makedirs(os.path.dirname(zip_path), exist_ok=True)

        with zipfile.ZipFile(zip_path, 'w') as zip_file:
            for root, _, files in os.walk(base_dir):
                for file in files:
                    file_path = os.path.join(root, file)
                    arcname = os.path.relpath(file_path, base_dir)
                    zip_file.write(file_path, arcname)

        # Return redirect URL to gallery
        return jsonify({"redirect": f"/gallery/{session_id}"})

    except Exception as e:
        return jsonify({"error": str(e)}), 500
    
@app.route('/gallery/<session_id>')
def show_gallery(session_id):
    folder_path = os.path.join("static", "downloads", session_id)
    zip_path = os.path.join("static", "zips", f"{session_id}.zip")

    if not os.path.exists(folder_path):
        return "Gallery not found", 404

    images_by_category = {}
    for root, _, files in os.walk(folder_path):
        for file in files:
            rel_path = os.path.relpath(os.path.join(root, file), "static")
            img_url = f"/static/{rel_path.replace('\\','/')}"
            category = file.split("_")[0]  # Assuming file name is like Healthy_0.jpg
            if category not in images_by_category:
                images_by_category[category] = []

            images_by_category[category].append(img_url)
    return render_template("gallery.html", images_by_category=images_by_category, zip_url=f"/{zip_path}",session_id=session_id)

@app.route('/download-zip/<session_id>')
def download_zip(session_id):
    zip_dir = os.path.join("static", "zips")
    # Find the first zip file that matches the session_id
    for file in os.listdir(zip_dir):
        if file.endswith(".zip") and session_id in file:
            zip_path = os.path.join(zip_dir, file)
            return send_file(zip_path, as_attachment=True, download_name="dataset.zip")

    return "ZIP file not found", 404

# Optional cleanup route (can be automated later)
def run_cleanup_logic():
    now = time.time()

    def clean_dir_and_collect_ids(path, age_minutes=15):
        deleted_ids = []
        if not os.path.exists(path): return deleted_ids
        for folder in os.listdir(path):
            folder_path = os.path.join(path, folder)
            if os.path.isdir(folder_path) and now - os.path.getmtime(folder_path) > age_minutes * 60:
                shutil.rmtree(folder_path)
                deleted_ids.append(folder)
        return deleted_ids

    deleted_sessions = clean_dir_and_collect_ids("static/downloads")
    folders_deleted = len(deleted_sessions)

    zips_deleted = 0
    for filename in os.listdir("static/zips"):
        if filename.endswith(".zip") and filename.replace(".zip", "") in deleted_sessions:
            os.remove(os.path.join("static/zips", filename))
            zips_deleted += 1

    cleanup_log["folders_deleted"] = folders_deleted
    cleanup_log["zips_deleted"] = zips_deleted
    cleanup_log["last_run"] = time.strftime("%Y-%m-%d %H:%M:%S")
    cleanup_log["triggered_by_scheduler"] = True

# Route to render the cleanup report
@app.route("/cleanup")
def manual_cleanup():
    cleanup_log["triggered_by_scheduler"] = False  # reset flag after displaying
    return render_template("cleanup.html", log=cleanup_log)

# Used by frontend to check status
@app.route("/check-cleanup-status")
def check_cleanup_status():
    return jsonify({"redirect": cleanup_log.get("triggered_by_scheduler", False)})

if __name__ == "__main__":
    scheduler = BackgroundScheduler()
    scheduler.add_job(func=lambda: app.app_context().push() or run_cleanup_logic(), trigger="interval", minutes=20)
    scheduler.start()

    # port = int(os.environ.get("PORT", 5000))  # default to 5000 if not set
    # app.run(host='0.0.0.0', port=port,debug=True)
    try:
        app.run(host='0.0.0.0', debug=True)
    except (KeyboardInterrupt, SystemExit):
        scheduler.shutdown()
    
