# applications/auth_api.py
from flask import request
from flask_restful import Resource, reqparse
from flask_security import auth_token_required, current_user
from flask_security.utils import hash_password, verify_password
from applications.user_datastore import user_datastore
from applications.database import db
from applications.audit_helper import log_action

# Define the parser for registration
reg_parser = reqparse.RequestParser()
reg_parser.add_argument('email', type=str, required=True, help="Email is required")
reg_parser.add_argument('password', type=str, required=True, help="Password is required")
reg_parser.add_argument('name', type=str, required=True, help="Full name is required")
reg_parser.add_argument('role', type=str, required=True, choices=('doctor', 'patient'), help="Role must be 'doctor' or 'patient'")


class Login(Resource):
    def post(self):
        data = request.get_json()
        email = data.get('email')
        password = data.get('password')

        if not email or not password:
            return {"message": "Email and password are required"}, 400

        user = user_datastore.find_user(email=email)

        if user and verify_password(password, user.password):
            # ✅ Log every login with role info
            log_action(
                user_id=user.id,
                action=f"Login — {user.name} ({user.type})",
                endpoint='/api/v1/login'
            )
            db.session.commit()  # ✅ commit the audit log

            return {
                "message": "Login successful",
                "token": user.get_auth_token(),
                "user": {
                    "id": user.id,
                    "email": user.email,
                    "name": user.name,
                    "role": user.type
                }
            }, 200

        # ✅ Log failed login attempts too (user_id=None since we don't know who it is)
        log_action(
            user_id=None,
            action=f"Failed login attempt for email: {email}",
            endpoint='/api/v1/login'
        )
        db.session.commit()

        return {"message": "Invalid credentials"}, 401


class Logout(Resource):
    @auth_token_required  # ✅ require token so we know who is logging out
    def post(self):
        # ✅ Log every logout
        log_action(
            user_id=current_user.id,
            action=f"Logout — {current_user.name} ({current_user.type})",
            endpoint='/api/v1/logout'
        )
        db.session.commit()
        return {"message": "Successfully logged out"}, 200


class Register(Resource):
    @auth_token_required
    def post(self):
        args = reg_parser.parse_args()

        # Rule 1: Only Admin can register a Doctor
        if args['role'] == 'doctor':
            if current_user.type != 'admin':
                # ✅ Log unauthorized access attempt
                log_action(
                    user_id=current_user.id,
                    action=f"Unauthorized doctor registration attempt by {current_user.name} ({current_user.type})",
                    endpoint='/api/v1/register'
                )
                db.session.commit()
                return {"message": "Access denied: Only Admins can register doctors."}, 403

        # Rule 2: Only Receptionist can register a Patient
        elif args['role'] == 'patient':
            if current_user.type != 'receptionist':
                # ✅ Log unauthorized access attempt
                log_action(
                    user_id=current_user.id,
                    action=f"Unauthorized patient registration attempt by {current_user.name} ({current_user.type})",
                    endpoint='/api/v1/register'
                )
                db.session.commit()
                return {"message": "Access denied: Only Receptionists can register patients."}, 403

        if user_datastore.find_user(email=args['email']):
            return {"message": "User with this email already exists"}, 409

        try:
            user_datastore.create_user(
                email=args['email'],
                password=hash_password(args['password']),
                name=args['name'],
                type=args['role'],
                active=True
            )

            # ✅ Log successful registration
            log_action(
                user_id=current_user.id,
                action=f"Registered new {args['role']}: {args['name']} ({args['email']})",
                endpoint='/api/v1/register'
            )

            db.session.commit()  # ✅ commits both new user and audit atomically
            return {"message": f"{args['role'].capitalize()} registered successfully"}, 201

        except Exception as e:
            db.session.rollback()
            return {"message": f"Error during registration: {str(e)}"}, 500