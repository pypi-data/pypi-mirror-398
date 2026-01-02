# ojsTerminalBio - UI Templates & Assets

Cyberpunk-themed academic portfolio UI files for [ojsTerminalBio](https://pypi.org/project/ojsTerminalBio/).

## � Screenshots

### Home Page
![Home Page](screenshots/home.png)

### Admin Dashboard
![Admin Dashboard](screenshots/admin_dashboard.png)

### Profile Editor
![Profile Editor](screenshots/admin_profile.png)

### Page Editor
![Page Editor](screenshots/page_editor.png)

## �📦 Installation

### Option 1: Install via PyPI (Recommended)
```bash
pip install ojsterminalbio
ojsterminalbio init-db
ojsterminalbio runserver
```

### Option 2: Use these templates with custom backend
Clone this repo and copy templates/static to your project.

---

## 📁 Structure

```
ojsterminalbio/
├── templates/
│   ├── admin/          # Admin panel UI
│   │   ├── base.html
│   │   ├── dashboard.html
│   │   ├── profile.html
│   │   ├── page_editor.html
│   │   └── ...
│   └── public/         # Public website UI
│       ├── base.html
│       ├── index.html
│       ├── about.html
│       ├── research.html
│       └── ...
└── static/
    └── css/
        └── tailwind.css
```

---

## 🚀 Quick Start

### One-Click Setup

**macOS/Linux:**
```bash
chmod +x setup.sh
./setup.sh
```

**Windows:**
```cmd
setup.bat
```

### Manual Installation
```bash
# Install package
pip install ojsterminalbio

# Initialize database
ojsterminalbio init-db

# Run server
ojsterminalbio runserver
```

**Access:** http://localhost:7777

**Admin Login:**
- Email: `admin@example.com`
- Password: `admin123`

---

## ⚙️ Configuration

```bash
export OJSTB_SECRET_KEY="your-secret-key"
export OJSTB_DEFAULT_ADMIN_EMAIL="your@email.com"
export OJSTB_DEFAULT_ADMIN_PASSWORD="secure-password"
export OJSTB_DATABASE_URL="sqlite:///./ojsterminalbio.db"
```

---

## 🎨 Features

- Cyberpunk terminal-style theme
- Matrix rain background effect
- Light/Dark mode toggle
- Responsive design
- Dynamic page editor
- Customizable colors (Cyan, Pink, Amber, Green)

---

## � Admin Panel Access

1. Navigate to: **http://localhost:7777/admin/login**
2. Enter credentials:
   - Email: `admin@example.com`
   - Password: `admin123`
3. Click Login

### Admin Pages

| URL | Description |
|-----|-------------|
| `/admin/dashboard` | Overview with stats |
| `/admin/profile` | Edit name, bio, contact info |
| `/admin/publications` | Manage research papers |
| `/admin/projects` | Manage sponsored projects |
| `/admin/students` | Add PhD/MTech students |
| `/admin/courses` | Add courses taught |
| `/admin/pages` | Create custom pages |
| `/admin/settings` | Theme & site settings |

---

## 🎨 Customization Guide

### 1. Change Theme Color
Go to **Admin → Settings → Theme Primary Color**
- Cyan (default)
- Pink
- Amber
- Green

### 2. Edit Profile Info
Go to **Admin → Profile**
- Basic Info: Name, Title, Department
- Contact: Email, Phone, Address
- Bio: About yourself
- External Links: Google Scholar, DBLP, etc.

### 3. Matrix Effect
Go to **Admin → Settings**
- Enable/disable matrix rain
- Change characters (supports emoji, Unicode)
- Adjust opacity

### 4. Add Custom Pages
Go to **Admin → Pages → Create Page**
- Drag & drop blocks
- Add cards, text, buttons
- Publish to menu

### 5. Manage Content
- **Publications**: Add research papers with DOI links
- **Projects**: Add sponsored projects with funding info
- **Students**: Add supervised students
- **Courses**: Add courses with syllabus

---

## 📄 License

MIT License

## 👤 Author

Okram Jimmy Singh
