"""
ojsTerminalBio - CLI Entrypoint
"""
import argparse
import sys


def init_database():
    """Initialize database schema and create default admin user."""
    from ojsterminalbio.database import init_db, SessionLocal
    from ojsterminalbio.models.user import User
    from ojsterminalbio.models.profile import Profile
    from ojsterminalbio.config import settings
    
    print("[*] Initializing database...")
    init_db()
    
    db = SessionLocal()
    try:
        # Initialize default profile
        if not db.query(Profile).first():
            profile = Profile(
                name="Administrator",
                title="Academic Professional",
                institution="University Name",
                bio="Welcome to your new portfolio site.",
                site_title="ojsTerminalBio",
                hero_title="ojsTerminalBio",
                footer_text="© 2025 ojsTerminalBio",
                projects_stat1_value="₹17 Cr+",
                projects_stat1_label="Total Funding", 
                projects_stat2_label="Total Projects",
                projects_stat3_label="Ongoing"
            )
            db.add(profile)
            db.commit()
            print("[+] Default profile created.")

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
            print(f"[+] Default admin created: {settings.default_admin_email}")
            print("")
            print("=" * 60)
            print("[!] WARNING: Default credentials are INSECURE!")
            print(f"[!] Email:    {settings.default_admin_email}")
            print(f"[!] Password: {settings.default_admin_password}")
            print("[!] Change these immediately via environment variables:")
            print("[!]   OJSTB_DEFAULT_ADMIN_EMAIL")
            print("[!]   OJSTB_DEFAULT_ADMIN_PASSWORD")
            print("[!]   OJSTB_SECRET_KEY")
            print("=" * 60)
        else:
            print(f"[*] Admin already exists: {settings.default_admin_email}")
    finally:
        db.close()
    
    print("[+] Database initialized successfully.")


def runserver():
    """Start development server."""
    import uvicorn
    print("[*] Starting ojsTerminalBio development server...")
    print("[*] Access at: http://localhost:7777")
    print("[*] Press Ctrl+C to stop")
    uvicorn.run(
        "ojsterminalbio.main:app",
        host="0.0.0.0",
        port=7777,
        reload=True
    )


def main():
    """Main CLI entrypoint."""
    parser = argparse.ArgumentParser(
        prog="ojsterminalbio",
        description="ojsTerminalBio - Academic Portfolio CMS"
    )
    subparsers = parser.add_subparsers(dest="command", help="Available commands")
    
    # init-db command
    subparsers.add_parser(
        "init-db",
        help="Initialize database and create default admin user"
    )
    
    # runserver command
    subparsers.add_parser(
        "runserver",
        help="Start development server on port 7777"
    )
    
    args = parser.parse_args()
    
    if args.command == "init-db":
        init_database()
    elif args.command == "runserver":
        runserver()
    else:
        parser.print_help()
        sys.exit(1)


if __name__ == "__main__":
    main()
