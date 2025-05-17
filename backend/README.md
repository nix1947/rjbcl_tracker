# Django API Project

This project provides a RESTful API for authentication, user management, banks, and transactions using Django and Django REST Framework.

---

## 🚀 Getting Started (Local Development Setup)

### 1. Clone the Repository

```bash
git clone [<repository_url>](https://github.com/nix1947/statementTracker.git)
cd <project_directory>
```

### 2. Create a Virtual Environment

```bash
python -m venv venv
 For Windows: venv\Scripts\activate # For Linux source venv/bin/activate 
```

### 3. Install Dependencies

```bash
pip install -r requirements.txt
```

### 4. Apply Migrations

```bash
python manage.py migrate
```

### 5. Create Superuser 

```bash
python manage.py createsuperuser
```

### 6. Run the Server

```bash
python manage.py runserver
```

Now open your browser at: `http://127.0.0.1:8000`
Admin endpoint at: `http://127.0.0.1:8000`

---

## 📃 API Endpoints Documentation
**http://localhost:8000/swagger**
**http://localhost:8000/rdoc**

### Authentication

* `POST /api/auth/change-password/` — Change password
* `POST /api/auth/login/` — Login
* `POST /api/auth/password-reset/` — Request password reset
* `POST /api/auth/password-reset-confirm/` — Confirm password reset
* `POST /api/auth/refresh/` — Refresh token

### Banks

* `GET /api/banks/` — List banks
* `POST /api/banks/` — Create bank
* `GET /api/banks/{id}/` — Retrieve bank
* `PUT /api/banks/{id}/` — Update bank
* `PATCH /api/banks/{id}/` — Partial update bank
* `DELETE /api/banks/{id}/` — Delete bank

### Transactions

* `GET /api/transactions/` — List transactions
* `POST /api/transactions/` — Create transaction
* `GET /api/transactions/{id}/` — Retrieve transaction
* `PUT /api/transactions/{id}/` — Update transaction
* `PATCH /api/transactions/{id}/` — Partial update transaction
* `DELETE /api/transactions/{id}/` — Delete transaction
* `POST /api/transactions/{id}/reconcile/` — Reconcile transaction
* `POST /api/transactions/{id}/verify/` — Verify transaction

### Users

* `GET /api/users/` — List users
* `POST /api/users/` — Create user
* `GET /api/users/me/` — Get current user profile
* `GET /api/users/{id}/` — Retrieve user
* `PUT /api/users/{id}/` — Update user
* `PATCH /api/users/{id}/` — Partial update user
* `DELETE /api/users/{id}/` — Delete user

---

## 🔧 API Testing Example

Example using `curl` to create a new user:

```bash
curl -X POST http://127.0.0.1:8000/api/users/ \
-H "Content-Type: application/json" \
-d '{"username": "testuser", "password": "password123"}'
```

---

![image](https://github.com/user-attachments/assets/a443b129-d6e5-472b-9ad8-6ee121c15682)


## 📖 References

* [Django Documentation](https://docs.djangoproject.com/)
* [Django REST Framework](https://www.django-rest-framework.org/)

---

## 📅 License

MIT License — feel free to use and modify!

## Production deployment
```angular2html
python manage.py migrate --settings=rjbcl.production
```
- Run with gunicorn
```angular2html
gunicorn --bind 127.0.0.1:8000 your_project_name.wsgi:application
```
**SystemD with gunicorn**
```angular2html
sudo mkdir -p /run/gunicorn
sudo chown centos:centos /run/gunicorn
sudo vim /etc/systemd/system/gunicorn.service
sudo chcon -t httpd_var_run_t /run/gunicorn
```
```angular2html
[Unit]
Description=Gunicorn Daemon for RJBCL Statement Tracker
After=network.target mariadb.service
Requires=mariadb.service

[Service]
User=centos
Group=nginx
WorkingDirectory=/data/www/statement_tracker.rbs.gov.np/backend
Environment="PATH=/data/www/statement_tracker.rbs.gov.np/backend/venv/bin:/usr/local/bin:/usr/bin:/bin"
Environment="DJANGO_SETTINGS_MODULE=rjbcl.production"

# Runtime Directory Setup
RuntimeDirectory=gunicorn
RuntimeDirectoryMode=0750
PIDFile=/run/gunicorn/gunicorn.pid

# Security (minimal for troubleshooting)
PrivateTmp=true
NoNewPrivileges=yes
ProtectSystem=strict
ReadWritePaths=/run/gunicorn /var/log /data/www/statement_tracker.rbs.gov.np

# Gunicorn Execution
ExecStart=/data/www/statement_tracker.rbs.gov.np/backend/venv/bin/gunicorn \
          --workers 3 \
          --timeout 120 \
          --bind unix:/run/gunicorn/gunicorn.sock \
          --pid /run/gunicorn/gunicorn.pid \
          --access-logfile /var/log/gunicorn/access.log \
          --error-logfile /var/log/gunicorn/error.log \
          --capture-output \
          --log-level info \
          rjbcl.wsgi:application

# Process management
Restart=on-failure
RestartSec=10s
StartLimitIntervalSec=60
StartLimitBurst=5

[Install]
WantedBy=multi-user.target


```

** Run this **
```angular2html
chmod +x /data/www/statement_tracker.rbs.gov.np/backend/venv/bin/gunicorn

sudo systemctl daemon-reexec
sudo systemctl start gunicorn
sudo systemctl enable gunicorn

```

**Nginx configuration**
```angular2html

server {
    listen 80;
    server_name statement.rbs.gov.np;
    return 301 https://$server_name$request_uri;
}

server {
    listen 443 ssl;
    server_name statement.rbs.gov.np;
    
    # SSL Configuration
    ssl_certificate /etc/ssl/certs/star_rbs_gov_np_combined.crt;
    ssl_certificate_key /etc/ssl/private/rbs_private.key;
    ssl_trusted_certificate /etc/ssl/certs/ca-bundle.crt;

    # SSL Optimization
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers 'ECDHE-ECDSA-AES128-GCM-SHA256:ECDHE-RSA-AES128-GCM-SHA256:ECDHE-ECDSA-AES256-GCM-SHA384:ECDHE-RSA-AES256-GCM-SHA384:DHE-RSA-AES128-GCM-SHA256:DHE-RSA-AES256-GCM-SHA384';
    ssl_prefer_server_ciphers on;
    ssl_session_cache shared:SSL:10m;
    ssl_session_timeout 10m;
    ssl_dhparam /etc/nginx/dhparam.pem;

    # Security Headers
    add_header Strict-Transport-Security "max-age=31536000; includeSubDomains" always;
    add_header X-Content-Type-Options nosniff;
    add_header X-Frame-Options "SAMEORIGIN";
    add_header X-XSS-Protection "1; mode=block";
    add_header Referrer-Policy "strict-origin-when-cross-origin";

    # Static files
    location /static/ {
        alias /data/www/statement.rbs.gov.np/backend/staticfiles/;
        expires 365d;
        access_log off;
        gzip on;
        gzip_types text/plain text/css application/json application/javascript;
    }

    # Media files
    location /media/ {
        alias /data/www/statement.rbs.gov.np/backend/media/;
        expires 30d;
        access_log off;
    }

    # Django application
    location / {
        include proxy_params;
        proxy_pass http://unix:/run/gunicorn/gunicorn.sock;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header Host $host;
        proxy_redirect off;
        
        # WebSocket support (if needed)
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
    }

    # Error pages
    error_page 500 502 503 504 /500.html;
    location = /500.html {
        root /data/www/statement.rbs.gov.np/backend/templates/;
    }
}


```

