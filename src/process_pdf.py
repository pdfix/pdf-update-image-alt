import ctypes  # noqa: I001

from vision import alt_description

from pdfixsdk.Pdfix import (
    GetPdfix,
    PdfDoc,
    PdfImageParams,
    PdfPageRenderParams,
    PdfRect,
    PdsDictionary,
    PdsStructElement,
    kImageDIBFormatArgb,
    kImageFormatJpg,
    kPdsStructChildElement,
    kRotate0,
    kSaveFull,
)


def render_page(doc: PdfDoc, page_num: int, bbox: PdfRect, zoom: float) -> bytearray:
    page = doc.AcquirePage(page_num)
    page_view = page.AcquirePageView(zoom, kRotate0)

    rect = page_view.RectToDevice(bbox)

    # render content
    render_params = PdfPageRenderParams()
    render_params.matrix = page_view.GetDeviceMatrix()
    render_params.clip_box = bbox
    render_params.image = GetPdfix().CreateImage(
        rect.right - rect.left,
        rect.bottom - rect.top,
        kImageDIBFormatArgb,
    )
    page.DrawContent(render_params)

    # save image to stream and data
    stm = GetPdfix().CreateMemStream()
    img_params = PdfImageParams()
    img_params.format = kImageFormatJpg
    render_params.image.SaveToStream(stm, img_params)

    data = bytearray(stm.GetSize())
    raw_data = (ctypes.c_ubyte * len(data)).from_buffer(data)
    stm.Read(0, raw_data, len(data))

    # cleanup
    stm.Destroy()
    render_params.image.Destroy()
    page_view.Release()
    page.Release()

    return data


def update_image_alt(elem: PdsStructElement, doc: PdfDoc, overwrite: bool) -> None:
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
    page_num = elem.GetPageNumber(0)
    if page_num == -1:
        for i in range(0, elem.GetNumChildren()):
            page_num = elem.GetChildPageNumber(i)
            if page_num != -1:
                break
    if page_num == -1:
        print("[" + img + "] image found but can't determine the page number")
        return

    data = render_page(doc, page_num, bbox, 1)
    with open(img, "wb") as bf:
        bf.write(data)

    response = alt_description(img)

    alt = response[0]

    if overwrite or not org_alt:
        elem.SetAlt(alt)


def browse_figure_tags(parent: PdsStructElement, doc: PdfDoc, overwrite: bool) -> None:
    count = parent.GetNumChildren()
    struct_tree = doc.GetStructTree()
    for i in range(0, count):
        if parent.GetChildType(i) != kPdsStructChildElement:
            continue
        child_elem = struct_tree.GetStructElementFromObject(parent.GetChildObject(i))
        if child_elem.GetType(True) == "Figure":
            # process figure element
            update_image_alt(child_elem, doc, overwrite)
        else:
            browse_figure_tags(child_elem, doc, overwrite)

    return


def alt_text(
    input_path: str,
    output_path: str,
    license_name: str,
    license_key: str,
    overwrite: bool,
) -> None:
    """Run OCR using Tesseract.

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
