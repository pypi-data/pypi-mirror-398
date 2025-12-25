import random
from faker import Faker
import uuid
import rstr
from datetime import datetime, timedelta

fake = Faker()

def simple_type(t):
    # phone_number=fake.phone_number()
    return {
        "string": fake.word(),
        "boolean": random.choice([True, False]),
        "uuid": str(uuid.uuid4()),
        "name": fake.name(),
        "email": fake.email(),
        # "phone": "".join(filter(str.isdigit, phone_number)),
        "phone": fake.phone_number(),
        "date": str(fake.date()),
        "image_url": f"https://picsum.photos/200/300?random={uuid.uuid4()}",
        "file_url": f"https://example.com/file_{uuid.uuid4()}.txt"
    }.get(t, None)

def generate_unique(field_name, field_info, unique_tracker):
    if field_name not in unique_tracker:
        unique_tracker[field_name] = set()

    while True:
        val = generate_value(field_info, unique_tracker)
        if val not in unique_tracker[field_name]:
            unique_tracker[field_name].add(val)
            return val

def generate_value(field, unique_tracker):
    t = field.get("type") if isinstance(field, dict) else field

    
    # Regex
    if isinstance(field, dict) and "regex" in field:
        return rstr.xeger(field["regex"])
    # Enum
    if isinstance(field, dict) and "enum" in field:
        return random.choice(field["enum"])

    if t in ["string", "boolean", "uuid", "name", "email", "phone", "date", "image_url", "file_url"]:
        return simple_type(t)

    if t == "integer":
        return random.randint(field.get("min", 0), field.get("max", 100))
    elif t == "float":
        return random.uniform(field.get("min", 0.0), field.get("max", 100.0))
    elif t == "date":
        min_date = datetime.strptime(field.get("min", "2000-01-01"), "%Y-%m-%d")
        max_date = datetime.strptime(field.get("max", "2100-12-31"), "%Y-%m-%d")
        delta_days = (max_date - min_date).days
        random_days = random.randint(0, delta_days)
        return str(min_date + timedelta(days=random_days))
    elif t == "array":
        length = field.get("length", 3)
        return [generate_value(field["items"], unique_tracker) for _ in range(length)]
    elif t == "object":
        return generate_data(field["schema"], unique_tracker)

    return None

def generate_data(schema: dict, unique_tracker=None) -> dict:
    if unique_tracker is None:
        unique_tracker = {} #dict to track unique fields across multiple objects

    result = {}
    for field_name, field_info in schema.items():
        if isinstance(field_info, dict):
            if field_info.get("unique", False):
                result[field_name] = generate_unique(field_name, field_info, unique_tracker)
            else:
                result[field_name] = generate_value(field_info, unique_tracker)
        else:
            result[field_name] = simple_type(field_info)
    return result