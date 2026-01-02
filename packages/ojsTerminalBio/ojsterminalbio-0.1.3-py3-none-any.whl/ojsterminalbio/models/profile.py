"""
Profile Model - Basic information
"""
from sqlalchemy import Column, Integer, String, Text, Boolean
from sqlalchemy.orm import relationship

from ..database import Base


class Profile(Base):
    __tablename__ = "profiles"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=True)
    native_name = Column(String(255), nullable=True)
    title = Column(String(255), nullable=True)  # e.g., "Professor"
    department = Column(String(255), nullable=True)
    institution = Column(String(255), nullable=True)
    
    # Contact
    email = Column(String(255), nullable=True)
    phone = Column(String(50), nullable=True)
    fax = Column(String(50), nullable=True)
    address = Column(Text, nullable=True)
    
    # Bio
    bio = Column(Text, nullable=True)
    
    # Links
    links = relationship("ProfileLink", backref="profile", cascade="all, delete-orphan")
    
    # Profile image
    image_url = Column(String(500), nullable=True)

    # Site Customization
    site_title = Column(String(255), default="ojsTerminalBio")
    hero_title = Column(String(255), default="ojsTerminalBio")
    hero_subtitle = Column(String(255), default="Academic Portfolio CMS")
    footer_text = Column(String(255), default="© 2025 ojsTerminalBio")
    show_matrix_effect = Column(Boolean, default=True)
    matrix_characters = Column(String(500), default="ꯀꯁꯂꯃꯄꯅꯆꯇꯈꯉ01")  # Characters for Matrix rain animation
    matrix_opacity = Column(String(10), default="0.05")  # Background fade opacity
    matrix_font_size = Column(Integer, default=14)  # Font size in px
    theme_primary_color = Column(String(50), default="cyan")  # cyan, pink, amber, etc.
    
    # Page Visibility Settings
    show_about_page = Column(Boolean, default=True)
    show_research_page = Column(Boolean, default=True)
    show_projects_page = Column(Boolean, default=True)
    show_students_page = Column(Boolean, default=True)
    show_teaching_page = Column(Boolean, default=True)
    show_publications_page = Column(Boolean, default=True)
    
    # Page Labels (Editable standard tabs)
    label_about_page = Column(String(50), default="About")
    label_research_page = Column(String(50), default="Research")
    label_projects_page = Column(String(50), default="Projects")
    label_students_page = Column(String(50), default="Students")
    label_teaching_page = Column(String(50), default="Teaching")
    label_publications_page = Column(String(50), default="Publications")

    # Profile Section Settings (Labels & Visibility)
    # Basic Info
    label_basic_info = Column(String(50), default="Basic Information")
    show_basic_info = Column(Boolean, default=True)
    
    # Contact
    label_contact_info = Column(String(50), default="Contact Information")
    show_contact_info = Column(Boolean, default=True)
    
    # Bio
    label_bio = Column(String(50), default="Biography")
    show_bio = Column(Boolean, default=True)
    
    # Links
    label_links = Column(String(50), default="External Links")
    show_links = Column(Boolean, default=True)
    
    # Education
    label_education = Column(String(50), default="Education")
    show_education = Column(Boolean, default=True)
    
    # Experience
    label_experience = Column(String(50), default="Experience")
    show_experience = Column(Boolean, default=True)
    
    # Awards
    label_awards = Column(String(50), default="Awards")
    show_awards = Column(Boolean, default=True)
    
    # Research Areas
    label_research_areas = Column(String(50), default="Research Areas")
    label_custom_sections = Column(String(50), default="Custom Sections")
    show_research_areas = Column(Boolean, default=True)
    
    # Home Page - Quick Stats Section
    stat1_value = Column(String(50), default="100+")
    stat1_label = Column(String(50), default="Publications")
    stat2_value = Column(String(50), default="10+")
    stat2_label = Column(String(50), default="PhD Scholars")
    stat3_value = Column(String(50), default="₹10Cr+")
    stat3_label = Column(String(50), default="Project Funding")
    
    # Home Page - Quick Links Section
    link1_title = Column(String(100), default="Research & Publications")
    link1_description = Column(String(255), default="Lorem ipsum dolor sit amet, consectetur adipiscing elit.")
    link2_title = Column(String(100), default="Sponsored Projects")
    link2_description = Column(String(255), default="Lorem ipsum dolor sit amet, consectetur adipiscing elit.")
    link3_title = Column(String(100), default="Students Supervised")
    link3_description = Column(String(255), default="Lorem ipsum dolor sit amet, consectetur adipiscing elit.")

    # Projects Page Customization
    projects_header = Column(String(255), default="Sponsored & Consultancy Projects")
    projects_subheader = Column(String(255), default="Principal Investigator and Co-Investigator on Major Research Projects")
    projects_stat1_value = Column(String(50), default="₹17 Cr+")
    projects_stat1_label = Column(String(50), default="Total Funding")
    projects_stat2_label = Column(String(50), default="Total Projects")
    projects_stat3_label = Column(String(50), default="Ongoing")
    projects_ongoing_title = Column(String(100), default="Ongoing_Projects")
    projects_completed_title = Column(String(100), default="Completed_Projects")

    # Students Page Customization
    students_header = Column(String(255), default="Students Supervised")
    students_subheader = Column(String(255), default="PhD Scholars and MTech Students")
    students_stat1_label = Column(String(50), default="Total PhD")
    students_stat2_label = Column(String(50), default="PhD Completed")
    students_stat3_label = Column(String(50), default="PhD Ongoing")
    students_stat4_label = Column(String(50), default="MTech Supervised")
    students_phd_title = Column(String(100), default="PhD_Scholars")
    students_mtech_title = Column(String(100), default="MTech_Students")

    # Teaching Page Customization
    teaching_header = Column(String(255), default="Teaching")
    teaching_subheader = Column(String(255), default="Courses Taught at IIT Guwahati")
    teaching_stat1_label = Column(String(50), default="Courses Taught")
    teaching_stat2_label = Column(String(50), default="Levels")
    teaching_stat2_value = Column(String(50), default="UG & PG")
    teaching_stat3_label = Column(String(50), default="Teaching Experience")
    teaching_stat3_value = Column(String(50), default="15+ Years")
    teaching_theory_title = Column(String(100), default="Theory_Courses")
    teaching_lab_title = Column(String(100), default="Lab_Courses")

    # Research Page Customization
    research_header = Column(String(255), default="Research & Publications")
    research_subheader = Column(String(255), default="Peer-Reviewed Papers in International Journals and Conferences")
    research_interests_title = Column(String(100), default="RESEARCH_INTERESTS")
    research_indexes_title = Column(String(100), default="Digital_Library_Indexes")
    research_google_label = Column(String(100), default="Google Scholar")
    research_google_desc = Column(String(100), default="View all citations and publications")
    research_dblp_label = Column(String(100), default="DBLP")
    research_dblp_desc = Column(String(100), default="Computer Science Bibliography")
    research_publications_title = Column(String(100), default="Publications")

    # About Page Customization
    about_header = Column(String(255), default="About Me")
    about_subheader = Column(String(255), default="Professor, Department of Computer Science and Engineering")
    about_location_label = Column(String(50), default="LOCATION")

