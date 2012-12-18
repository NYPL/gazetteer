import sys, json, os, datetime

from shapely.geometry import asShape, mapping
from fiona import collection

from core import Dump


def extract_shapefile(shapefile, uri_name, simplify_tolerance=None):
    
    for feature in collection(shapefile, "r"):
        
        geometry = feature["geometry"]
        properties = feature["properties"]
        
        #calculate centroid
        geom_obj = asShape(geometry)

        try:
            centroid = [geom_obj.centroid.x , geom_obj.centroid.y]    
        except AttributeError:
            print "Error: ", feature
            continue

       
        if properties["NAME"]:
            name = properties["NAME"]
        else:
            continue
        
        #feature code mapping
        feature_code = "ADM3"
       
        area = properties["AREATOT"]
                
        source = properties  #keep all fields anyhow
        
        # unique URI which internally gets converted to the place id
        # Must be unique!
        uri = uri_name + "." + properties["GEOID"] + "."+ feature["id"]
         
        timeframe = {}
        timeframe = {"start": "1980", "end": "1990"}
        
        updated = "2012-01-31"

        place = {
            "name":name,
            "centroid":centroid,
            "feature_code": feature_code,
            "geometry":geometry,
            "is_primary": True,
            "source": source,
            "alternate": [],
            "updated": updated,
            "area": area,
            "uris":[uri],
            "relationships": [],
            "timeframe":timeframe,
            "admin":[]

        }
        #print place
        dump.write(uri, place)
        

if __name__ == "__main__":
    shapefile, dump_path = sys.argv[1:3]
    uri_name = "http://www.census.gov/geo/www/cob/cs1990.html"
    #simplify_tolerance = .01 # ~ 11km (.001 = 111m)
    simplify_tolerance = None
    
    dump_basename = os.path.basename(shapefile)
    dump = Dump(dump_path + "/shapefile/"+ dump_basename + ".%04d.json.gz")
    
    extract_shapefile(shapefile, uri_name, simplify_tolerance)
    
    dump.close()


#python shapefile.py "/path/to/shapefile/buildings.shp"  /path/to/gz_dump

