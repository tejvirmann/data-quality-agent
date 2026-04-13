"""Vercel serverless entry point — docs landing page."""

from starlette.applications import Starlette
from starlette.requests import Request
from starlette.responses import HTMLResponse
from starlette.routing import Route

from src.docs_html import DOCS_HTML


async def docs_page(request: Request) -> HTMLResponse:
    return HTMLResponse(DOCS_HTML)


app = Starlette(routes=[Route("/", docs_page)])
