import hashlib, json, os, gzip, sys, re
from unidecode import unidecode

def tab_file(fname, cols):
    for line in file(fname).readlines():
        vals = line.strip().split("\t")
        yield dict(zip(cols, vals))

def _id(uri):
    return hashlib.md5(uri).hexdigest()[:16]

has_unicode = re.compile(r'[^\0x00-0x7f]')
def transliterate(alt_name):
    if has_unicode.search(alt_name["name"]):
        try:
            xlit = unidecode(alt_name["name"].decode("utf8"))
        except UnicodeDecodeError:
            return
        if xlit != alt_name["name"]:
            addl_name = alt_name.copy()
            addl_name["lang"] = alt_name["lang"] + ":ascii"
            addl_name["name"] = xlit
            return addl_name

class Dump(object):
    def __init__(self, template):
        self.max_rows = 10000
        self.rows = 0
        self.content = ""
        self.template = template
        path = os.path.dirname(template)
        if not os.path.exists(path): os.makedirs(path)

    def write(self, uri, place):
        self.content += json.dumps({"index": {"_id":_id(uri)}})
        self.content += "\n" + json.dumps(place, sort_keys=True) + "\n"
        self.rows += 1
        if self.rows % 1000 == 0: print >>sys.stderr, "\r% 9d" % self.rows,
        if self.rows % 10000 == 0: self.flush()

    def flush(self, final=0):
        fname = self.template % (int(self.rows/self.max_rows)+final)
        print >>sys.stderr, " ", fname
        out = gzip.open(fname, "wb")
        out.write(self.content)
        out.close()
        self.content = ""

    def close(self):
        self.flush(final=1)