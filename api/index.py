"""Vercel serverless entry point: docs and live demo page, plus the demo JSON endpoints."""

from src.web import app  # noqa: F401  (Vercel looks for `app`)
