# MeBox - Social Wiki Network

A social media network based around shared wikis and userboxes, inspired by Wikipedia's user namespace.

## Features

- **User Authentication**: Sign up, login, and logout functionality
- **Personal Wiki Pages**: Create, edit, and view wiki pages in your own user namespace
- **Markdown Support**: Rich text editing using markdown-it-py
- **User Profiles**: View your own and others' wiki pages
- **SQLite Database**: Lightweight database backend

## Installation

### Prerequisites

- Python 3.9+
- uv (Python package manager)

### Local Installation

1. Clone the repository:
   ```bash
   git clone https://github.com/yourusername/mebox.git
   cd mebox
   ```

2. Install dependencies:
   ```bash
   uv pip install django markdown-it-py mdurl python-multipart django-humanize
   ```

3. Set up the Django project:
   ```bash
   python manage.py migrate
   python manage.py createsuperuser
   ```

## Running the Application

```bash
python manage.py runserver
```

Then open your browser to `http://localhost:8000`

## Usage

### Creating an Account

1. Visit `http://localhost:8000/signup/`
2. Fill in your username, email, and password
3. Click "Sign Up"

### Creating Wiki Pages

1. Login to your account
2. Click "Create Page" in the navigation
3. Enter a title and content using Markdown
4. Click "Create Page"

### Viewing Wiki Pages

- Visit `http://localhost:8000/user/username/` to view a user's profile
- Click on any wiki page title to view the full content

### Editing Wiki Pages

1. Visit your own profile or a wiki page you created
2. Click "Edit" on the page you want to modify
3. Update the content and click "Update Page"

## Markdown Support

MeBox supports standard Markdown syntax:

```markdown
# Heading 1
## Heading 2

**Bold text**
*Italic text*

- Bullet point 1
- Bullet point 2

1. Numbered item 1
2. Numbered item 2

`inline code`

```python
# Code block
print("Hello, World!")
```

[Link text](https://example.com)

![Image alt text](https://example.com/image.jpg)
```

## Project Structure

```
mebox/
├── mebox/                  # Django project settings
│   ├── __init__.py
│   ├── settings.py
│   ├── urls.py
│   └── wsgi.py
│
├── wiki/                   # Wiki application
│   ├── migrations/         # Database migrations
│   ├── templates/wiki/     # HTML templates
│   ├── __init__.py
│   ├── admin.py
│   ├── apps.py
│   ├── forms.py            # Form definitions
│   ├── models.py           # Database models
│   ├── urls.py             # URL routing
│   └── views.py            # View functions
│
├── db.sqlite3              # SQLite database
├── manage.py               # Django management script
├── pyproject.toml          # Project configuration
├── Dockerfile              # Docker configuration
├── docker-compose.yml      # Docker Compose configuration
└── README.md               # This file
```

## Database

MeBox uses SQLite by default, which is configured in `mebox/settings.py`:

```python
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db.sqlite3',
    }
}
```

## Administration

Access the Django admin interface at `http://localhost:8000/admin/`:

- Username: `admin` (created during setup)
- Password: (set during `createsuperuser`)

## Deployment

For production deployment, consider:

1. Using a proper web server (Nginx, Apache) with WSGI
2. Switching to PostgreSQL for better performance
3. Setting `DEBUG = False` in settings.py
4. Configuring proper ALLOWED_HOSTS
5. Setting up static file storage
6. Using environment variables for secrets

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## License

This project is open source and available under the MIT License.
=======