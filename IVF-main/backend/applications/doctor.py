# applications/doctor.py
import os
import json
import requests

from flask_restful import Resource
from flask_security import auth_token_required, current_user
from applications.database import db
from applications.models import Doctor, Patient, Appointment, Prescription, Invoice, Availability
from applications.audit_helper import log_action
from flask import request
from datetime import datetime, date, timedelta
from zoneinfo import ZoneInfo

IST = ZoneInfo("Asia/Kolkata")

# IVF stage progression
IVF_STAGES = [
    'Onboarding',
    'Baseline Assessment',
    'Stimulation Protocol',
    'Mid-Cycle Monitoring',
    'Trigger Administration',
    'Retrieval Procedure',
    'Transfer Procedure'
]

def doctor_only():
    if current_user.type != 'doctor':
        log_action(
            user_id=current_user.id,
            action=f"Unauthorized doctor access attempt by {current_user.name} ({current_user.type})",
            endpoint=request.path
        )
        db.session.commit()
        return {"message": "Access denied"}, 403
    return None


class DoctorQueue(Resource):
    @auth_token_required
    def get(self, target_date):
        err = doctor_only()
        if err: return err

        target = datetime.strptime(target_date, '%Y-%m-%d').date()

        appointments = Appointment.query.filter_by(
            doctor_id=current_user.id,
            date=target
        ).order_by(Appointment.start_time).all()

        queue = []
        for appt in appointments:
            patient = appt.patient
            first_appt = Appointment.query.filter_by(
                patient_id=patient.id
            ).order_by(Appointment.date.asc()).first()

            cycle_day = ((target - first_appt.date).days + 1) if first_appt else 1

            queue.append({
                "appointment_id":   appt.id,
                "patient_id":       patient.id,
                "patient_name":     patient.name,
                "service_id":       patient.service_id,
                "age":              patient.age,
                "blood_type":       patient.blood_type,
                "start_time":       appt.start_time.strftime('%H:%M'),
                "end_time":         appt.end_time.strftime('%H:%M'),
                "status":           appt.status,
                "cycle_day":        cycle_day,
                "current_stage":    patient.current_cycle_stage,
                "stage_at_visit":   appt.stage_at_visit,
                "is_walkin":        appt.is_walkin,
            })

        return {"queue": queue, "date": target_date}, 200


class PatientDetail(Resource):
    @auth_token_required
    def get(self, patient_id):
        err = doctor_only()
        if err: return err

        patient = Patient.query.get(patient_id)
        if not patient:
            return {"message": "Patient not found"}, 404

        history = Appointment.query.filter_by(
            patient_id=patient_id,
            doctor_id=current_user.id
        ).order_by(Appointment.date.desc()).all()

        history_data = []
        for appt in history:
            prescription = appt.prescription
            history_data.append({
                "appointment_id": appt.id,
                "date":           appt.date.strftime('%Y-%m-%d'),
                "start_time":     appt.start_time.strftime('%H:%M'),
                "status":         appt.status,
                "stage":          appt.stage_at_visit,
                "clinical_notes": appt.clinical_notes,
                "prescription":   prescription.verified_content if prescription else None,
                "is_finalized":   prescription.is_finalized if prescription else False,
            })

        return {
            "patient": {
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
            },
            "history": history_data
        }, 200


class StartSession(Resource):
    @auth_token_required
    def post(self, appointment_id):
        err = doctor_only()
        if err: return err

        appt = Appointment.query.get(appointment_id)
        if not appt:
            return {"message": "Appointment not found"}, 404
        if appt.doctor_id != current_user.id:
            return {"message": "Not your appointment"}, 403
        if appt.status != 'waiting':
            return {"message": f"Cannot start — status is '{appt.status}'"}, 400

        appt.status = 'in-session'

        log_action(
            user_id=current_user.id,
            action=f"Started session for {appt.patient.name} ({appt.patient.service_id})",
            endpoint=f'/api/v1/doctor/appointment/{appointment_id}/start'
        )
        db.session.commit()

        return {"message": "Session started", "status": "in-session"}, 200


class CompleteSession(Resource):
    @auth_token_required
    def post(self, appointment_id):
        err = doctor_only()
        if err: return err

        appt = Appointment.query.get(appointment_id)
        if not appt:
            return {"message": "Appointment not found"}, 404
        if appt.doctor_id != current_user.id:
            return {"message": "Not your appointment"}, 403
        if appt.status != 'in-session':
            return {"message": f"Cannot complete — status is '{appt.status}'"}, 400

        data               = request.get_json(force=True, silent=True) or {}
        clinical_notes     = data.get('clinical_notes', '')
        prescription_text  = data.get('prescription', '')
        advance_stage      = data.get('advance_stage', True)

        appt.clinical_notes = clinical_notes
        appt.status         = 'completed'

        if prescription_text:
            if appt.prescription:
                appt.prescription.verified_content = prescription_text
                appt.prescription.is_finalized     = True
            else:
                from applications.models import Prescription
                prescription = Prescription(
                    appointment_id=appointment_id,
                    doctor_id=current_user.id,
                    patient_id=appt.patient_id,
                    raw_draft=prescription_text,
                    verified_content=prescription_text,
                    is_finalized=True
                )
                db.session.add(prescription)

        patient = appt.patient
        if advance_stage:
            current_idx = IVF_STAGES.index(patient.current_cycle_stage) \
                if patient.current_cycle_stage in IVF_STAGES else 0
            if current_idx < len(IVF_STAGES) - 1:
                patient.current_cycle_stage = IVF_STAGES[current_idx + 1]

        service_code = f"IVF-STAGE-{IVF_STAGES.index(appt.stage_at_visit or 'Onboarding') + 1:02d}"
        invoice = Invoice(
            patient_service_id=patient.service_id,
            appointment_id=appointment_id,
            amount=5000.00,
            service_code=service_code,
            status='pending'
        )
        db.session.add(invoice)

        log_action(
            user_id=current_user.id,
            action=f"Completed session for {patient.name} ({patient.service_id}) — stage: {appt.stage_at_visit} — invoice pushed",
            endpoint=f'/api/v1/doctor/appointment/{appointment_id}/complete'
        )
        db.session.commit()

        return {
            "message":      "Session completed, invoice generated",
            "new_stage":    patient.current_cycle_stage,
            "invoice_code": service_code
        }, 200


class DoctorAvailability(Resource):
    @auth_token_required
    def get(self):
        err = doctor_only()
        if err: return err

        availabilities = Availability.query.filter_by(doctor_id=current_user.id).all()
        return {"availability": [{
            "id":                    a.id,
            "day_of_week":           a.day_of_week,
            "start_time":            a.start_time.strftime('%H:%M'),
            "end_time":              a.end_time.strftime('%H:%M'),
            "slot_duration_minutes": a.slot_duration_minutes
        } for a in availabilities]}, 200

    @auth_token_required
    def post(self):
        err = doctor_only()
        if err: return err

        data  = request.get_json(force=True, silent=True) or {}
        slots = data.get('slots', [])

        if not slots:
            return {"message": "No slots provided"}, 400

        Availability.query.filter_by(doctor_id=current_user.id).delete()

        for slot in slots:
            avail = Availability(
                doctor_id=current_user.id,
                day_of_week=slot['day_of_week'],
                start_time=datetime.strptime(slot['start_time'], '%H:%M').time(),
                end_time=datetime.strptime(slot['end_time'], '%H:%M').time(),
                slot_duration_minutes=slot.get('slot_duration_minutes', 30)
            )
            db.session.add(avail)

        log_action(
            user_id=current_user.id,
            action=f"Updated availability schedule ({len(slots)} day slots)",
            endpoint='/api/v1/doctor/availability'
        )
        db.session.commit()

        return {"message": f"Availability updated — {len(slots)} slots saved"}, 200


class DoctorPatients(Resource):
    """
    Returns all unique patients this doctor has ever seen.
    Used by the History tab search — replaces the forbidden /receptionist/patients call.
    """
    @auth_token_required
    def get(self):
        err = doctor_only()
        if err: return err

        appointments = Appointment.query.filter_by(doctor_id=current_user.id).all()

        seen = {}
        for appt in appointments:
            p = appt.patient
            if p.id not in seen:
                seen[p.id] = {
                    "id":         p.id,
                    "name":       p.name,
                    "service_id": p.service_id,
                }

        return {"patients": list(seen.values())}, 200


# ─────────────────────────────────────────────────────────────────────────────
# AI PRESCRIPTION CHECKER
# ─────────────────────────────────────────────────────────────────────────────

AI_SYSTEM_PROMPT = """You are a clinical pharmacist and medical writing assistant embedded inside an IVF clinic's EMR system.
Your job is to review a doctor's prescription draft and identify human errors such as:
- Misspelled drug names (e.g. "Letrozle" → "Letrozole", "Gonalf" → "Gonal-F")
- Wrong or missing dosage units (e.g. "100" instead of "100 IU", "0.5" instead of "0.5 mg")
- Ambiguous or incomplete instructions (e.g. "take twice" → "take twice daily")
- Potentially dangerous frequency errors (e.g. "every 2 hours" for a drug normally given daily)
- Missing route of administration where it matters (e.g. "Progesterone 200" vs "Progesterone 200 mg vaginally")

You must respond ONLY with a valid JSON object — no markdown, no explanation outside the JSON.

The JSON must follow this exact schema:
{
  "has_suggestions": true | false,
  "corrected_text": "<full corrected prescription text, or same as input if no changes>",
  "suggestions": [
    {
      "original": "<the exact fragment from the draft that has the error>",
      "corrected": "<the corrected replacement>",
      "reason": "<one concise sentence explaining why this change is needed>"
    }
  ]
}

If the prescription looks correct and needs no changes, return has_suggestions: false, corrected_text equal to the input, and an empty suggestions array.
Never add drugs that weren't in the original. Never remove drugs. Only fix what appears to be a human error."""


class PrescriptionAICheck(Resource):
    """
    POST /api/v1/doctor/prescription/ai-check
    Body: { "prescription_text": "...", "patient_context": { "age": 32, "stage": "Stimulation Protocol" } }
    Returns: { has_suggestions, corrected_text, suggestions: [{original, corrected, reason}] }
    """

    @auth_token_required
    def post(self):
        err = doctor_only()
        if err: return err

        data              = request.get_json(force=True, silent=True) or {}
        prescription_text = data.get('prescription_text', '').strip()
        patient_context   = data.get('patient_context', {})

        if not prescription_text:
            return {"message": "prescription_text is required"}, 400

        # Build context-aware user message
        context_snippet = ""
        if patient_context:
            parts = []
            if patient_context.get('age'):
                parts.append(f"Patient age: {patient_context['age']}")
            if patient_context.get('stage'):
                parts.append(f"IVF stage: {patient_context['stage']}")
            if patient_context.get('blood_type'):
                parts.append(f"Blood type: {patient_context['blood_type']}")
            if parts:
                context_snippet = "Patient context:\n" + "\n".join(parts) + "\n\n"

        user_message = (
            f"{context_snippet}"
            f"Please review the following prescription draft for errors:\n\n"
            f"{prescription_text}"
        )

        ollama_url = os.environ.get("OLLAMA_URL", "http://localhost:11434")

        try:
            response = requests.post(
                f"{ollama_url}/api/chat",
                json={
                    "model": "llama3.2",
                    "stream": False,
                    "messages": [
                        {"role": "system", "content": AI_SYSTEM_PROMPT},
                        {"role": "user",   "content": user_message}
                    ]
                },
                timeout=60   # llama3.2 can be slow on first load
            )
            response.raise_for_status()

            raw_text = response.json()["message"]["content"].strip()

            # Strip accidental markdown fences if the model adds them
            if raw_text.startswith("```"):
                raw_text = raw_text.split("```")[1]
                if raw_text.startswith("json"):
                    raw_text = raw_text[4:]
                raw_text = raw_text.strip()

            result = json.loads(raw_text)

            log_action(
                user_id=current_user.id,
                action=f"AI prescription check (llama3.2) — {len(result.get('suggestions', []))} suggestion(s) returned",
                endpoint='/api/v1/doctor/prescription/ai-check'
            )
            db.session.commit()

            return result, 200

        except json.JSONDecodeError:
            return {"message": "AI returned an unexpected response. Please try again."}, 502
        except requests.exceptions.ConnectionError:
            return {"message": "Could not reach Ollama. Make sure it is running (ollama serve)."}, 503
        except requests.exceptions.Timeout:
            return {"message": "Ollama timed out. The model may still be loading — try again."}, 504
        except requests.exceptions.HTTPError as e:
            return {"message": f"Ollama error: {e.response.status_code}"}, 502
        except Exception as e:
            return {"message": f"Unexpected error: {str(e)}"}, 500