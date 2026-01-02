"""
Ranbir Portfolio CMS - Public Router
"""
from fastapi import APIRouter, Depends, Request, HTTPException
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session

from ..database import get_db
from ..models import (
    Profile, Education, Experience, Award,
    ResearchArea, Publication, Project, Student, Course, Page, CustomSection
)
from pathlib import Path

router = APIRouter(tags=["public"])
PACKAGE_DIR = Path(__file__).parent.parent
templates = Jinja2Templates(directory=str(PACKAGE_DIR / "templates"))


def get_profile(db: Session):
    """Get profile or default"""
    return db.query(Profile).first()


@router.get("/", response_class=HTMLResponse)
async def home(request: Request, db: Session = Depends(get_db)):
    """Home page"""
    profile = get_profile(db)
    pages = db.query(Page).filter(Page.show_in_menu == True, Page.is_published == True).order_by(Page.menu_order).all()
    request.state.pages = pages
    
    research_areas = db.query(ResearchArea).order_by(ResearchArea.order).all()
    publications_count = db.query(Publication).count()
    phd_count = db.query(Student).filter(Student.program == "PhD", Student.status == "Completed").count()
    projects_count = db.query(Project).count()
    
    return templates.TemplateResponse(
        "public/index.html",
        {
            "request": request,
            "profile": profile,
            "research_areas": research_areas,
            "stats": {
                "publications": publications_count,
                "phd_completed": phd_count,
                "projects": projects_count,
            }
        }
    )


@router.get("/about", response_class=HTMLResponse)
async def about(request: Request, db: Session = Depends(get_db)):
    """About page"""
    profile = get_profile(db)
    pages = db.query(Page).filter(Page.show_in_menu == True, Page.is_published == True).order_by(Page.menu_order).all()
    request.state.pages = pages
    
    education = db.query(Education).order_by(Education.order).all()
    experiences = db.query(Experience).order_by(Experience.order).all()
    awards = db.query(Award).order_by(Award.order).all()
    research_areas = db.query(ResearchArea).order_by(ResearchArea.order).all()
    custom_sections = db.query(CustomSection).filter(CustomSection.is_visible == True).order_by(CustomSection.order).all()
    
    return templates.TemplateResponse(
        "public/about.html",
        {
            "request": request,
            "profile": profile,
            "education": education,
            "experiences": experiences,
            "awards": awards,
            "research_areas": research_areas,
            "custom_sections": custom_sections
        }
    )


@router.get("/research", response_class=HTMLResponse)
async def research(request: Request, db: Session = Depends(get_db)):
    """Research & Publications page"""
    profile = get_profile(db)
    pages = db.query(Page).filter(Page.show_in_menu == True, Page.is_published == True).order_by(Page.menu_order).all()
    request.state.pages = pages

    research_areas = db.query(ResearchArea).order_by(ResearchArea.order).all()
    publications = db.query(Publication).order_by(Publication.year.desc(), Publication.order).all()
    
    # Group publications by year
    pubs_by_year = {}
    for pub in publications:
        year = pub.year
        if year not in pubs_by_year:
            pubs_by_year[year] = []
        pubs_by_year[year].append(pub)
    
    return templates.TemplateResponse(
        "public/research.html",
        {
            "request": request,
            "profile": profile,
            "research_areas": research_areas,
            "publications": publications,
            "pubs_by_year": pubs_by_year
        }
    )


@router.get("/projects", response_class=HTMLResponse)
async def projects(request: Request, db: Session = Depends(get_db)):
    """Sponsored Projects page"""
    profile = get_profile(db)
    pages = db.query(Page).filter(Page.show_in_menu == True, Page.is_published == True).order_by(Page.menu_order).all()
    request.state.pages = pages

    ongoing = db.query(Project).filter(Project.is_ongoing == True).order_by(Project.order).all()
    completed = db.query(Project).filter(Project.is_ongoing == False).order_by(Project.order).all()
    
    return templates.TemplateResponse(
        "public/projects.html",
        {
            "request": request,
            "profile": profile,
            "ongoing_projects": ongoing,
            "completed_projects": completed,
            "total_count": len(ongoing) + len(completed)
        }
    )


@router.get("/students", response_class=HTMLResponse)
async def students(request: Request, db: Session = Depends(get_db)):
    """Students Supervised page"""
    profile = get_profile(db)
    pages = db.query(Page).filter(Page.show_in_menu == True, Page.is_published == True).order_by(Page.menu_order).all()
    request.state.pages = pages

    phd_students = db.query(Student).filter(Student.program == "PhD").order_by(Student.order).all()
    mtech_students = db.query(Student).filter(Student.program == "MTech").order_by(Student.order).all()
    
    phd_completed = len([s for s in phd_students if s.status == "Completed"])
    phd_ongoing = len([s for s in phd_students if s.status == "Ongoing"])
    
    return templates.TemplateResponse(
        "public/students.html",
        {
            "request": request,
            "profile": profile,
            "phd_students": phd_students,
            "mtech_students": mtech_students,
            "stats": {
                "phd_total": len(phd_students),
                "phd_completed": phd_completed,
                "phd_ongoing": phd_ongoing,
                "mtech_total": len(mtech_students)
            }
        }
    )


@router.get("/teaching", response_class=HTMLResponse)
async def teaching(request: Request, db: Session = Depends(get_db)):
    """Teaching page"""
    profile = get_profile(db)
    pages = db.query(Page).filter(Page.show_in_menu == True, Page.is_published == True).order_by(Page.menu_order).all()
    request.state.pages = pages

    theory_courses = db.query(Course).filter(Course.is_lab == False).order_by(Course.order).all()
    lab_courses = db.query(Course).filter(Course.is_lab == True).order_by(Course.order).all()
    
    return templates.TemplateResponse(
        "public/teaching.html",
        {
            "request": request,
            "profile": profile,
            "theory_courses": theory_courses,
            "lab_courses": lab_courses
        }
    )


@router.get("/{slug}", response_class=HTMLResponse)
async def dynamic_page(slug: str, request: Request, db: Session = Depends(get_db)):
    """Render dynamic page"""
    profile = get_profile(db)
    
    # Check if page exists
    page = db.query(Page).filter(Page.slug == slug, Page.is_published == True).first()
    
    if page:
        # Get all pages for menu
        pages = db.query(Page).filter(Page.show_in_menu == True, Page.is_published == True).order_by(Page.menu_order).all()
        request.state.pages = pages
        
        return templates.TemplateResponse(
            "public/page.html",
            {
                "request": request,
                "profile": profile,
                "page": page
            }
        )
        
    # Standard 404
    raise HTTPException(status_code=404, detail="Page not found")
