import arrest

gazetteer = arrest.Client("http://gazetteer.in:9090/1.0/place", ext="json")

def candidates(place):
    subject = place["properties"]
    similar = getattr(gazetteer, subject["id"]).similar()
    for feature in similar["features"]:
        if feature["confidence"] < 0.9: break
        print u"\t".join(map(unicode,
                        [subject["id"], feature["id"],
                        subject["name"], subject["feature_code"],
                        feature["name"], feature["feature_code"],
                        feature["confidence"], feature["distance"]])).encode("utf-8")

def iterate_over_all_places():
    result = {"features": True}
    page = 1
    while result["features"]:
        result = gazetteer.search(per_page=100, distance="50km", page=page)
        for place in result["features"]:
            candidates(place)
        page += 1
        
if __name__ == "__main__":
    iterate_over_all_places()
