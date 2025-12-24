import json
import logging
import os
import pathlib
import shutil

# import urllib
# import urlparse
# import time
import urllib.parse
from datetime import datetime

import shortuuid
from bq.metadoc import Metadoc

log = logging.getLogger("vqapi.util")
ALLOWED = shortuuid.get_alphabet()


# TODO: remove this and include utils package instead
def is_uniq_code(uniq, version=None):
    """Check that the code is a bisque uniq code

    @param uniq: The uniq code
    @param version: Test for a particular version:
    @return:  The version of the code or None
    """
    if uniq and uniq.startswith("00-"):
        if len(uniq) <= 26 and all(c in ALLOWED for c in uniq[3:]):
            return True
        else:
            log.warning(">>>>>>>>>>>>>>>> found unusual uniq code: %s", uniq)
            return False
    else:
        return False


#####################################################
# misc: unicode
#####################################################


def normalize_unicode(s):
    if isinstance(s, str):
        return s
    # s is bytestring
    try:
        s = s.decode("utf8")
    except UnicodeDecodeError:
        s = s.decode("ascii", "backslashreplace")
    return s


#####################################################
# misc: path manipulation
#####################################################

if os.name == "nt":

    def url2localpath(url):
        path = urllib.parse.urlparse(url).path
        if len(path) > 0 and path[0] == "/":
            path = path[1:]

        #         try:
        #             return urllib.parse.unquote(path).decode('utf-8')
        #         except UnicodeEncodeError:
        #             # dima: safeguard measure for old non-encoded unicode paths
        #             return urllib.parse.unquote(path)
        return urllib.parse.unquote(path)

    def localpath2url(path):
        path = path.replace("\\", "/")
        # url = urllib.parse.quote(path.encode('utf-8'))
        url = urllib.parse.quote(path)
        if len(path) > 3 and path[0] != "/" and path[1] == ":":
            # path starts with a drive letter: c:/
            url = f"file:///{url}"
        else:
            # path is a relative path
            url = f"file://{url}"
        return url

else:

    def url2localpath(url):
        # url = url.encode('utf-8') # safegurd against un-encoded values in the DB
        path = urllib.parse.urlparse(url).path
        return urllib.parse.unquote(path)

    def localpath2url(path):
        # url = urllib.parse.quote(path.encode('utf-8'))
        url = urllib.parse.quote(path)
        url = f"file://{url}"
        return url


def makedirs_and_pathdb_refresh(path_to_create: str, vqpath_to_create: str, dirs):
    """
    Ensures a directory path exists and refreshes the pathdb along the path.

    Args:
        path_to_create: The full directory path to create (e.g., "/homedir/clang@viqi.org/a/b/c")
        vqpath_to_create: The full directory path to create in the VQ path space (e.g., "/home/a/b/c")
        dirs: The directory service to use for refreshing the pathdb.
    """
    # Use pathlib for robust path manipulation
    os_path = pathlib.Path(path_to_create)
    vq_path = pathlib.PurePosixPath(vqpath_to_create)

    # If the path already exists, no new directories will be created
    if os_path.exists():
        return

    # Walk up the path's parents to find which ones need to be created
    dirs_to_refresh = []
    os_parent = os_path
    vq_parent = vq_path
    # Keep going up until we find a parent that exists or we reach the root
    while not os_parent.exists():
        dirs_to_refresh.append(str(vq_parent))
        os_parent = os_parent.parent
        vq_parent = vq_parent.parent

    # Create the directories
    # We use exist_ok=True to prevent race conditions in case another
    # process creates the directory between our check and this call.
    os.makedirs(path_to_create, exist_ok=True)

    # Refresh pathdb for each directory in the path
    for dir_to_refresh in reversed(dirs_to_refresh):
        dirs.refresh(dir_to_refresh)


#####################################################


class AttrDict(dict):
    def __init__(self, *args, **kwargs):
        dict.__init__(self, *args, **kwargs)

    def __getattr__(self, name):
        try:
            return self[name]
        except KeyError:
            raise AttributeError

    def __setattr__(self, name, value):
        self[name] = value
        return value

    def __getstate__(self):
        return list(self.items())

    def __setstate__(self, items):
        for key, val in items:
            self[key] = val


def safecopy(*largs):
    largs = list(largs)
    d = largs.pop()

    for f in largs:
        try:
            dest = d
            if os.path.isdir(d):
                dest = os.path.join(d, os.path.basename(f))
            log.debug("linking %s to %s", d, dest)
            if os.path.exists(dest):
                log.debug("Found existing file %s: removing ..", dest)
                os.unlink(dest)
            os.link(f, dest)
        except (OSError, AttributeError) as e:
            log.error("Problem in link %s .. trying copy", e)
            shutil.copy2(f, dest)


def parse_qs(query):
    """
    parse a uri query string into a dict
    """
    pd = {}
    if "&" in query:
        for el in query.split("&"):
            nm, junk, vl = el.partition("=")
            pd.setdefault(nm, []).append(vl)
    return pd


def make_qs(pd):
    """
    convert back from dict to qs
    """
    query = []
    for k, vl in list(pd.items()):
        for v in vl:
            pair = v and f"{k}={v}" or k
            query.append(pair)
    return "&".join(query)


def save_blob(session, localfile=None, destdir=None, resource=None):
    """
    put a local image on the server and return the URL
    to the METADATA XML record

    @param session: the local session
    @param image: an BQImage object
    @param localfile:  a file-like object or name of a localfile
    @param destdir: optional server-side dest directory
    @return XML content  when upload ok

    @exceptions comm.BQApiError - if blob is failed to be posted
    """
    # content = session.postblob(localfile, xml=resource)
    import_service = session.service("import")
    resource = Metadoc.convert(resource)
    content = import_service.transfer_file(localfile, dstpath=destdir, xml=resource, protocol="binary")

    # content = ET.XML(content)
    # print ("CONENT", content)
    # content = Metadoc.convert_to_etree(content)
    return content
    # if len(content) < 1:  # when would this happen
    #    return None
    # return content[0]


def fetch_blob(session, uri, dest=None, uselocalpath=False):
    """
    fetch original image locally as tif
    @param session: the bqsession
    @param uri: resource image uri
    @param dest: a destination directory
    @param uselocalpath: true when routine is run on same host as server
    """
    image = session.load(uri)
    name = image.name or next_name("blob")

    if uselocalpath:
        # Skip 'file:'
        path = image.value
        if path.startswith("file:"):
            path = path[5:]
        return {uri: path}

    #     url = session.service_url("blob_service", path=image.resource_uniq)
    #     blobdata = session.c.fetch(url)

    if os.path.isdir(dest):
        outdest = os.path.join(dest, os.path.basename(name))
    else:
        outdest = os.path.join(".", os.path.basename(name))

    blobs = session.service("blobs")
    with blobs.read_chunk(blob_id=image.resource_uniq, as_stream=True) as f:
        f.copy_into(outdest)
    return {uri: outdest}


def fetch_image_planes(session, uri, dest=None, uselocalpath=False):
    """
    fetch all the image planes of an image locally
    @param session: the bqsession
    @param uri: resource image uri
    @param dest: a destination directory
    @param uselocalpath: true when routine is run on same host as server

    """
    image = session.load(uri, view="full")
    # x,y,z,t,ch = image.geometry()
    meta = image.pixels().meta().fetch()
    # meta = ET.XML(meta)
    meta = session.factory.string2etree(meta)
    t = meta.findall('.//tag[@name="image_num_t"]')
    t = len(t) and t[0].get("value")
    z = meta.findall('.//tag[@name="image_num_z"]')
    z = len(z) and z[0].get("value")
    tplanes = int(t)
    zplanes = int(z)

    planes = []
    for t in range(tplanes):
        for z in range(zplanes):
            ip = image.pixels().slice(z=z + 1, t=t + 1).format("tiff")
            if uselocalpath:
                ip = ip.localpath()
            planes.append(ip)

    files = []
    for i, p in enumerate(planes):
        slize = p.fetch()
        fname = os.path.join(dest, f"{i:05d}.TIF")
        if uselocalpath:
            # path = ET.XML(slize).xpath('/resource/@src')[0]
            resource = session.factory.string2etree(slize)
            path = resource.get("value")
            # Strip file:/ from path
            if path.startswith("file:/"):
                path = path[5:]
            if os.path.exists(path):
                safecopy(path, fname)
            else:
                log.error("localpath did not return valid path: %s", path)
        else:
            f = open(fname, "wb")
            f.write(slize)
            f.close()
        files.append(fname)

    return files


def next_name(name):
    count = 0
    while os.path.exists(f"{name}-{count:05d}.TIF"):
        count = count + 1
    return f"{name}-{count:05d}.TIF"


def fetch_image_pixels(session, uri, dest, uselocalpath=False):
    """
    fetch original image locally as tif
    @param session: the bqsession
    @param uri: resource image uri
    @param dest: a destination directory
    @param uselocalpath: true when routine is run on same host as server
    """
    image = session.load(uri)
    name = image.name or next_name("image")
    ip = image.pixels().format("tiff")
    if uselocalpath:
        ip = ip.localpath()
    pixels = ip.fetch()
    if os.path.isdir(dest):
        dest = os.path.join(dest, os.path.basename(name))
    else:
        dest = os.path.join(".", os.path.basename(name))
    if not dest.lower().endswith(".tif"):
        dest = f"{dest}.tif"

    if uselocalpath:
        # path = ET.XML(pixels).xpath('/resource/@src')[0]
        resource = session.factory.string2etree(pixels)
        path = resource.get("value")
        # path = urllib.url2pathname(path[5:])
        if path.startswith("file:/"):
            path = path[5:]
            # Skip 'file:'
        if os.path.exists(path):
            safecopy(path, dest)
            return {uri: dest}
        else:
            log.error("localpath did not return valid path: %s", path)

    f = open(dest, "wb")
    f.write(pixels)
    f.close()
    return {uri: dest}


def fetch_dataset(session, uri, dest, uselocalpath=False):
    """
    fetch elemens of dataset locally as tif

    @param session: the bqsession
    @param uri: resource image uri
    @param dest: a destination directory
    @param uselocalpath: true when routine is run on same host as server

    @return:
    """
    dataset = session.fetchxml(uri, view="deep")
    members = dataset.findall('.//value[@type="object"]')

    results = {}
    for _, imgxml in enumerate(members):
        uri = imgxml.text  # imgxml.get('uri')
        # print("FETCHING", uri)
        # fname = os.path.join (dest, "%.5d.tif" % i)
        x = fetch_image_pixels(session, uri, dest, uselocalpath=uselocalpath)
        results.update(x)
    return results


def fetchImage(session, uri, dest, uselocalpath=False):
    """
    @param: session -
    @param: url -
    @param: dest -
    @param: uselocalpath- (default: False)

    @return
    """
    image = session.load(uri).pixels().info()
    # fileName = ET.XML(image.fetch()).xpath('//tag[@name="filename"]/@value')[0]
    fileName = session.factory.string2etree(image.fetch()).findall('.//tag[@name="filename"]')[0]
    fileName = fileName.get("value")

    ip = session.load(uri).pixels().format("tiff")

    if uselocalpath:
        ip = ip.localpath()

    pixels = ip.fetch()

    if os.path.isdir(dest):
        dest = os.path.join(dest, fileName)

    if uselocalpath:
        # path = ET.XML(pixels).xpath('/resource/@src')[0]
        resource = session.factory.string2etree(pixels)
        path = resource.get("value")
        # path = urllib.url2pathname(path[5:])
        if path.startswith("file:/"):
            # Skip 'file:'
            path = path[5:]
        if os.path.exists(path):
            safecopy(path, dest)
            return {uri: dest}
        else:
            log.error("localpath did not return valid path: %s", path)

    f = open(dest, "wb")
    f.write(pixels)
    f.close()
    return {uri: dest}


def fetchDataset(session, uri, dest, uselocalpath=False):
    dataset = session.fetchxml(uri, view="deep")
    members = dataset.findall('.//value[@type="object"]')
    results = {}

    for i, imgxml in enumerate(members):
        uri = imgxml.text
        # print("FETCHING: ", uri)
        # fname = os.path.join (dest, "%.5d.tif" % i)
        result = fetchImage(session, uri, dest, uselocalpath=uselocalpath)
        results[uri] = result[uri]
    return results


# Post fields and files to an http host as multipart/form-data.
# fields is a sequence of (name, value) elements for regular form
# fields.  files is a sequence of (name, filename, value) elements
# for data to be uploaded as files
# Return the tuple (rsponse headers, server's response page)

# example:
#   post_files ('http://..',
#   fields = {'file1': open('file.jpg','rb'), 'name':'file' })
#   post_files ('http://..', fields = [('file1', 'file.jpg', buffer), ('f1', 'v1' )] )


def save_image_pixels(session, localfile, image_tags=None):
    """
    put a local image on the server and return the URL
    to the METADATA XML record

    @param: session - the local session
    @param: image - an BQImage object
    @param: localfile - a file-like object or name of a localfile

    @return: XML content when upload ok
    """
    xml = None
    if image_tags:
        # xml = ET.tostring(toXml(image_tags))
        xml = session.factory.to_string(image_tags)
    return session.postblob(localfile, xml=xml)


def as_flat_dict_tag_value(xmltree):
    def _xml2d(e, d, path=""):
        for child in e:
            name = "{}{}".format(path, child.get("name", ""))
            value = child.get("value", None)
            if value is not None:
                if name not in d:
                    d[name] = value
                else:
                    if isinstance(d[name], list):
                        d[name].append(value)
                    else:
                        d[name] = [d[name], value]
            d = _xml2d(child, d, path="{}{}/".format(path, child.get("name", "")))
        return d

    return _xml2d(xmltree, {})


def as_flat_dicts_node(xmltree):
    def _xml2d(e, d, path=""):
        for child in e:
            name = "{}{}".format(path, child.get("name", ""))
            # value = child.get('value', None)
            value = child
            # if value is not None:
            if name not in d:
                d[name] = value
            else:
                if isinstance(d[name], list):
                    d[name].append(value)
                else:
                    d[name] = [d[name], value]
            d = _xml2d(child, d, path="{}{}/".format(path, child.get("name", "")))
        return d

    return _xml2d(xmltree, {})


def _deserialize_value(val):
    if not isinstance(val, str):
        return val
    try:
        # see if it is datetime
        return datetime.fromisoformat(val)
    except ValueError:
        return val


def _json_deserializer(dct):
    return {k: _deserialize_value(v) for k, v in dct.items()}


def _json_serializer(obj):
    if isinstance(obj, datetime):
        return obj.isoformat()
    raise TypeError(f"Object of type {type(obj).__name__} is not serializable")


def custom_json_loads(json_str: str, **kw) -> dict:
    return json.loads(json_str, object_hook=_json_deserializer, **kw) if json_str else {}


def custom_json_load(jsonfp, **kw) -> dict:
    return json.load(jsonfp, object_hook=_json_deserializer, **kw)


def custom_json_dumps(json_obj: dict, **kw) -> str:
    return json.dumps(json_obj, default=_json_serializer, **kw)
