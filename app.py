from flask import Flask, request, jsonify,render_template
from flask_cors import CORS
from downloadImage import image_downloader

app = Flask(__name__,template_folder="Template")
CORS(app)  # Allow requests from the web browser

@app.route('/')
def home():
    return render_template("index.html")

@app.route("/download-images", methods=["POST"])
def download_images():
    data = request.get_json()
    queries = data.get("queries")
    limit = data.get("limit", 10)

    # debug the Attributes
    print(f'{queries=}')
    
    if not queries:
        return jsonify({"error": "No queries provided"}), 400

    try:
        image_downloader(queries, base_dir="data", limit=limit)
        return jsonify({"status": "Download complete"})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == "__main__":
    app.run(debug=True)
