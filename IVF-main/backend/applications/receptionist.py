# applications/receptionist_api.py
from flask_restful import Resource
from flask_security import auth_token_required, current_user, hash_password
from applications.database import db
from applications.models import Patient, Doctor, Appointment, Invoice, Availability, Role
from applications.audit_helper import log_action
from flask import request
from datetime import datetime, date, timedelta
from zoneinfo import ZoneInfo
from sqlalchemy import and_
import uuid

IST = ZoneInfo("Asia/Kolkata")


# ── Role Guard ────────────────────────────────────────────────────────────────
def receptionist_only():
    if current_user.type != 'receptionist':
        log_action(
            user_id=current_user.id,
            action=f"Unauthorized receptionist access attempt by {current_user.name} ({current_user.type})",
            endpoint=request.path
        )
        db.session.commit()
        return {"message": "Access denied"}, 403
    return None


# ── Helpers ───────────────────────────────────────────────────────────────────
def generate_service_id():
    year = datetime.now(IST).year
    last = Patient.query.filter(
        Patient.service_id.like(f'SVC-{year}-%')
    ).order_by(Patient.service_id.desc()).first()
    new_num = (int(last.service_id.split('-')[-1]) + 1) if last else 1
    return f"SVC-{year}-{new_num:04d}"


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


def format_appointment(appt):
    invoice = appt.invoice
    return {
        "appointment_id": appt.id,
        "patient_id":     appt.patient.id,
        "patient_name":   appt.patient.name,
        "service_id":     appt.patient.service_id,
        "doctor_name":    appt.doctor.name,
        "date":           appt.date.strftime('%Y-%m-%d'),
        "start_time":     appt.start_time.strftime('%H:%M'),
        "end_time":       appt.end_time.strftime('%H:%M'),
        "status":         appt.status,
        "is_walkin":      appt.is_walkin,
        "stage":          appt.stage_at_visit,
        "invoice_id":     invoice.id if invoice else None,
        "payment_status": invoice.status if invoice else "no_invoice",
        "payment_source": invoice.payment_source if invoice else None,
    }


# ── Resources ──────────────────────────────────────────────────────────────────

class RegisterPatient(Resource):
    @auth_token_required
    def post(self):
        err = receptionist_only()
        if err: return err

        data     = request.get_json(force=True, silent=True) or {}
        email    = data.get('email')
        name     = data.get('name')
        password = data.get('password')

        if not email or not name or not password:
            return {"message": "Name, email and password are required"}, 400

        if Patient.query.filter_by(email=email).first():
            log_action(
                user_id=current_user.id,
                action=f"Failed registration — email exists: {email}",
                endpoint='/api/v1/receptionist/register-patient'
            )
            db.session.commit()
            return {"message": "Email already registered"}, 400

        service_id  = generate_service_id()
        new_patient = Patient(
            email=email,
            name=name,
            password=hash_password(password),
            fs_uniquifier=str(uuid.uuid4()),
            active=True,
            service_id=service_id,
            contact_info=data.get('contact_info'),
            age=data.get('age'),
            height_cm=data.get('height_cm'),
            weight_kg=data.get('weight_kg'),
            blood_type=data.get('blood_type'),
            current_cycle_stage='Onboarding'
        )

        role = Role.query.filter_by(name='patient').first()
        if role:
            new_patient.roles.append(role)

        db.session.add(new_patient)
        db.session.flush()

        log_action(
            user_id=current_user.id,
            action=f"Registered patient {new_patient.name} ({service_id})",
            endpoint='/api/v1/receptionist/register-patient'
        )
        db.session.commit()

        return {
            "message":    "Patient registered successfully",
            "service_id": service_id,
            "patient_id": new_patient.id
        }, 201


class PatientList(Resource):
    @auth_token_required
    def get(self):
        err = receptionist_only()
        if err: return err

        patients = Patient.query.order_by(Patient.name).all()
        return {"patients": [{
            "id":                  p.id,
            "name":                p.name,
            "email":               p.email,
            "service_id":          p.service_id,
            "contact_info":        p.contact_info,
            "age":                 p.age,
            "height_cm":           p.height_cm,
            "weight_kg":           p.weight_kg,
            "blood_type":          p.blood_type,
            "current_cycle_stage": p.current_cycle_stage
        } for p in patients]}, 200


class DoctorList(Resource):
    @auth_token_required
    def get(self):
        err = receptionist_only()
        if err: return err

        doctors = Doctor.query.filter_by(active=True).all()
        return {"doctors": [{
            "id":             d.id,
            "name":           d.name,
            "specialization": d.specialization
        } for d in doctors]}, 200


class AvailableSlots(Resource):
    @auth_token_required
    def get(self, doctor_id, target_date):
        err = receptionist_only()
        if err: return err

        today  = datetime.now(IST).date()
        target = datetime.strptime(target_date, '%Y-%m-%d').date()

        if target < today:
            return {"message": "Cannot book past dates"}, 400
        if (target - today).days > 7:
            return {"message": "Bookings only allowed up to 7 days in advance"}, 400

        slots = get_available_slots(doctor_id, target_date)
        return {"slots": slots, "date": target_date, "doctor_id": doctor_id}, 200


class BookAppointment(Resource):
    @auth_token_required
    def post(self):
        err = receptionist_only()
        if err: return err

        data       = request.get_json(force=True, silent=True) or {}
        patient_id = data.get('patient_id')
        doctor_id  = data.get('doctor_id')
        date_str   = data.get('date')
        start_str  = data.get('start_time')
        is_walkin  = data.get('is_walkin', False)

        if not all([patient_id, doctor_id, date_str, start_str]):
            return {"message": "patient_id, doctor_id, date and start_time are required"}, 400

        patient = Patient.query.get(patient_id)
        doctor  = Doctor.query.get(doctor_id)

        if not patient: return {"message": "Patient not found"}, 404
        if not doctor:  return {"message": "Doctor not found"}, 404

        target_date = datetime.strptime(date_str, '%Y-%m-%d').date()
        start_time  = datetime.strptime(start_str, '%H:%M').time()
        today       = datetime.now(IST).date()
        now_naive   = datetime.now(IST).replace(tzinfo=None)

        if target_date < today:
            return {"message": "Cannot book past dates"}, 400

        if target_date == today and start_time <= now_naive.time():
            return {"message": "Cannot book a slot that has already passed"}, 400

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
            log_action(
                user_id=current_user.id,
                action=f"Slot conflict for Dr. {doctor.name} on {date_str} at {start_str}",
                endpoint='/api/v1/receptionist/book-appointment'
            )
            db.session.commit()
            return {"message": "This slot is already booked by another patient"}, 409

        appointment = Appointment(
            patient_id=patient_id,
            doctor_id=doctor_id,
            date=target_date,
            start_time=start_time,
            end_time=end_time,
            status='waiting',
            is_walkin=is_walkin,
            stage_at_visit=patient.current_cycle_stage
        )

        db.session.add(appointment)
        db.session.flush()

        log_action(
            user_id=current_user.id,
            action=f"Booked appointment for {patient.name} ({patient.service_id}) with Dr. {doctor.name} on {date_str} at {start_str}",
            endpoint='/api/v1/receptionist/book-appointment'
        )
        db.session.commit()

        return {
            "message":        "Appointment booked successfully",
            "appointment_id": appointment.id
        }, 201


class DailyQueue(Resource):
    @auth_token_required
    def get(self, target_date):
        err = receptionist_only()
        if err: return err

        target       = datetime.strptime(target_date, '%Y-%m-%d').date()
        appointments = Appointment.query.filter_by(date=target)\
            .order_by(Appointment.start_time).all()

        return {
            "queue": [format_appointment(a) for a in appointments],
            "date":  target_date,
            "total": len(appointments)
        }, 200


class UpcomingBookings(Resource):
    @auth_token_required
    def get(self):
        err = receptionist_only()
        if err: return err

        today          = datetime.now(IST).date()
        now_naive      = datetime.now(IST).replace(tzinfo=None)
        patient_search = request.args.get('patient', '').lower()

        appointments = Appointment.query.filter(
            Appointment.date   >= today,
            Appointment.status != 'cancelled'
        ).order_by(Appointment.date.asc(), Appointment.start_time.asc()).all()

        if patient_search:
            appointments = [
                a for a in appointments
                if patient_search in a.patient.name.lower()
                or patient_search in a.patient.service_id.lower()
            ]

        result = []
        for appt in appointments:
            appt_datetime = datetime.combine(appt.date, appt.start_time)
            can_cancel    = (
                appt.status   == 'waiting' and
                appt_datetime >  now_naive
            )
            entry               = format_appointment(appt)
            entry['can_cancel'] = can_cancel
            result.append(entry)

        return {"bookings": result, "total": len(result)}, 200


class AppointmentHistory(Resource):
    @auth_token_required
    def get(self):
        err = receptionist_only()
        if err: return err

        today          = datetime.now(IST).date()
        patient_search = request.args.get('patient', '').lower()
        limit          = int(request.args.get('limit', 50))

        appointments = Appointment.query.filter(
            Appointment.date < today
        ).order_by(
            Appointment.date.desc(),
            Appointment.start_time.desc()
        ).limit(limit).all()

        if patient_search:
            appointments = [
                a for a in appointments
                if patient_search in a.patient.name.lower()
                or patient_search in a.patient.service_id.lower()
            ]

        return {
            "history": [format_appointment(a) for a in appointments],
            "total":   len(appointments)
        }, 200


class CancelAppointment(Resource):
    @auth_token_required
    def patch(self, appointment_id):
        err = receptionist_only()
        if err: return err

        appt = Appointment.query.get(appointment_id)
        if not appt:
            return {"message": "Appointment not found"}, 404

        if appt.status != 'waiting':
            return {"message": f"Cannot cancel — appointment is '{appt.status}'"}, 400

        now_naive = datetime.now(IST).replace(tzinfo=None)
        if datetime.combine(appt.date, appt.start_time) <= now_naive:
            return {"message": "Cannot cancel — session time has already started"}, 400

        appt.status = 'cancelled'

        log_action(
            user_id=current_user.id,
            action=f"Cancelled appointment #{appointment_id} for {appt.patient.name} ({appt.patient.service_id}) with Dr. {appt.doctor.name} on {appt.date} at {appt.start_time}",
            endpoint=f'/api/v1/receptionist/appointment/{appointment_id}/cancel'
        )
        db.session.commit()

        return {"message": "Appointment cancelled successfully"}, 200


class TogglePayment(Resource):
    @auth_token_required
    def patch(self, invoice_id):
        err = receptionist_only()
        if err: return err

        invoice = Invoice.query.get(invoice_id)
        if not invoice:
            return {"message": "Invoice not found"}, 404

        if invoice.status == 'pending':
            invoice.status         = 'paid'
            invoice.payment_source = 'front_desk'
            invoice.date_paid      = datetime.now(IST)
            log_action(
                user_id=current_user.id,
                action=f"Marked invoice #{invoice_id} as PAID (SVC: {invoice.patient_service_id})",
                endpoint=f'/api/v1/receptionist/invoice/{invoice_id}/toggle-payment'
            )
        else:
            invoice.status         = 'pending'
            invoice.payment_source = None
            invoice.date_paid      = None
            log_action(
                user_id=current_user.id,
                action=f"Reverted invoice #{invoice_id} to PENDING (SVC: {invoice.patient_service_id})",
                endpoint=f'/api/v1/receptionist/invoice/{invoice_id}/toggle-payment'
            )

        db.session.commit()
        return {
            "message": f"Payment status updated to '{invoice.status}'",
            "status":  invoice.status
        }, 200


class ConfirmCashPayment(Resource):
    @auth_token_required
    def patch(self, invoice_id):
        err = receptionist_only()
        if err: return err

        invoice = Invoice.query.get(invoice_id)
        if not invoice:
            return {"message": "Invoice not found"}, 404

        if invoice.status == 'paid':
            log_action(
                user_id=current_user.id,
                action=f"Attempted duplicate payment for invoice {invoice_id}",
                endpoint=f'/api/v1/receptionist/invoice/{invoice_id}/payment'
            )
            db.session.commit()
            return {"message": "Invoice already paid"}, 400

        invoice.status         = 'paid'
        invoice.payment_source = 'front_desk'
        invoice.date_paid      = datetime.now(IST)

        log_action(
            user_id=current_user.id,
            action=f"Confirmed cash payment for invoice {invoice_id} (SVC: {invoice.patient_service_id})",
            endpoint=f'/api/v1/receptionist/invoice/{invoice_id}/payment'
        )
        db.session.commit()

        return {"message": "Payment confirmed successfully"}, 200