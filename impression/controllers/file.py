import os
import json

from flask import (Blueprint, flash, request, redirect, url_for,
                   send_from_directory, jsonify, g)
from flask_login import login_user, logout_user, login_required
from impression.decorators import user_is, user_has

from impression.utils import success
from impression.controls import get_payload
from impression.extensions import cache
from impression.models import Content, File, Tag, User
from impression.mixin import safe_commit
from werkzeug.utils import secure_filename

file_controller = Blueprint('File_controller', __name__)

APP_ROOT = os.path.dirname(os.path.abspath(__file__))

def allowed_file(filename):
    return '.' in filename and \
        filename.rsplit('.', 1)[1] in g.allowed_extensions


@file_controller.route('/upload_ajax', methods=['POST'])
def upload_ajax():
    return_value = success('The file was uploaded.')
    payload = get_payload(request)
    ufile = request.files['file']
    file_id = upload_file(payload, ufile)
    return_value['id'] = file_id
    return jsonify(return_value)


@file_controller.route('/upload', methods=['POST'])
def upload():
    payload = get_payload(request)
    ufile = request.files['file']
    file_id = upload_file(payload, ufile)
    if file_id:
        flash("File uploaded!")
    else:
        flash("There was a problem uploading that file.")
    return redirect("/admin/files/add")


def upload_file(payload, ufile):
    upload_folder = os.path.abspath(os.path.join(APP_ROOT, "../", '../', g.upload_directory))
    if ufile and allowed_file(ufile.filename):
        filename = secure_filename(ufile.filename)
        thumbnail_name = ''
        thumbnail_path = ''
        path = os.path.join(upload_folder, filename)
        print(path)
        if not os.path.isfile(path):
            ufile.save(path)
            try:
                # Create thumbnail
                from PIL import Image
                size = 128, 128
                im = Image.open(path)
                width, height = im.size
                im.thumbnail(size, Image.ANTIALIAS)
                file, ext = os.path.splitext(path)
                fname, fext = os.path.splitext(filename)
                ext = ext.lower()
                etype = ext.replace(".", "")
                if etype == 'jpg':
                    etype = 'jpeg'
                thumbnail_path = file + "_thumbnail" + ext
                thumbnail_name = fname + "_thumbnail" + ext
                im.save(thumbnail_path, etype)
            except (ImportError, IOError):
                width = 0
                height = 0

            afile = File(name=filename, path=path, thumbnail_name=thumbnail_name,
                         thumbnail_path=thumbnail_path, user_id=payload.get('user_id'),
                         size=os.path.getsize(path), width=width, height=height,
                         mimetype=ufile.mimetype)
            afile.insert()
            safe_commit()
            return afile.id
    return None


@file_controller.route('/uploads/<filename>')
def uploaded_file(filename):
    upload_folder = os.path.abspath(os.path.join(APP_ROOT, "../", '../', g.upload_directory))
    return send_from_directory(upload_folder, filename)


@file_controller.route('/get_tags', methods=['GET'])
# @cache.cached(timeout=CACHE_TIMEOUT)
def get_tags():
    tags = [t.name for t in Tag.all()]
    return json.dumps(tags)
