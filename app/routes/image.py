from math import e
import os
import io
import re
from flask import Blueprint, render_template, request, redirect, url_for, session, send_file, send_from_directory, flash, jsonify
from werkzeug.utils import secure_filename
from app.utils.azure_utils import upload_image_to_azure, get_image_url, transform_image_in_cloud, rename_image_in_azure, downlaod_image_from_azure, delete_image_from_azure, list_user_images

bp = Blueprint('image', __name__)
# UPLOAD_FOLDER = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'uploads'))

# os.makedirs(UPLOAD_FOLDER, exist_ok=True)

def safe_int(value, default=0):
    try:
        return int(value)
    except (ValueError, TypeError):
        return default

def get_user_prefix():
    """Get the user prefix from the session."""
    return f"user_{session['user']}"

@bp.route('/upload', methods=['GET', 'POST'])
def upload_image():
    if "user" not in session:
        return redirect(url_for("auth.login"))
    
    if request.method == "POST":
        if 'image' not in request.files:
            flash("No image file part in the request.", "error")
            return redirect(request.url)
        
        image = request.files["image"]
        if image.filename == '':
            flash("No selected file.", "error")
            return redirect(request.url)
        if image:
            filename = secure_filename(image.filename)
            user_filename = f"{get_user_prefix()}_{filename}"
            try:
                azure_filename = upload_image_to_azure(image.stream, user_filename, image.content_type)
                image_url = get_image_url(azure_filename)
                
                #Store current image to session
                session['current_image'] = azure_filename
                session['original_filename'] =  filename
                
                flash("Image uploaded successfully!", "success")
                return render_template("dashboard.html", filename=azure_filename, image_url=image_url, original_name=filename)
            except Exception as e: 
                flash(f"Failed to upload image: {str(e)}", "error")
                return redirect(request.url)
    return render_template('upload.html')

@bp.route('/transform', methods=['POST'])
def transform_image():
    if "user" not in session:
        return redirect(url_for("auth.login"))
    
    current_image = session.get("current_image")
    if not current_image:
        flash("No image to transform.", "error")
        return redirect(url_for("image.upload_image"))
    
    width = safe_int(request.form.get("width"))
    height = safe_int(request.form.get("height"))
    angle = safe_int(request.form.get("angle"))
    
    if not any([width and height, angle]):
        flash("Please provide at least one transformation parameter (width and height, or angle).", "warning")
        return redirect(url_for("image.dashboard"))
    try:
        #transform image in cloud
        new_filename = transform_image_in_cloud(current_image, width=width, height=height, angle=angle)
        new_image_url = get_image_url(new_filename)
        session['current_image'] = new_filename
        flash("Image transformed successfully!", "success")
        return render_template("dashboard.html", filename=new_filename, image_url=new_image_url, original_ename=session.get('original_filename'))

    except Exception as e:
        flash("Failed to transform image: {str(e)}", "error")
        return redirect(url_for("image.dashboard"))



@bp.route('/rename', methods=['POST'])
def rename_image():
    if "user" not in session:
        return redirect(url_for("auth.login"))
    current_image = session.get("current_image")
    new_name = request.form.get("new_name", "").strip()
    
    if not current_image or not new_name:
        flash("No image to rename or new name not provided.", "error")
        return redirect(url_for("image.dashboard"))
    
    try:
        # Ensure the new name has a valid extension
        if '.' not in new_name:
            original_ext = current_image.split('.')[-1]
            new_name = f"{new_name}.{original_ext}"
            
        # Add user prefix to the new name
        new_filname = f"{get_user_prefix()}_{secure_filename(new_name)}"
        renamed_filename = rename_image_in_azure(current_image, new_filname)
        new_image_url = get_image_url(renamed_filename)
        
        session['current_image'] = renamed_filename 
        session['original_filename'] = new_name
        
        flash(f"Image renamed to {new_name}!", "success")
        return render_template("dashboard.html", filename=renamed_filename, image_url=new_image_url, original_name=new_name)
    except Exception as e:
        flash(f"Rename failed: {str(e)}", "error")
        return redirect(url_for('image.dashboard'))

@bp.route('/download')
def download_image():
    if "user" not in session:
        return redirect(url_for("auth.login"))
    current_image = session.get("current_image")
    if not current_image:
        flash("No image to download.", "error")
        return redirect(url_for("image.upload_image"))

    try:
        # Download the image from Azure Blob Storage
        pil_image = downlaod_image_from_azure(current_image)
        
        # Convert the PIL image to a byte stream
        img_io = io.BytesIO()
        format = 'PNG' if current_image.lower().endswith('.png') else 'JPEG'
        pil_image.save(img_io, format=format, quality=95)
        
        # Get original filename for download
        download_name = session.get('original_filename', current_image.split('_', 2)[-1])
        
        return send_file(
            img_io,
            mimetype=f'image/{format.lower()}',
            as_attachment=True,
            download_name=download_name
        )
    except Exception as e:
        flash(f"Failed to download image: {str(e)}", "error")
        return redirect(url_for("image.dashboard"))


    
@bp.route('/delete', methods=['POST'])
def delete_image():
    if "user" not in session:
        return redirect(url_for("auth.login"))
    
    current_image = session.get("current_image")
    if not current_image:
        flash("No image to delete.", "error")
        return redirect(url_for("image.upload_image"))
    
    try:
        delete_image_from_azure(current_image)
        session.pop('current_image', None)
        session.pop('original_filename', None)
        
        flash("Image deleted successfully!", "success")
        return redirect(url_for("image.upload_image"))
    
    except Exception as e:
        flash(f"Failed to delete image: {str(e)}", "error")
        return redirect(url_for("image.dashboard"))    

@bp.route('/gallery')
def gallery():
    if "user" not in session:
        return redirect(url_for("auth.login"))
    
    try:
        user_prefix = get_user_prefix()
        user_images = list_user_images(user_prefix)
        print(user_prefix)
        print(user_images)
        images_with_urls = [
            {
                "filename": img,
                "url": get_image_url(img),
                "display_name": img.split('_',2)[-1]
                # Remove user prefix
            }
            for img in user_images
        ]
        return render_template("gallery.html", images=images_with_urls)
    except Exception as e:
        flash(f"Failed to load gallery: {str(e)}", "error")
        return redirect(url_for("image.upload_image"))

@bp.route("/select/<filename>")
def select_image(filename):
    if "user" not in session:
        return redirect(url_for("auth.login"))
    
    # Validate the filename belongs to user
    if not filename.startswith(get_user_prefix()):
        flash("Unauthorised access.", "error")
        return redirect(url_for("image.gallery"))
    
    try:
        image_url = get_image_url(filename)
        session['current_image'] = filename
        session['original_filename'] = filename.split('_', 2)[-1]  # Remove user prefix for display
        
        return render_template("dashboard.html", filename=filename, image_url=image_url, original_name=session.get('original_filename'))
    except Exception as e:
        flash(f"Failed to select image: {str(e)}", "error")
        return redirect(url_for("image.gallery"))

@bp.route('/dashboard')
def dashboard():
    if "user" not in session:
        return redirect(url_for("auth.login"))

    current_image = session.get("current_image")
    if not current_image:
        flash("No image selected. Please upload an image first.", "info")
        return redirect(url_for("image.upload_image"))
    
    try:
        image_url = get_image_url(current_image)
        return render_template("dashboard.html", filename=current_image, image_url=image_url, original_name=session.get('original_filename'))
    
    except Exception as e:
        flash(f"Failed to load dashboard: {str(e)}", "error")
        return redirect(url_for("image.upload_image"))
# This code defines the routes for image upload, transformation, renaming, downloading, deleting, and viewing a gallery of images.