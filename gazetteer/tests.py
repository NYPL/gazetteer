from django.utils import unittest
import json
from gazetteer.place import *

#1. edit test_settings.py if appropriate
#2. Run using " python manage.py test --settings=gazetteer.test_settings gazetteer "


class PlaceTestCase(unittest.TestCase):
    def setUp(self):
        self.conn = ElasticHistory('http://localhost:9200/')
        try:
            self.conn.create_index('gaz-test-index')
        except:
            pass
            
        #add mapping
        json_mapping = open('./etl/mapping/place.json')
        mapping = json.load(json_mapping)
        self.conn.put_mapping('gaz-test-index', 'place', mapping["mappings"])
        
        #add data
        place_obj = json.loads('{"relationships": [], "admin": [], "updated": "2006-01-15T01:00:00+01:00", "name": "Vonasek Dam", "geometry": {"type": "Point", "coordinates": [-98.20869, 42.67167]}, "is_primary": true, "uris": ["geonames.org/5081200"], "feature_code": "DAM", "centroid": [-98.20869, 42.67167], "timeframe": {}}')
        place_id = "41dab90514cfc28e"
        ppp =  self.conn.index("gaz-test-index", "place", place_obj, place_id, metadata={"user_created": "test program"})
        
        p1 = Place()
        self.assertEqual(p1.objects.index, "gaz-test-index")
                

    def tearDown(self):
        try:
            self.conn.delete_index("gaz-test-index")
            self.conn.delete_index("gaz-test-index-history")
        except:
            pass
            
            
class PlaceGetCase(PlaceTestCase):
    
    def testGetPlace(self):        
        place = Place.objects.get("41dab90514cfc28e")
        self.assertEqual(place.name, "Vonasek Dam")
    
    
    def testRevisionRollback(self):
        return None
        #print Place.RELATIONSHIP_CHOICES
        #place1 = Place.objects.get("83031b99361ca551")
        ##place2 = Place.objects.get("03407abf333a71dc")
        ##place3 = Place.objects.get("fbeab34f647b9ae1")
        ##place4 = Place.objects.get("9484c3bd08cf7a8d")

        ##place1.add_relationship(place2.id, "conflates", {"comment":"add 1"})
        
        ##place1 = Place.objects.get("83031b99361ca551")
           
        ##place2 = Place.objects.get("03407abf333a71dc")
        
        ##place1.add_relationship(place3.id, "conflates", {"comment":"add 2"})
        ##place1.add_relationship(place4.id, "conflates", {"comment":"add 3"})
        
        ###place1 should have 3 relationships now
        ###reload
        ##place1 = Place.objects.get("83031b99361ca551")
        
        ##self.assertEqual(len(place1.relationships), 3)
        
        #history = place1.history()
        #print history
        
        ##rollback
        #place1.rollback("e51b6c052f0d3bad9b3dcb26f79ecea08afa4377", {"comment":"rollback to second rev"})
        #place1 = Place.objects.get("83031b99361ca551")
        #print place1.relationships
        #place2 = Place.objects.get("03407abf333a71dc")
        #print place1.relationships
        #place3 = Place.objects.get("fbeab34f647b9ae1")
        #print place1.relationships
        #place4 = Place.objects.get("9484c3bd08cf7a8d")
