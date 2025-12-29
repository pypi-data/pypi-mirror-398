import os
from .crud_template import CRUD_TEMPLATE
from .formdata_template import FORMDATA_TEMPLATE


def generate_files():
    files = {
        "crud.py": CRUD_TEMPLATE,
        "formData.py": FORMDATA_TEMPLATE,
    }

    for name, content in files.items():
        if os.path.exists(name):
            print(f"⚠️ {name} exists, skipped")
            continue

        with open(name, "w", encoding="utf-8") as f:
            f.write(content)

        print(f"✅ {name} created")


def cli():
    print("🚀 Generating files...")
    generate_files()
