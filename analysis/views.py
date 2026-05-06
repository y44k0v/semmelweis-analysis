# analysis/views.py

from django.views.generic import (
    TemplateView, ListView,
    CreateView, UpdateView, DeleteView,
)
from django.views import View
from django.shortcuts import render, redirect
from django.urls import reverse_lazy
from django.http import HttpResponse

from .models import YearlyRecord, MonthlyRecord
from .forms import CSVUploadForm, YearlyRecordForm, MonthlyRecordForm
from . import services


# ─────────────────────────────────────────────
# UPLOAD
# ─────────────────────────────────────────────

class UploadCSVView(View):
    template_name = "analysis/upload.html"

    def get(self, request):
        return render(request, self.template_name, {"form": CSVUploadForm()})

    def post(self, request):
        form = CSVUploadForm(request.POST, request.FILES)
        if not form.is_valid():
            return render(request, self.template_name, {"form": form})
        if form.cleaned_data.get("yearly_csv"):
            services.import_yearly_csv(form.cleaned_data["yearly_csv"])
        if form.cleaned_data.get("monthly_csv"):
            services.import_monthly_csv(form.cleaned_data["monthly_csv"])
        return redirect("analysis:dashboard")


# ─────────────────────────────────────────────
# DASHBOARD (homepage)
# ─────────────────────────────────────────────

class DashboardView(TemplateView):
    template_name = "analysis/dashboard.html"

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["yearly_count"]      = YearlyRecord.objects.count()
        ctx["monthly_count"]     = MonthlyRecord.objects.count()
        ctx["has_data"]          = ctx["yearly_count"] > 0 or ctx["monthly_count"] > 0
        ctx["yearly_chart_data"] = services.yearly_chart_data()
        ctx["monthly_chart_data"]= services.monthly_chart_data()
        return ctx


# ─────────────────────────────────────────────
# YEARLY — CRUD
# ─────────────────────────────────────────────

class YearlyListView(ListView):
    model               = YearlyRecord
    template_name       = "analysis/yearly_list.html"
    context_object_name = "records"

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["clinic1"]        = YearlyRecord.objects.filter(clinic="clinic 1")
        ctx["clinic2"]        = YearlyRecord.objects.filter(clinic="clinic 2")
        ctx["chart_data"]     = services.yearly_chart_data()
        return ctx


class YearlyCreateView(CreateView):
    model         = YearlyRecord
    form_class    = YearlyRecordForm
    template_name = "analysis/yearly_form.html"
    success_url   = reverse_lazy("analysis:yearly-list")

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["title"] = "Add Yearly Record"
        ctx["cancel_url"] = reverse_lazy("analysis:yearly-list")
        return ctx


class YearlyUpdateView(UpdateView):
    model         = YearlyRecord
    form_class    = YearlyRecordForm
    template_name = "analysis/yearly_form.html"
    success_url   = reverse_lazy("analysis:yearly-list")

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["title"] = f"Edit Yearly Record — {self.object}"
        ctx["cancel_url"] = reverse_lazy("analysis:yearly-list")
        return ctx


class YearlyDeleteView(DeleteView):
    model         = YearlyRecord
    template_name = "analysis/confirm_delete.html"
    success_url   = reverse_lazy("analysis:yearly-list")

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["cancel_url"] = reverse_lazy("analysis:yearly-list")
        return ctx


# ─────────────────────────────────────────────
# MONTHLY — CRUD
# ─────────────────────────────────────────────

class MonthlyListView(ListView):
    model               = MonthlyRecord
    template_name       = "analysis/monthly_list.html"
    context_object_name = "records"

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["chart_data"]         = services.monthly_chart_data()
        ctx["handwashing_start"]  = MonthlyRecord.HANDWASHING_START
        return ctx


class MonthlyCreateView(CreateView):
    model         = MonthlyRecord
    form_class    = MonthlyRecordForm
    template_name = "analysis/monthly_form.html"
    success_url   = reverse_lazy("analysis:monthly-list")

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["title"] = "Add Monthly Record"
        ctx["cancel_url"] = reverse_lazy("analysis:monthly-list")
        return ctx


class MonthlyUpdateView(UpdateView):
    model         = MonthlyRecord
    form_class    = MonthlyRecordForm
    template_name = "analysis/monthly_form.html"
    success_url   = reverse_lazy("analysis:monthly-list")

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["title"] = f"Edit Monthly Record — {self.object}"
        ctx["cancel_url"] = reverse_lazy("analysis:monthly-list")
        return ctx


class MonthlyDeleteView(DeleteView):
    model         = MonthlyRecord
    template_name = "analysis/confirm_delete.html"
    success_url   = reverse_lazy("analysis:monthly-list")

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["cancel_url"] = reverse_lazy("analysis:monthly-list")
        return ctx


# ─────────────────────────────────────────────
# ANALYSIS
# ─────────────────────────────────────────────

class AnalysisView(TemplateView):
    template_name = "analysis/analysis_results.html"

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx.update(services.run_full_analysis())
        return ctx


# ─────────────────────────────────────────────
# DOWNLOADS
# ─────────────────────────────────────────────

class DownloadYearlyCSVView(View):
    def get(self, request):
        df = services.yearly_to_dataframe()
        resp = HttpResponse(content_type="text/csv")
        resp["Content-Disposition"] = 'attachment; filename="yearly_deaths.csv"'
        df.to_csv(resp, index=False)
        return resp


class DownloadMonthlyCSVView(View):
    def get(self, request):
        df = services.monthly_to_dataframe()
        resp = HttpResponse(content_type="text/csv")
        resp["Content-Disposition"] = 'attachment; filename="monthly_deaths.csv"'
        df.to_csv(resp, index=False)
        return resp


class DownloadClinicChartView(View):
    def get(self, request):
        png = services.clinic_comparison_chart_png()
        resp = HttpResponse(content_type="image/png")
        resp["Content-Disposition"] = 'attachment; filename="clinic_comparison.png"'
        resp.write(png)
        return resp


class DownloadMonthlyChartView(View):
    def get(self, request):
        png = services.monthly_proportion_chart_png()
        resp = HttpResponse(content_type="image/png")
        resp["Content-Disposition"] = 'attachment; filename="monthly_proportion.png"'
        resp.write(png)
        return resp


class DownloadBootstrapChartView(View):
    def get(self, request):
        png = services.bootstrap_histogram_png()
        resp = HttpResponse(content_type="image/png")
        resp["Content-Disposition"] = 'attachment; filename="bootstrap_ci.png"'
        resp.write(png)
        return resp