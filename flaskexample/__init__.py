import os,numpy as np
from flask import Flask, flash, request, redirect, url_for

local_path_stem=os.getenv('PATH_TO_APP')
UPLOAD_FOLDER = local_path_stem+'/flaskexample/upload_here'
CUTOUTS_FOLDER=local_path_stem+'/flaskexample/cutouts'
MODEL_PATH=local_path_stem+'/flaskexample/latest_model_GPU.h5'

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



#from flask import send_from_directory
