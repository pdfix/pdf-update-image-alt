import ctypes
import os
from pdfixsdk.Pdfix import *

# render a portion of a PDF page into a PNG image data
def renderPage(doc: PdfDoc, pageNum: int, bbox: PdfRect, zoom: float) -> bytearray:
    page = doc.AcquirePage(pageNum)
    pageView = page.AcquirePageView(zoom, kRotate0)

    rect = pageView.RectToDevice(bbox)

    # render content
    renderParams = PdfPageRenderParams()
    renderParams.matrix = pageView.GetDeviceMatrix()
    renderParams.clip_box = bbox
    renderParams.image = GetPdfix().CreateImage(rect.right - rect.left, rect.bottom - rect.top, kImageDIBFormatArgb)
    page.DrawContent(renderParams, 0, None)

    # save image to stream and data
    stm = GetPdfix().CreateMemStream()
    imgParams = PdfImageParams()
    imgParams.format = kImageFormatPng
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


# render test
# pdf = os.path.dirname(os.path.abspath(__file__)) +"/example.pdf"
# doc = GetPdfix().OpenDoc(pdf, "")
# rect = PdfRect()
# rect.left = rect.bottom = 100
# rect.right = rect.top = 400
# data = renderPage(doc, 0, rect, 1.0)
# with open("image.png", "wb") as bf:
#     bf.write(data)