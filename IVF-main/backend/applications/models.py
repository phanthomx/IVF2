from applications.database import db
from flask_security import UserMixin, RoleMixin
from datetime import datetime
from zoneinfo import ZoneInfo

IST = ZoneInfo("Asia/Kolkata")

# --------------------------------------------------------------------------
# 1. CORE AUTH & POLYMORPHISM BASE
# --------------------------------------------------------------------------

class User(db.Model, UserMixin):
    __tablename__ = 'user'
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(255), nullable=False, unique=True)
    name = db.Column(db.String(100), nullable=False)
    password = db.Column(db.String(255), nullable=False)
    active = db.Column(db.Boolean, default=True)
    fs_uniquifier = db.Column(db.String(255), nullable=False, unique=True)

    type = db.Column(db.String(50))

    roles = db.relationship(
        'Role',
        secondary='user_roles',
        backref=db.backref('users', lazy=True)
    )

    __mapper_args__ = {
        'polymorphic_on': type,
        'polymorphic_identity': 'user'
    }


class Role(db.Model, RoleMixin):
    __tablename__ = 'role'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(80), unique=True, nullable=False)
    description = db.Column(db.String(255))


class UserRoles(db.Model):
    __tablename__ = 'user_roles'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    role_id = db.Column(db.Integer, db.ForeignKey('role.id'))


# --------------------------------------------------------------------------
# 2. STAKEHOLDER MODELS
# --------------------------------------------------------------------------

class Doctor(User):
    __tablename__ = 'doctor'
    id = db.Column(db.Integer, db.ForeignKey('user.id'), primary_key=True)
    specialization = db.Column(db.String(100))
    license_number = db.Column(db.String(50), unique=True)

    availabilities = db.relationship('Availability', backref='doctor', lazy=True)
    appointments = db.relationship('Appointment', backref='doctor', lazy=True)

    __mapper_args__ = {'polymorphic_identity': 'doctor'}


class Patient(User):
    __tablename__ = 'patient'
    id = db.Column(db.Integer, db.ForeignKey('user.id'), primary_key=True)

    service_id = db.Column(db.String(20), unique=True, nullable=False)
    contact_info = db.Column(db.String(15))

    current_cycle_stage = db.Column(db.String(50), default='Onboarding')

    age = db.Column(db.Integer, nullable=True)
    height_cm = db.Column(db.Float, nullable=True)
    weight_kg = db.Column(db.Float, nullable=True)
    blood_type = db.Column(db.String(5), nullable=True)

    appointments = db.relationship(
        'Appointment',
        backref='patient',
        lazy=True,
        foreign_keys='Appointment.patient_id'
    )

    __mapper_args__ = {'polymorphic_identity': 'patient'}


class Receptionist(User):
    __tablename__ = 'receptionist'
    id = db.Column(db.Integer, db.ForeignKey('user.id'), primary_key=True)
    desk_id = db.Column(db.String(20))

    __mapper_args__ = {'polymorphic_identity': 'receptionist'}


class Accountant(User):
    __tablename__ = 'accountant'
    id = db.Column(db.Integer, db.ForeignKey('user.id'), primary_key=True)

    __mapper_args__ = {'polymorphic_identity': 'accountant'}


class Administrator(User):
    __tablename__ = 'administrator'
    id = db.Column(db.Integer, db.ForeignKey('user.id'), primary_key=True)

    __mapper_args__ = {'polymorphic_identity': 'admin'}


# --------------------------------------------------------------------------
# 3. AVAILABILITY & SCHEDULING
# --------------------------------------------------------------------------

class Availability(db.Model):
    __tablename__ = 'availability'
    id = db.Column(db.Integer, primary_key=True)
    doctor_id = db.Column(db.Integer, db.ForeignKey('doctor.id'), nullable=False)

    day_of_week = db.Column(db.Integer, nullable=False)
    start_time = db.Column(db.Time, nullable=False)
    end_time = db.Column(db.Time, nullable=False)
    slot_duration_minutes = db.Column(db.Integer, default=30)


class Appointment(db.Model):
    __tablename__ = 'appointment'
    id = db.Column(db.Integer, primary_key=True)
    patient_id = db.Column(db.Integer, db.ForeignKey('patient.id'), nullable=False)
    doctor_id = db.Column(db.Integer, db.ForeignKey('doctor.id'), nullable=False)

    date = db.Column(db.Date, nullable=False)
    start_time = db.Column(db.Time, nullable=False)
    end_time = db.Column(db.Time, nullable=False)

    status = db.Column(db.String(20), default='waiting')
    is_walkin = db.Column(db.Boolean, default=False)

    clinical_notes = db.Column(db.Text)
    stage_at_visit = db.Column(db.String(50))

    prescription = db.relationship('Prescription', backref='appointment', uselist=False)
    invoice = db.relationship('Invoice', backref='appointment', uselist=False)


# --------------------------------------------------------------------------
# 4. AI-ENHANCED DOCUMENTATION
# --------------------------------------------------------------------------

class Prescription(db.Model):
    __tablename__ = 'prescription'
    id = db.Column(db.Integer, primary_key=True)

    appointment_id = db.Column(
        db.Integer,
        db.ForeignKey('appointment.id'),
        nullable=False,
        unique=True
    )

    doctor_id = db.Column(db.Integer, db.ForeignKey('doctor.id'), nullable=False)
    patient_id = db.Column(db.Integer, db.ForeignKey('patient.id'), nullable=False)

    raw_draft = db.Column(db.Text)
    verified_content = db.Column(db.Text)
    is_finalized = db.Column(db.Boolean, default=False)

    created_at = db.Column(
        db.DateTime(timezone=True),
        default=lambda: datetime.now(IST)
    )

    doctor = db.relationship('Doctor', backref=db.backref('prescriptions', lazy=True))
    patient = db.relationship('Patient', backref=db.backref('prescriptions', lazy=True))


# --------------------------------------------------------------------------
# 5. FINANCIALS
# --------------------------------------------------------------------------

class Invoice(db.Model):
    __tablename__ = 'invoice'
    id = db.Column(db.Integer, primary_key=True)

    patient_service_id = db.Column(db.String(20), nullable=False)

    appointment_id = db.Column(
        db.Integer,
        db.ForeignKey('appointment.id'),
        nullable=False,
        unique=True
    )

    amount = db.Column(db.Float, nullable=False)
    service_code = db.Column(db.String(20))

    status = db.Column(db.String(20), default='pending')
    payment_source = db.Column(db.String(20))

    date_generated = db.Column(
        db.DateTime(timezone=True),
        default=lambda: datetime.now(IST)
    )

    date_paid = db.Column(
        db.DateTime(timezone=True),
        nullable=True
    )


# --------------------------------------------------------------------------
# 6. AUDIT LOGS
# --------------------------------------------------------------------------

class AuditLog(db.Model):
    __tablename__ = 'audit_log'
    id = db.Column(db.Integer, primary_key=True)

    timestamp = db.Column(
        db.DateTime(timezone=True),
        default=lambda: datetime.now(IST)
    )

    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    ip_address = db.Column(db.String(45))
    endpoint = db.Column(db.String(100))
    action = db.Column(db.String(255))