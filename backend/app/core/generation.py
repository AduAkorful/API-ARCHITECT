import os
import shutil
import zipfile
from pathlib import Path
from typing import Dict, Any
from jinja2 import Environment, FileSystemLoader
import tempfile # <-- IMPORT THE CORRECT LIBRARY

template_dir = Path(__file__).parent.parent.parent / "templates"
env = Environment(loader=FileSystemLoader(str(template_dir)))

def generate_flask_service(spec: Dict[str, Any], gcp_config: Dict[str, str]) -> str:
    """
    Generates a Flask service source code from a spec, zips it, and returns the path.
    """
    service_name = spec["service_name"]
    # --- ROBUST FIX: Use tempfile to create a temporary directory ---
    with tempfile.TemporaryDirectory() as temp_dir:
        output_dir = Path(temp_dir)
        source_dir = output_dir / "source"
        source_dir.mkdir(parents=True, exist_ok=True)
        
        flask_template_dir = template_dir / "flask_template"
        
        context = {
            "endpoint": spec["endpoint"],
            "storage": spec.get("storage"),
            "service": {"name": service_name},
            "gcp": gcp_config
        }

        for template_file in flask_template_dir.rglob("*.j2"):
            relative_path = template_file.relative_to(flask_template_dir)
            output_file = source_dir / relative_path.with_suffix("")
            output_file.parent.mkdir(parents=True, exist_ok=True)
            template_name = template_file.relative_to(template_dir).as_posix()
            template = env.get_template(template_name)
            with open(output_file, "w") as f:
                f.write(template.render(context))

        # Create the zip file inside a persistent temp location
        # because the TemporaryDirectory will be deleted.
        zip_path_obj = Path(tempfile.gettempdir()) / f"{service_name}.zip"

        with zipfile.ZipFile(zip_path_obj, 'w', zipfile.ZIP_DEFLATED) as zipf:
            for root, _, files in os.walk(source_dir):
                for file in files:
                    file_path = Path(root) / file
                    archive_path = file_path.relative_to(source_dir)
                    zipf.write(file_path, archive_path)

        return str(zip_path_obj)