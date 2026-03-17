# applications/patient_api.py
from flask_restful import Resource
from flask_security import auth_token_required, current_user
from applications.database import db
from applications.models import Patient, Doctor, Appointment, Prescription, Invoice, Availability
from applications.audit_helper import log_action
from flask import request
from datetime import datetime, date, timedelta
from zoneinfo import ZoneInfo
from sqlalchemy import and_

IST = ZoneInfo("Asia/Kolkata")

IVF_STAGES = [
    'Onboarding',
    'Baseline Assessment',
    'Stimulation Protocol',
    'Mid-Cycle Monitoring',
    'Trigger Administration',
    'Retrieval Procedure',
    'Transfer Procedure'
]


# ── Role Guard ────────────────────────────────────────────────────────────────
def patient_only():
    if current_user.type != 'patient':
        log_action(
            user_id=current_user.id,
            action=f"Unauthorized patient access attempt by {current_user.name} ({current_user.type})",
            endpoint=request.path
        )
        db.session.commit()
        return {"message": "Access denied"}, 403
    return None


# ── Helpers ───────────────────────────────────────────────────────────────────
def get_available_slots(doctor_id, target_date):
    target      = datetime.strptime(target_date, '%Y-%m-%d').date()
    day_of_week = target.weekday()
    is_today    = (target == datetime.now(IST).date())
    now         = datetime.now(IST).replace(tzinfo=None)

    availability = Availability.query.filter_by(
        doctor_id=doctor_id,
        day_of_week=day_of_week
    ).first()

    if not availability:
        return []

    slots    = []
    current  = datetime.combine(target, availability.start_time)
    end      = datetime.combine(target, availability.end_time)
    duration = timedelta(minutes=availability.slot_duration_minutes)

    while current + duration <= end:
        slot_end = current + duration

        if is_today and current <= now:
            current += duration
            continue

        conflict = Appointment.query.filter(and_(
            Appointment.doctor_id  == doctor_id,
            Appointment.date       == target,
            Appointment.start_time == current.time(),
            Appointment.status     != 'cancelled'
        )).first()

        slots.append({
            "start_time": current.strftime('%H:%M'),
            "end_time":   slot_end.strftime('%H:%M'),
            "available":  conflict is None
        })
        current += duration

    return slots


# ── Resources ──────────────────────────────────────────────────────────────────

class PatientProfile(Resource):
    @auth_token_required
    def get(self):
        err = patient_only()
        if err: return err

        patient = Patient.query.get(current_user.id)
        if not patient:
            return {"message": "Patient not found"}, 404

        today    = datetime.now(IST).date()
        upcoming = Appointment.query.filter(
            Appointment.patient_id == current_user.id,
            Appointment.date       >= today,
            Appointment.status.in_(['waiting', 'in-session'])
        ).order_by(Appointment.date, Appointment.start_time).limit(3).all()

        now_naive = datetime.now(IST).replace(tzinfo=None)

        upcoming_data = []
        for a in upcoming:
            appt_datetime = datetime.combine(a.date, a.start_time)
            upcoming_data.append({
                "appointment_id": a.id,
                "date":           a.date.strftime('%Y-%m-%d'),
                "start_time":     a.start_time.strftime('%H:%M'),
                "end_time":       a.end_time.strftime('%H:%M'),
                "doctor_name":    a.doctor.name,
                "specialization": a.doctor.specialization,
                "status":         a.status,
                "stage":          a.stage_at_visit,
                "can_cancel":     a.status == 'waiting' and appt_datetime > now_naive
            })

        current_idx = IVF_STAGES.index(patient.current_cycle_stage) \
            if patient.current_cycle_stage in IVF_STAGES else 0

        return {
            "profile": {
                "id":                  patient.id,
                "name":                patient.name,
                "email":               patient.email,
                "service_id":          patient.service_id,
                "contact_info":        patient.contact_info,
                "age":                 patient.age,
                "height_cm":           patient.height_cm,
                "weight_kg":           patient.weight_kg,
                "blood_type":          patient.blood_type,
                "current_cycle_stage": patient.current_cycle_stage,
                "stage_index":         current_idx,
                "total_stages":        len(IVF_STAGES),
                "stages":              IVF_STAGES,
            },
            "upcoming": upcoming_data
        }, 200


class PatientHistory(Resource):
    @auth_token_required
    def get(self):
        err = patient_only()
        if err: return err

        appointments = Appointment.query.filter_by(
            patient_id=current_user.id
        ).order_by(Appointment.date.desc()).all()

        history = []
        for appt in appointments:
            prescription = appt.prescription
            history.append({
                "appointment_id":   appt.id,
                "date":             appt.date.strftime('%Y-%m-%d'),
                "start_time":       appt.start_time.strftime('%H:%M'),
                "doctor_name":      appt.doctor.name,
                "specialization":   appt.doctor.specialization,
                "status":           appt.status,
                "stage":            appt.stage_at_visit,
                "has_prescription": prescription is not None and prescription.is_finalized,
                "prescription_id":  prescription.id if prescription else None,
            })

        return {"history": history}, 200


class PatientInvoices(Resource):
    @auth_token_required
    def get(self):
        err = patient_only()
        if err: return err

        patient = Patient.query.get(current_user.id)
        if not patient:
            return {"message": "Patient not found"}, 404

        invoices = Invoice.query.filter_by(
            patient_service_id=patient.service_id
        ).order_by(Invoice.date_generated.desc()).all()

        pending_total = sum(i.amount for i in invoices if i.status == 'pending')
        paid_total    = sum(i.amount for i in invoices if i.status == 'paid')

        invoice_data = []
        for inv in invoices:
            appt = Appointment.query.get(inv.appointment_id)
            invoice_data.append({
                "invoice_id":     inv.id,
                "service_code":   inv.service_code,
                "amount":         inv.amount,
                "status":         inv.status,
                "payment_source": inv.payment_source,
                "date_generated": inv.date_generated.strftime('%Y-%m-%d'),
                "date_paid":      inv.date_paid.strftime('%Y-%m-%d') if inv.date_paid else None,
                "visit_date":     appt.date.strftime('%Y-%m-%d') if appt else None,
            })

        return {
            "invoices":      invoice_data,
            "pending_total": pending_total,
            "paid_total":    paid_total,
            "total_billed":  pending_total + paid_total
        }, 200


class PatientDoctorList(Resource):
    @auth_token_required
    def get(self):
        err = patient_only()
        if err: return err

        doctors = Doctor.query.filter_by(active=True).all()
        return {"doctors": [{
            "id":             d.id,
            "name":           d.name,
            "specialization": d.specialization,
            "available_days": sorted(list(set(
                a.day_of_week for a in d.availabilities
            )))
        } for d in doctors]}, 200


class PatientAvailableSlots(Resource):
    @auth_token_required
    def get(self, doctor_id, target_date):
        err = patient_only()
        if err: return err

        today  = datetime.now(IST).date()
        target = datetime.strptime(target_date, '%Y-%m-%d').date()

        if target < today:
            return {"message": "Cannot book past dates"}, 400
        if (target - today).days > 7:
            return {"message": "Bookings only allowed up to 7 days in advance"}, 400

        slots = get_available_slots(doctor_id, target_date)
        return {"slots": slots, "date": target_date, "doctor_id": doctor_id}, 200


class PatientBookAppointment(Resource):
    @auth_token_required
    def post(self):
        err = patient_only()
        if err: return err

        data = request.get_json(force=True, silent=True) or {}

        doctor_id = data.get('doctor_id')
        date_str  = data.get('date')
        start_str = data.get('start_time')

        if not all([doctor_id, date_str, start_str]):
            return {"message": "doctor_id, date and start_time are required"}, 400

        doctor = Doctor.query.get(doctor_id)
        if not doctor:
            return {"message": "Doctor not found"}, 404

        patient     = Patient.query.get(current_user.id)
        target_date = datetime.strptime(date_str, '%Y-%m-%d').date()
        start_time  = datetime.strptime(start_str, '%H:%M').time()
        today       = datetime.now(IST).date()
        now_naive   = datetime.now(IST).replace(tzinfo=None)

        if target_date < today:
            return {"message": "Cannot book past dates"}, 400

        if target_date == today and start_time <= now_naive.time():
            return {"message": "Cannot book a slot that has already passed"}, 400

        if (target_date - today).days > 7:
            return {"message": "Bookings only allowed up to 7 days in advance"}, 400

        day_of_week  = target_date.weekday()
        availability = Availability.query.filter_by(
            doctor_id=doctor_id,
            day_of_week=day_of_week
        ).first()

        if not availability:
            return {"message": "Doctor has no availability on this day"}, 400

        duration = timedelta(minutes=availability.slot_duration_minutes)
        end_time = (datetime.combine(target_date, start_time) + duration).time()

        conflict = Appointment.query.filter(and_(
            Appointment.doctor_id  == doctor_id,
            Appointment.date       == target_date,
            Appointment.start_time == start_time,
            Appointment.status     != 'cancelled'
        )).first()

        if conflict:
            return {"message": "This slot is already booked by another patient"}, 409

        appointment = Appointment(
            patient_id=current_user.id,
            doctor_id=doctor_id,
            date=target_date,
            start_time=start_time,
            end_time=end_time,
            status='waiting',
            is_walkin=False,
            stage_at_visit=patient.current_cycle_stage
        )

        db.session.add(appointment)
        db.session.flush()

        log_action(
            user_id=current_user.id,
            action=f"Patient {patient.name} ({patient.service_id}) self-booked with Dr. {doctor.name} on {date_str} at {start_str}",
            endpoint='/api/v1/patient/book-appointment'
        )
        db.session.commit()

        # Send confirmation email
        try:
            from flask import current_app
            send_booking_confirmation(current_app._get_current_object(), patient, doctor, appointment)
        except Exception as e:
            current_app.logger.error(f"[Booking] Confirmation email failed for {patient.email}: {e}")

        return {
            "message":        "Appointment booked successfully",
            "appointment_id": appointment.id
        }, 201


class PatientCancelAppointment(Resource):
    @auth_token_required
    def patch(self, appointment_id):
        err = patient_only()
        if err: return err

        appt = Appointment.query.get(appointment_id)
        if not appt:
            return {"message": "Appointment not found"}, 404

        if appt.patient_id != current_user.id:
            return {"message": "Access denied — not your appointment"}, 403

        if appt.status != 'waiting':
            return {"message": f"Cannot cancel — appointment is '{appt.status}'"}, 400

        now_naive = datetime.now(IST).replace(tzinfo=None)
        if datetime.combine(appt.date, appt.start_time) <= now_naive:
            return {"message": "Cannot cancel — session time has already started"}, 400

        appt.status = 'cancelled'

        log_action(
            user_id=current_user.id,
            action=f"Patient cancelled appointment #{appointment_id} with Dr. {appt.doctor.name} on {appt.date} at {appt.start_time}",
            endpoint=f'/api/v1/patient/appointment/{appointment_id}/cancel'
        )
        db.session.commit()

        return {"message": "Appointment cancelled successfully"}, 200


class PatientPrescription(Resource):
    @auth_token_required
    def get(self, appointment_id):
        err = patient_only()
        if err: return err

        appt = Appointment.query.get(appointment_id)
        if not appt:
            return {"message": "Appointment not found"}, 404

        if appt.patient_id != current_user.id:
            return {"message": "Access denied — not your appointment"}, 403

        prescription = appt.prescription
        if not prescription or not prescription.is_finalized:
            return {"message": "No prescription available for this visit"}, 404

        return {
            "prescription": {
                "appointment_id": appointment_id,
                "visit_date":     appt.date.strftime('%Y-%m-%d'),
                "doctor_name":    appt.doctor.name,
                "stage":          appt.stage_at_visit,
                "content":        prescription.verified_content,
            }
        }, 200


# ── Booking Confirmation Email ─────────────────────────────────────────────

def send_booking_confirmation(app, patient, doctor, appointment):
    """
    Sends a styled HTML booking confirmation email to the patient
    immediately after a successful appointment booking.
    """
    from flask_mail import Message

    date_str  = appointment.date.strftime('%A, %d %B %Y')
    start_str = appointment.start_time.strftime('%I:%M %p')
    end_str   = appointment.end_time.strftime('%I:%M %p')
    stage_str = appointment.stage_at_visit or patient.current_cycle_stage or '—'

    msg = Message(
        subject="✅ Appointment Confirmed — Ivy Clinic",
        recipients=[patient.email],
        html=_confirmation_html(patient, doctor, appointment, date_str, start_str, end_str, stage_str),
        body=_confirmation_text(patient, doctor, appointment, date_str, start_str, end_str, stage_str)
    )
    app.mail.send(msg)


def _confirmation_html(patient, doctor, appointment, date_str, start_str, end_str, stage_str):
    return f"""<!DOCTYPE html>
<html>
<head><meta charset="utf-8"/></head>
<body style="margin:0;padding:0;background:#f0f5f9;font-family:'Segoe UI',Arial,sans-serif;">
  <div style="max-width:560px;margin:40px auto;background:#fff;border-radius:12px;overflow:hidden;box-shadow:0 4px 20px rgba(0,0,0,0.08);">

    <!-- Header -->
    <div style="background:#0a7ea4;padding:28px 32px;">
      <div style="font-size:22px;font-weight:700;color:#fff;">Ivy Clinic</div>
      <div style="font-size:12px;color:rgba(255,255,255,0.75);margin-top:2px;letter-spacing:0.08em;text-transform:uppercase;">IVF &amp; Reproductive Medicine</div>
    </div>

    <!-- Body -->
    <div style="padding:32px;">
      <div style="font-size:32px;margin-bottom:8px;">✅</div>
      <h2 style="font-size:20px;font-weight:700;color:#1a2535;margin:0 0 6px;">Appointment <span style="color:#059669;">Confirmed</span></h2>
      <p style="font-size:14px;color:#64748b;margin:0 0 24px;">
        Hi {patient.name.split()[0]}, your appointment has been successfully booked. Here are your details:
      </p>

      <!-- Appointment card -->
      <div style="background:#f8fafc;border:1px solid #e2e8f0;border-radius:10px;padding:20px;margin-bottom:24px;">
        <table style="width:100%;border-collapse:collapse;">
          <tr>
            <td style="padding:9px 0;font-size:12px;font-weight:700;text-transform:uppercase;letter-spacing:0.08em;color:#94a3b8;width:130px;">Date</td>
            <td style="padding:9px 0;font-size:14px;font-weight:600;color:#1a2535;">{date_str}</td>
          </tr>
          <tr style="border-top:1px solid #f1f5f9;">
            <td style="padding:9px 0;font-size:12px;font-weight:700;text-transform:uppercase;letter-spacing:0.08em;color:#94a3b8;">Time</td>
            <td style="padding:9px 0;font-size:14px;font-weight:600;color:#0a7ea4;">{start_str} – {end_str}</td>
          </tr>
          <tr style="border-top:1px solid #f1f5f9;">
            <td style="padding:9px 0;font-size:12px;font-weight:700;text-transform:uppercase;letter-spacing:0.08em;color:#94a3b8;">Doctor</td>
            <td style="padding:9px 0;font-size:14px;font-weight:600;color:#1a2535;">Dr. {doctor.name}
              <div style="font-size:12px;color:#94a3b8;font-weight:400;margin-top:2px;">{doctor.specialization or ''}</div>
            </td>
          </tr>
          <tr style="border-top:1px solid #f1f5f9;">
            <td style="padding:9px 0;font-size:12px;font-weight:700;text-transform:uppercase;letter-spacing:0.08em;color:#94a3b8;">IVF Stage</td>
            <td style="padding:9px 0;">
              <span style="background:#eff9fc;color:#0a7ea4;border:1px solid #bae6fd;padding:3px 10px;border-radius:4px;font-size:12px;font-weight:600;">{stage_str}</span>
            </td>
          </tr>
          <tr style="border-top:1px solid #f1f5f9;">
            <td style="padding:9px 0;font-size:12px;font-weight:700;text-transform:uppercase;letter-spacing:0.08em;color:#94a3b8;">Service ID</td>
            <td style="padding:9px 0;font-size:13px;font-family:monospace;color:#64748b;">{patient.service_id}</td>
          </tr>
          <tr style="border-top:1px solid #f1f5f9;">
            <td style="padding:9px 0;font-size:12px;font-weight:700;text-transform:uppercase;letter-spacing:0.08em;color:#94a3b8;">Booking Ref</td>
            <td style="padding:9px 0;font-size:13px;font-family:monospace;color:#7c3aed;">#APT-{str(appointment.id).zfill(5)}</td>
          </tr>
        </table>
      </div>

      <!-- Notice -->
      <div style="background:#fffbeb;border:1px solid #fde68a;border-radius:8px;padding:14px 16px;margin-bottom:20px;">
        <p style="font-size:13px;color:#92400e;margin:0;line-height:1.6;">
          📋 <strong>Please arrive 10 minutes early.</strong> Bring any previous reports or prescriptions if this is a follow-up visit.
        </p>
      </div>

      <p style="font-size:13px;color:#94a3b8;line-height:1.6;margin:0;">
        You will receive another reminder 1 hour before your appointment. To cancel, please visit the patient portal or contact the clinic.
      </p>
    </div>

    <!-- Footer -->
    <div style="background:#f8fafc;border-top:1px solid #e2e8f0;padding:16px 32px;text-align:center;">
      <p style="font-size:11px;color:#94a3b8;margin:0;">
        Ivy Clinic &nbsp;·&nbsp; This is an automated confirmation. Please do not reply to this email.
      </p>
    </div>

  </div>
</body>
</html>"""


def _confirmation_text(patient, doctor, appointment, date_str, start_str, end_str, stage_str):
    return f"""Hi {patient.name},

Your appointment at Ivy Clinic has been confirmed.

  Booking Ref : #APT-{str(appointment.id).zfill(5)}
  Date        : {date_str}
  Time        : {start_str} – {end_str}
  Doctor      : Dr. {doctor.name}
  IVF Stage   : {stage_str}
  Service ID  : {patient.service_id}

Please arrive 10 minutes early.
You will receive a reminder 1 hour before your appointment.

To cancel, visit the patient portal or contact the clinic directly.

— Ivy Clinic
"""