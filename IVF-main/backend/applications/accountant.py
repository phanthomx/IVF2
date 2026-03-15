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