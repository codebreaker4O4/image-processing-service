import os
from flask import Blueprint, render_template, request, redirect, url_for, session, send_from_directory, flash
from werkzeug.utils import secure_filename
from app.utils.image_utils import resize_image, rotate_image
from app.utils.azure_utils import upload_image_to_azure, get_image_url

bp = Blueprint('image', __name__)
UPLOAD_FOLDER = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'uploads'))

os.makedirs(UPLOAD_FOLDER, exist_ok=True)

def safe_int(value, default=0):
    try:
        return int(value)
    except (ValueError, TypeError):
        return default


@bp.route('/upload', methods=['GET', 'POST'])
def upload_image():
    if "user" not in session:
        return redirect(url_for("auth.login"))
    if request.method == "POST":
        image = request.files["image"]
        filename = secure_filename(image.filename)
        azure_filename = upload_image_to_azure(image.stream, filename, image.content_type)
        image_url = get_image_url(azure_filename)
        return render_template("dashboard.html", filename=azure_filename, image_url=image_url)
    return render_template('upload.html')

@bp.route('/transform/<filename>', methods=['POST'])
def transform_image(filename):
    path = os.path.join(UPLOAD_FOLDER, filename)
    width = safe_int(request.form.get("width"))
    height = safe_int(request.form.get("height"))
    angle = safe_int(request.form.get("angle"))
    try:
        if width and height:
            resize_image(path, width, height)
        if angle:
            rotate_image(path, angle)
        flash("Image transformed successfully!", "success")

    except Exception as e:
        print("Error:", e)
        flash("Failed to transform image. Please try again.", "error")


    return redirect(url_for("image.upload_image", filename=filename))

@bp.route("/uploads/<filename>")
def serve_image(filename):
    # print("Serving file from path:", os.path.join(UPLOAD_FOLDER, filename))
    # print("Trying to serve:", filename)
    # print("From folder:", UPLOAD_FOLDER)
    # full_path = os.path.join(UPLOAD_FOLDER, filename)
    # print("Full file path:", full_path)
    # print("File exists:", os.path.exists(full_path))

    return send_from_directory(UPLOAD_FOLDER, filename)

@bp.route('/dashboard')
def dashboard():
    if "user" not in session:
        return redirect(url_for("auth.login"))

    filename = session.get("last_uploaded")
    if not filename:
        flash("No image uploaded yet.")
        return redirect(url_for("image.upload_image"))

    return render_template("dashboard.html", filename=filename)
