from dataclasses import asdict


def dump(obj):
    return asdict(obj)


class ApplicantController:
    def __init__(self, auth, apps):
        self.auth, self.apps = auth, apps

    def _me(self, token):
        return self.auth.user_from_token(token, "applicant")

    def register(self, data):
        return dump(self.auth.register(data))

    def login(self, data):
        token, user = self.auth.login("applicant", data.get("user_name"), data.get("password"))
        return {"token": token, "user": dump(user)}

    def apply_passport(self, token):
        return dump(self.apps.apply_passport(self._me(token)))

    def pay_fee(self, token, application_id, cards):
        ok, app = self.apps.pay_with_retry(self._me(token), application_id, cards)
        return {"success": ok, "application": dump(app)}

    def track_application_status(self, token):
        user = self.auth.user_from_token(token)
        return [dump(a) for a in self.apps.list_for(user)]

    def receive_passport(self, token, application_id):
        return dump(self.apps.receive_passport(self._me(token), application_id))


class AdministratorController:
    def __init__(self, auth, apps):
        self.auth, self.apps = auth, apps

    def _admin(self, token):
        return self.auth.user_from_token(token, "admin")

    def login(self, data):
        token, user = self.auth.login("admin", data.get("user_name"), data.get("password"))
        return {"token": token, "user": dump(user)}

    def manage_user_accounts(self, token, action, data=None, role=None, account_id=None):
        self._admin(token)
        if action == "list":
            return self.auth.list_accounts()
        if action == "create_police":
            return self.auth.create_police_officer(data or {})
        self.auth.delete_account(role, account_id)
        return {"deleted": True}

    def list_applications(self, token):
        return [dump(a) for a in self.apps.list_for(self._admin(token))]

    def verify_and_manage_applicant_details(self, token, application_id, updates=None):
        self._admin(token)
        return dump(self.apps.verify_and_manage_details(application_id, updates))

    def forward_verified_document(self, token, application_id):
        self._admin(token)
        return dump(self.apps.forward_verified_document(application_id))

    def update_document_verification_status(self, token, application_id):
        self._admin(token)
        return dump(self.apps.update_document_verification_status(application_id))

    def generate_passport(self, token, application_id):
        self._admin(token)
        return dump(self.apps.generate_passport(application_id))


class PoliceOfficerController:
    def __init__(self, auth, apps):
        self.auth, self.apps = auth, apps

    def _officer(self, token):
        return self.auth.user_from_token(token, "police")

    def login(self, data):
        token, user = self.auth.login("police", data.get("user_name"), data.get("password"))
        return {"token": token, "user": dump(user)}

    def receive_verification_requests(self, token):
        return [dump(a) for a in self.apps.list_for(self._officer(token))]

    def verify(self, token, application_id):
        self._officer(token)
        return {"verified": self.apps.verify(application_id)}

    def update(self, token, application_id):
        self._officer(token)
        return dump(self.apps.update_verification_status(application_id))