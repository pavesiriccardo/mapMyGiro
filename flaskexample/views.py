from flask import render_template
from flaskexample import app,backend,JS_google_key,static_google_key
from flask import request,redirect,url_for
import os,json,pickle


@app.route('/')
@app.route('/input')
def produce_input_page():
    return render_template("input.html")


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




