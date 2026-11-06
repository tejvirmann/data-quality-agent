"""Web layer for the Vercel deployment: docs + live demo page and the JSON endpoints behind it."""

import io

from PIL import Image, UnidentifiedImageError
from starlette.applications import Starlette
from starlette.requests import Request
from starlette.responses import HTMLResponse, JSONResponse, Response
from starlette.routing import Route

from src.docs_html import DOCS_HTML
from src.report import run_quality_checks, unreadable_report
from src.samples import SAMPLES, make_sample

# Vercel rejects request bodies over 4.5 MB before they reach us.
MAX_UPLOAD_BYTES = int(4.4 * 1024 * 1024)


async def docs_page(request: Request) -> HTMLResponse:
    return HTMLResponse(DOCS_HTML)


async def list_samples(request: Request) -> JSONResponse:
    return JSONResponse([s.__dict__ for s in SAMPLES])


async def sample_image(request: Request) -> Response:
    try:
        data = make_sample(request.path_params["name"])
    except KeyError:
        return JSONResponse({"error": "unknown sample"}, status_code=404)
    return Response(data, media_type="image/jpeg", headers={"Cache-Control": "public, max-age=86400"})


async def _read_upload(request: Request) -> tuple[bytes, str]:
    """Accept either a raw image body or a multipart form with a `file` field."""
    if request.headers.get("content-type", "").startswith("multipart/form-data"):
        form = await request.form()
        upload = form.get("file")
        if upload is None or isinstance(upload, str):
            raise ValueError("Send the image in a form field named 'file'.")
        return await upload.read(), upload.filename or "upload"
    return await request.body(), request.headers.get("x-filename", "upload")


async def check_image(request: Request) -> JSONResponse:
    try:
        data, filename = await _read_upload(request)
    except ValueError as e:
        return JSONResponse({"error": str(e)}, status_code=400)
    if not data:
        return JSONResponse({"error": "No image received."}, status_code=400)
    if len(data) > MAX_UPLOAD_BYTES:
        return JSONResponse({"error": "That image is over 4 MB. Resize or compress it and try again."}, status_code=413)

    try:
        image = Image.open(io.BytesIO(data))
        image.load()  # force a full decode so truncated files fail here, not mid-check
        report = run_quality_checks(image, data, filename)
    except (UnidentifiedImageError, OSError, SyntaxError, ValueError) as e:
        report = unreadable_report(filename, str(e) or e.__class__.__name__)
    return JSONResponse(report.model_dump(mode="json"))


app = Starlette(routes=[
    Route("/", docs_page),
    Route("/api/samples", list_samples),
    Route("/api/sample/{name}", sample_image),
    Route("/api/check", check_image, methods=["POST"]),
])
