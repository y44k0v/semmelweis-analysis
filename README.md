# Semmelweis Handwashing Analysis - Django App

## Python for Web Develpment Feb-26

Demo for file uploading and static site generation.

### 0. Source & Static Rendering

[Kaggel](https://www.kaggle.com/code/arijit75/dr-semmelweis-and-the-discovery-of-handwashing) and folder `ORIGINAL`.

[Static Website - No Django](https://y44k0v.github.io/semmelweis-analysis/)

### 1. Project Structure

```BASH

semmelweis_project/
├── README.md
├── analysis
│   ├── __init__.py
│   ├── admin.py
│   ├── apps.py
│   ├── forms.py
│   ├── migrations
│   │   └──  __init__.py
│   ├── models.py
│   ├── services.py
│   ├── tests.py
│   ├── urls.py
│   └── views.py
├── docs                            # GitHub pages
│   ├── analysis.html
│   ├── downloads
│   │   ├── bootstrap_ci.png
│   │   ├── clinic_comparison.png
│   │   ├── monthly_deaths.csv
│   │   ├── monthly_proportion.png
│   │   └── yearly_deaths.csv
│   ├── index.html
│   ├── media
│   │   └── uploads
│   │       └── semmelweis.jpeg
│   ├── monthly.html
│   ├── static
│   │   └── js
│   │       └── charts.js
│   └── yearly.html
├── export_static.py
├── manage.py
├── media
│   └── uploads
│       └── semmelweis.jpeg
├── requirements.txt
├── semmelweis_project
│   ├── __init__.py
│   ├── asgi.py
│   ├── settings.py
│   ├── urls.py
│   └── wsgi.py
├── static
│   └── js
│       └── charts.js
└── templates
    ├── analysis
    │   ├── _yearly_table.html
    │   ├── analysis_results.html
    │   ├── confirm_delete.html
    │   ├── dashboard.html
    │   ├── monthly_detail.html
    │   ├── monthly_form.html
    │   ├── monthly_list.html
    │   ├── upload.html
    │   ├── yearly_detail.html
    │   ├── yearly_form.html
    │   └── yearly_list.html
    └── base.html

```

---

### 2. Setup & Installation

Clone and/or Fork/Clone

```Python
Django>=4.2,<5.0
pandas>=2.0
matplotlib>=3.7
numpy>=1.24
scipy>=1.10
```

```bash
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
 
django-admin startproject semmelweis_project .
python manage.py startapp analysis
```

---
