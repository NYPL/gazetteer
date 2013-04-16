from ox.django.shortcuts import render_to_json_response
from django.core.paginator import Paginator, InvalidPage, EmptyPage
from django.db.models import Q
#from django.http import HttpResponse
from place import Place
from pyelasticsearch.exceptions import ElasticHttpNotFoundError
try:
    import json
except:
    import simplejson as json
from django.views.decorators.csrf import csrf_exempt
from django.http import QueryDict
import datetime
import math
from models import FeatureCode
from django.contrib.gis.geos import GEOSGeometry
from shortcuts import get_place_or_404
import re


@csrf_exempt 
def new_place_json(request):
    ''' Takes a GeoJSON string as POST data and saves it as a new place
         saves and returns back geojson for the place
    '''
    if not request.user.is_authenticated():
        return render_to_json_response({'error': 'You do not have permissions to do this.'}, status=403)
        
    if not request.method == 'POST':
        return render_to_json_response({'error': 'Method Not Allowed'}, status=405)
        
    geojson = json.loads(request.body)
    if geojson.has_key("comment"):
        comment = geojson.pop("comment")
    else:
        comment = ''
    json_obj = geojson.pop("properties")
    json_obj['geometry'] = geojson['geometry']
    json_obj['centroid'] = []
    if geojson["geometry"]:
        centroid = GEOSGeometry(json.dumps(json_obj['geometry'])).centroid
        json_obj['centroid'] = list(centroid.coords)      
        
    p = Place(json_obj)
    
    import random, hashlib
    p.id = hashlib.md5(p.name + str(random.random())).hexdigest()[:16]        
    p.relationships = []
    
    p.uris.append("http://gazetteer.in/feature/"+p.id)  #FIXME for the url
    
    if request.user.is_authenticated():
        user = request.user.email
    else:
        user = 'unknown'
        
    metadata = {
        'user': user,
        'comment': comment
    }
    
    p.save(metadata=metadata)
    
    return render_to_json_response(p.to_geojson())
        
        
     
@csrf_exempt
def place_json(request, id):

    place = get_place_or_404(id)
              
    if request.method == 'GET':
        '''
            Return GeoJSON for Place
        '''
        geo_json = place.to_geojson()
        return render_to_json_response(geo_json)
    
    elif request.method == 'PUT':
        '''
            Takes a GeoJSON string as PUT data and saves Place
            Saves and returns  back GeoJSON for place.
        '''
        #FIXME: check permissions
#        if not request.user.is_staff():
#            return render_to_json_response({'error': 'You do not have permissions to edit this place.'}, status=403)    
        if not request.user.is_authenticated():
            return render_to_json_response({'error': 'You do not have permissions to edit this place.'}, status=403) 
        geojson = json.loads(request.body)
        if geojson.has_key("comment"):
            comment = geojson.pop("comment")
        else:
            comment = ''
        json_obj = geojson.pop("properties")
        json_obj['geometry'] = geojson['geometry']

        #handle getting centroid:
        centroid = GEOSGeometry(json.dumps(json_obj['geometry'])).centroid
        json_obj['centroid'] = centroid.coords      
        
        p = Place(json_obj)        
        
        if request.user.is_authenticated():
            user = request.user.email
        else:
            user = 'unknown'
        metadata = { #What all does metadata need? Should this be in a function?
            'user': user,
            'comment': comment
        }

        p.save(metadata=metadata)
        new_place = Place.objects.get(id)
        return render_to_json_response(new_place.to_geojson())
        

    elif request.method == 'DELETE':
        #check permissions / delete object       
        if not request.user.is_authenticated():
            return render_to_json_response({'error': 'You do not have permissions to delete this place.'}, status=403) 
        return render_to_json_response({'error': 'Not implemented'}, status=501)

    else:
        return render_to_json_response({'error': 'Method Not Allowed'}, status=405)


def search(request):
    '''
        Takes GET params:
            q: search string
            bbox: bounding box string
                - if "false", will search for places without geos
                - if empty string / not specified, will search for places with and without geos, not constrained by bbox
            per_page: results per page int, default=100
            page: page no (starting with 1) int, default=1

        Returns:
            GeoJSON feed of search results
            Extra properties of feed:
                total: total number of results
                max_score: max score in results (?)
                page: page number
    '''
    query = request.GET.get("q", "")
    if query == "":
        query = '*'
    feature_type = request.GET.get("feature_type", None)
    if feature_type:
        if FeatureCode.objects.filter(typ=feature_type).count() > 0:
            query += ' feature_code:%s' % feature_type.upper()
    per_page = int(request.GET.get("per_page", 100)) #FIXME: add error handling if int conversion fails
    page = int(request.GET.get("page", 1))
    page_0 = page - 1 #model method requires page number to be zero-based whereas API accepts 1-based.
    bboxString = request.GET.get("bbox", "")
    start_date = request.GET.get("start_date", None)
    end_date = request.GET.get("end_date", None)

    year_regex = re.compile(r'^[0-9]{4}')

    if start_date and year_regex.match(start_date):
        start_date += "-01-01"

    if end_date and year_regex.match(end_date):
        end_date += "-12-31"

    if bboxString and bboxString != "false":
        bbox = [float(b) for b in bboxString.split(",")]
    elif bboxString == 'false':
        bbox = False
    else:
        bbox = None
    result = Place.objects.search(query, bbox=bbox, start_date=start_date, end_date=end_date, per_page=per_page, page=page_0)
    total = result['total']
    pages = int(math.ceil(total / (per_page + .0))) #get total number of pages
     
    ret = {
        'type': 'FeatureCollection',
        'features': [p.to_geojson() for p in result['places']],
        'total': total,
        'page': result['page'],
        'pages': pages,
        'per_page': result['per_page'],
        'max_score': result['max_score']
    }
    return render_to_json_response(ret)


def similar(request, id):
    '''
        Takes place ID
        Returns GeoJSON feed of similar places.
            Extra properties of feed:
                total: total number of similar places
                max_score: max score of similarity (?)
    '''
    try:
        place = Place.objects.get(id)
    except ElasticHttpNotFoundError:
        return render_to_json_response({'error': 'Place not found'}, status=404)          

    if request.method == 'GET':
        similar_places = place.find_similar()
        geojson = {
            'type': 'FeatureCollection',
            'total': similar_places['total'],
            'max_score': similar_places['max_score'],
            'features': [p.to_geojson() for p in similar_places['places']]
        }
        return render_to_json_response(geojson)
        #return render_to_json_response({'error': 'Not implemented'}, status=501)

    else:
        return render_to_json_response({'error': 'Method Not Allowed'}, status=405)


def hierarchy(request, id):
    try:
        place = Place.objects.get(id)
    except ElasticHttpNotFoundError:
        return render_to_json_response({'error': 'Place not found'}, status=404)

    if request.method == 'GET':
        #hierarchy_json = place.get_hierarchy()        
        #return render_to_json_response(hierarchy_json)
        return render_to_json_response({'error': 'Not implemented'}, status=501)

    else:
        return render_to_json_response({'error': 'Method Not Allowed'}, status=405)


def history(request, id):
    '''
        Returns array of revision objects for Place
    '''
    try:
        place = Place.objects.get(id)
    except ElasticHttpNotFoundError:
        return render_to_json_response({'error': 'Place not found'}, status=404)

    if request.method == 'GET':
        history_json = Place.objects.history(place)
        #history_json = place.get_history()        
        return render_to_json_response(history_json)
        #return render_to_json_response({'error': 'Not implemented'}, status=501)

    else:
        return render_to_json_response({'error': 'Method Not Allowed'}, status=405)

@csrf_exempt
def revision(request, id, revision):
    '''
        Get GeoJSON of a place at given revision
    '''
    place = get_place_or_404(id)

    if request.method == 'GET':
        revision = Place.objects.revision(place,revision)
        geojson = revision['place'].to_geojson()
        geojson['version'] = revision['version']
        geojson['digest'] = revision['digest']
        return render_to_json_response(geojson)


    elif request.method == 'PUT':
        if not request.user.is_authenticated():
            return render_to_json_response({'error': 'You do not have permissions to rollback this place.'}, status=403) 
        user = request.user.email
        data = json.loads(request.body)
        comment = data.get('comment', '')
        metadata = {
            'user': user,
            'comment': comment
        }       
        place.rollback(revision, metadata=metadata) #FIXME: handle invalid revision ids
        return render_to_json_response(place.to_geojson())

    else:
        return render_to_json_response({'error': 'Method Not Allowed'}, status=405)

@csrf_exempt
def relations(request, id):
    '''
        Returns GeoJSON feed for related places. Adds a property 'relation_type' to geojson properties to indicate type of relations
    '''

    place = get_place_or_404(id)

    features = []
    for obj in place.relationships:
        geojson = Place.objects.get(obj['id']).to_geojson()
        geojson['properties']['relation_type'] = obj['type']
        features.append(geojson)

    relations_geojson = {
        'type': 'FeatureCollection',
        'features': features
    }
   
    return render_to_json_response(relations_geojson)

@csrf_exempt
def add_delete_relation(request, id1, relation_type, id2):
    place1 = get_place_or_404(id1)
    place2 = get_place_or_404(id2)
    if relation_type not in Place.RELATION_CHOICES.keys():
        return render_to_json_response({'error': 'Invalid relation type'}, status=404)

    if not request.user.is_authenticated():
        return render_to_json_response({'error': 'You do not have permissions to edit delations for this place.'}, status=403) 
  
    comment = QueryDict(request.body).get("comment", "")
    username = request.user.email

    metadata = {
        'user': username,
        'comment': comment
    }

    if request.method == 'PUT':
        place1.add_relation(place2, relation_type, metadata)
    if request.method == 'DELETE':
        place1.delete_relation(place2, metadata)

    return relations(request, place1.id)


#@csrf_exempt
#def add_relation(request, id):
#    '''
#    Add relation for a place with id, takes JSON in a PUT request
#        target_id: <string> id of place being related to
#        relation_type: <string> type of relation
#        metadata:
#            user: <string> username
#            comment: <string> comment about change
#    '''

#    place = get_place_or_404(id)
#    if request.method == 'PUT':
#        #FIXME: check permissions
#        data = json.loads(request.body)
#        #FIXME: handle validation / sending back errors
#        place.add_relation(data['target_id'], data['relation_type'], data['metadata'])
#        return render_to_json_response(place.to_geojson())
#    else:
#        return render_to_json_response({'error': 'Method Not Allowed'}, status=405)



def feature_codes_autocomplete(request):
    '''
        Used for autocomplete: return Feature Codes matching GET param 'q'
    '''
    query = request.GET.get("q", "a")
    page_limit = int(request.GET.get("page_limit", 10))
    page = int(request.GET.get("page", 1))
    matched_codes = FeatureCode.objects.filter(Q(cls__icontains=query) | Q(typ__icontains=query) | Q(name__icontains=query) | Q(description__icontains=query))       
    paginator = Paginator(matched_codes, page_limit)
    results = paginator.page(page)
    items = [obj.to_json() for obj in results.object_list]  
    return render_to_json_response({
        'items': items,
        'has_next': results.has_next()
    })    


