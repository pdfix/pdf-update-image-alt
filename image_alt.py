import os
from pdfixsdk.Pdfix import *
from render import renderPage
from image_captioning import predict_step


def updateImageAlt(elem: PdsStructElement):
    img = "image_" + str(elem.GetObject().GetId()) + ".png"

    # get image bbox from attributes
    bbox = PdfRect()
    for i in range(0, elem.GetNumAttrObjects()):
        attr = PdsDictionary(elem.GetAttrObject(i).obj)
        arr = attr.GetArray("BBox")
        if not arr: 
            continue
        bbox.left = arr.GetNumber(0)
        bbox.bottom = arr.GetNumber(1)
        bbox.right = arr.GetNumber(2)
        bbox.top = arr.GetNumber(3)
        break

    # check bounding box
    if bbox.left == bbox.right or bbox.top == bbox.bottom:
        print("[" + img + "] image found but no BBox attribute was set")
        return
    
    # get the object page number (it may be written in child objects)
    pageNum = elem.GetPageNumber()
    if pageNum == -1:
        for i in range(0, elem.GetNumChildren()):
            pageNum = elem.GetChildPageNumber(i)
            if not pageNum == -1:
                break
    if pageNum == -1:
        print("[" + img + "] image found but can't determine the page number")
        return

    data = renderPage(doc, pageNum, bbox, 1)
    with open(img, "wb") as bf:
      bf.write(data)

    pred = predict_step([img])
    if pred.count == 0:
        print("[" + img + "] image found but no description was found")
        return
    
    alt = pred[0]
    print("[" + img + "] alt: '" + elem.GetAlt() + "' -> '" + alt + "'")
    elem.SetAlt(alt)


def browseFigureTags(parent: PdsStructElement):
    count = parent.GetNumChildren()
    for i in range(0, count):
        if not parent.GetChildType(i) == kPdsStructChildElement:
            continue
        childElem = structTree.GetStructElementFromObject(parent.GetChildObject(i))
        if childElem.GetType(True) == "Figure":
            # process figure element
            updateImageAlt(childElem)
        else:
          browseFigureTags(childElem)
            
    return None


# test
pdf = os.path.dirname(os.path.abspath(__file__)) +"/example.pdf"
doc = GetPdfix().OpenDoc(pdf, "")
tagParams = PdfTagsParams()
doc.AddTags(tagParams, 0, None)
structTree = doc.GetStructTree()

childElem = structTree.GetStructElementFromObject(structTree.GetChildObject(0))
browseFigureTags(childElem)

pdf2 = os.path.dirname(os.path.abspath(__file__)) +"/example_saved.pdf"
doc.Save(pdf2, kSaveFull)



