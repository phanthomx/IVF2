from flask_restful import Resource, reqparse
from flask_security import auth_token_required, current_user, hash_password
from applications.database import db
from applications.models import User, Doctor, Patient, AuditLog, Role, Appointment
from applications.audit_helper import log_action
from flask import request
import uuid

class AdminDashboard(Resource):
    @auth_token_required
    def get(self):
        if current_user.type != 'admin':
            return {"message": "Access denied"}, 403

        try:
            total_patients = Patient.query.count()
            active_doctors = Doctor.query.count()

            logs = AuditLog.query.order_by(AuditLog.timestamp.desc()).limit(8).all()

            formatted_logs = []
            for log in logs:
                try:
                    # Safely format user_id — could be None or non-int
                    uid = log.user_id
                    user_id_str = f"USR-{int(uid):04d}" if uid is not None else "USR-0000"

                    # Safely determine method from action string
                    action = log.action or ""
                    is_post = any(
                        word in action.lower()
                        for word in ["onboard", "register", "create", "login", "logout", "removed"]
                    )
                    method = "POST" if is_post else "GET"

                    formatted_logs.append({
                        "timestamp": log.timestamp.strftime("%Y-%m-%d %H:%M:%S") if log.timestamp else "—",
                        "user_id": user_id_str,
                        "ip_address": log.ip_address or "—",
                        "endpoint": log.endpoint or "—",
                        "method": method
                    })
                except Exception:
                    # Skip malformed log entries rather than crashing the whole response
                    continue

            return {
                "stats": {
                    "total_patients": f"{total_patients:,}",
                    "patient_growth": "+12 this month",
                    "active_doctors": active_doctors,
                    "online_now": f"{active_doctors} online now",
                    "system_status": "Online",
                    "uptime": "99.98%"
                },
                "logs": formatted_logs
            }, 200

        except Exception as e:
            return {"message": f"Dashboard error: {str(e)}"}, 500


class OnboardDoctor(Resource):
    @auth_token_required
    def post(self):
        if current_user.type != 'admin':
            return {"message": "Access denied"}, 403

        parser = reqparse.RequestParser()
        parser.add_argument('email',          required=True, location='json', help="Email is required")
        parser.add_argument('name',           required=True, location='json', help="Name is required")
        parser.add_argument('password',       required=True, location='json', help="Password is required")
        parser.add_argument('specialization', required=True, location='json', help="Specialization is required")
        parser.add_argument('license_number', required=True, location='json', help="License number is required")
        args = parser.parse_args()

        if Doctor.query.filter_by(email=args['email']).first():
            return {"message": "Email already exists"}, 400

        try:
            new_doc = Doctor(
                email=args['email'],
                name=args['name'],
                password=hash_password(args['password']),
                fs_uniquifier=str(uuid.uuid4()),
                specialization=args['specialization'],
                license_number=args['license_number'],
                active=True
            )

            role = Role.query.filter_by(name='doctor').first()
            if role:
                new_doc.roles.append(role)

            db.session.add(new_doc)
            db.session.flush()

            log_action(
                user_id=current_user.id,
                action=f"Onboarded Dr. {new_doc.name} ({new_doc.specialization})",
                endpoint='/api/v1/admin/onboard-doctor'
            )

            db.session.commit()
            return {"message": "Doctor created successfully"}, 201

        except Exception as e:
            db.session.rollback()
            return {"message": f"Failed to create doctor: {str(e)}"}, 500


class AllUsers(Resource):
    @auth_token_required
    def get(self):
        if current_user.type != 'admin':
            return {"message": "Access denied"}, 403

        try:
            doctors = Doctor.query.all()
            patients = Patient.query.all()

            formatted_doctors = [{
                "id": doc.id,
                "name": doc.name,
                "email": doc.email,
                "role": "doctor",
                "active": doc.active,
                "specialization": doc.specialization or "—",
                "license_number": doc.license_number or "—",
            } for doc in doctors]

            formatted_patients = [{
                "id": pat.id,
                "name": pat.name,
                "email": pat.email,
                "role": "patient",
                "active": pat.active,
                "service_id": pat.service_id or "—",
                "contact_info": pat.contact_info or "—",
                "current_cycle_stage": pat.current_cycle_stage or "—",
            } for pat in patients]

            return {
                "users": formatted_doctors + formatted_patients
            }, 200

        except Exception as e:
            return {"message": f"Failed to load users: {str(e)}"}, 500


class RemoveDoctor(Resource):
    @auth_token_required
    def delete(self, doctor_id):
        if current_user.type != 'admin':
            return {"message": "Access denied"}, 403

        doctor = Doctor.query.get(doctor_id)
        if not doctor:
            return {"message": "Doctor not found"}, 404

        try:
            doctor_name = doctor.name

            # Delete associated appointments first to prevent IntegrityError
            Appointment.query.filter_by(doctor_id=doctor_id).delete()

            db.session.delete(doctor)

            log_action(
                user_id=current_user.id,
                action=f"Removed Dr. {doctor_name} (ID: {doctor_id}) from system",
                endpoint=f'/api/v1/admin/remove-doctor/{doctor_id}'
            )

            db.session.commit()
            return {"message": f"Dr. {doctor_name} has been removed successfully"}, 200

        except Exception as e:
            db.session.rollback()
            return {"message": f"Failed to remove doctor: {str(e)}"}, 500


class RemovePatient(Resource):
    @auth_token_required
    def delete(self, patient_id):
        if current_user.type != 'admin':
            return {"message": "Access denied"}, 403

        patient = Patient.query.get(patient_id)
        if not patient:
            return {"message": "Patient not found"}, 404

        try:
            patient_name = patient.name
            service_id = patient.service_id

            # Delete associated appointments first to prevent IntegrityError
            Appointment.query.filter_by(patient_id=patient_id).delete()

            db.session.delete(patient)

            log_action(
                user_id=current_user.id,
                action=f"Removed patient {patient_name} (SVC: {service_id}) from system",
                endpoint=f'/api/v1/admin/remove-patient/{patient_id}'
            )

            db.session.commit()
            return {"message": f"{patient_name} has been removed successfully"}, 200

        except Exception as e:
            db.session.rollback()
            return {"message": f"Failed to remove patient: {str(e)}"}, 500