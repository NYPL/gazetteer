# pass in shapefile 
#open shapefile
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

        name_array = []
        if properties["LM_NAME"]:
            name_array.append(properties["LM_NAME"])
            
        if properties["DESIG_ADDR"]:
            name_array.append(properties["DESIG_ADDR"])
        
        name = ','.join(name_array)
        #feature code mapping
        feature_code = "BLDG"
                
        source = properties  #keep all fields anyhow
        
        # unique URI which internally gets converted to the place id
        # Must be unique!
        uri = uri_name + "." + properties["BBL"] + "."+ feature["id"]
         
        timeframe = {}
        
        #admin?
        
        updated = "2009-06-23"
        

        place = {
            "name":name,
            "centroid":centroid,
            "feature_code": feature_code,
            "geometry":geometry,
            "is_primary": True,
            "source": source,
            "updated": updated,
            "uris":[uri],
            "relationships": [],
            "timeframe":timeframe,
            "admin":[]

        }

        dump.write(uri, place)
        

if __name__ == "__main__":
    shapefile, uri_name, dump_path = sys.argv[1:4]
    
    #simplify_tolerance = .01 # ~ 11km (.001 = 111m)
    simplify_tolerance = None
    
    dump_basename = os.path.basename(shapefile)
    dump = Dump(dump_path + "/shapefile/"+ dump_basename + ".%04d.json.gz")
    
    extract_shapefile(shapefile, uri_name, simplify_tolerance)
    
    dump.close()


#python shapefile.py "/path/to/shapefile/buildings.shp" "http://maps.nypl.org/warper/layers/870" /path/to/gz_dump 0.002

#COUNT_BLDG (Integer) = 1
#NON_BLDG (String) = (null)
#VACANT_LOT (Integer) = 0
#SECND_BLDG (Integer) = 0
#BIN_NUMBER (Integer) = 3030162
#BBL (String) = 3012090050
#BOROUGH (String) = BK
#BLOCK (Integer) = 1209
#LOT (Integer) = 50  
#LP_NUMBER (String) = LP-2204
#LM_NAME (String) = Crown Heights North Historic District
#OTHER_NAME (String) = (null)
#HOUSE_NUMB (String) = 1407
#STREET_NAM (String) = DEAN STREET
#DESIG_ADDR (String) = 1407 DEAN STREET
#DESIG_DATE (Date) = 2007/04/24
#PUBLIC_HEA (String) = (null)
#LM_TYPE (String) = Historic District
#HIST_DISTR (String) = Yes, Crown Heights North
#BOUNDARIES (String) = Block & Lot
#NOTES (String) = (null)
#STATUS (String) = DESIGNATED
#POINT (1000326.79629946150817 185800.306167847127654)
