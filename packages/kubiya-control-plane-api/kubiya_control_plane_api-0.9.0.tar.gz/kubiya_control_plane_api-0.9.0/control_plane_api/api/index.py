"""
Vercel serverless entry point for Agent Control Plane API.

This file exports the FastAPI app for Vercel's Python runtime.
Vercel automatically detects and handles FastAPI apps without needing Mangum.
"""

from control_plane_api.app.main import app

# Vercel expects the FastAPI app to be exported as 'app'
# No additional wrapper or Mangum needed with modern Vercel Python runtime
__all__ = ["app"]
