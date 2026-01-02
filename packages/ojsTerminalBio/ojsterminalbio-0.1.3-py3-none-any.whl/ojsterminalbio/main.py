"""
Ranbir Portfolio CMS - Main Application
"""
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware

from .database import init_db
from .routers import admin_router, public_router

# Create app
app = FastAPI(
    title="ojsTerminalBio",
    description="ojsTerminalBio: Academic Portfolio CMS",
    version="1.0.0"
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

from pathlib import Path

# Static files
PACKAGE_DIR = Path(__file__).parent
import os
# Check for local uploads directory (for user uploaded content)
if os.path.exists("static/uploads"):
    app.mount("/static/uploads", StaticFiles(directory="static/uploads"), name="uploads")

app.mount("/static", StaticFiles(directory=str(PACKAGE_DIR / "static")), name="static")


# Include routers
app.include_router(admin_router)
app.include_router(public_router)


from starlette.requests import Request
from starlette.responses import RedirectResponse
from fastapi import HTTPException

@app.exception_handler(HTTPException)
async def unauthorized_exception_handler(request: Request, exc: HTTPException):
    """Redirect to login if 401 and admin route"""
    if exc.status_code == 401 and request.url.path.startswith("/admin"):
        return RedirectResponse(url="/admin/login")
    
    # Return default JSON handling for other errors
    from fastapi.responses import JSONResponse
    return JSONResponse(
        status_code=exc.status_code,
        content={"detail": exc.detail},
        headers=exc.headers
    )


@app.on_event("startup")
async def startup():
    """Initialize database on startup"""
    init_db()
    
    # Create default admin user if not exists
    from .database import SessionLocal
    from .models.user import User
    from .config import settings
    
    db = SessionLocal()
    try:
        existing = db.query(User).filter(User.email == settings.default_admin_email).first()
        if not existing:
            admin = User(
                email=settings.default_admin_email,
                hashed_password=User.hash_password(settings.default_admin_password),
                full_name="Admin",
                is_superuser=True
            )
            db.add(admin)
            db.commit()
            print(f"✓ Default admin user created: {settings.default_admin_email}")
            
        # Create default profile if not exists
        from .models.profile import Profile
        existing_profile = db.query(Profile).first()
        if not existing_profile:
            default_profile = Profile(
                name="Dr. First Last",
                site_title="ojsTerminalBio",
                hero_title="Academic Portfolio",
                hero_subtitle="Researcher & Educator",
                theme_primary_color="cyan"
            )
            db.add(default_profile)
            db.commit()
            print("✓ Default profile created")
    finally:
        db.close()


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host="0.0.0.0", port=8002, reload=True)
