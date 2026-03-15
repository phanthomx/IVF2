import os
from flask import Flask
from sqlalchemy import text
from flask_restful import Api
from flask_cors import CORS
from flask_mail import Mail
from flask_security import Security

# Internal Imports
from applications.config import Config
from applications.database import db
from applications.models import *
from applications.user_datastore import user_datastore
from create_initial_data import create_initial_data
from applications.auth_api import Login, Logout, Register
from applications.admin import AdminDashboard, OnboardDoctor, AllUsers, RemoveDoctor, RemovePatient


from applications.receptionist import (
    RegisterPatient, PatientList, DoctorList,
    AvailableSlots, BookAppointment, DailyQueue,
    UpcomingBookings, AppointmentHistory,
    CancelAppointment, TogglePayment, ConfirmCashPayment
)



from applications.doctor import (
    DoctorQueue, PatientDetail, StartSession, CompleteSession,
    DoctorAvailability, DoctorPatients,
    PrescriptionAICheck           # ← NEW
)

from applications.patient import (
    PatientProfile, PatientHistory, PatientInvoices,
    PatientDoctorList, PatientAvailableSlots,
    PatientBookAppointment, PatientCancelAppointment,
    PatientPrescription
)

from applications.accountant import (
    BillingQueue, GenerateBill, InvoiceLedger,
    DailyReport, WeeklyReport, MonthlyReport
)

def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)

    # 1. Enhanced CORS (matching your reference for credentials & headers)
    CORS(app, resources={r"/*": {
    "origins": ["http://localhost:3000", "http://127.0.0.1:3000"],  # ✅ added localhost for React
    "supports_credentials": True,
    "allow_headers": ["Content-Type", "Authorization", "user-id", "Authentication-Token"],  # ✅ added
    "methods": ["GET", "POST", "PUT", "PATCH","DELETE", "OPTIONS"]
}})
    db.init_app(app)
    api = Api(app, prefix='/api/v1')

    app.security = Security(app, user_datastore)
    app.mail = Mail(app)

    return app, api

app, api = create_app()
api.add_resource(Login, '/login')   # Resulting URL: /api/v1/login
api.add_resource(Logout, '/logout') # Resulting URL: /api/v1/logout
#api.add_resource(Register, '/register')

#ADMIN
api.add_resource(AdminDashboard, '/admin/dashboard')   # /api/v1/admin/dashboard
api.add_resource(OnboardDoctor, '/admin/onboard-doctor')
api.add_resource(AllUsers,     '/admin/users')                    # GET  /api/v1/admin/users
api.add_resource(RemoveDoctor, '/admin/remove-doctor/<int:doctor_id>')  # DELETE /api/v1/admin/remove-doctor/5
api.add_resource(RemovePatient, '/admin/remove-patient/<int:patient_id>') 




##RECEPTIONIST
api.add_resource(RegisterPatient,    '/receptionist/register-patient')
api.add_resource(PatientList,        '/receptionist/patients')
api.add_resource(DoctorList,         '/receptionist/doctors')
api.add_resource(AvailableSlots,     '/receptionist/slots/<int:doctor_id>/<string:target_date>')
api.add_resource(BookAppointment,    '/receptionist/book-appointment')
api.add_resource(DailyQueue,         '/receptionist/queue/<string:target_date>')
api.add_resource(UpcomingBookings,   '/receptionist/bookings')
api.add_resource(AppointmentHistory, '/receptionist/history')
api.add_resource(CancelAppointment,  '/receptionist/appointment/<int:appointment_id>/cancel')
api.add_resource(TogglePayment,      '/receptionist/invoice/<int:invoice_id>/toggle-payment')
api.add_resource(ConfirmCashPayment, '/receptionist/invoice/<int:invoice_id>/payment')


##DOCTOR
api.add_resource(DoctorQueue,         '/doctor/queue/<string:target_date>')
api.add_resource(PatientDetail,       '/doctor/patient/<int:patient_id>')
api.add_resource(StartSession,        '/doctor/appointment/<int:appointment_id>/start')
api.add_resource(CompleteSession,     '/doctor/appointment/<int:appointment_id>/complete')
api.add_resource(DoctorAvailability,  '/doctor/availability')
api.add_resource(DoctorPatients,      '/doctor/patients')
api.add_resource(PrescriptionAICheck, '/doctor/prescription/ai-check')   # ← NEW

#PATIENT
api.add_resource(PatientProfile,           '/patient/profile')
api.add_resource(PatientHistory,           '/patient/history')
api.add_resource(PatientInvoices,          '/patient/invoices')
api.add_resource(PatientDoctorList,        '/patient/doctors')
api.add_resource(PatientAvailableSlots,    '/patient/slots/<int:doctor_id>/<string:target_date>')
api.add_resource(PatientBookAppointment,   '/patient/book-appointment')
api.add_resource(PatientCancelAppointment, '/patient/appointment/<int:appointment_id>/cancel')
api.add_resource(PatientPrescription,      '/patient/prescription/<int:appointment_id>')
#ACCOUNTANT
api.add_resource(BillingQueue,   '/accountant/billing-queue')
api.add_resource(GenerateBill,   '/accountant/invoice/<int:invoice_id>/generate')
api.add_resource(InvoiceLedger,  '/accountant/invoices')
api.add_resource(DailyReport,    '/accountant/report/daily')
api.add_resource(WeeklyReport,   '/accountant/report/weekly')
api.add_resource(MonthlyReport,  '/accountant/report/monthly')

db_path = os.path.join(app.root_path, 'applications', 'instance', 'database.sqlite3')

if __name__ == '__main__':
    # 2. Conditional Database Setup (only runs once)
    if not os.path.exists(db_path):
        with app.app_context():
            try:
                os.makedirs(os.path.dirname(db_path), exist_ok=True)
                db.session.execute(text('PRAGMA foreign_keys=ON'))
                db.create_all()
                create_initial_data(app, db)
                print("Database initialized successfully.")
            except Exception as e:
                print(f"Error initializing DB: {e}")
    
    # 3. Start Server on Port 5001 (matching your store's expectation)
    app.run(debug=True, host='0.0.0.0', port=5001)