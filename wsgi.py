"""
Mind Link — WSGI Entry Point
Used by Gunicorn in production (Render deployment).
"""

from app import app

if __name__ == '__main__':
    app.run()
