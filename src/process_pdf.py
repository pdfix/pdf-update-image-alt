import ctypes

from ai import alt_description
from pdfixsdk.Pdfix import (
    PdsStructElement,
    GetPdfix,
    kPdsStructChildElement,
    PdfDoc,
    PdsDictionary,
    PdfRect,
    kRotate0,
    PdfPageRenderParams,
    kImageDIBFormatArgb,
    PdfImageParams,
    kImageFormatJpg,
    kSaveFull,
    PdfTagsParams,
)


def renderPage(doc: PdfDoc, pageNum: int, bbox: PdfRect, zoom: float) -> bytearray:
    page = doc.AcquirePage(pageNum)
    pageView = page.AcquirePageView(zoom, kRotate0)

    rect = pageView.RectToDevice(bbox)

    # render content
    renderParams = PdfPageRenderParams()
    renderParams.matrix = pageView.GetDeviceMatrix()
    renderParams.clip_box = bbox
    renderParams.image = GetPdfix().CreateImage(
        rect.right - rect.left, rect.bottom - rect.top, kImageDIBFormatArgb
    )
    page.DrawContent(renderParams)

    # save image to stream and data
    stm = GetPdfix().CreateMemStream()
    imgParams = PdfImageParams()
    imgParams.format = kImageFormatJpg
    renderParams.image.SaveToStream(stm, imgParams)

    data = bytearray(stm.GetSize())
    rawData = (ctypes.c_ubyte * len(data)).from_buffer(data)
    stm.Read(0, rawData, len(data))

    # cleanup
    stm.Destroy()
    renderParams.image.Destroy()
    pageView.Release()
    page.Release()

    return data


def updateImageAlt(elem: PdsStructElement, doc: PdfDoc, overwrite: bool):
    img = "image_" + str(elem.GetObject().GetId()) + ".jpg"

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

    response = alt_description(img)

    alt = response[0]
    org_alt = elem.GetAlt()

    if overwrite or not org_alt:
        elem.SetAlt(alt)


def browse_figure_tags(parent: PdsStructElement, doc: PdfDoc, overwrite: bool):
    count = parent.GetNumChildren()
    struct_tree = doc.GetStructTree()
    for i in range(0, count):
        if not parent.GetChildType(i) == kPdsStructChildElement:
            continue
        childElem = struct_tree.GetStructElementFromObject(parent.GetChildObject(i))
        if childElem.GetType(True) == "Figure":
            # process figure element
            updateImageAlt(childElem, doc, overwrite)
        else:
            browse_figure_tags(childElem, doc, overwrite)

    return None


def alt_text(
    input_path: str,
    output_path: str,
    license_name: str,
    license_key: str,
    overwrite: bool,
) -> None:
    """
    Run OCR using Tesseract.

    Parameters
    ----------
    input_path : str
        Input path to the PDF file.
    output_path : str
        Output path for saving the PDF file.
    license_name : str
        Pdfix SDK license name.
    license_key : str
        Pdfix SDK license key.
    overwrite : bool
        Overwrite alternate text if already present.
    """
    pdfix = GetPdfix()
    if pdfix is None:
        raise Exception("Pdfix Initialization fail")

    if license_name and license_key:
        if not pdfix.GetAccountAuthorization().Authorize(license_name, license_key):
            raise Exception("Pdfix Authorization fail")
    else:
        print("No license name or key provided. Using Pdfix trial")

    # Open doc
    doc = pdfix.OpenDoc(input_path, "")
    if doc is None:
        raise Exception("Unable to open pdf : " + str(pdfix.GetError()))

    struct_tree = doc.GetStructTree()
    if struct_tree is None:
        raise Exception("PDF has no structure tree : " + str(pdfix.GetError()))

    child_elem = struct_tree.GetStructElementFromObject(struct_tree.GetChildObject(0))
    try:
        browse_figure_tags(child_elem, doc, overwrite)
    except Exception as e:
        raise e

    if not doc.Save(output_path, kSaveFull):
        raise Exception("Unable to save PDF " + str(pdfix.GetError()))
