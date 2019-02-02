from flaskexample import app,run_model,JS_google_key,static_google_key,google_secret_key
from flask import render_template,flash,redirect,url_for
import os,glob,numpy as np,pickle
import requests
from multiprocessing.dummy import Pool
from matplotlib import cm,colors
from requests.adapters import HTTPAdapter
from requests.packages.urllib3.util.retry import Retry

from requests.packages.urllib3.util import parse_url
import hashlib
import hmac
import base64

 

@app.route('/uploads/<filename>?<L_touse>')
def uploaded_file(filename,L_touse):
	L_touse=float(L_touse)
	if filename=='map_defined':
		dic_path_Ltouse=pickle.load(open(os.path.join(app.config['UPLOAD_FOLDER'], filename),'rb'))
		path=dic_path_Ltouse['path']
	else:
		path=load_path(os.path.join(app.config['UPLOAD_FOLDER'], filename))
	list_of_coords=[{'lat':pnt[0],'lng':pnt[1]} for pnt in path]#[{'lat':37.772, 'lng':-122.214},{'lat':21.291, 'lng':-157.821},{'lat':-18.142, 'lng':178.431},{'lat': -27.467,  'lng':153.027}]
	minlat=min([pnt[0] for pnt in path])
	minlong=min([pnt[1] for pnt in path])
	maxlat=max([pnt[0] for pnt in path])
	maxlong=max([pnt[1] for pnt in path])
	center_long=(minlong+maxlong)*.5
	center_lat=(minlat+maxlat)*.5
	route_length=path_len(path)

	points_list=points_along_path(path,L_touse)
	Nsamples=len(points_list)
	if Nsamples>250:
		flash('More than 250 images required, it is too many, sorry!')
		return redirect(url_for('produce_input_page'))
	#get list of nodes along colored polylines AND including the line endpoints. should start out the first L/2 bit as paved and the last little bit too

	list_of_lines=segmented_nodes_list(path,L=L_touse)
	list_of_lines=[[{'lat':pnt[0],'lng':pnt[1]} for pnt in single_line] for single_line in list_of_lines]
	jet=cm.get_cmap('jet',20)
	#color_list=[colors.to_hex(jet(col_fl)) for col_fl in np.linspace(0,1,len(list_of_lines))]
	list_of_filenames=[app.config['CUTOUTS_FOLDER']+'/test/'+str(idx) for idx in range(len(points_list))]
	fetch_from_Google(points_list,list_of_filenames)
	unpaved_ids,paved_ids=run_model.predict_batch(app.config['CUTOUTS_FOLDER'])
	all_probabi={idx:prob for (idx,prob) in unpaved_ids+paved_ids}
	color_list=[colors.to_hex(jet(0))]+[colors.to_hex(jet(all_probabi[idx])) for idx in range(len(points_list))]
	#Produce list_of_lines encoding the colored polylines
	#set colors of polylines and export them to the javascript

	#HTML='Path length is: '+str(path_len(path))+' km <BR>'
	#for pnt in points_list:
	#	HTML+=str(pnt)+' <BR> '
	#HTML+='<BR> For a Total of '+str(len(points_list))+' point estimates:'
	#HTML+=' <BR> '+'The Unpaved pieces are ID: '+str(unpaved_ids)+' <BR> '
	#HTML+=' <BR> '+'The Paved pieces are ID: '+str(paved_ids)+' <BR> <BR> <BR>'
	#return HTML #send_from_directory(app.config['UPLOAD_FOLDER'],filename)
	return render_template("my_output.html",Nsamples=Nsamples,route_length="{:.1f}".format(round(route_length*10)/10.),JS_google_key=JS_google_key,color_list=color_list,list_of_lines=list_of_lines,maxlong=maxlong,minlat=minlat,maxlat=maxlat,minlong=minlong,center_lat=center_lat,center_long=center_long,filename=filename,L_touse=L_touse)



def load_path(filename):
	inp=open(filename)
	idx=0
	st1=False
	st2=False
	path=[]
	for line in inp:
	    if '</LineString>' in line:
	        st1=False
	    if '</coordinates>' in line:
	        st2=False
	    if st1 and st2:
	        #print(tuple(map(float,line.split(',')))[:2][::-1])
	        path.append(tuple(map(float,line.split(',')))[:2][::-1])
	        idx+=1
	    elif '<coordinates>' in line:
	        st2=True
	    elif '<LineString>' in line:
	        st1=True
	return path

def distance_two_points(lat1,long1,lat2,long2,cos_lat1=None):
    if cos_lat1 is None:
        cos_lat1=np.cos(lat1/180.*np.pi)
    earth_rad=3958.761 #in mi   #6371.008 #in km
    lat1*=np.pi/180
    lat2*=np.pi/180
    long1*=np.pi/180
    long2*=np.pi/180
    return earth_rad*np.sqrt((lat1-lat2)**2+cos_lat1**2*(long1-long2)**2)

def path_len(path):
	last_p=path[0]
	cos_lat1=np.cos(last_p[0]/180.*np.pi)
	dist=0
	for loc in path[1:]:
	    dist+=distance_two_points(last_p[0],last_p[1],loc[0],loc[1],cos_lat1)
	    last_p=loc
	return dist


def points_along_path(path,L=1.,start_from=0):
	cos_lat1=np.cos(path[0][0]/180.*np.pi)
	points_list=[]
	last_node=path[0]
	d_accum=start_from
	for loc in path[1:]:
	    current_segment_l=distance_two_points(last_node[0],last_node[1],loc[0],loc[1],cos_lat1)
	    #print('New node, current_segment length is ',current_segment_l,' and the distance count is at:', d_accum)
	    if d_accum+current_segment_l>L:
	        #print('Need to put down at least a point')
	        #Need to put at least a point before the next node. after inserting the point reset d_accum=0
	        end_point_lat=last_node[0]
	        end_point_long=last_node[1]
	        dist_to_segment_end=current_segment_l    
	        while(dist_to_segment_end>L-d_accum):
	            current_step_l=L-d_accum
	            frac_of_segment=current_step_l/current_segment_l
	            end_point_lat+=frac_of_segment*(loc[0]-last_node[0])
	            end_point_long+=frac_of_segment*(loc[1]-last_node[1])
	            points_list.append((end_point_lat,end_point_long))
	            #print('Putting down a point with step of:',current_step_l)
	            d_accum=0
	            dist_to_segment_end-=current_step_l    
	        d_accum=dist_to_segment_end
	    else:
	        d_accum+=current_segment_l
	    last_node=loc
	return points_list

def empty_cutouts_folder():
	files = glob.glob(app.config['CUTOUTS_FOLDER']+'/test/*')
	for f in files:
	    os.remove(f)



def requests_retry_session(retries=6,backoff_factor=0.4,status_forcelist=(500, 502, 504),session=None):
    session = session or requests.Session()
    retry = Retry(total=retries,read=retries,connect=retries,backoff_factor=backoff_factor,status_forcelist=status_forcelist)
    adapter = HTTPAdapter(max_retries=retry)
    session.mount('http://', adapter)
    session.mount('https://', adapter)
    return session

def fetch_from_Google(list_of_coords,list_of_filenames):
    empty_cutouts_folder()
    api_key = static_google_key
    url = "https://maps.googleapis.com/maps/api/staticmap?"
    zoom = 20
    def fetch_one_image(argum):
        idx,(lat,long)=argum
        print(idx,lat,long)
        center = "{0:.6f}".format(lat)+","+"{0:.6f}".format(long)     #max size=640
        #r = requests.get(url + "center=" + center + "&zoom=" +str(zoom) + "&size=640x640&format=jpg&maptype=satellite&key=" +api_key)
        unsigned_url=url + "center=" + center + "&zoom=" +str(zoom) + "&size=640x640&format=jpg&maptype=satellite&key=" +api_key
        signed_url=sign_url(input_url=unsigned_url,  secret=google_secret_key)
        r = requests_retry_session().get(signed_url) 
        f = open(list_of_filenames[idx]+'.jpeg', 'wb') 
        f.write(r.content) 
        f.close() 
    #map(fetch_one_image,enumerate(list_of_coords))
    with Pool(30) as p:
        pm = p.map(fetch_one_image,enumerate(list_of_coords))
    #for argum in enumerate(list_of_coords):
     #       fetch_one_image(argum)




#get list of nodes along colored polylines AND including the line endpoints. should start out the first L/2 bit as paved and the last little bit too

def segmented_nodes_list(path,L=1.):
	cos_lat1=np.cos(path[0][0]/180.*np.pi)
	nodes_plus_endpoints_list=[path[0]]
	is_endpoint=[False]
	last_node=path[0]
	d_accum=L/2.  #This makes the points which are endpoints of the colored polylines.
	for loc in path[1:]:
	    current_segment_l=distance_two_points(last_node[0],last_node[1],loc[0],loc[1],cos_lat1)
	    #print('New node, current_segment length is ',current_segment_l,' and the distance count is at:', d_accum)
	    if d_accum+current_segment_l>L:
	        #print('Need to put down at least a point')
	        #Need to put at least a point before the next node. after inserting the point reset d_accum=0
	        end_point_lat=last_node[0]
	        end_point_long=last_node[1]
	        dist_to_segment_end=current_segment_l    
	        while(dist_to_segment_end>L-d_accum):
	            current_step_l=L-d_accum
	            frac_of_segment=current_step_l/current_segment_l
	            end_point_lat+=frac_of_segment*(loc[0]-last_node[0])
	            end_point_long+=frac_of_segment*(loc[1]-last_node[1])
	            nodes_plus_endpoints_list.append((end_point_lat,end_point_long))
	            is_endpoint.append(True)
	            #print('Putting down a point with step of:',current_step_l)
	            d_accum=0
	            dist_to_segment_end-=current_step_l    
	        d_accum=dist_to_segment_end
	    else:
	        d_accum+=current_segment_l
	    nodes_plus_endpoints_list.append(loc)
	    is_endpoint.append(False)
	    last_node=loc
	list_of_paths=[[]]
	for pnt,is_end in zip(nodes_plus_endpoints_list,is_endpoint):
		if not is_end:
			list_of_paths[-1].append(pnt)
		else:
			list_of_paths[-1].append(pnt)
			list_of_paths.append([pnt])
	return list_of_paths


class geocoo(object):
    def __init__(self,lat=0,long=0):
        self.lat=lat
        self.long=long
    def latlong(self):
        return (self.lat,self.long)
    def longlat(self):
        return (self.long,self.lat)
    def __str__(self):
        return (str(self.lat),str(self.long))
    def __repr__(self):
        return repr((self.lat,self.long))



def get_route_from_waypoints(coordinate_list):
	#coordinate_list needs to be list of pairs in lat,long order
	coordinate_list=[geocoo(lat,long) for lat,long in coordinate_list]
	html_OSRM_1='http://router.project-osrm.org/route/v1/driving/'
	html_OSRM_2=';'.join([','.join([str(coo) for coo in geo.longlat()]) for geo in coordinate_list+[coordinate_list[0]]])
	html_OSRM_3='?alternatives=false&annotations=nodes'
	#print(html_OSRM_1+html_OSRM_2+html_OSRM_3)
	response = requests.get(html_OSRM_1+html_OSRM_2+html_OSRM_3)
	nodes_json = response.json()
	N_routes=len(nodes_json['routes'])

	#Use the first route for now
	id_route=0
	distance=nodes_json['routes'][id_route]['distance']
	assert(len(nodes_json['routes'][id_route]['legs'])==len(coordinate_list))

	all_nodes=[]
	for id_leg in range(len(coordinate_list)):
	    all_nodes+=nodes_json['routes'][id_route]['legs'][id_leg]['annotation']['nodes']
	    
	print('Nodes along route:',len(all_nodes),'Unique nodes:',len(set(all_nodes)))#,all_nodes[:4]

	overpass_url = "http://overpass-api.de/api/interpreter"
	overpass_query_1 = """[out:json];
	        (
	         """
	overpass_query_2=""" );
	        (._;>;);
	        out;
	        """

	all_coords={id_node:(0,0) for id_node in all_nodes}
	next_node_to_fetch=0#len(all_nodes)
	while next_node_to_fetch<len(all_nodes):
	    Nleft=len(all_nodes)-next_node_to_fetch
	    Nfetc=min(Nleft,300)
	    fetching=all_nodes[next_node_to_fetch:(next_node_to_fetch+Nfetc)]
	    overpass_query=overpass_query_1
	    for node in fetching:
	        overpass_query+="node("+str(node)+");\n "
	    overpass_query+=overpass_query_2
	    next_node_to_fetch+=Nfetc
	    response = requests.get(overpass_url, params={'data': overpass_query})
	    jso=response.json()
	    for node_co in jso['elements']:
	        all_coords[node_co['id']]=geocoo(node_co['lat'],node_co['lon'])

	#print(all_coords)
	route=[]
	for node in all_nodes:
	    route.append(all_coords[node].latlong()) #list of pairs of (lat,long) in floats
	#print(len(route))
	return route




def sign_url(input_url=None,  secret=None):
  """ Sign a request URL with a Crypto Key.
      Usage:
      from urlsigner import sign_url
      signed_url = sign_url(input_url=my_url,
                            client_id=CLIENT_ID,
                            client_secret=CLIENT_SECRET)
      Args:
      input_url - The URL to sign
      client_id - Your Client ID
      client_secret - Your Crypto Key
      Returns:
      The signed request URL
  """
  # Return if any parameters aren't given
  if not input_url  or not secret:
    return None
  # Add the Client ID to the URL
  #input_url += "&client=%s" % (client_id)
  url = parse_url(input_url)
  # We only need to sign the path+query part of the string
  url_to_sign = url.path + "?" + url.query
  # Decode the private key into its binary format
  # We need to decode the URL-encoded private key
  decoded_key = base64.urlsafe_b64decode(secret)
  # Create a signature using the private key and the URL-encoded
  # string using HMAC SHA1. This signature will be binary.
  signature = hmac.new(decoded_key, url_to_sign.encode(), hashlib.sha1)
  # Encode the binary signature into base64 for use within a URL
  encoded_signature = base64.urlsafe_b64encode(signature.digest())
  original_url = url.scheme + "://" + url.netloc + url.path + "?" + url.query
  # Return signed URL
  return original_url + "&signature=" + encoded_signature.decode()

