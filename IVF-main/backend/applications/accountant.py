from flask_restful import Resource
from flask_security import auth_token_required, current_user
from applications.database import db
from applications.models import Invoice, Appointment, AuditLog
from applications.audit_helper import log_action
from flask import request
from datetime import datetime, date, timedelta
from sqlalchemy import func

FLAT_FEE = 5000.00  # Change this one line to update all invoice amounts


# ── Role Guard ────────────────────────────────────────────────────────────────
def accountant_only():
    if current_user.type != 'accountant':
        log_action(
            user_id=current_user.id,
            action=f"Unauthorized accountant access attempt by {current_user.name} ({current_user.type})",
            endpoint=request.path
        )
        db.session.commit()
        return {"message": "Access denied"}, 403
    return None


# ── Billing Queue ─────────────────────────────────────────────────────────────
class BillingQueue(Resource):
    """Pending invoices pushed by doctors — PHI-free, service ID only."""
    @auth_token_required
    def get(self):
        err = accountant_only()
        if err: return err

        invoices = Invoice.query.filter_by(
            status='pending'
        ).order_by(Invoice.date_generated.desc()).all()

        queue = []
        for inv in invoices:
            appt = Appointment.query.get(inv.appointment_id)
            queue.append({
                "invoice_id":     inv.id,
                "service_id":     inv.patient_service_id,
                "service_code":   inv.service_code,
                "amount":         inv.amount,
                "status":         inv.status,
                "payment_source": inv.payment_source or None,
                "date_generated": inv.date_generated.strftime('%Y-%m-%d %H:%M'),
                "visit_date":     appt.date.strftime('%Y-%m-%d') if appt else None,
                "visit_time":     appt.start_time.strftime('%H:%M') if appt else None,
            })

        return {"queue": queue, "total": len(queue)}, 200


# ── Generate Bill ─────────────────────────────────────────────────────────────
class GenerateBill(Resource):
    """Accountant confirms/finalizes the invoice pushed by doctor."""
    @auth_token_required
    def post(self, invoice_id):
        err = accountant_only()
        if err: return err

        invoice = Invoice.query.get(invoice_id)
        if not invoice:
            return {"message": "Invoice not found"}, 404
        if invoice.status == 'paid':
            return {"message": "Invoice already paid"}, 400

        data = request.get_json(force=True, silent=True) or {}
        # Accountant may optionally override the amount
        new_amount = data.get('amount')
        if new_amount is not None:
            try:
                invoice.amount = float(new_amount)
            except (ValueError, TypeError):
                return {"message": "Invalid amount"}, 400

        log_action(
            user_id=current_user.id,
            action=f"Generated bill — invoice #{invoice_id} (SVC: {invoice.patient_service_id}) {invoice.service_code} ₹{invoice.amount}",
            endpoint=f'/api/v1/accountant/invoice/{invoice_id}/generate'
        )
        db.session.commit()

        return {
            "message":      "Bill generated successfully",
            "invoice_id":   invoice_id,
            "service_code": invoice.service_code,
            "amount":       invoice.amount,
            "status":       invoice.status
        }, 200


# ── Invoice Ledger ────────────────────────────────────────────────────────────
class InvoiceLedger(Resource):
    """All invoices — paid and pending — no PHI."""
    @auth_token_required
    def get(self):
        err = accountant_only()
        if err: return err

        # Optional status filter: ?status=paid or ?status=pending
        status_filter = request.args.get('status')

        query = Invoice.query.order_by(Invoice.date_generated.desc())
        if status_filter in ('paid', 'pending'):
            query = query.filter_by(status=status_filter)

        invoices = query.all()

        data = []
        for inv in invoices:
            appt = Appointment.query.get(inv.appointment_id)
            data.append({
                "invoice_id":     inv.id,
                "service_id":     inv.patient_service_id,
                "service_code":   inv.service_code,
                "amount":         inv.amount,
                "status":         inv.status,
                "payment_source": inv.payment_source,
                "date_generated": inv.date_generated.strftime('%Y-%m-%d'),
                "date_paid":      inv.date_paid.strftime('%Y-%m-%d') if inv.date_paid else None,
                "visit_date":     appt.date.strftime('%Y-%m-%d') if appt else None,
            })

        all_invoices   = Invoice.query.all()
        total_revenue  = sum(i.amount for i in all_invoices if i.status == 'paid')
        total_pending  = sum(i.amount for i in all_invoices if i.status == 'pending')

        return {
            "invoices":      data,
            "total_revenue": total_revenue,
            "total_pending": total_pending,
            "total_billed":  total_revenue + total_pending
        }, 200


# ── Daily Report ──────────────────────────────────────────────────────────────
class DailyReport(Resource):
    @auth_token_required
    def get(self):
        err = accountant_only()
        if err: return err

        today     = date.today()
        days_data = []

        for i in range(29, -1, -1):
            day          = today - timedelta(days=i)
            day_invoices = Invoice.query.filter(
                func.date(Invoice.date_generated) == day
            ).all()

            days_data.append({
                "date":    day.strftime('%Y-%m-%d'),
                "label":   day.strftime('%b %d'),
                "revenue": sum(inv.amount for inv in day_invoices if inv.status == 'paid'),
                "pending": sum(inv.amount for inv in day_invoices if inv.status == 'pending'),
                "total":   sum(inv.amount for inv in day_invoices),
                "count":   len(day_invoices)
            })

        return {"daily": days_data}, 200


# ── Weekly Report ─────────────────────────────────────────────────────────────
class WeeklyReport(Resource):
    @auth_token_required
    def get(self):
        err = accountant_only()
        if err: return err

        today      = date.today()
        weeks_data = []

        for i in range(11, -1, -1):
            week_start    = today - timedelta(weeks=i, days=today.weekday())
            week_end      = week_start + timedelta(days=6)
            week_invoices = Invoice.query.filter(
                func.date(Invoice.date_generated) >= week_start,
                func.date(Invoice.date_generated) <= week_end
            ).all()

            weeks_data.append({
                "week":    f"W{12 - i}",
                "label":   week_start.strftime('%b %d'),
                "revenue": sum(inv.amount for inv in week_invoices if inv.status == 'paid'),
                "pending": sum(inv.amount for inv in week_invoices if inv.status == 'pending'),
                "total":   sum(inv.amount for inv in week_invoices),
                "count":   len(week_invoices)
            })

        return {"weekly": weeks_data}, 200


# ── Monthly Report ────────────────────────────────────────────────────────────
class MonthlyReport(Resource):
    @auth_token_required
    def get(self):
        err = accountant_only()
        if err: return err

        today       = date.today()
        months_data = []

        for i in range(11, -1, -1):
            month = today.month - i
            year  = today.year
            while month <= 0:
                month += 12
                year  -= 1

            month_invoices = Invoice.query.filter(
                func.strftime('%Y', Invoice.date_generated) == str(year),
                func.strftime('%m', Invoice.date_generated) == f'{month:02d}'
            ).all()

            months_data.append({
                "month":   f"{year}-{month:02d}",
                "label":   datetime(year, month, 1).strftime('%b %Y'),
                "revenue": sum(inv.amount for inv in month_invoices if inv.status == 'paid'),
                "pending": sum(inv.amount for inv in month_invoices if inv.status == 'pending'),
                "total":   sum(inv.amount for inv in month_invoices),
                "count":   len(month_invoices)
            })

        return {"monthly": months_data}, 200



# ── Chart Data ────────────────────────────────────────────────────────────────
class ChartData(Resource):
    """
    Returns all chart data for the Reports tab in one request.
    GET /api/v1/accountant/charts/<period>   period = daily | weekly | monthly
    """
    @auth_token_required
    def get(self, period):
        err = accountant_only()
        if err: return err

        if period not in ('daily', 'weekly', 'monthly'):
            return {"message": "period must be daily, weekly, or monthly"}, 400

        today = date.today()

        # ── 1. Build time-series buckets (bar + line charts) ──────────────────
        buckets = []

        if period == 'daily':
            for i in range(29, -1, -1):
                day  = today - timedelta(days=i)
                invs = Invoice.query.filter(func.date(Invoice.date_generated) == day).all()
                buckets.append({
                    "label":   day.strftime('%b %d'),
                    "revenue": sum(inv.amount for inv in invs if inv.status == 'paid'),
                    "pending": sum(inv.amount for inv in invs if inv.status == 'pending'),
                    "total":   sum(inv.amount for inv in invs),
                    "count":   len(invs),
                })

        elif period == 'weekly':
            for i in range(11, -1, -1):
                w_start = today - timedelta(weeks=i, days=today.weekday())
                w_end   = w_start + timedelta(days=6)
                invs    = Invoice.query.filter(
                    func.date(Invoice.date_generated) >= w_start,
                    func.date(Invoice.date_generated) <= w_end
                ).all()
                buckets.append({
                    "label":   w_start.strftime('%b %d'),
                    "revenue": sum(inv.amount for inv in invs if inv.status == 'paid'),
                    "pending": sum(inv.amount for inv in invs if inv.status == 'pending'),
                    "total":   sum(inv.amount for inv in invs),
                    "count":   len(invs),
                })

        elif period == 'monthly':
            for i in range(11, -1, -1):
                month = today.month - i
                year  = today.year
                while month <= 0:
                    month += 12
                    year  -= 1
                invs = Invoice.query.filter(
                    func.strftime('%Y', Invoice.date_generated) == str(year),
                    func.strftime('%m', Invoice.date_generated) == f'{month:02d}'
                ).all()
                buckets.append({
                    "label":   datetime(year, month, 1).strftime('%b %Y'),
                    "revenue": sum(inv.amount for inv in invs if inv.status == 'paid'),
                    "pending": sum(inv.amount for inv in invs if inv.status == 'pending'),
                    "total":   sum(inv.amount for inv in invs),
                    "count":   len(invs),
                })

        # ── 2. Donut — period-scoped paid vs pending totals ───────────────────
        period_revenue = sum(b["revenue"] for b in buckets)
        period_pending = sum(b["pending"] for b in buckets)

        donut = {
            "labels": ["Collected", "Pending"],
            "values": [period_revenue, period_pending],
        }

        # ── 3. Service code breakdown — all-time horizontal bar ───────────────
        all_invs  = Invoice.query.all()
        code_map  = {}
        for inv in all_invs:
            c = inv.service_code or "Unknown"
            if c not in code_map:
                code_map[c] = {"revenue": 0.0, "pending": 0.0}
            if inv.status == 'paid':
                code_map[c]["revenue"] += inv.amount
            elif inv.status == 'pending':
                code_map[c]["pending"] += inv.amount

        sorted_codes = sorted(
            code_map.items(),
            key=lambda x: x[1]["revenue"] + x[1]["pending"],
            reverse=True
        )[:8]

        service_codes = {
            "labels":  [c for c, _ in sorted_codes],
            "revenue": [v["revenue"] for _, v in sorted_codes],
            "pending": [v["pending"] for _, v in sorted_codes],
        }

        # ── 4. KPI summary ────────────────────────────────────────────────────
        period_total = period_revenue + period_pending
        kpi = {
            "period_revenue":    period_revenue,
            "period_pending":    period_pending,
            "period_count":      sum(b["count"] for b in buckets),
            "collection_rate":   round((period_revenue / period_total * 100), 1) if period_total else 0,
        }

        return {
            "period":        period,
            "kpi":           kpi,
            "timeseries":    buckets,   # → bar chart + line chart
            "donut":         donut,     # → donut chart
            "service_codes": service_codes,  # → horizontal bar
        }, 200
        
# ── Doctor-Wise Analysis ───────────────────────────────────────────────────────
class DoctorAnalysis(Resource):
    """
    Returns per-doctor revenue breakdown for the Reports tab.
    GET /api/v1/accountant/charts/doctors
    Optional query param: ?period=daily|weekly|monthly  (defaults to all-time)
    """
    @auth_token_required
    def get(self):
        err = accountant_only()
        if err: return err

        period = request.args.get('period', 'all')

        # ── Date range filter ─────────────────────────────────────────────────
        today = date.today()
        date_from = None

        if period == 'daily':
            date_from = today - timedelta(days=30)
        elif period == 'weekly':
            date_from = today - timedelta(weeks=12)
        elif period == 'monthly':
            date_from = today - timedelta(days=365)
        # 'all' → no date filter

        # ── Pull all doctors ──────────────────────────────────────────────────
        from applications.models import Doctor
        doctors = Doctor.query.all()

        doctor_rows = []

        for doc in doctors:
            # Get all appointments for this doctor
            appt_query = Appointment.query.filter_by(doctor_id=doc.id)
            if date_from:
                appt_query = appt_query.filter(Appointment.date >= date_from)
            appt_ids = [a.id for a in appt_query.all()]

            if not appt_ids:
                continue  # skip doctors with no appointments in range

            # Get invoices for those appointments
            inv_query = Invoice.query.filter(Invoice.appointment_id.in_(appt_ids))
            invoices  = inv_query.all()

            if not invoices:
                continue  # skip doctors with no invoices

            revenue  = sum(i.amount for i in invoices if i.status == 'paid')
            pending  = sum(i.amount for i in invoices if i.status == 'pending')
            total    = revenue + pending
            col_rate = round((revenue / total * 100), 1) if total else 0

            doctor_rows.append({
                "doctor_id":       doc.id,
                "doctor_name":     doc.name,
                "specialization":  doc.specialization or "General",
                "revenue":         revenue,
                "pending":         pending,
                "total_billed":    total,
                "collection_rate": col_rate,
                "session_count":   len(invoices),
            })

        # Sort by total billed descending
        doctor_rows.sort(key=lambda x: x["total_billed"], reverse=True)

        return {
            "period":  period,
            "doctors": doctor_rows,
        }, 200