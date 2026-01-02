"""
Ranbir Portfolio CMS - Pydantic Schemas
"""
from pydantic import BaseModel, EmailStr
from typing import Optional, List


# User schemas
class UserBase(BaseModel):
    email: EmailStr
    full_name: Optional[str] = None


class UserCreate(UserBase):
    password: str


class UserLogin(BaseModel):
    email: EmailStr
    password: str


class User(UserBase):
    id: int
    is_active: bool

    class Config:
        from_attributes = True


class Token(BaseModel):
    access_token: str
    token_type: str


# Profile schemas
class ProfileBase(BaseModel):
    name: str
    title: Optional[str] = None
    department: Optional[str] = None
    institution: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    fax: Optional[str] = None
    address: Optional[str] = None
    bio: Optional[str] = None
    google_scholar: Optional[str] = None
    dblp: Optional[str] = None
    website: Optional[str] = None
    osint_lab: Optional[str] = None


class ProfileCreate(ProfileBase):
    pass


class Profile(ProfileBase):
    id: int

    class Config:
        from_attributes = True


# Education schemas
class EducationBase(BaseModel):
    degree: str
    field: Optional[str] = None
    institution: str
    location: Optional[str] = None
    year: Optional[str] = None
    description: Optional[str] = None
    order: int = 0


class EducationCreate(EducationBase):
    pass


class Education(EducationBase):
    id: int

    class Config:
        from_attributes = True


# Experience schemas
class ExperienceBase(BaseModel):
    position: str
    organization: str
    department: Optional[str] = None
    location: Optional[str] = None
    start_date: Optional[str] = None
    end_date: Optional[str] = None
    is_current: bool = False
    description: Optional[str] = None
    order: int = 0


class ExperienceCreate(ExperienceBase):
    pass


class Experience(ExperienceBase):
    id: int

    class Config:
        from_attributes = True


# Award schemas
class AwardBase(BaseModel):
    title: str
    year: Optional[str] = None
    description: Optional[str] = None
    organization: Optional[str] = None
    order: int = 0


class AwardCreate(AwardBase):
    pass


class Award(AwardBase):
    id: int

    class Config:
        from_attributes = True


# Research Area schemas
class ResearchAreaBase(BaseModel):
    name: str
    color: str = "cyan"
    order: int = 0


class ResearchAreaCreate(ResearchAreaBase):
    pass


class ResearchArea(ResearchAreaBase):
    id: int

    class Config:
        from_attributes = True


# Publication schemas
class PublicationBase(BaseModel):
    title: str
    authors: Optional[str] = None
    venue: Optional[str] = None
    venue_type: Optional[str] = None
    year: int
    month: Optional[str] = None
    pages: Optional[str] = None
    volume: Optional[str] = None
    doi: Optional[str] = None
    url: Optional[str] = None
    status: str = "published"
    order: int = 0


class PublicationCreate(PublicationBase):
    pass


class Publication(PublicationBase):
    id: int

    class Config:
        from_attributes = True


# Project schemas
class ProjectBase(BaseModel):
    title: str
    sponsor: Optional[str] = None
    amount: Optional[str] = None
    amount_value: Optional[float] = None
    start_date: Optional[str] = None
    end_date: Optional[str] = None
    is_ongoing: bool = True
    role: Optional[str] = None
    pi_name: Optional[str] = None
    co_pi_names: Optional[str] = None
    description: Optional[str] = None
    order: int = 0


class ProjectCreate(ProjectBase):
    pass


class Project(ProjectBase):
    id: int

    class Config:
        from_attributes = True


# Student schemas
class StudentBase(BaseModel):
    name: str
    program: str
    thesis_title: Optional[str] = None
    status: Optional[str] = None
    category: Optional[str] = None
    supervision: Optional[str] = None
    start_year: Optional[str] = None
    end_year: Optional[str] = None
    current_position: Optional[str] = None
    order: int = 0


class StudentCreate(StudentBase):
    pass


class Student(StudentBase):
    id: int

    class Config:
        from_attributes = True


# Course schemas
class CourseBase(BaseModel):
    name: str
    code: Optional[str] = None
    level: Optional[str] = None
    course_type: Optional[str] = None
    is_lab: bool = False
    description: Optional[str] = None
    color: str = "cyan"
    order: int = 0


class CourseCreate(CourseBase):
    pass


class Course(CourseBase):
    id: int

    class Config:
        from_attributes = True
