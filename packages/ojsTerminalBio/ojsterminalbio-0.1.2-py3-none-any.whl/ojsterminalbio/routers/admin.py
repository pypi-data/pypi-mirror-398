"""
Ranbir Portfolio CMS - Admin Router
"""
from datetime import timedelta
from typing import List

from fastapi import APIRouter, Depends, HTTPException, status, Request, Form
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session

from ..database import get_db
from ..auth import (
    authenticate_user, create_access_token, require_auth,
    get_current_user, ACCESS_TOKEN_EXPIRE_MINUTES
)
from ..models import (
    User, Profile, Education, Experience, Award,
    ResearchArea, Publication, Project, Student, Course, Page,
    CustomSection, ProfileLink
)
from .. import schemas

from pathlib import Path

router = APIRouter(prefix="/admin", tags=["admin"])
PACKAGE_DIR = Path(__file__).parent.parent
templates = Jinja2Templates(directory=str(PACKAGE_DIR / "templates"))

@router.get("/ping")
def ping():
    return {"message": "pong"}


# Helper to get common context
def get_context(request: Request, user: User, **kwargs):
    return {"request": request, "user": user, **kwargs}


# ========== Authentication ==========

@router.get("/login", response_class=HTMLResponse)
async def login_page(request: Request):
    """Admin login page"""
    return templates.TemplateResponse("admin/login.html", {"request": request})


@router.post("/login")
async def login(
    request: Request,
    email: str = Form(...),
    password: str = Form(...),
    db: Session = Depends(get_db)
):
    """Process login"""
    user = authenticate_user(db, email, password)
    if not user:
        return templates.TemplateResponse(
            "admin/login.html",
            {"request": request, "error": "Invalid email or password"}
        )
    
    access_token = create_access_token(
        data={"sub": user.email},
        expires_delta=timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    )
    
    response = RedirectResponse(url="/admin/dashboard", status_code=303)
    response.set_cookie(
        key="access_token",
        value=access_token,
        httponly=True,
        max_age=ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        path="/",
        samesite="lax",
        secure=False
    )
    return response


@router.get("/logout")
async def logout():
    """Logout and clear cookie"""
    response = RedirectResponse(url="/admin/login", status_code=303)
    response.delete_cookie("access_token")
    return response


# ========== Dashboard ==========

@router.get("/dashboard", response_class=HTMLResponse)
async def dashboard(
    request: Request,
    user: User = Depends(require_auth),
    db: Session = Depends(get_db)
):
    """Admin dashboard"""
    stats = {
        "publications": db.query(Publication).count(),
        "projects": db.query(Project).count(),
        "students": db.query(Student).count(),
        "courses": db.query(Course).count(),
    }
    return templates.TemplateResponse(
        "admin/dashboard.html",
        get_context(request, user, stats=stats)
    )


# ========== Profile ==========

from ..models.custom_section import CustomSection

@router.get("/profile", response_class=HTMLResponse)
async def profile_page(
    request: Request,
    user: User = Depends(require_auth),
    db: Session = Depends(get_db)
):
    """Profile editor"""
    profile = db.query(Profile).first()
    education = db.query(Education).order_by(Education.order).all()
    experiences = db.query(Experience).order_by(Experience.order).all()
    awards = db.query(Award).order_by(Award.order).all()
    research_areas = db.query(ResearchArea).order_by(ResearchArea.order).all()
    custom_sections = db.query(CustomSection).order_by(CustomSection.order).all()
    profile_links = db.query(ProfileLink).filter(ProfileLink.profile_id == profile.id).order_by(ProfileLink.order).all() if profile else []
    
    return templates.TemplateResponse(
        "admin/profile.html",
        get_context(
            request, user,
            profile=profile,
            education=education,
            experiences=experiences,
            awards=awards,
            research_areas=research_areas,
            custom_sections=custom_sections,
            profile_links=profile_links
        )
    )


@router.post("/profile/update")
async def update_profile(
    request: Request,
    user: User = Depends(require_auth),
    db: Session = Depends(get_db)
):
    """Update profile and handle image upload"""
    form = await request.form()
    profile = db.query(Profile).first()
    
    if not profile:
        profile = Profile()
        db.add(profile)
    
    # Handle Text Fields
    for field in ["name", "native_name", "title", "department", "institution", "email", 
                  "phone", "fax", "address", "bio",
                  "site_title", "hero_title", "hero_subtitle", "footer_text", "theme_primary_color",
                  "matrix_characters",
                  # Section Labels
                  "label_basic_info", "label_contact_info", "label_bio", "label_links",
                  "label_education", "label_experience", "label_awards", "label_research_areas", "label_custom_sections"]:
        if field in form:
            setattr(profile, field, form[field])
            
    # Handle Boolean Fields
    profile.show_matrix_effect = form.get("show_matrix_effect") == "on"
    profile.show_basic_info = form.get("show_basic_info") == "on"
    profile.show_contact_info = form.get("show_contact_info") == "on"
    profile.show_bio = form.get("show_bio") == "on"
    profile.show_links = form.get("show_links") == "on"
    profile.show_education = form.get("show_education") == "on"
    profile.show_experience = form.get("show_experience") == "on"
    profile.show_awards = form.get("show_awards") == "on"
    profile.show_research_areas = form.get("show_research_areas") == "on"
            
    # Handle File Upload
    image_file = form.get("image_file")
    if image_file and image_file.filename:
        import shutil
        import os
        
        # Ensure upload dir exists
        upload_dir = "static/uploads"
        os.makedirs(upload_dir, exist_ok=True)
        
        # Save file
        file_path = f"{upload_dir}/{image_file.filename}"
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(image_file.file, buffer)
            
        # Update profile URL
        profile.image_url = f"/{file_path}"
    
    db.commit()
    return RedirectResponse(url="/admin/profile?success=1", status_code=303)



@router.post("/profile/links/add")
async def add_profile_link(
    request: Request,
    user: User = Depends(require_auth),
    db: Session = Depends(get_db)
):
    """Add new profile link"""
    form = await request.form()
    profile = db.query(Profile).first()
    if not profile:
        profile = Profile()
        db.add(profile)
        db.commit()
    
    link = ProfileLink(
        profile_id=profile.id,
        label=form.get("label"),
        url=form.get("url"),
        icon=form.get("icon"), # Optional
        order=int(form.get("order", 0))
    )
    db.add(link)
    db.commit()
    return RedirectResponse(url="/admin/profile?success=1", status_code=303)


@router.post("/profile/links/delete/{link_id}")
async def delete_profile_link(
    link_id: int,
    user: User = Depends(require_auth),
    db: Session = Depends(get_db)
):
    """Delete profile link"""
    link = db.query(ProfileLink).filter(ProfileLink.id == link_id).first()
    if link:
        db.delete(link)
        db.commit()
    return RedirectResponse(url="/admin/profile?success=1", status_code=303)


# ========== Publications ==========

@router.get("/publications", response_class=HTMLResponse)
async def publications_page(
    request: Request,
    user: User = Depends(require_auth),
    db: Session = Depends(get_db)
):
    """Publications manager"""
    publications = db.query(Publication).order_by(Publication.year.desc(), Publication.order).all()
    
    # Get unique option values
    venues = sorted([v[0] for v in db.query(Publication.venue).distinct().all() if v[0]])
    venue_types = sorted([vt[0] for vt in db.query(Publication.venue_type).distinct().all() if vt[0]])
    statuses = sorted([s[0] for s in db.query(Publication.status).distinct().all() if s[0]])
    
    return templates.TemplateResponse(
        "admin/publications.html",
        get_context(request, user, publications=publications,
                   venues=venues, venue_types=venue_types, statuses=statuses)
    )


@router.post("/publications/add")
async def add_publication(
    request: Request,
    user: User = Depends(require_auth),
    db: Session = Depends(get_db)
):
    """Add new publication"""
    form = await request.form()
    pub = Publication(
        title=form.get("title"),
        authors=form.get("authors"),
        venue=form.get("venue"),
        venue_type=form.get("venue_type"),
        year=int(form.get("year", 2024)),
        status=form.get("status", "published"),
        doi=form.get("doi"),
        url=form.get("url")
    )
    db.add(pub)
    db.commit()
    return RedirectResponse(url="/admin/publications?success=1", status_code=303)


@router.post("/publications/update/{pub_id}")
async def update_publication(
    pub_id: int,
    request: Request,
    user: User = Depends(require_auth),
    db: Session = Depends(get_db)
):
    """Update publication"""
    form = await request.form()
    pub = db.query(Publication).filter(Publication.id == pub_id).first()
    if pub:
        pub.title = form.get("title", pub.title)
        pub.authors = form.get("authors", pub.authors)
        pub.venue = form.get("venue", pub.venue)
        pub.venue_type = form.get("venue_type", pub.venue_type)
        if form.get("year"):
            pub.year = int(form.get("year"))
        pub.status = form.get("status", pub.status)
        pub.doi = form.get("doi", pub.doi)
        pub.url = form.get("url", pub.url)
        db.commit()
    return RedirectResponse(url="/admin/publications?success=1", status_code=303)


@router.post("/publications/delete/{pub_id}")
async def delete_publication(
    pub_id: int,
    user: User = Depends(require_auth),
    db: Session = Depends(get_db)
):
    """Delete publication"""
    pub = db.query(Publication).filter(Publication.id == pub_id).first()
    if pub:
        db.delete(pub)
        db.commit()
    return RedirectResponse(url="/admin/publications", status_code=303)



# ========== Custom Section Editor ==========

@router.get("/custom-sections/editor/{section_id}", response_class=HTMLResponse)
async def custom_section_editor(
    section_id: int,
    request: Request,
    user: User = Depends(require_auth),
    db: Session = Depends(get_db)
):
    """Full-page editor for custom section"""
    section = db.query(CustomSection).filter(CustomSection.id == section_id).first()
    if not section:
        return RedirectResponse(url="/admin/profile?error=SectionNotFound", status_code=303)
    
    return templates.TemplateResponse(
        "admin/custom_section_editor.html",
        get_context(request, user, section=section)
    )

@router.post("/custom-sections/save-editor")
async def save_custom_section_editor(
    request: Request,
    user: User = Depends(require_auth),
    db: Session = Depends(get_db)
):
    """Save custom section from editor"""
    form = await request.form()
    section_id = form.get("id")
    section = db.query(CustomSection).filter(CustomSection.id == section_id).first()
    
    if section:
        section.title = form.get("title", section.title)
        section.subtitle = form.get("subtitle")
        section.year = form.get("year")
        section.content = form.get("content")
        section.order = int(form.get("order", 0))
        section.tags = form.get("tags")
        section.color = form.get("color", "cyan")
        section.alignment = form.get("alignment", "left")
        section.is_visible = form.get("is_visible") == "on"
        
        db.commit()
    
    return RedirectResponse(url="/admin/profile?success=1", status_code=303)

@router.get("/assets/custom-section-editor.js")
async def get_custom_section_editor_js():
    return FileResponse("app/assets/custom_section_editor.js", media_type="application/javascript")

# ========== Projects ==========

@router.get("/projects", response_class=HTMLResponse)
async def projects_page(
    request: Request,
    user: User = Depends(require_auth),
    db: Session = Depends(get_db)
):
    """Projects manager"""
    projects = db.query(Project).order_by(Project.is_ongoing.desc(), Project.order).all()
    
    # Get unique option values
    sponsors = sorted([s[0] for s in db.query(Project.sponsor).distinct().all() if s[0]])
    roles = sorted([r[0] for r in db.query(Project.role).distinct().all() if r[0]])
    
    return templates.TemplateResponse(
        "admin/projects.html",
        get_context(request, user, projects=projects,
                   sponsors=sponsors, roles=roles)
    )


@router.post("/projects/add")
async def add_project(
    request: Request,
    user: User = Depends(require_auth),
    db: Session = Depends(get_db)
):
    """Add new project"""
    form = await request.form()
    project = Project(
        title=form.get("title"),
        sponsor=form.get("sponsor"),
        amount=form.get("amount"),
        start_date=form.get("start_date"),
        end_date=form.get("end_date"),
        is_ongoing=form.get("is_ongoing") == "on",
        role=form.get("role"),
        pi_name=form.get("pi_name"),
        co_pi_names=form.get("co_pi_names"),
        description=form.get("description")
    )
    db.add(project)
    db.commit()
    return RedirectResponse(url="/admin/projects?success=1", status_code=303)


@router.post("/projects/update/{project_id}")
async def update_project(
    project_id: int,
    request: Request,
    user: User = Depends(require_auth),
    db: Session = Depends(get_db)
):
    """Update project"""
    form = await request.form()
    project = db.query(Project).filter(Project.id == project_id).first()
    if project:
        project.title = form.get("title", project.title)
        project.sponsor = form.get("sponsor", project.sponsor)
        project.amount = form.get("amount", project.amount)
        project.start_date = form.get("start_date", project.start_date)
        project.end_date = form.get("end_date", project.end_date)
        project.is_ongoing = form.get("is_ongoing") == "on"
        project.role = form.get("role", project.role)
        project.pi_name = form.get("pi_name", project.pi_name)
        project.co_pi_names = form.get("co_pi_names", project.co_pi_names)
        project.description = form.get("description", project.description)
        db.commit()
    return RedirectResponse(url="/admin/projects?success=1", status_code=303)


@router.post("/projects/delete/{project_id}")
async def delete_project(
    project_id: int,
    user: User = Depends(require_auth),
    db: Session = Depends(get_db)
):
    """Delete project"""
    project = db.query(Project).filter(Project.id == project_id).first()
    if project:
        db.delete(project)
        db.commit()
    return RedirectResponse(url="/admin/projects", status_code=303)


# ========== Students ==========

@router.get("/students", response_class=HTMLResponse)
async def students_page(
    request: Request,
    user: User = Depends(require_auth),
    db: Session = Depends(get_db)
):
    """Students manager"""
    students = db.query(Student).order_by(Student.program, Student.order).all()
    
    # Get unique option values
    programs = sorted([p[0] for p in db.query(Student.program).distinct().all() if p[0]])
    statuses = sorted([s[0] for s in db.query(Student.status).distinct().all() if s[0]])
    categories = sorted([c[0] for c in db.query(Student.category).distinct().all() if c[0]])
    supervisions = sorted([s[0] for s in db.query(Student.supervision).distinct().all() if s[0]])
    
    return templates.TemplateResponse(
        "admin/students.html",
        get_context(request, user, students=students, 
                   programs=programs, statuses=statuses, 
                   categories=categories, supervisions=supervisions)
    )


@router.post("/students/add")
async def add_student(
    request: Request,
    user: User = Depends(require_auth),
    db: Session = Depends(get_db)
):
    """Add new student"""
    form = await request.form()
    student = Student(
        name=form.get("name"),
        program=form.get("program"),
        thesis_title=form.get("thesis_title"),
        status=form.get("status"),
        category=form.get("category"),
        supervision=form.get("supervision"),
        start_year=form.get("start_year"),
        end_year=form.get("end_year")
    )
    db.add(student)
    db.commit()
    return RedirectResponse(url="/admin/students?success=1", status_code=303)


@router.post("/students/update/{student_id}")
async def update_student(
    student_id: int,
    request: Request,
    user: User = Depends(require_auth),
    db: Session = Depends(get_db)
):
    """Update student"""
    form = await request.form()
    student = db.query(Student).filter(Student.id == student_id).first()
    if student:
        student.name = form.get("name", student.name)
        student.program = form.get("program", student.program)
        student.thesis_title = form.get("thesis_title", student.thesis_title)
        student.status = form.get("status", student.status)
        student.category = form.get("category", student.category)
        student.supervision = form.get("supervision", student.supervision)
        student.start_year = form.get("start_year", student.start_year)
        student.end_year = form.get("end_year", student.end_year)
        db.commit()
    return RedirectResponse(url="/admin/students?success=1", status_code=303)


@router.post("/students/delete/{student_id}")
async def delete_student(
    student_id: int,
    user: User = Depends(require_auth),
    db: Session = Depends(get_db)
):
    """Delete student"""
    student = db.query(Student).filter(Student.id == student_id).first()
    if student:
        db.delete(student)
        db.commit()
    return RedirectResponse(url="/admin/students", status_code=303)


# ========== Courses ==========

@router.get("/courses", response_class=HTMLResponse)
async def courses_page(
    request: Request,
    user: User = Depends(require_auth),
    db: Session = Depends(get_db)
):
    """Courses manager"""
    courses = db.query(Course).order_by(Course.is_lab, Course.order).all()
    
    # Get unique option values
    levels = sorted([l[0] for l in db.query(Course.level).distinct().all() if l[0]])
    course_types = sorted([t[0] for t in db.query(Course.course_type).distinct().all() if t[0]])
    
    return templates.TemplateResponse(
        "admin/courses.html",
        get_context(request, user, courses=courses,
                   levels=levels, course_types=course_types)
    )


@router.post("/courses/add")
async def add_course(
    request: Request,
    user: User = Depends(require_auth),
    db: Session = Depends(get_db)
):
    """Add new course"""
    form = await request.form()
    course = Course(
        name=form.get("name"),
        code=form.get("code"),
        level=form.get("level"),
        course_type=form.get("course_type"),
        is_lab=form.get("is_lab") == "on",
        description=form.get("description"),
        color=form.get("color", "cyan")
    )
    db.add(course)
    db.commit()
    return RedirectResponse(url="/admin/courses?success=1", status_code=303)


@router.post("/courses/update/{course_id}")
async def update_course(
    course_id: int,
    request: Request,
    user: User = Depends(require_auth),
    db: Session = Depends(get_db)
):
    """Update course"""
    form = await request.form()
    course = db.query(Course).filter(Course.id == course_id).first()
    if course:
        course.name = form.get("name", course.name)
        course.code = form.get("code", course.code)
        course.level = form.get("level", course.level)
        course.course_type = form.get("course_type", course.course_type)
        course.is_lab = form.get("is_lab") == "on"
        course.description = form.get("description", course.description)
        course.color = form.get("color", course.color)
        db.commit()
    return RedirectResponse(url="/admin/courses?success=1", status_code=303)


@router.post("/courses/delete/{course_id}")
async def delete_course(
    course_id: int,
    user: User = Depends(require_auth),
    db: Session = Depends(get_db)
):
    """Delete course"""
    course = db.query(Course).filter(Course.id == course_id).first()
    if course:
        db.delete(course)
        db.commit()
    return RedirectResponse(url="/admin/courses", status_code=303)


# ========== Education CRUD ==========

@router.post("/education/add")
async def add_education(
    request: Request,
    user: User = Depends(require_auth),
    db: Session = Depends(get_db)
):
    """Add education entry"""
    form = await request.form()
    edu = Education(
        degree=form.get("degree"),
        field=form.get("field"),
        institution=form.get("institution"),
        location=form.get("location"),
        year=form.get("year"),
        description=form.get("description")
    )
    db.add(edu)
    db.commit()
    return RedirectResponse(url="/admin/profile?success=1", status_code=303)


@router.post("/education/delete/{edu_id}")
async def delete_education(
    edu_id: int,
    user: User = Depends(require_auth),
    db: Session = Depends(get_db)
):
    """Delete education entry"""
    edu = db.query(Education).filter(Education.id == edu_id).first()
    if edu:
        db.delete(edu)
        db.commit()
    return RedirectResponse(url="/admin/profile", status_code=303)


@router.post("/education/update/{edu_id}")
async def update_education(
    edu_id: int,
    request: Request,
    user: User = Depends(require_auth),
    db: Session = Depends(get_db)
):
    """Update education entry"""
    form = await request.form()
    edu = db.query(Education).filter(Education.id == edu_id).first()
    if edu:
        edu.degree = form.get("degree", edu.degree)
        edu.field = form.get("field", edu.field)
        edu.institution = form.get("institution", edu.institution)
        edu.location = form.get("location", edu.location)
        edu.year = form.get("year", edu.year)
        edu.description = form.get("description", edu.description)
        db.commit()
    return RedirectResponse(url="/admin/profile?success=1", status_code=303)


# ========== Experience CRUD ==========

@router.post("/experience/add")
async def add_experience(
    request: Request,
    user: User = Depends(require_auth),
    db: Session = Depends(get_db)
):
    """Add experience entry"""
    form = await request.form()
    exp = Experience(
        position=form.get("position"),
        organization=form.get("organization"),
        department=form.get("department"),
        start_date=form.get("start_date"),
        end_date=form.get("end_date"),
        is_current=form.get("is_current") == "on"
    )
    db.add(exp)
    db.commit()
    return RedirectResponse(url="/admin/profile?success=1", status_code=303)


@router.post("/experience/update/{exp_id}")
async def update_experience(
    exp_id: int,
    request: Request,
    user: User = Depends(require_auth),
    db: Session = Depends(get_db)
):
    """Update experience entry"""
    form = await request.form()
    exp = db.query(Experience).filter(Experience.id == exp_id).first()
    if exp:
        exp.position = form.get("position", exp.position)
        exp.organization = form.get("organization", exp.organization)
        exp.department = form.get("department", exp.department)
        exp.start_date = form.get("start_date", exp.start_date)
        exp.end_date = form.get("end_date", exp.end_date)
        exp.is_current = form.get("is_current") == "on"
        db.commit()
    return RedirectResponse(url="/admin/profile?success=1", status_code=303)


@router.post("/experience/delete/{exp_id}")
async def delete_experience(
    exp_id: int,
    user: User = Depends(require_auth),
    db: Session = Depends(get_db)
):
    """Delete experience entry"""
    exp = db.query(Experience).filter(Experience.id == exp_id).first()
    if exp:
        db.delete(exp)
        db.commit()
    return RedirectResponse(url="/admin/profile", status_code=303)


# ========== Awards CRUD ==========

@router.post("/awards/add")
async def add_award(
    request: Request,
    user: User = Depends(require_auth),
    db: Session = Depends(get_db)
):
    """Add award entry"""
    form = await request.form()
    award = Award(
        title=form.get("title"),
        year=form.get("year"),
        organization=form.get("organization"),
        description=form.get("description")
    )
    db.add(award)
    db.commit()
    return RedirectResponse(url="/admin/profile?success=1", status_code=303)


@router.post("/awards/update/{award_id}")
async def update_award(
    award_id: int,
    request: Request,
    user: User = Depends(require_auth),
    db: Session = Depends(get_db)
):
    """Update award entry"""
    form = await request.form()
    award = db.query(Award).filter(Award.id == award_id).first()
    if award:
        award.title = form.get("title", award.title)
        award.year = form.get("year", award.year)
        award.organization = form.get("organization", award.organization)
        award.description = form.get("description", award.description)
        db.commit()
    return RedirectResponse(url="/admin/profile?success=1", status_code=303)


@router.post("/awards/delete/{award_id}")
async def delete_award(
    award_id: int,
    user: User = Depends(require_auth),
    db: Session = Depends(get_db)
):
    """Delete award entry"""
    award = db.query(Award).filter(Award.id == award_id).first()
    if award:
        db.delete(award)
        db.commit()
    return RedirectResponse(url="/admin/profile", status_code=303)


# ========== Research Areas CRUD ==========

@router.post("/research-areas/add")
async def add_research_area(
    request: Request,
    user: User = Depends(require_auth),
    db: Session = Depends(get_db)
):
    """Add research area"""
    form = await request.form()
    area = ResearchArea(
        name=form.get("name"),
        color=form.get("color", "cyan")
    )
    db.add(area)
    db.commit()
    return RedirectResponse(url="/admin/profile?success=1", status_code=303)


@router.post("/research-areas/update/{area_id}")
async def update_research_area(
    area_id: int,
    request: Request,
    user: User = Depends(require_auth),
    db: Session = Depends(get_db)
):
    """Update research area"""
    form = await request.form()
    area = db.query(ResearchArea).filter(ResearchArea.id == area_id).first()
    if area:
        area.name = form.get("name", area.name)
        area.color = form.get("color", area.color)
        db.commit()
    return RedirectResponse(url="/admin/profile?success=1", status_code=303)


@router.post("/research-areas/delete/{area_id}")
async def delete_research_area(
    area_id: int,
    user: User = Depends(require_auth),
    db: Session = Depends(get_db)
):
    if area:
        db.delete(area)
        db.commit()
    return RedirectResponse(url="/admin/profile", status_code=303)



# ========== Custom Sections CRUD ==========

@router.post("/custom-sections/add")
async def add_custom_section(
    request: Request,
    user: User = Depends(require_auth),
    db: Session = Depends(get_db)
):
    """Add custom section"""
    form = await request.form()
    section = CustomSection(
        title=form.get("title"),
        content=form.get("content"),
        order=form.get("order", 0),
        is_visible=form.get("is_visible") == "on",
        subtitle=form.get("subtitle"),
        year=form.get("year"),
        tags=form.get("tags"),
        color=form.get("color", "cyan"),
        alignment=form.get("alignment", "left")
    )
    db.add(section)
    db.commit()
    return RedirectResponse(url="/admin/profile?success=1", status_code=303)


@router.post("/custom-sections/update/{section_id}")
async def update_custom_section(
    section_id: int,
    request: Request,
    user: User = Depends(require_auth),
    db: Session = Depends(get_db)
):
    """Update custom section"""
    form = await request.form()
    section = db.query(CustomSection).filter(CustomSection.id == section_id).first()
    if section:
        section.title = form.get("title", section.title)
        section.content = form.get("content", section.content)
        section.order = form.get("order", section.order)
        section.is_visible = form.get("is_visible") == "on"
        section.subtitle = form.get("subtitle", section.subtitle)
        section.year = form.get("year", section.year)
        section.tags = form.get("tags", section.tags)
        section.color = form.get("color", section.color)
        section.alignment = form.get("alignment", section.alignment)
        db.commit()
    return RedirectResponse(url="/admin/profile?success=1", status_code=303)


@router.post("/custom-sections/delete/{section_id}")
async def delete_custom_section(
    section_id: int,
    user: User = Depends(require_auth),
    db: Session = Depends(get_db)
):
    """Delete custom section"""
    section = db.query(CustomSection).filter(CustomSection.id == section_id).first()
    if section:
        db.delete(section)
        db.commit()
    return RedirectResponse(url="/admin/profile", status_code=303)


# ========== Custom Section Items CRUD ==========

@router.post("/custom-sections/{section_id}/items/add")
async def add_custom_section_item(
    section_id: int,
    request: Request,
    user: User = Depends(require_auth),
    db: Session = Depends(get_db)
):
    """Add item to custom section"""
    form = await request.form()
    from ..models.custom_section_item import CustomSectionItem
    
    item = CustomSectionItem(
        section_id=section_id,
        title=form.get("title"),
        subtitle=form.get("subtitle"),
        year=form.get("year"),
        content=form.get("content"),
        link=form.get("link"),
        link_text=form.get("link_text"),
        order=form.get("order", 0),
        is_visible=form.get("is_visible") == "on"
    )
    db.add(item)
    db.commit()
    return RedirectResponse(url="/admin/profile?success=1", status_code=303)


@router.post("/custom-sections/items/update/{item_id}")
async def update_custom_section_item(
    item_id: int,
    request: Request,
    user: User = Depends(require_auth),
    db: Session = Depends(get_db)
):
    """Update custom section item"""
    form = await request.form()
    from ..models.custom_section_item import CustomSectionItem
    
    item = db.query(CustomSectionItem).filter(CustomSectionItem.id == item_id).first()
    if item:
        item.title = form.get("title", item.title)
        item.subtitle = form.get("subtitle", item.subtitle)
        item.year = form.get("year", item.year)
        item.content = form.get("content", item.content)
        item.link = form.get("link", item.link)
        item.link_text = form.get("link_text", item.link_text)
        item.order = form.get("order", item.order)
        item.is_visible = form.get("is_visible") == "on"
        db.commit()
    return RedirectResponse(url="/admin/profile?success=1", status_code=303)


@router.post("/custom-sections/items/delete/{item_id}")
async def delete_custom_section_item(
    item_id: int,
    user: User = Depends(require_auth),
    db: Session = Depends(get_db)
):
    """Delete custom section item"""
    from ..models.custom_section_item import CustomSectionItem
    
    item = db.query(CustomSectionItem).filter(CustomSectionItem.id == item_id).first()
    if item:
        db.delete(item)
        db.commit()
    return RedirectResponse(url="/admin/profile?success=1", status_code=303)


# ========== User Management ==========

@router.get("/users", response_class=HTMLResponse)
async def users_page(
    request: Request,
    user: User = Depends(require_auth),
    db: Session = Depends(get_db)
):
    """List all users"""
    # Only allow access if user is superuser? For now let all admins see it.
    users = db.query(User).order_by(User.id).all()
    return templates.TemplateResponse(
        "admin/users.html",
        get_context(request, user, users=users)
    )


@router.post("/users/add")
async def add_user(
    request: Request,
    user: User = Depends(require_auth),
    db: Session = Depends(get_db)
):
    """Add new user"""
    # Only superusers should be able to add users
    if not user.is_superuser:
         raise HTTPException(status_code=403, detail="Not authorized")
         
    form = await request.form()
    email = form.get("email")
    password = form.get("password")
    full_name = form.get("full_name")
    is_superuser = form.get("is_superuser") == "on"
    
    # Check if user exists
    existing = db.query(User).filter(User.email == email).first()
    if existing:
        return RedirectResponse(url="/admin/users?error=User already exists", status_code=303)
        
    new_user = User(
        email=email,
        hashed_password=User.hash_password(password),
        full_name=full_name,
        is_superuser=is_superuser
    )
    db.add(new_user)
    db.commit()
    return RedirectResponse(url="/admin/users?success=1", status_code=303)


@router.post("/users/delete/{user_id}")
async def delete_user(
    user_id: int,
    user: User = Depends(require_auth),
    db: Session = Depends(get_db)
):
    """Delete user"""
    # Only superusers should be able to delete users
    if not user.is_superuser:
         raise HTTPException(status_code=403, detail="Not authorized")
         
    # Prevent self-deletion
    if user.id == user_id:
        return RedirectResponse(url="/admin/users?error=Cannot delete yourself", status_code=303)
        
    user_to_delete = db.query(User).filter(User.id == user_id).first()
    if user_to_delete:
        db.delete(user_to_delete)
        db.commit()
    return RedirectResponse(url="/admin/users?success=1", status_code=303)


@router.post("/users/password/{user_id}")
async def update_user_password(
    user_id: int,
    request: Request,
    user: User = Depends(require_auth),
    db: Session = Depends(get_db)
):
    """Update user password"""
    form = await request.form()
    password = form.get("password")
    
    if not password or len(password) < 6:
        return RedirectResponse(url="/admin/users?error=Password+must+be+at+least+6+characters", status_code=303)
    
    target_user = db.query(User).filter(User.id == user_id).first()
    if target_user:
        target_user.hashed_password = User.hash_password(password)
        db.commit()
    return RedirectResponse(url="/admin/users?success=1", status_code=303)


# ========== Photo Management ==========

@router.post("/profile/delete-photo")
async def delete_profile_photo(
    request: Request,
    user: User = Depends(require_auth),
    db: Session = Depends(get_db)
):
    """Delete profile photo"""
    import os
    
    profile = db.query(Profile).first()
    if profile and profile.image_url:
        # Remove file from filesystem
        # image_url format is "/static/uploads/filename"
        try:
            file_path = profile.image_url.lstrip("/")
            if os.path.exists(file_path):
                os.remove(file_path)
        except Exception as e:
            print(f"Error deleting file: {e}")
            
        profile.image_url = None
        db.commit()
        
    return RedirectResponse(url="/admin/profile?success=1", status_code=303)


# ========== Pages Management ==========

@router.get("/pages", response_class=HTMLResponse)
async def pages_page(
    request: Request,
    user: User = Depends(require_auth),
    db: Session = Depends(get_db)
):
    """List all pages"""
    pages = db.query(Page).order_by(Page.menu_order).all()
    return templates.TemplateResponse(
        "admin/pages.html",
        get_context(request, user, pages=pages)
    )


@router.get("/pages/editor", response_class=HTMLResponse)
async def page_editor(
    request: Request,
    id: int = None,
    user: User = Depends(require_auth),
    db: Session = Depends(get_db)
):
    """Page editor (Create/Edit)"""
    page = None
    if id:
        page = db.query(Page).filter(Page.id == id).first()
        
    return templates.TemplateResponse(
        "admin/page_editor.html",
        get_context(request, user, page=page)
    )


@router.post("/pages/preview")
async def preview_page(
    request: Request,
    user: User = Depends(require_auth),
    db: Session = Depends(get_db)
):
    """Preview page content"""
    form = await request.form()
    
    # Construct a temporary page object
    # We need to render public/page.html, which expects "page" object with title, content, etc.
    # And "profile" object.
    
    class TempPage:
        def __init__(self, title, content):
            self.title = title
            self.content = content
            self.slug = "preview"
            self.is_published = False
            
    page = TempPage(
        title=form.get("title", "Preview"),
        content=form.get("content", "")
    )
    
    # Get profile for context
    profile = db.query(Profile).first()
    
    # We also need navigation pages if we want the navbar to look right, though it might not be strictly necessary for previewing content.
    # Let's get them to be consistent.
    pages = db.query(Page).filter(Page.show_in_menu == True, Page.is_published == True).order_by(Page.menu_order).all()
    request.state.pages = pages # Inject if needed by base template
    
    return templates.TemplateResponse(
        "public/page.html",
        {
            "request": request,
            "profile": profile,
            "page": page, 
            "preview_mode": True # Optional flag if we want to show a "Preview Mode" banner
        }
    )


@router.post("/pages/save")
async def save_page(
    request: Request,
    user: User = Depends(require_auth),
    db: Session = Depends(get_db)
):
    """Save page (Create/Update)"""
    form = await request.form()
    page_id = form.get("id")
    
    if page_id:
        page = db.query(Page).filter(Page.id == int(page_id)).first()
        if not page:
            raise HTTPException(status_code=404, detail="Page not found")
    else:
        # Check slug uniqueness
        slug = form.get("slug")
        if slug:
            existing = db.query(Page).filter(Page.slug == slug).first()
            if existing: # Basic uniqueness check
                pass
        page = Page()
        db.add(page)
    
    page.title = form.get("title")
    page.slug = form.get("slug")
    page.content = form.get("content")
    page.is_published = form.get("is_published") == "on"
    page.show_in_menu = form.get("show_in_menu") == "on"
    try:
        page.menu_order = int(form.get("menu_order", 0))
    except ValueError:
        page.menu_order = 0
    page.meta_description = form.get("meta_description")
    
    try:
        db.commit()
    except Exception as e:
        db.rollback()
        return RedirectResponse(url=f"/admin/pages/editor?error=Error saving page", status_code=303)
        
    return RedirectResponse(url="/admin/pages?success=1", status_code=303)


@router.post("/pages/delete/{page_id}")
async def delete_page(
    page_id: int,
    user: User = Depends(require_auth),
    db: Session = Depends(get_db)
):
    """Delete page"""
    page = db.query(Page).filter(Page.id == page_id).first()
    if page:
        db.delete(page)
        db.commit()
    return RedirectResponse(url="/admin/pages", status_code=303)


@router.get("/assets/page-editor.js")
async def get_page_editor_js(
    user: User = Depends(require_auth)
):
    """Serve page editor JavaScript (authenticated only)"""
    from fastapi.responses import FileResponse
    import os
    # JS file is inside app/assets/ for bundling with Python code
    js_path = os.path.join(os.path.dirname(__file__), '../assets/page_editor.js')
    return FileResponse(
        js_path, 
        media_type='application/javascript',
        headers={'Cache-Control': 'no-store'}  # Prevent caching for security
    )


# ========== Settings ==========

@router.get("/settings", response_class=HTMLResponse)
async def settings_page(
    request: Request,
    user: User = Depends(require_auth),
    db: Session = Depends(get_db)
):
    """Site settings page"""
    profile = db.query(Profile).first()
    pages = db.query(Page).all()
    return templates.TemplateResponse(
        "admin/settings.html",
        get_context(request, user, profile=profile, pages=pages)
    )


@router.post("/settings")
async def save_settings(
    request: Request,
    user: User = Depends(require_auth),
    db: Session = Depends(get_db)
):
    """Save site settings"""
    form = await request.form()
    
    # Update profile settings
    profile = db.query(Profile).first()
    if not profile:
        profile = Profile(name="Administrator") # Default required field
        db.add(profile)
    
    if profile:
        profile.site_title = form.get("site_title") or "ojsTerminalBio"
        profile.hero_title = form.get("hero_title") or "ojsTerminalBio"
        profile.hero_subtitle = form.get("hero_subtitle") or ""
        profile.show_matrix_effect = form.get("show_matrix_effect") == "on"
        profile.matrix_characters = form.get("matrix_characters") or "ꯀꯁꯂꯃꯄꯅꯆꯇꯈꯉ01"
        profile.matrix_opacity = form.get("matrix_opacity") or "0.05"
        profile.matrix_font_size = int(form.get("matrix_font_size") or 14)
        profile.theme_primary_color = form.get("theme_primary_color") or "cyan"
        profile.footer_text = form.get("footer_text") or "© 2025 ojsTerminalBio"
        
        # Home Page - Quick Stats
        profile.stat1_value = form.get("stat1_value")
        profile.stat1_label = form.get("stat1_label")
        profile.stat2_value = form.get("stat2_value")
        profile.stat2_label = form.get("stat2_label")
        profile.stat3_value = form.get("stat3_value")
        profile.stat3_label = form.get("stat3_label")
        
        # Home Page - Quick Links
        profile.link1_title = form.get("link1_title")
        profile.link1_description = form.get("link1_description")
        profile.link2_title = form.get("link2_title")
        profile.link2_description = form.get("link2_description")
        profile.link3_title = form.get("link3_title")
        profile.link3_description = form.get("link3_description")

        # Projects Page Customization
        profile.projects_header = form.get("projects_header")
        profile.projects_subheader = form.get("projects_subheader")
        profile.projects_stat1_value = form.get("projects_stat1_value")
        profile.projects_stat1_label = form.get("projects_stat1_label")
        profile.projects_stat2_label = form.get("projects_stat2_label")
        profile.projects_stat3_label = form.get("projects_stat3_label")
        profile.projects_ongoing_title = form.get("projects_ongoing_title")
        profile.projects_completed_title = form.get("projects_completed_title")

        # Students Page Customization
        profile.students_header = form.get("students_header")
        profile.students_subheader = form.get("students_subheader")
        profile.students_stat1_label = form.get("students_stat1_label")
        profile.students_stat2_label = form.get("students_stat2_label")
        profile.students_stat3_label = form.get("students_stat3_label")
        profile.students_stat4_label = form.get("students_stat4_label")
        profile.students_phd_title = form.get("students_phd_title")
        profile.students_mtech_title = form.get("students_mtech_title")

        # Teaching Page Customization
        profile.teaching_header = form.get("teaching_header")
        profile.teaching_subheader = form.get("teaching_subheader")
        profile.teaching_stat1_label = form.get("teaching_stat1_label")
        profile.teaching_stat2_label = form.get("teaching_stat2_label")
        profile.teaching_stat2_value = form.get("teaching_stat2_value")
        profile.teaching_stat3_label = form.get("teaching_stat3_label")
        profile.teaching_stat3_value = form.get("teaching_stat3_value")
        profile.teaching_theory_title = form.get("teaching_theory_title")
        profile.teaching_lab_title = form.get("teaching_lab_title")

        # Research Page Customization
        profile.research_header = form.get("research_header")
        profile.research_subheader = form.get("research_subheader")
        profile.research_interests_title = form.get("research_interests_title")
        profile.research_indexes_title = form.get("research_indexes_title")
        profile.research_google_label = form.get("research_google_label")
        profile.research_google_desc = form.get("research_google_desc")
        profile.research_dblp_label = form.get("research_dblp_label")
        profile.research_dblp_desc = form.get("research_dblp_desc")
        profile.research_publications_title = form.get("research_publications_title")

        # About Page Customization
        profile.about_header = form.get("about_header")
        profile.about_subheader = form.get("about_subheader")
        profile.about_location_label = form.get("about_location_label")
        
        # Navigation page visibility
        profile.show_about_page = form.get("show_about_page") == "on"
        profile.show_research_page = form.get("show_research_page") == "on"
        profile.show_publications_page = form.get("show_publications_page") == "on"
        profile.show_projects_page = form.get("show_projects_page") == "on"
        profile.show_students_page = form.get("show_students_page") == "on"
        profile.show_teaching_page = form.get("show_teaching_page") == "on"
        
        # Navigation page labels
        profile.label_about_page = form.get("label_about_page") or "About"
        profile.label_research_page = form.get("label_research_page") or "Research"
        profile.label_projects_page = form.get("label_projects_page") or "Projects"
        profile.label_students_page = form.get("label_students_page") or "Students"
        profile.label_teaching_page = form.get("label_teaching_page") or "Teaching"
        profile.label_publications_page = form.get("label_publications_page") or "Publications"
    
    # Update dynamic page visibility and menu settings
    visible_page_ids = []
    for pid in form.getlist("visible_pages"):
        try:
            visible_page_ids.append(int(pid))
        except:
            pass
    
    menu_page_ids = []
    for pid in form.getlist("menu_pages"):
        try:
            menu_page_ids.append(int(pid))
        except:
            pass
    
    all_pages = db.query(Page).all()
    for page in all_pages:
        page.is_published = page.id in visible_page_ids
        page.show_in_menu = page.id in menu_page_ids
        
        # Parent ID
        pid_val = form.get(f"parent_page_{page.id}")
        if pid_val and pid_val.isdigit():
            pid_int = int(pid_val)
            if pid_int != page.id: # Prevent self-parenting
                page.parent_id = pid_int
            else:
                page.parent_id = None
        else:
            page.parent_id = None
    
    db.commit()
    return RedirectResponse(url="/admin/settings", status_code=303)
