import os

MAX_ASYNC_PAGES: int = int(os.getenv("MAX_ASYNC_PAGES", os.cpu_count()))
if "DEOCR_PDF2IMAGE_WORKERS" in os.environ:
    MAX_WORKERS = int(os.environ["DEOCR_PDF2IMAGE_WORKERS"])
else:
    MAX_WORKERS = None
