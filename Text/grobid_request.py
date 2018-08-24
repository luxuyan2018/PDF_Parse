import requests

def grobidPost(grobidurl, service, filename):
    """Post the grobid service."""
    try:
        PDFfile = open(filename, 'rb')
        r = requests.post(grobidurl + "/" + service, files={"input": (filename, PDFfile)})
        return (r.status_code, r.text)
    except IOError:
        print("Document does not exist or Grobid is not running.")
        return (404, "")