import os
import sys
import shutil
import re
import django
from django.conf import settings
from django.test import RequestFactory
from django.template.loader import render_to_string

# 1. Setup Django Environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'semmelweis_project.settings')
django.setup()

from analysis import services
from analysis.models import YearlyRecord, MonthlyRecord

# 2. Configuration & Paths
BASE_DIR = settings.BASE_DIR
BUILD_DIR = os.path.join(BASE_DIR, 'docs') # 'docs' is the standard folder for GitHub pages
STATIC_BUILD_DIR = os.path.join(BUILD_DIR, 'static')
MEDIA_BUILD_DIR = os.path.join(BUILD_DIR, 'media')
DOWNLOADS_DIR = os.path.join(BUILD_DIR, 'downloads')

def prepare_build_directory():
    print("🧹 Cleaning old build directory...")
    if os.path.exists(BUILD_DIR):
        shutil.rmtree(BUILD_DIR)
    
    os.makedirs(BUILD_DIR)
    os.makedirs(DOWNLOADS_DIR)

    # Copy static files
    print("📁 Copying static and media files...")
    local_static = os.path.join(BASE_DIR, 'static')
    if os.path.exists(local_static):
        shutil.copytree(local_static, STATIC_BUILD_DIR)
        
    # Copy media files (for the semmelweis.jpeg image)
    local_media = os.path.join(BASE_DIR, 'media')
    if os.path.exists(local_media):
        shutil.copytree(local_media, MEDIA_BUILD_DIR)

def process_html(html_content):
    """
    Replaces dynamic Django URLs with static HTML links and disabled CRUD buttons.
    """
    # 1. Map Django routing paths to static HTML files
    url_map = {
        'href="/"': 'href="index.html"',
        'href="/yearly/"': 'href="yearly.html"',
        'href="/monthly/"': 'href="monthly.html"',
        'href="/analysis/"': 'href="analysis.html"',
        
        # 2. Map Download endpoints to physically generated files
        'href="/download/yearly-csv/"': 'href="downloads/yearly_deaths.csv" download',
        'href="/download/monthly-csv/"': 'href="downloads/monthly_deaths.csv" download',
        'href="/download/clinic-chart/"': 'href="downloads/clinic_comparison.png" download',
        'href="/download/monthly-chart/"': 'href="downloads/monthly_proportion.png" download',
        'href="/download/bootstrap-chart/"': 'href="downloads/bootstrap_ci.png" download',
        
        # 3. Make asset paths relative for GitHub Pages
        'src="/static/': 'src="./static/',
        'href="/static/': 'href="./static/',
        'src="/media/': 'src="./media/',
    }
    
    for old, new in url_map.items():
        html_content = html_content.replace(old, new)
        
    # 4. Disable Upload and CRUD Links (Edit, Delete, Add) for static version
    html_content = html_content.replace('href="/upload/"', 'href="#" onclick="alert(\'Upload disabled in static version.\'); return false;"')
    
    # Regex to catch dynamic CRUD URLs like /yearly/add/ or /monthly/12/edit/
    crud_pattern = r'href="/(?:yearly|monthly)/(\d+|add|delete)/[^"]*"'
    disabled_js = r'href="#" onclick="alert(\'CRUD operations are disabled in this static export.\'); return false;"'
    html_content = re.sub(crud_pattern, disabled_js, html_content)
    
    return html_content

def generate_downloads():
    print("⬇ Generating downloadable CSVs and PNGs...")
    
    # Yearly CSV
    df_yearly = services.yearly_to_dataframe()
    if not df_yearly.empty:
        df_yearly.to_csv(os.path.join(DOWNLOADS_DIR, 'yearly_deaths.csv'), index=False)
        
    # Monthly CSV
    df_monthly = services.monthly_to_dataframe()
    if not df_monthly.empty:
        df_monthly.to_csv(os.path.join(DOWNLOADS_DIR, 'monthly_deaths.csv'), index=False)
        
    # Charts (PNGs)
    try:
        with open(os.path.join(DOWNLOADS_DIR, 'clinic_comparison.png'), 'wb') as f:
            f.write(services.clinic_comparison_chart_png())
        with open(os.path.join(DOWNLOADS_DIR, 'monthly_proportion.png'), 'wb') as f:
            f.write(services.monthly_proportion_chart_png())
        with open(os.path.join(DOWNLOADS_DIR, 'bootstrap_ci.png'), 'wb') as f:
            f.write(services.bootstrap_histogram_png())
    except Exception as e:
        print(f"⚠️ Warning: Could not generate some PNGs. Data might be missing. Error: {e}")

def build_site():
    prepare_build_directory()
    generate_downloads()
    
    request = RequestFactory().get('/')
    print("🌐 Rendering static HTML pages...")

    # --- 1. Dashboard (index.html) ---
    ctx_dash = {
        "yearly_count": YearlyRecord.objects.count(),
        "monthly_count": MonthlyRecord.objects.count(),
        "has_data": YearlyRecord.objects.exists() or MonthlyRecord.objects.exists(),
        "yearly_chart_data": services.yearly_chart_data(),
        "monthly_chart_data": services.monthly_chart_data(),
    }
    dash_html = render_to_string('analysis/dashboard.html', ctx_dash, request=request)
    with open(os.path.join(BUILD_DIR, 'index.html'), 'w', encoding='utf-8') as f:
        f.write(process_html(dash_html))

    # --- 2. Yearly Data (yearly.html) ---
    ctx_yearly = {
        "records": YearlyRecord.objects.all(),
        "clinic1": YearlyRecord.objects.filter(clinic="clinic 1"),
        "clinic2": YearlyRecord.objects.filter(clinic="clinic 2"),
        "chart_data": services.yearly_chart_data(),
    }
    yearly_html = render_to_string('analysis/yearly_list.html', ctx_yearly, request=request)
    with open(os.path.join(BUILD_DIR, 'yearly.html'), 'w', encoding='utf-8') as f:
        f.write(process_html(yearly_html))

    # --- 3. Monthly Data (monthly.html) ---
    ctx_monthly = {
        "records": MonthlyRecord.objects.all(),
        "chart_data": services.monthly_chart_data(),
        "handwashing_start": MonthlyRecord.HANDWASHING_START,
    }
    monthly_html = render_to_string('analysis/monthly_list.html', ctx_monthly, request=request)
    with open(os.path.join(BUILD_DIR, 'monthly.html'), 'w', encoding='utf-8') as f:
        f.write(process_html(monthly_html))

    # --- 4. Analysis Results (analysis.html) ---
    ctx_analysis = services.run_full_analysis()
    analysis_html = render_to_string('analysis/analysis_results.html', ctx_analysis, request=request)
    with open(os.path.join(BUILD_DIR, 'analysis.html'), 'w', encoding='utf-8') as f:
        f.write(process_html(analysis_html))
        
    print(f"\n✅ Static site successfully built in: {BUILD_DIR}")
    print("🚀 You can now push this folder to GitHub and enable GitHub Pages for the '/docs' directory.")

if __name__ == '__main__':
    build_site()