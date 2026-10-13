import os
import sqlite3
from flask import Flask, request, jsonify, render_template_string
from dotenv import load_dotenv
import cloudinary
import cloudinary.utils

# Load environment variables and configure Cloudinary
load_dotenv()
cloudinary.config(secure=True)  # Automatically picks up CLOUDINARY_URL from .env

app = Flask(__name__)

# ----------------------------------------------------
# DATABASE SETUP (Simulating your existing DB)
# ----------------------------------------------------
def init_db():
    conn = sqlite3.connect(':memory:', check_same_thread=False)
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE images (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT,
            public_id TEXT
        )
    ''')
    # Seed with existing Cloudinary public_ids (e.g., standard demo assets)
    cursor.executemany('INSERT INTO images (name, public_id) VALUES (?, ?)', [
        ('Puppy', 'samples/animals/puppy-bike'),
        ('Shoes', 'samples/ecommerce/shoes'),
        ('Beach', 'samples/landscapes/beach-boat')
    ])
    conn.commit()
    return conn

db_conn = init_db()

# ----------------------------------------------------
# ROUTES & WEB SERVICE
# ----------------------------------------------------
@app.route('/')
def index():
    """Simple Frontend to query images with transformations."""
    cursor = db_conn.cursor()
    cursor.execute('SELECT id, name FROM images')
    images = cursor.fetchall()
    
    # HTML template with a built-in transformation control form
    html_template = """
    <!DOCTYPE html>
    <html>
    <head><title>Cloudinary Image Transformer</title></head>
    <body>
        <h2>Select an Image & Apply Transformations</h2>
        <form action="/view-image" method="get">
            <label>Image:</label>
            <select name="img_id">
                {% for img in images %}
                    <option value="{{ img[0] }}">{{ img[1] }}</option>
                {% endfor %}
            </select>
            <br><br>
            <label>Width:</label> <input type="number" name="width" value="400"><br>
            <label>Height:</label> <input type="number" name="height" value="400"><br>
            <label>Crop Mode:</label>
            <select name="crop">
                <option value="fill">Fill (Resizes & crops)</option>
                <option value="thumb">Thumbnail</option>
                <option value="scale">Scale</option>
            </select><br>
            <label>Effect:</label>
            <select name="effect">
                <option value="none">None</option>
                <option value="grayscale">Grayscale</option>
                <option value="sepia">Sepia</option>
                <option value="cartoonify">Cartoonify</option>
            </select><br><br>
            <button type="submit">Generate Image</button>
        </form>
    </body>
    </html>
    """
    return render_template_string(html_template, images=images)


@app.route('/view-image', methods=['GET'])
def view_image():
    """Fetches public_id from DB and builds a modified Cloudinary URL on-the-fly."""
    img_id = request.args.get('img_id')
    width = request.args.get('width', 300)
    height = request.args.get('height', 300)
    crop = request.args.get('crop', 'fill')
    effect = request.args.get('effect', 'none')

    # 1. Fetch the image public_id from the database
    cursor = db_conn.cursor()
    cursor.execute('SELECT public_id FROM images WHERE id = ?', (img_id,))
    result = cursor.fetchone()

    if not result:
        return jsonify({"error": "Image not found"}), 404
    
    public_id = result[0]

    # 2. Build the transformation dictionary dynamically
    transformations = {
        "width": int(width),
        "height": int(height),
        "crop": crop
    }
    if effect != "none":
        transformations["effect"] = effect

    # 3. Use Cloudinary SDK to construct the optimized URL mapping
    transformed_url, _ = cloudinary.utils.cloudinary_url(
        public_id, 
        transformation=[transformations]
    )

    # 4. Render the transformed image directly to the client browser
    return f"""
    <h3>Transformed Image URL:</h3>
    <a href="{transformed_url}" target="_blank">{transformed_url}</a><br><br>
    <img src="{transformed_url}" alt="Transformed Image Output">
    <br><br><a href="/">Back</a>
    """

if __name__ == '__main__':
    app.run(debug=True)
