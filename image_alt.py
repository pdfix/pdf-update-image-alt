import os
from pdfixsdk.Pdfix import *
from render import renderPage
from image_captioning import predict_step


def updateImageAlt(elem: PdsStructElement):
    # TODO: get image bbox from attributes
    # for i in range(0, elem.GetNumAttrObjects()):
    #     attr = elem.GetAttrObject(i)
        
    rect = PdfRect()
    rect.left = 73.5
    rect.bottom = 135
    rect.right = 541.5
    rect.top = 398.25

    data = renderPage(doc, elem.GetPageNumber(), rect, 1)
    img = "image_" + str(elem.GetObject().GetId()) + ".png"
    with open(img, "wb") as bf:
      bf.write(data)

    pred = predict_step([img])
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
structTree = doc.GetStructTree()
childElem = structTree.GetStructElementFromObject(structTree.GetChildObject(0))
browseFigureTags(childElem)

pdf2 = os.path.dirname(os.path.abspath(__file__)) +"/example_saved.pdf"
doc.Save(pdf2, kSaveFull)



