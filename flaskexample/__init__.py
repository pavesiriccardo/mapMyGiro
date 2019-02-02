import os,numpy as np
from flask import Flask, flash, request, redirect, url_for
from werkzeug.utils import secure_filename

local_path_stem=os.getenv('PATH_TO_APP')
UPLOAD_FOLDER = local_path_stem+'/flaskexample/upload_here'
CUTOUTS_FOLDER=local_path_stem+'/flaskexample/cutouts'
MODEL_PATH=local_path_stem+'/flaskexample/latest_model.h5'
ALLOWED_EXTENSIONS = set(['kml'])

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['CUTOUTS_FOLDER'] = CUTOUTS_FOLDER
app.config['MODEL_PATH'] = MODEL_PATH
app.config['SECRET_KEY']=os.getenv('SECRET_KEY')
print(app.secret_key)
JS_google_key=os.getenv('JS_GMAPS_KEY')
static_google_key=os.getenv('STC_GMAPS_KEY')
google_secret_key=os.getenv('GOOGLE_SECRET')


from flaskexample import backend,views


def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

#@app.route('/', methods=['GET', 'POST'])
@app.route('/compute', methods=['GET','POST'])
def upload_file():
    if request.method == 'POST':
        #print(request.form,'files:',request.files)
        L_touse=request.form['L']
        # check if the post request has the file part
        if "submit_upload" in request.form:
            file = request.files['file']
            if 'file' not in request.files:
            #flash('No file part')
                return redirect('/')
            if file.filename == '':
            #flash('No selected file')
                return redirect('/')
            if file and allowed_file(file.filename):
                filename = secure_filename(file.filename)
                file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
        elif "submit_example" in request.form:
            filename='example_directions.kml'
        # if user does not select file, browser also
        # submit an empty part without filename
        path=backend.load_path(os.path.join(app.config['UPLOAD_FOLDER'], filename))
        if len(L_touse)==0:
            route_length=backend.path_len(path)
            L_touse=route_length/100.
        else:
            L_touse=float(L_touse)
        return redirect(url_for('show_temp_page',
                                filename=filename,L_touse=L_touse))
    return '''
    <!doctype html>
    <title>Upload new File</title>
    <h1>Upload new KML File</h1>
    <form method=post enctype=multipart/form-data>
      <input type=file name=file>
      <input type="text" id="L_field" name='L' placeholder="Interval in km">
      <input type=submit value=Upload>
    </form>
    '''


#from flask import send_from_directory
