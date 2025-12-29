import os
from .crud_template import CRUD_TEMPLATE
from .formdata_template import FORMDATA_TEMPLATE

FILES = {
    "crud.py": CRUD_TEMPLATE,
    "formData.py": FORMDATA_TEMPLATE,
}


def generate_files():
    cwd = os.getcwd()

    for filename, content in FILES.items():
        path = os.path.join(cwd, filename)

        if os.path.exists(path):
            print(f"⚠️ {filename} already exists. Skipped.")
            continue

        with open(path, "w", encoding="utf-8") as f:
            f.write(content)

        print(f"✅ {filename} generated")
