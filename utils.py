import hashlib
import hmac
import os
from datetime import date


class ValidationError(Exception): pass
class AuthError(Exception): pass
class ForbiddenError(Exception): pass
class NotFoundError(Exception): pass
class InvalidTransition(Exception): pass


def hash_password(password, salt=None):
    salt = salt or os.urandom(16).hex()
    digest = hashlib.pbkdf2_hmac("sha256", password.encode(), salt.encode(), 100_000).hex()
    return f"{salt}${digest}"


def verify_password(password, stored):
    salt = stored.split("$")[0]
    return hmac.compare_digest(hash_password(password, salt), stored)


def require(data, fields):
    missing = [f for f in fields if not str(data.get(f, "")).strip()]
    if missing:
        raise ValidationError("Missing fields: " + ", ".join(missing))


def validate_registration(data):
    require(data, ["name", "father_name", "dob", "address", "email", "phone_no", "user_name", "password"])
    try:
        date.fromisoformat(data["dob"])
    except ValueError:
        raise ValidationError("dob must be YYYY-MM-DD")
    if "@" not in data["email"]:
        raise ValidationError("Invalid email")
    if not data["phone_no"].replace("+", "").isdigit():
        raise ValidationError("Invalid phone_no")
    if len(data["password"]) < 6:
        raise ValidationError("Password must be at least 6 characters")