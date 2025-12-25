# Mock Data Forge (CLI)

**Mock Data Forge** is a powerful command-line tool to generate mock JSON data based on custom schemas. It supports saving to files, sending data to APIs, and enforcing constraints for realistic and structured test data.

---

## Features

- **Generate Mock Data**: Quickly produce JSON objects based on your schema.
- **Supports Multiple Data Types**:
  1. **Primitive Data Types**: `string`, `integer`, `float`, `boolean`
  2. **Semantic Data Types**: `name`, `email`, `phone`, `date`
  3. **File Data Types**: `image_url`, `file_url`
  4. **Complex Data Types**: `object`, `array`
- **Constraints & Logic**:
  - **Range**: Set minimum and maximum for numbers.
  - **Choice/Enum**: Pick values from a specific list.
  - **Regex**: Generated strings match a regex pattern.
- **Automated API Support**: If you provide an API endpoint, the generator will automatically send the generated data.

---

## Quick Start

Install the CLI via `pip`:

```bash
pip install mock-data-forge
```

## Usage
Generate data with default schema
```bash
mock-data
```
Specify a custom schema file
```bash
mock-data -s path/to/schema.json
```
Generate multiple objects
```bash
mock-data -c 10
```
Save output to a file
```bash
mock-data -S output.json
```
Send data to API endpoints
```bash
mock-data -a http://example.com/api1 http://example.com/api2
```
Combine options
```bash
mock-data -s schema.json -c 5 -S output.json -a http://example.com/api -n
```

- -n / --no-print prevents output from being printed to the console.

## Options:

`-s, --schema` : Path to schema JSON file (default: example-schema.json)  
`-c, --count` : Number of objects to generate (default: 1)  
`-a, --api` : API endpoints to send the generated data  
`-S, --save` : Save output to a file (default: data-save.json)  
`-n, --no-print` : Do not print generated data to stdout

## Example Schema
```json
{
  "name": { "type": "name" },
  "email": { "type": "email" },
  "age": { "type": "integer", "min": 18, "max": 65 },
  "tags": { "type": "array", "length": 3, "items": { "type": "string", "enum": ["red","green","blue"] } }
}
```

## Repository Structure
```bash
mock-data-forge/  
├── mock_data_forge/  
│   ├── __init__.py
│   ├── __main__.py 
│   └── generator.py  
├── README.md  
├── example-schema.json  
├── pyproject.toml  
├── LICENSE
└── MANIFEST.in
```

## Logging
Mock Data Forge uses Python’s built-in logging module. By default, it logs info and warning messages to the console.

## GUI Version
- If you prefer a graphical interface, you can check out the GUI version of Mock Data Forge:  
[Mock Data Forge GUI + CLI on GitHub](https://github.com/HattoriMan/Mock-Data-Forge)
- Clone the repo and follow its README to set up the GUI.

## License
MIT License © 2025 HattoriMan