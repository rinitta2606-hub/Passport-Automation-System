from dataclasses import dataclass, field, fields
from enum import Enum
from typing import List, Optional


class ApplicationState(str, Enum):
    PAYMENT_PENDING = "payment_pending"
    APPLICATION_SUBMITTED = "application_submitted"
    UNDER_ADMIN_VERIFICATION = "under_admin_verification"
    UNDER_POLICE_VERIFICATION = "under_police_verification"
    POLICE_VERIFIED = "police_verified"
    PASSPORT_GENERATED = "passport_generated"
    DELIVERED = "delivered"


def _build(cls, row):
    names = {f.name for f in fields(cls)}
    return cls(**{k: v for k, v in row.items() if k in names})


@dataclass
class User:
    id: int
    user_name: str

    @classmethod
    def from_row(cls, row):
        return _build(cls, row)


@dataclass
class Applicant(User):
    name: str
    father_name: str
    dob: str
    address: str
    email: str
    phone_no: str
    ROLE = "applicant"


@dataclass
class PassportAdministrator(User):
    ROLE = "admin"


@dataclass
class PoliceOfficer(User):   # "ID" attribute of the class diagram is `id`
    ROLE = "police"


@dataclass
class Payment:
    id: int
    application_id: int
    amount: int
    status: str
    reference: Optional[str] = None

    @classmethod
    def from_row(cls, row):
        return _build(cls, row)


@dataclass
class Application:       # Applicant 1 --- 0..* Application ; Application 1 --- 1..* Payment
    application_id: int
    applicant_id: int
    state: ApplicationState
    document_status: str
    passport_number: Optional[str] = None
    created_at: str = ""
    payments: List[Payment] = field(default_factory=list)

    @classmethod
    def from_row(cls, row):
        row = dict(row)
        row["state"] = ApplicationState(row["state"])
        return _build(cls, row)


ROLE_CLASSES = {"applicant": Applicant, "admin": PassportAdministrator, "police": PoliceOfficer}
ROLE_TABLES = {"applicant": "applicants", "admin": "administrators", "police": "police_officers"}