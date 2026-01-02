# ojsTerminalBio

A cyberpunk-themed academic portfolio CMS built with FastAPI. Create stunning terminal-style portfolio websites with a powerful admin interface.

![Python](https://img.shields.io/badge/Python-3.10%2B-blue)
![License](https://img.shields.io/badge/License-MIT-green)
[![PyPI](https://img.shields.io/pypi/v/ojsterminalbio)](https://pypi.org/project/ojsTerminalBio/)

## ✨ Features

- 🎨 Cyberpunk terminal-style UI with matrix rain effect
- 📊 Admin dashboard for managing all content
- 📄 Dynamic page editor with drag-and-drop blocks
- 📚 Publications, Projects, Students, Courses management
- 🎓 Education & Experience sections
- 🔗 Dynamic external links (Google Scholar, DBLP, etc.)
- 🌙 Light/Dark theme toggle
- 📱 Fully responsive design

## 🚀 Quick Start

### Installation

```bash
pip install ojsterminalbio
```

### Initialize Database

```bash
ojsterminalbio init-db
```

### Run Server

```bash
ojsterminalbio runserver
```

**Access at:** http://localhost:7777

**Default Admin Login:**
- Email: `admin@example.com`
- Password: `admin123`

> ⚠️ **Change these credentials immediately in production!**

---

## ⚙️ Configuration

Set environment variables or create a `.env` file:

```bash
# Required for production
export OJSTB_SECRET_KEY="your-secure-random-key"
export OJSTB_DEFAULT_ADMIN_EMAIL="your@email.com"
export OJSTB_DEFAULT_ADMIN_PASSWORD="secure-password"

# Optional
export OJSTB_DATABASE_URL="sqlite:///./ojsterminalbio.db"
export OJSTB_DEBUG="false"
```

---

## 🖥️ CLI Commands

| Command | Description |
|---------|-------------|
| `ojsterminalbio init-db` | Initialize/reset database |
| `ojsterminalbio runserver` | Start development server |
| `ojsterminalbio runserver --port 8000` | Custom port |
| `ojsterminalbio runserver --host 0.0.0.0` | Allow external access |

---

## 📁 Project Structure

After installation, the package includes:

```
ojsterminalbio/
├── templates/           # Jinja2 HTML templates
│   ├── admin/          # Admin panel templates
│   └── public/         # Public-facing templates
├── static/             # CSS, JS, images
│   └── css/
│       └── tailwind.css
├── models/             # SQLAlchemy models
├── routers/            # FastAPI routes
└── cli.py              # Command-line interface
```

---

## 🎨 Customization

### Theme Colors
In admin panel: **Settings → Theme Primary Color**
- Cyan (default)
- Pink
- Amber
- Green

### Matrix Effect
Customize via admin:
- Enable/disable matrix rain
- Change characters (supports Unicode/Meitei script)
- Adjust opacity and speed

---

## 🔧 Development

### Clone & Setup
```bash
git clone https://github.com/Okramjimmy/ojsTerminalBio.git
cd ojsTerminalBio
python -m venv venv
source venv/bin/activate
pip install -e .
```

### Run locally
```bash
ojsterminalbio init-db
ojsterminalbio runserver
```

---

## 📦 Building from Source

```bash
pip install build
python -m build
pip install dist/ojsterminalbio-*.whl
```

---

## 🤝 Contributing

1. Fork the repository
2. Create feature branch (`git checkout -b feature/amazing`)
3. Commit changes (`git commit -m 'Add amazing feature'`)
4. Push to branch (`git push origin feature/amazing`)
5. Open a Pull Request

---

## 📄 License

MIT License - see [LICENSE](LICENSE) file.

---

## 👤 Author

**Okram Jimmy Singh**
- Email: jimmy.lamzing@gmail.com

---

## 🙏 Acknowledgments

- FastAPI framework
- Tailwind CSS
- Jinja2 templating
