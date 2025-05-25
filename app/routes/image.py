import os
from flask import Blueprint, render_template, request, redirect, url_for, session, send_from_directory
from werkzeug.utils import secure_filename
from app.utils.image_utils import resize_image, rotate_image

bp = Blueprint('image', __name__)
UPLOAD_FOLDER = 'uploads'

os.makedirs(UPLOAD_FOLDER, exist_ok=True)

@bp.route('/upload', methods=['GET', 'POST'])
def upload_image():
    if "user" not in session:
        return redirect(url_for("auth.login"))
    if request.method == "POST":
        image = request.files["image"]
        filename = secure_filename(image.filename)
        path = os.path.join(UPLOAD_FOLDER, filename)
        image.save(path)
        return render_template("dashboard.html", filename=filename)
    return render_template('upload.html')

@bp.route('/transform/<filename>', methods=['POST'])
def transform_image(filename):
    path = os.path.join(UPLOAD_FOLDER, filename)
    width = int(request.form.get("width", 0))
    height = int(request.form.get("height", 0))
    angle = int(request.form.get("angle", 0))

    if width and height:
        resize_image(path, width, height)
    if angle:
        rotate_image(path, angle)

    return render_template("dashboard.html", filename=filename)

@bp.route("/uploads/<filename>")
def serve_image(filename):
    return send_from_directory(UPLOAD_FOLDER, filename)
