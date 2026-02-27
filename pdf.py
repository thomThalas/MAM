import pymupdf as ppdf

TEMPLATE_PATH = "./template.pdf"
#ROOT_PATH = os.getcwd()

def CreateRatioRect(img_path: str, x0: int, x1: int, y0: int):
    pix = ppdf.Pixmap(img_path)
    img_width = pix.width
    img_height = pix.height
    aspect = img_height / img_width
    width = (x1 - x0) * aspect
    return ppdf.Rect(x0, y0, x1, y0 + width)