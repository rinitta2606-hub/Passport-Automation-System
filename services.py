import logging
import secrets

from models import (Application, ApplicationState as S, Applicant, Payment,
                    ROLE_CLASSES, ROLE_TABLES)
from utils import (AuthError, ForbiddenError, InvalidTransition, NotFoundError,
                   ValidationError, hash_password, require, validate_registration, verify_password)

log = logging.getLogger("notifications")
FEE = 1500


class StateMachine:
    TRANSITIONS = {
        (S.PAYMENT_PENDING, "pay_success"): S.APPLICATION_SUBMITTED,
        (S.PAYMENT_PENDING, "pay_failed"): S.PAYMENT_PENDING,           # retry loop
        (S.APPLICATION_SUBMITTED, "admin_verify"): S.UNDER_ADMIN_VERIFICATION,
        (S.UNDER_ADMIN_VERIFICATION, "forward"): S.UNDER_POLICE_VERIFICATION,
        (S.UNDER_POLICE_VERIFICATION, "police_update"): S.POLICE_VERIFIED,
        (S.POLICE_VERIFIED, "generate"): S.PASSPORT_GENERATED,
        (S.PASSPORT_GENERATED, "receive"): S.DELIVERED,
    }

    @classmethod
    def next(cls, state, event):
        try:
            return cls.TRANSITIONS[(state, event)]
        except KeyError:
            raise InvalidTransition(f"Event '{event}' is not allowed in state '{state.value}'")


class PaymentGateway:
    """External system: Payment Processing. Card ending 0000 is declined (demo rule)."""

    def process(self, card_number, amount):
        digits = str(card_number or "").replace(" ", "")
        return digits.isdigit() and len(digits) == 16 and not digits.endswith("0000")


class PoliceSystem:
    """External system: Police Verification. Accepts applicants with a complete record."""

    def verify(self, applicant):
        return bool(applicant.name and applicant.address and applicant.dob)


class NotificationService:
    """Delivery/Notification component."""

    def __init__(self):
        self.sent = []

    def notify(self, applicant_id, message):
        self.sent.append((applicant_id, message))
        log.info("notify applicant %s: %s", applicant_id, message)


class AuthService:
    """Registration & Login component."""

    def __init__(self, db):
        self.db = db
        self.sessions = {}

    def seed_defaults(self):
        if not self.db.one("SELECT 1 FROM administrators"):
            self.db.execute("INSERT INTO administrators (user_name, password_hash) VALUES (?,?)",
                            ("admin", hash_password("admin123")))
        if not self.db.one("SELECT 1 FROM police_officers"):
            self.db.execute("INSERT INTO police_officers (user_name, password_hash) VALUES (?,?)",
                            ("police1", hash_password("police123")))

    def register(self, d):
        validate_registration(d)
        if self.db.one("SELECT 1 FROM applicants WHERE user_name=? OR email=?", (d["user_name"], d["email"])):
            raise ValidationError("user_name or email already registered")
        new_id = self.db.execute(
            "INSERT INTO applicants (name, father_name, dob, address, email, phone_no, user_name, password_hash)"
            " VALUES (?,?,?,?,?,?,?,?)",
            (d["name"].strip(), d["father_name"].strip(), d["dob"], d["address"].strip(),
             d["email"].strip(), d["phone_no"].strip(), d["user_name"].strip(), hash_password(d["password"])))
        return Applicant.from_row(self.db.one("SELECT * FROM applicants WHERE id=?", (new_id,)))

    def login(self, role, user_name, password):
        row = self.db.one(f"SELECT * FROM {ROLE_TABLES[role]} WHERE user_name=?", (user_name or "",))
        if not row or not verify_password(password or "", row["password_hash"]):
            raise AuthError("Invalid user name or password")
        token = secrets.token_hex(16)
        self.sessions[token] = (role, row["id"])
        return token, ROLE_CLASSES[role].from_row(row)

    def user_from_token(self, token, role=None):
        if token not in self.sessions:
            raise AuthError("Login required")
        r, uid = self.sessions[token]
        if role and r != role:
            raise ForbiddenError("Not permitted for your role")
        row = self.db.one(f"SELECT * FROM {ROLE_TABLES[r]} WHERE id=?", (uid,))
        if not row:
            raise AuthError("Account no longer exists")
        return ROLE_CLASSES[r].from_row(row)

    # Manage User Accounts (administrator)
    def list_accounts(self):
        out = []
        for role in ROLE_TABLES:
            for r in self.db.query(f"SELECT id, user_name FROM {ROLE_TABLES[role]}"):
                out.append({"role": role, **r})
        return out

    def create_police_officer(self, d):
        require(d, ["user_name", "password"])
        if self.db.one("SELECT 1 FROM police_officers WHERE user_name=?", (d["user_name"],)):
            raise ValidationError("user_name already exists")
        new_id = self.db.execute("INSERT INTO police_officers (user_name, password_hash) VALUES (?,?)",
                                 (d["user_name"], hash_password(d["password"])))
        return {"role": "police", "id": new_id, "user_name": d["user_name"]}

    def delete_account(self, role, account_id):
        if role not in ("applicant", "police"):
            raise ValidationError("Only applicant or police accounts can be deleted")
        if not self.db.one(f"SELECT 1 FROM {ROLE_TABLES[role]} WHERE id=?", (account_id,)):
            raise NotFoundError("Account not found")
        self.db.execute(f"DELETE FROM {ROLE_TABLES[role]} WHERE id=?", (account_id,))
        self.sessions = {t: v for t, v in self.sessions.items() if v != (role, account_id)}


class ApplicationService:
    """Application Management, Admin/Police Verification, Payment and Passport Generation components."""

    EDITABLE = ("name", "father_name", "dob", "address", "phone_no")

    def __init__(self, db, gateway, police_system, notifier):
        self.db, self.gateway, self.police, self.notifier = db, gateway, police_system, notifier

    def _get(self, application_id):
        row = self.db.one("SELECT * FROM applications WHERE application_id=?", (application_id,))
        if not row:
            raise NotFoundError("Application not found")
        app = Application.from_row(row)
        app.payments = [Payment.from_row(p) for p in
                        self.db.query("SELECT * FROM payments WHERE application_id=?", (application_id,))]
        return app

    def _applicant(self, applicant_id):
        return Applicant.from_row(self.db.one("SELECT * FROM applicants WHERE id=?", (applicant_id,)))

    def _fire(self, app, event):
        app.state = StateMachine.next(app.state, event)
        self.db.execute("UPDATE applications SET state=? WHERE application_id=?",
                        (app.state.value, app.application_id))

    # --- Applicant ---
    def apply_passport(self, applicant):
        if any(a["state"] != S.DELIVERED.value for a in
               self.db.query("SELECT state FROM applications WHERE applicant_id=?", (applicant.id,))):
            raise ValidationError("You already have an application in progress")
        new_id = self.db.execute("INSERT INTO applications (applicant_id, state) VALUES (?,?)",
                                 (applicant.id, S.PAYMENT_PENDING.value))
        return self._get(new_id)

    def pay_application_fee(self, applicant, application_id, card):
        app = self._get(application_id)
        if app.applicant_id != applicant.id:
            raise ForbiddenError("Not your application")
        StateMachine.next(app.state, "pay_failed")            # only valid in PAYMENT_PENDING
        ok = self.gateway.process(card, FEE)
        self.db.execute("INSERT INTO payments (application_id, amount, status, reference) VALUES (?,?,?,?)",
                        (application_id, FEE, "success" if ok else "failed",
                         secrets.token_hex(8) if ok else None))
        self._fire(app, "pay_success" if ok else "pay_failed")
        if ok:
            self.notifier.notify(applicant.id, "Payment successful; application submitted")
        return ok, self._get(application_id)

    def pay_with_retry(self, applicant, application_id, cards):
        """Activity diagram loop: Pay -> [failed] Retry Payment -> ... -> [successful]."""
        for card in cards:
            ok, app = self.pay_application_fee(applicant, application_id, card)
            if ok:
                return True, app
        return False, self._get(application_id)

    def list_for(self, user):
        if user.ROLE == "applicant":
            rows = self.db.query("SELECT application_id FROM applications WHERE applicant_id=?", (user.id,))
        elif user.ROLE == "police":
            rows = self.db.query("SELECT application_id FROM applications WHERE state IN (?,?)",
                                 (S.UNDER_POLICE_VERIFICATION.value, S.POLICE_VERIFIED.value))
        else:
            rows = self.db.query("SELECT application_id FROM applications")
        return [self._get(r["application_id"]) for r in rows]

    def track(self, user, application_id):
        app = self._get(application_id)
        if user.ROLE == "applicant" and app.applicant_id != user.id:
            raise ForbiddenError("Not your application")
        return app

    def receive_passport(self, applicant, application_id):
        app = self.track(applicant, application_id)
        self._fire(app, "receive")
        return app

    # --- Administrator ---
    def verify_and_manage_details(self, application_id, updates=None):
        app = self._get(application_id)
        updates = {k: str(v).strip() for k, v in (updates or {}).items() if k in self.EDITABLE and str(v).strip()}
        for col, val in updates.items():
            self.db.execute(f"UPDATE applicants SET {col}=? WHERE id=?", (val, app.applicant_id))
        self._fire(app, "admin_verify")
        return app

    def forward_verified_document(self, application_id):
        app = self._get(application_id)
        self._fire(app, "forward")
        return app

    def update_document_verification_status(self, application_id):
        app = self._get(application_id)
        if app.state != S.POLICE_VERIFIED:
            raise InvalidTransition("Document status can be updated only after police verification")
        self.db.execute("UPDATE applications SET document_status='approved' WHERE application_id=?", (application_id,))
        return self._get(application_id)

    def generate_passport(self, application_id):
        app = self._get(application_id)
        if app.document_status != "approved":
            raise InvalidTransition("Document verification status must be approved first")
        self._fire(app, "generate")
        number = "P" + secrets.token_hex(4).upper()
        self.db.execute("UPDATE applications SET passport_number=? WHERE application_id=?", (number, application_id))
        self.notifier.notify(app.applicant_id, f"Passport {number} generated")
        return self._get(application_id)

    # --- Police officer ---
    def verify(self, application_id):
        app = self._get(application_id)
        if app.state != S.UNDER_POLICE_VERIFICATION:
            raise InvalidTransition("Application is not awaiting police verification")
        return self.police.verify(self._applicant(app.applicant_id))

    def update_verification_status(self, application_id):
        if not self.verify(application_id):
            raise ValidationError("Police verification failed")
        app = self._get(application_id)
        self._fire(app, "police_update")
        return app