from flaskexample import app,backend,JS_google_key,static_google_key,run_model
from flask import request,redirect,url_for,send_from_directory,render_template,flash
import os,json,pickle,glob
from matplotlib import cm,colors
from werkzeug.utils import secure_filename


ALLOWED_EXTENSIONS = set(['kml'])


@app.route('/')
@app.route('/input')
def produce_input_page():
    return render_template("input.html")

@app.route('/about_page')
def about_p():
  return render_template("about_page.html")



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


@app.route('/temp_route/<filename>?<L_touse>')
def show_temp_page(filename,L_touse):
  if filename=='map_defined':
    dic_path_Ltouse=pickle.load(open(os.path.join(app.config['UPLOAD_FOLDER'], filename),'rb'))
    path=dic_path_Ltouse['path']
    L_touse=dic_path_Ltouse['L_touse']
    print(len(path))
  else:
    path=backend.load_path(os.path.join(app.config['UPLOAD_FOLDER'], filename))
  list_of_coords=[{'lat':pnt[0],'lng':pnt[1]} for pnt in path]#[{'lat':37.772, 'lng':-122.214},{'lat':21.291, 'lng':-157.821},{'lat':-18.142, 'lng':178.431},{'lat': -27.467,  'lng':153.027}]
  minlat=min([pnt[0] for pnt in path])
  minlong=min([pnt[1] for pnt in path])
  maxlat=max([pnt[0] for pnt in path])
  maxlong=max([pnt[1] for pnt in path])
  center_long=(minlong+maxlong)*.5
  center_lat=(minlat+maxlat)*.5
  return render_template("temp_route2.html",JS_google_key=JS_google_key,list_of_coords=list_of_coords,maxlong=maxlong,minlat=minlat,maxlat=maxlat,minlong=minlong,center_lat=center_lat,center_long=center_long,filename=filename,L_touse=L_touse)
  #return render_template("my_output.html",list_of_lines=list_of_lines,maxlong=maxlong,minlat=minlat,maxlat=maxlat,minlong=minlong,center_lat=center_lat,center_long=center_long,filename=filename,L_touse=L_touse)


@app.route('/read_waypoints',methods=['GET','POST'])
def read_waypoints():
  if request.method == 'POST':
    alljson = request.get_data()
    #print(alljson)
    print(list(request.form.keys()),[request.form[key] for key in request.form.keys()])
    list_of_dicts=json.loads(request.form['path'])
    print(list_of_dicts)
    path=backend.get_route_from_waypoints([(pnt['lat'],pnt['lng'])  for pnt in list_of_dicts])
    if len(request.form['L_touse'])==0:
      route_length=backend.path_len(path)
      L_touse=route_length/100. #Use 100 samples by default
    else:
      L_touse=float(request.form['L_touse'])
    dic_path_Ltouse={'path':path,'L_touse':L_touse}
    outp=open(os.path.join(app.config['UPLOAD_FOLDER'], 'map_defined'),'wb')
    pickle.dump(dic_path_Ltouse, outp)
    outp.close()
    return ""
  else:
    return redirect(url_for('show_temp_page',filename='map_defined',L_touse=1.))

@app.route('/input_map',methods=['GET'])
def temp_input_map():
    return render_template("temp_input_map.html",JS_google_key=JS_google_key,center_lat=42.446435, center_long=-76.501122)

@app.route('/export_route/<filename>')
def export_route_func(filename):
  if filename=='map_defined':
    dic_path_Ltouse=pickle.load(open(os.path.join(app.config['UPLOAD_FOLDER'], filename),'rb'))
    path=dic_path_Ltouse['path']
  else:
    path=backend.load_path(os.path.join(app.config['UPLOAD_FOLDER'], filename))
  #kml = simplekml.Kml()
  #lin = kml.newlinestring(name="mapMyGiro_export", description="A route generated by mapMyGiro",coords=[(lng,lat) for (lat,lng) in path],tessellate=1)
  #lin.style.linestyle.color = simplekml.Color.red  # Red
  #lin.style.linestyle.width = 3
  #kml.save(os.path.join(app.config['UPLOAD_FOLDER'], 'mapMyGiro_route.kml'))
  outp=open(os.path.join(app.config['UPLOAD_FOLDER'], 'mapMyGiro_route.kml'),'w')
  outp.write(KML_opening)
  for (lat,lng) in path:
    outp.write(str(lng)+','+str(lat)+',0\n')
  outp.write(KML_closing)
  outp.close()
  return send_from_directory(app.config['UPLOAD_FOLDER'],'mapMyGiro_route.kml', as_attachment=True)






KML_opening="""<?xml version="1.0" encoding="UTF-8"?>
<kml xmlns="http://www.opengis.net/kml/2.2">
  <Document>
    <name>mapMyGiro_route.kml</name>
    <Style id="line-FF0000-3000-normal">
      <LineStyle>
        <color>ff0000ff</color>
        <width>3</width>
      </LineStyle>
    </Style>
    <Style id="line-FF0000-3000-highlight">
      <LineStyle>
        <color>ff0000ff</color>
        <width>4.5</width>
      </LineStyle>
    </Style>
    <StyleMap id="line-FF0000-3000">
      <Pair>
        <key>normal</key>
        <styleUrl>#line-FF0000-3000-normal</styleUrl>
      </Pair>
      <Pair>
        <key>highlight</key>
        <styleUrl>#line-FF0000-3000-highlight</styleUrl>
      </Pair>
    </StyleMap>
    <Placemark>
      <name>mapMyGiro_export</name>
      <description>A route generated by mapMyGiro</description>
      <styleUrl>#line-FF0000-3000</styleUrl>
      <LineString>
        <tessellate>1</tessellate>
        <coordinates>
        """

KML_closing="""</coordinates>
      </LineString>
    </Placemark>
  </Document>
</kml>
"""




@app.route('/results/<filename>?<L_touse>')
def compute_results(filename,L_touse):
  L_touse=float(L_touse)
  if filename=='map_defined':
    dic_path_Ltouse=pickle.load(open(os.path.join(app.config['UPLOAD_FOLDER'], filename),'rb'))
    path=dic_path_Ltouse['path']
  else:
    path=backend.load_path(os.path.join(app.config['UPLOAD_FOLDER'], filename))
  list_of_coords=[{'lat':pnt[0],'lng':pnt[1]} for pnt in path]#[{'lat':37.772, 'lng':-122.214},{'lat':21.291, 'lng':-157.821},{'lat':-18.142, 'lng':178.431},{'lat': -27.467,  'lng':153.027}]
  minlat=min([pnt[0] for pnt in path])
  minlong=min([pnt[1] for pnt in path])
  maxlat=max([pnt[0] for pnt in path])
  maxlong=max([pnt[1] for pnt in path])
  center_long=(minlong+maxlong)*.5
  center_lat=(minlat+maxlat)*.5
  route_length=backend.path_len(path)

  points_list=backend.points_along_path(path,L_touse)
  Nsamples=len(points_list)
  if Nsamples>250:
    flash('More than 250 images required, it is too many, sorry!')
    return redirect(url_for('produce_input_page'))
  #get list of nodes along colored polylines AND including the line endpoints. should start out the first L/2 bit as paved and the last little bit too

  list_of_lines=backend.segmented_nodes_list(path,L=L_touse)
  list_of_lines=[[{'lat':pnt[0],'lng':pnt[1]} for pnt in single_line] for single_line in list_of_lines]
  jet=cm.get_cmap('jet',20)
  #color_list=[colors.to_hex(jet(col_fl)) for col_fl in np.linspace(0,1,len(list_of_lines))]
  list_of_filenames=[app.config['CUTOUTS_FOLDER']+'/test/'+str(idx) for idx in range(len(points_list))]
  backend.fetch_from_Google(points_list,list_of_filenames)
  unpaved_ids,paved_ids=run_model.predict_batch(app.config['CUTOUTS_FOLDER'])
  all_probabi={idx:prob for (idx,prob) in unpaved_ids+paved_ids}
  color_list=[colors.to_hex(jet(0))]+[colors.to_hex(jet(all_probabi[idx])) for idx in range(len(points_list))]
  #Produce list_of_lines encoding the colored polylines
  #set colors of polylines and export them to the javascript

  #HTML='Path length is: '+str(path_len(path))+' km <BR>'
  #for pnt in points_list:
  # HTML+=str(pnt)+' <BR> '
  #HTML+='<BR> For a Total of '+str(len(points_list))+' point estimates:'
  #HTML+=' <BR> '+'The Unpaved pieces are ID: '+str(unpaved_ids)+' <BR> '
  #HTML+=' <BR> '+'The Paved pieces are ID: '+str(paved_ids)+' <BR> <BR> <BR>'
  #return HTML #send_from_directory(app.config['UPLOAD_FOLDER'],filename)
  return render_template("my_output.html",Nsamples=Nsamples,route_length="{:.1f}".format(round(route_length*10)/10.),JS_google_key=JS_google_key,color_list=color_list,list_of_lines=list_of_lines,maxlong=maxlong,minlat=minlat,maxlat=maxlat,minlong=minlong,center_lat=center_lat,center_long=center_long,filename=filename,L_touse=L_touse)



