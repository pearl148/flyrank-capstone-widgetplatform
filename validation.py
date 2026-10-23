from email_validator import validate_email, EmailNotValidError

def validate_submission_data(fields_def: dict, data: dict) -> dict:
    unknown = set(data) - set(fields_def)
    if unknown:
        raise ValueError(f"Unknown field(s): {', '.join(sorted(unknown))}")

    cleaned = {}
    for name, rules in fields_def.items():
        value = data.get(name)

        # empty: reject if required, otherwise skip
        if value is None or (isinstance(value, str) and not value.strip()):
            if rules.get("required"):
                raise ValueError(f"Missing required field: {name}")
            continue

        if not isinstance(value, str):
            raise ValueError(f"Field {name} must be a string")
        value = value.strip()
        if len(value) > 1000:
            raise ValueError(f"Field {name} exceeds 1000 characters")

        if rules.get("type") == "email":
            try:
                value = validate_email(value, check_deliverability=False).normalized
            except EmailNotValidError:
                raise ValueError(f"Field {name} must be a valid email address")

        cleaned[name] = value
    return cleaned