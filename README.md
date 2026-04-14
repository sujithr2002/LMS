# 🎓 LMS Platform – Django Learning Management System

A full-featured Learning Management System built with Django 6.0, featuring role-based access (Admin, Teacher, Student), course management, module/content delivery (video & PDF), enrollment request workflows, assignments, grading, and email-verified registration.

---

## 📋 Table of Contents

1. [Features](#-features)
2. [Tech Stack](#-tech-stack)
3. [Local Development](#-local-development)
4. [Hosting on Amazon EC2 – Complete Guide](#-hosting-on-amazon-ec2--complete-guide)
   - [Step 1 – Launch an EC2 Instance](#step-1--launch-an-ec2-instance)
   - [Step 2 – Connect to Your Instance](#step-2--connect-to-your-instance)
   - [Step 3 – Install System Dependencies](#step-3--install-system-dependencies)
   - [Step 4 – Clone Your Project](#step-4--clone-your-project)
   - [Step 5 – Configure the Environment](#step-5--configure-the-environment)
   - [Step 6 – Set Up the Database & Static Files](#step-6--set-up-the-database--static-files)
   - [Step 7 – Test with Gunicorn](#step-7--test-with-gunicorn)
   - [Step 8 – Create a Systemd Service for Gunicorn](#step-8--create-a-systemd-service-for-gunicorn)
   - [Step 9 – Configure Nginx as Reverse Proxy](#step-9--configure-nginx-as-reverse-proxy)
   - [Step 10 – Open Firewall / Security Group](#step-10--open-firewall--security-group)
   - [Step 11 – Verify Everything](#step-11--verify-everything)
5. [Optional: Custom Domain & HTTPS](#-optional-custom-domain--https)
6. [Maintenance & Useful Commands](#-maintenance--useful-commands)
7. [Troubleshooting](#-troubleshooting)
8. [Project Structure](#-project-structure)

---

## ✨ Features

| Role | Capabilities |
|------|-------------|
| **Admin** | Create/edit/delete courses, manage users (CRUD), approve/reject enrollment requests, view all submissions, access Django admin panel |
| **Teacher** | Manage modules & content (video/PDF) for assigned courses, create assignments, grade submissions, view enrolled students |
| **Student** | Browse courses, request enrollment (admin-approved), view course content, submit assignments (text/PDF), track grades |

**Common:** Email OTP verification, password reset, profile management, responsive sidebar UI.

---

## 🛠 Tech Stack

- **Backend:** Django 6.0.4, Python 3.12+
- **Database:** SQLite (production-ready for small-to-medium scale)
- **Server:** Gunicorn (WSGI) + Nginx (reverse proxy)
- **Styling:** Custom CSS with Inter font
- **Hosting:** Amazon EC2 (Ubuntu)

---

## 💻 Local Development

```bash
# Clone the repository
git clone <your-repo-url>
cd lms

# Create virtual environment
python -m venv venv

# Activate (Windows)
venv\Scripts\activate
# Activate (Linux/Mac)
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Create .env from template (optional for local dev – defaults work out of the box)
cp .env.example .env

# Run migrations
python manage.py migrate

# (Optional) Load sample data
python manage.py seed_data

# Create superuser
python manage.py createsuperuser

# Run development server
python manage.py runserver
```

Visit: `http://127.0.0.1:8000`

---

## 🚀 Hosting on Amazon EC2 – Complete Guide

> This guide walks you through every single step to deploy the LMS on a fresh **Ubuntu 22.04/24.04 EC2 instance** using **Gunicorn + Nginx**.

---

### Step 1 – Launch an EC2 Instance

1. Log in to the **[AWS Console](https://console.aws.amazon.com/ec2/)**.
2. Click **"Launch Instance"**.
3. Configure:

| Setting | Recommended Value |
|---------|-------------------|
| **Name** | `lms-server` |
| **AMI** | Ubuntu Server 22.04 LTS (or 24.04 LTS) |
| **Instance type** | `t2.micro` (free tier) or `t3.small` for production |
| **Key pair** | Create a new key pair → download the `.pem` file → **keep it safe** |
| **Network settings** | Allow SSH (port 22) from your IP |
| **Storage** | 20 GB gp3 (minimum) |

4. Click **"Launch Instance"**.
5. Note the **Public IPv4 address** (e.g., `54.123.45.67`) from the instance details.

---

### Step 2 – Connect to Your Instance

**From your local terminal (Linux/Mac/Windows PowerShell):**

```bash
# Set correct permissions on the key file (Linux/Mac only)
chmod 400 your-key.pem

# Connect
ssh -i your-key.pem ubuntu@<YOUR_EC2_PUBLIC_IP>
```

> **Windows users:** You can also use PuTTY (convert `.pem` to `.ppk` with PuTTYgen) or the built-in AWS "Connect" button in the EC2 console.

---

### Step 3 – Install System Dependencies

Run these commands on the EC2 instance:

```bash
# Update system packages
sudo apt update && sudo apt upgrade -y

# Install Python, pip, venv, and Nginx
sudo apt install -y python3 python3-pip python3-venv nginx git
```

---

### Step 4 – Clone Your Project

```bash
# Option A: Clone from Git
cd /home/ubuntu
git clone <your-repo-url> lms
cd lms

# Option B: Upload via SCP (from your local machine)
# scp -i your-key.pem -r /path/to/lms ubuntu@<YOUR_EC2_PUBLIC_IP>:/home/ubuntu/lms
```

Now set up the Python environment:

```bash
# Create virtual environment
python3 -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

---

### Step 5 – Configure the Environment

```bash
# Copy the example env file
cp .env.example .env

# Edit with nano (or vim)
nano .env
```

**Fill in your actual values:**

```ini
SECRET_KEY=your-very-long-random-secret-key-here
DEBUG=False
ALLOWED_HOSTS=<YOUR_EC2_PUBLIC_IP>,your-domain.com

EMAIL_HOST_USER=your-email@gmail.com
EMAIL_HOST_PASSWORD=your-gmail-app-password
DEFAULT_FROM_EMAIL=your-email@gmail.com

ADMIN_REGISTRATION_CODE=YourSecretAdminCode
SECURE_SSL_REDIRECT=False
```

> **Generate a Django secret key:**
> ```bash
> python3 -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"
> ```

> **Gmail App Password:** Go to [Google Account → Security → App passwords](https://myaccount.google.com/apppasswords) and generate one. You need 2FA enabled on your Google account.

---

### Step 6 – Set Up the Database & Static Files

```bash
# Activate venv if not active
source venv/bin/activate

# Run migrations
python manage.py migrate

# Collect static files into 'staticfiles/' directory
python manage.py collectstatic --noinput

# Create a superuser (admin account)
python manage.py createsuperuser

# (Optional) Load sample data
python manage.py seed_data
```

---

### Step 7 – Test with Gunicorn

```bash
# Quick test – should start without errors
gunicorn --bind 0.0.0.0:8000 core.wsgi:application
```

Visit `http://<YOUR_EC2_PUBLIC_IP>:8000` in your browser (you'll need port 8000 open in Security Groups temporarily).

If it works, press **Ctrl+C** to stop. Now we'll set it up as a proper system service.

---

### Step 8 – Create a Systemd Service for Gunicorn

This ensures Gunicorn starts automatically on boot and restarts on failure.

```bash
sudo nano /etc/systemd/system/lms.service
```

Paste the following (adjust paths if your project is in a different location):

```ini
[Unit]
Description=LMS Django Gunicorn Daemon
After=network.target

[Service]
User=ubuntu
Group=www-data
WorkingDirectory=/home/ubuntu/lms
EnvironmentFile=/home/ubuntu/lms/.env
ExecStart=/home/ubuntu/lms/venv/bin/gunicorn \
    --access-logfile - \
    --error-logfile /home/ubuntu/lms/gunicorn-error.log \
    --workers 3 \
    --bind unix:/home/ubuntu/lms/lms.sock \
    core.wsgi:application
Restart=on-failure
RestartSec=5

[Install]
WantedBy=multi-user.target
```

Enable and start the service:

```bash
sudo systemctl daemon-reload
sudo systemctl start lms
sudo systemctl enable lms

# Check status
sudo systemctl status lms
```

You should see `active (running)` in green. If not, check logs:

```bash
sudo journalctl -u lms -n 50
```

---

### Step 9 – Configure Nginx as Reverse Proxy

Nginx will serve static/media files directly and forward all other requests to Gunicorn.

```bash
sudo nano /etc/nginx/sites-available/lms
```

Paste this configuration:

```nginx
server {
    listen 80;
    server_name <YOUR_EC2_PUBLIC_IP>;
    # If you have a domain, replace the above with:
    # server_name your-domain.com www.your-domain.com;

    client_max_body_size 50M;

    # Serve static files
    location /static/ {
        alias /home/ubuntu/lms/staticfiles/;
    }

    # Serve media files (uploaded content)
    location /media/ {
        alias /home/ubuntu/lms/media/;
    }

    # Forward everything else to Gunicorn
    location / {
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_pass http://unix:/home/ubuntu/lms/lms.sock;
    }
}
```

Enable the site and restart Nginx:

```bash
# Create symlink to enable the site
sudo ln -s /etc/nginx/sites-available/lms /etc/nginx/sites-enabled/

# Remove default site (optional)
sudo rm /etc/nginx/sites-enabled/default

# Test Nginx configuration for errors
sudo nginx -t

# Restart Nginx
sudo systemctl restart nginx
```

---

### Step 10 – Open Firewall / Security Group

Go to **AWS Console → EC2 → Instances → your instance → Security → Security groups → Edit inbound rules**:

| Type | Port Range | Source | Description |
|------|-----------|--------|-------------|
| SSH | 22 | Your IP | SSH access |
| HTTP | 80 | 0.0.0.0/0 | Web traffic |
| HTTPS | 443 | 0.0.0.0/0 | SSL traffic (if using HTTPS) |

> **Remove** any temporary port 8000 rule you added during testing.

Also allow Nginx through the system firewall:

```bash
sudo ufw allow 'Nginx Full'
sudo ufw allow OpenSSH
sudo ufw enable
```

---

### Step 11 – Verify Everything

Open your browser and go to:

```
http://<YOUR_EC2_PUBLIC_IP>
```

You should see the LMS login page with full CSS styling. ✅

**Test checklist:**
- [ ] Login/Register pages load with proper styling
- [ ] Registration with OTP email works
- [ ] Admin dashboard loads after login
- [ ] Course creation & file upload works
- [ ] Static files (CSS) load correctly
- [ ] Media files (thumbnails, PDFs) load correctly

---

## 🔒 Optional: Custom Domain & HTTPS

### Point a Domain to EC2

1. In your domain registrar (GoDaddy, Namecheap, etc.), add an **A record**:
   - **Host:** `@`
   - **Value:** `<YOUR_EC2_PUBLIC_IP>`
2. Update `ALLOWED_HOSTS` in `.env`:
   ```ini
   ALLOWED_HOSTS=your-domain.com,www.your-domain.com,<YOUR_EC2_PUBLIC_IP>
   ```
3. Update `server_name` in `/etc/nginx/sites-available/lms`:
   ```nginx
   server_name your-domain.com www.your-domain.com;
   ```
4. Restart services:
   ```bash
   sudo systemctl restart lms
   sudo systemctl restart nginx
   ```

### Install Free SSL with Let's Encrypt

```bash
# Install Certbot
sudo apt install -y certbot python3-certbot-nginx

# Get & install certificate (auto-configures Nginx)
sudo certbot --nginx -d your-domain.com -d www.your-domain.com

# Enable auto-renewal
sudo systemctl enable certbot.timer
```

After SSL is working, update your `.env`:
```ini
SECURE_SSL_REDIRECT=True
```

And restart the LMS service:
```bash
sudo systemctl restart lms
```

---

## 🔧 Maintenance & Useful Commands

```bash
# SSH into your server
ssh -i your-key.pem ubuntu@<YOUR_EC2_PUBLIC_IP>

# Activate the virtual environment
cd /home/ubuntu/lms && source venv/bin/activate

# Pull latest code changes
git pull origin main

# Install new dependencies (if requirements.txt changed)
pip install -r requirements.txt

# Run new migrations
python manage.py migrate

# Collect updated static files
python manage.py collectstatic --noinput

# Restart the application
sudo systemctl restart lms
sudo systemctl restart nginx

# View application logs
sudo journalctl -u lms -f              # live Gunicorn logs
tail -f /home/ubuntu/lms/gunicorn-error.log  # error log

# View Nginx logs
sudo tail -f /var/log/nginx/access.log
sudo tail -f /var/log/nginx/error.log

# Check service status
sudo systemctl status lms
sudo systemctl status nginx

# Django shell (for debugging)
python manage.py shell

# Create a new superuser
python manage.py createsuperuser
```

---

## ❓ Troubleshooting

### 502 Bad Gateway
```bash
# Check if Gunicorn is running
sudo systemctl status lms

# Check the socket file exists
ls -la /home/ubuntu/lms/lms.sock

# Check Gunicorn logs
sudo journalctl -u lms -n 50

# Restart everything
sudo systemctl restart lms && sudo systemctl restart nginx
```

### Static files not loading (unstyled pages)
```bash
# Re-collect static files
source venv/bin/activate
python manage.py collectstatic --noinput

# Check Nginx static path matches STATIC_ROOT
ls /home/ubuntu/lms/staticfiles/

# Restart Nginx
sudo systemctl restart nginx
```

### Permission errors
```bash
# Fix project directory ownership
sudo chown -R ubuntu:www-data /home/ubuntu/lms

# Fix socket permissions
sudo chmod 755 /home/ubuntu
```

### Email not sending
- Ensure you're using a **Gmail App Password**, not your regular password.
- Verify 2FA is enabled on the Google account.
- Check the `.env` email settings are correct.
- Test from Django shell:
  ```bash
  python manage.py shell
  >>> from django.core.mail import send_mail
  >>> send_mail('Test', 'Body', 'your@email.com', ['test@email.com'])
  ```

### Database errors after code update
```bash
python manage.py migrate
python manage.py migrate --run-syncdb
```

---

## 📁 Project Structure

```
lms/
├── core/                   # Django project settings
│   ├── settings.py         # Configuration (reads from .env)
│   ├── urls.py             # Root URL configuration
│   ├── wsgi.py             # WSGI entry point (for Gunicorn)
│   └── asgi.py             # ASGI entry point
├── accounts/               # User management app
│   ├── models.py           # CustomUser model (email-based auth)
│   ├── views.py            # Register, login, OTP, profile, admin user CRUD
│   └── urls.py             # Account URL routes
├── courses/                # Course management app
│   ├── models.py           # Course, Module, Content, Enrollment, Assignment models
│   ├── views.py            # Course CRUD, enrollment flow, assignment/grading
│   ├── admin.py            # Django admin configuration
│   ├── templatetags/       # Custom template filters
│   └── management/commands/# seed_data command
├── templates/              # HTML templates
│   ├── base.html           # Base layout with sidebar
│   ├── accounts/           # Auth & user management pages
│   ├── courses/            # Course, module, assignment pages
│   └── registration/       # Password reset templates
├── static/css/style.css    # Application styles
├── requirements.txt        # Python dependencies
├── .env.example            # Environment variable template
├── .gitignore              # Git ignore rules
└── manage.py               # Django CLI
```

---

## 📝 Default Credentials

After running `python manage.py seed_data`:

| Role | Email | Password |
|------|-------|----------|
| Admin | `admin@lms.com` | Check seed_data command |
| Teacher | Check seed_data command | Check seed_data command |
| Student | Check seed_data command | Check seed_data command |

> ⚠️ **Change all default passwords immediately in production!**

---

## 📄 License

This project is for educational purposes.
