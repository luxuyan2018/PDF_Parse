"""
Parse the fulltext from the json response.
"""
from xml.dom.minidom import parseString
import re

def processFulltext(grobidRes):
    """
    Process fulltext from grobid.
    Response: json, json["fulltext-status"]
    """
    if grobidRes[0] == 200:
        grobidTree = parseString(grobidRes[1].encode('utf-8').strip())
        body = grobidTree.getElementsByTagName('body')[0]
        mainText = body.getElementsByTagName("div")

        sections = []

        for i in range(len(mainText)): # for all text sections in xml
            textDiv = mainText[i]
            sectionHead = textDiv.getElementsByTagName("head")[0]
            sectionNumber = sectionHead.getAttribute("n")
            sectionTitle = sectionHead.firstChild.nodeValue

            text = []
            refs = []

            for element in textDiv.childNodes[1:]:  # the number 0 childNode is <head>
                for refel in element.getElementsByTagName("ref"):
                    ref = {}
                    ref["type"] = refel.getAttribute("type")
                    ref["grobidTarget"] = refel.getAttribute("target")

                    if ref["type"] == "bibr": # paper reference
                        ref["name"] = refel.firstChild.nodeValue
                        refNumbers = re.findall('\d+', ref["name"])[0]
                        idcheck = '#b' + str(int(refNumbers) - 1)  # check whether # of 'target' is # of 'name'-1
                        if ref["grobidTarget"] != idcheck:
                            # refel.setAttribute("target", idcheck)
                            ref["grobidTarget"] = idcheck
                        refs.append(ref)
                    elif ref["type"] == "figure" or ref["type"] == "table": # figure reference and table reference
                        refNumbers = re.findall('\d+', refel.firstChild.nodeValue )
                        if len(refNumbers) > 0:
                            ref["name"] = refNumbers[0]
                            if ref["grobidTarget"] == '':
                                idstring = "#" + ref['type'][0:3] + '_' + str(int(refNumbers[0])-1)
                                # refel.setAttribute("target", idstring)
                                ref["grobidTarget"] = idstring
                            refs.append(ref)
                        else:
                            ref["name"] = None

                pUnicodeText = element.toxml()
                pUnicodeText =  re.sub('<.*?>', '', pUnicodeText) # remove <...>

                # remove nasty unicode scum
                pText = pUnicodeText.encode('ascii', 'ignore').decode('ascii')
                text.append(pText)

            sections.append({
                "header": {
                    "number": sectionNumber,
                    "lnumber": i,
                    "text": sectionTitle
                },
                "text": text,
                "refs": refs
            })

        return {"fulltext-status": "successful", "fulltext": sections}
    else:
        return {"fulltext-status": "unsuccessful", "reason": "bad input"}

