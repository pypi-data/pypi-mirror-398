import json
import sys
import argparse
import os
import requests
from .generator import generate_data
import logging

logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
logger = logging.getLogger(__name__)

# Default schema with all types of fields and constraints
DEFAULT_SCHEMA = {
    "primitive_string": {"type": "string"},
    "string_with_regex": {"type": "string", "regex": "^[A-Z]{3}[0-9]{2}$"},
    "string_with_enum": {"type": "string", "enum": ["red", "green", "blue"]},
    "integer_basic": {"type": "integer"},
    "integer_with_range": {"type": "integer", "min": 10, "max": 100},
    "float_basic": {"type": "float"},
    "float_with_range": {"type": "float", "min": 0.5, "max": 99.9},
    "boolean_field": {"type": "boolean"},
    "uuid_field": {"type": "uuid"},
    "name_field": {"type": "name"},
    "email_field": {"type": "email"},
    "phone_field": {"type": "phone"},
    "date_field": {"type": "date", "min": "2000-01-01", "max": "2030-12-31"},
    "image_url_field": {"type": "image_url"},
    "file_url_field": {"type": "file_url"},
    "array_of_integers": {
        "type": "array",
        "length": 5,
        "items": {"type": "integer", "min": 1, "max": 50}
    },
    "array_of_strings": {
        "type": "array",
        "length": 3,
        "items": {"type": "string", "enum": ["apple", "banana", "cherry"]}
    },
    "nested_object": {
        "type": "object",
        "schema": {
            "street": {"type": "string"},
            "city": {"type": "string"},
            "zipcode": {"type": "integer", "min": 10000, "max": 99999},
            "coordinates": {
                "type": "object",
                "schema": {
                    "lat": {"type": "float", "min": -90, "max": 90},
                    "lng": {"type": "float", "min": -180, "max": 180}
                }
            }
        }
    }
}

# default_schema_path = os.path.join(os.getcwd(), "example-schema.json")
# default_save_path = os.path.join(os.getcwd(), "data-save.json")

repo_root = os.path.dirname(os.path.dirname(__file__))
default_schema_path = os.path.join(repo_root, "example-schema.json")
default_save_path = os.path.join(repo_root, "data-save.json")

def positive_int(value):
    try:
        ivalue = int(value)
    except ValueError:
        raise argparse.ArgumentTypeError("count must be an integer")
    if ivalue < 1:
        raise argparse.ArgumentTypeError("count must be >= 1")
    return ivalue

def ensure_schema_file(path):
    if not os.path.exists(path):
        try:
            with open(path, "w") as f:
                json.dump(DEFAULT_SCHEMA, f, indent=4)
            logger.info(f"File not found at {path}. Created example-schema.json.")
        except Exception as e:
            logger.error(f"Failed to create schema file: {e}")
            sys.exit(1)
    else:
        logger.info(f"Using existing schema file: {path}")

def generate_multiple(schema, count):
    unique_tracker = {}
    return [generate_data(schema, unique_tracker) for _ in range(count)]

def send_to_apis(data, urls):
    for url in urls:
        url = url.strip()
        if not url:
            continue
        try:
            response = requests.post(url, json=data)
            if response.status_code == 200:
                logger.info(f"Data successfully sent to {url}")
            else:
                logger.warning(f"Failed to send data to {url}. Status code: {response.status_code}, Response: {response.text}")
        except Exception as e:
            logger.error(f"Error sending data to {url}: {e}")

def run_from_stdin(no_print=False, save=None, api=None):
    try:
        input_data = json.load(sys.stdin)
        schema = input_data["schema"]
        count = input_data.get("count", 1)
        data = generate_multiple(schema, count)
        if api:
            send_to_apis(data, api)
        if save:
            with open(save, "w") as f:
                json.dump(data, f, indent=4)
            logger.info(f"Data saved to {save}")
        if not no_print:
            print(json.dumps(data))
    except Exception as e:
        logger.error(e)

def run_from_cli():
    parser = argparse.ArgumentParser(description="Mock Data Forge")
    parser.add_argument("-s", "--schema", type=str, default=default_schema_path, help="Path to schema JSON file (defaults to example-schema.json)")
    parser.add_argument("-c", "--count", type=positive_int, default=1, help="Number of objects to generate (defaults to 1)")
    parser.add_argument("-a", "--api", nargs="*", help="API endpoints to send generated data to, e.g., http://api1.com http://api2.com")
    parser.add_argument("-S", "--save", nargs="?", const=default_save_path, default=None, help="Save output to a file. Optional path (default: data-save.json)")
    parser.add_argument("-n", "--no-print", action="store_true", help="Do not print generated data to stdout")

    args = parser.parse_args()

    if args.api is not None and len(args.api) == 0:
        logger.error("--api flag provided but no URLs given")
        sys.exit(1)

    ensure_schema_file(args.schema)

    try:
        with open(args.schema) as f:
            schema = json.load(f)
    except Exception as e:
        logger.error(f"Failed to read schema file: {e}")
        sys.exit(1)

    data = generate_multiple(schema, args.count)
    if not args.no_print:
        print(json.dumps(data, indent=4))


    # Sends to APIs if provided
    if args.api:
        send_to_apis(data, args.api)

    # Save feature
    if args.save:
        try:
            with open(args.save,'w') as f:
                json.dump(data,f,indent=4)
            logger.info(f"Data saved to {args.save}")
        except Exception as e:
            logger.error(f"Failed to write in save file: {e}")
            sys.exit(1)

    if args.no_print and not args.save and not args.api:
        logger.warning("--no-print used with no --save or --api; output will be discarded")


def main():
    parser = argparse.ArgumentParser(add_help=False)
    parser.add_argument("-n", "--no-print", action="store_true")
    parser.add_argument("-S", "--save", nargs="?", const=default_save_path)
    parser.add_argument("-a", "--api", nargs="*")
    args, _ = parser.parse_known_args()

    if not sys.stdin.isatty():
        run_from_stdin(
            no_print=args.no_print,
            save=args.save,
            api=args.api
        )
    else:
        run_from_cli()

if __name__ == "__main__":
    main()