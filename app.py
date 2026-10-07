import os

from flask import Flask, jsonify, request, render_template

from controllers import AdministratorController, ApplicantController, PoliceOfficerController
from database import Database
from services import (ApplicationService, AuthService, NotificationService,
                      PaymentGateway, PoliceSystem)
from utils import (AuthError, ForbiddenError, InvalidTransition, NotFoundError, ValidationError)


def create_app(db_path=None):
    app = Flask(__name__)
    app.config["SECRET_KEY"] = os.environ.get("SECRET_KEY", "dev-change-me")
    db = Database(db_path or os.environ.get("DATABASE_PATH", "passport.db"))
    auth = AuthService(db)
    auth.seed_defaults()
    apps = ApplicationService(db, PaymentGateway(), PoliceSystem(), NotificationService())
    applicant, admin, police = (ApplicantController(auth, apps), AdministratorController(auth, apps),
                                PoliceOfficerController(auth, apps))

    def token():
        return request.headers.get("Authorization", "").replace("Bearer ", "")

    def body():
        return request.get_json(silent=True) or {}

    for exc, code in [(ValidationError, 400), (AuthError, 401), (ForbiddenError, 403),
                      (NotFoundError, 404), (InvalidTransition, 409)]:
        app.register_error_handler(exc, lambda e, c=code: (jsonify(error=str(e)), c))

    # Applicant: Register, Login, Apply, Pay, Track, Receive
    @app.post("/api/applicants/register")
    def register(): return jsonify(applicant.register(body())), 201

    @app.post("/api/applicants/login")
    def applicant_login(): return jsonify(applicant.login(body()))

    @app.post("/api/applications")
    def apply(): return jsonify(applicant.apply_passport(token())), 201

    @app.post("/api/applications/<int:app_id>/pay")
    def pay(app_id):
        d = body()
        result = applicant.pay_fee(token(), app_id, d.get("cards") or [d.get("card")])
        return jsonify(result), (200 if result["success"] else 402)

    @app.get("/api/applications")
    def track(): return jsonify(applicant.track_application_status(token()))

    @app.post("/api/applications/<int:app_id>/receive")
    def receive(app_id): return jsonify(applicant.receive_passport(token(), app_id))

    # Passport Administrator
    @app.post("/api/admin/login")
    def admin_login(): return jsonify(admin.login(body()))

    @app.get("/api/admin/applications")
    def admin_apps(): return jsonify(admin.list_applications(token()))

    @app.get("/api/admin/accounts")
    def accounts(): return jsonify(admin.manage_user_accounts(token(), "list"))

    @app.post("/api/admin/accounts/police")
    def add_police(): return jsonify(admin.manage_user_accounts(token(), "create_police", data=body())), 201

    @app.delete("/api/admin/accounts/<role>/<int:account_id>")
    def del_account(role, account_id):
        return jsonify(admin.manage_user_accounts(token(), "delete", role=role, account_id=account_id))

    @app.post("/api/admin/applications/<int:app_id>/verify")
    def admin_verify(app_id):
        return jsonify(admin.verify_and_manage_applicant_details(token(), app_id, body()))

    @app.post("/api/admin/applications/<int:app_id>/forward")
    def forward(app_id): return jsonify(admin.forward_verified_document(token(), app_id))

    @app.post("/api/admin/applications/<int:app_id>/document-status")
    def doc_status(app_id): return jsonify(admin.update_document_verification_status(token(), app_id))

    @app.post("/api/admin/applications/<int:app_id>/generate")
    def generate(app_id): return jsonify(admin.generate_passport(token(), app_id))

    # Police Verification Officer
    @app.post("/api/police/login")
    def police_login(): return jsonify(police.login(body()))

    @app.get("/api/police/requests")
    def requests_(): return jsonify(police.receive_verification_requests(token()))

    @app.post("/api/police/applications/<int:app_id>/verify")
    def police_verify(app_id): return jsonify(police.verify(token(), app_id))

    @app.post("/api/police/applications/<int:app_id>/update")
    def police_update(app_id): return jsonify(police.update(token(), app_id))

    @app.get("/")
    def home():
        return render_template("index.html")

    return app


if __name__ == "__main__":
    create_app().run(debug=os.environ.get("FLASK_DEBUG") == "1")