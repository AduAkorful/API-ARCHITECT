import os
import shutil
import zipfile
from pathlib import Path
from typing import Dict, Any
from jinja2 import Environment, FileSystemLoader
import tempfile

template_dir = Path(__file__).parent.parent.parent / "templates"
env = Environment(loader=FileSystemLoader(str(template_dir)))

def generate_flask_service(spec: Dict[str, Any], gcp_config: Dict[str, str]) -> str:
    service_name = spec["service_name"]
    
    # Create a persistent temporary file path for the final zip file
    zip_path_obj = Path(tempfile.gettempdir()) / f"{service_name}_{os.urandom(4).hex()}.zip"

    # Use a temporary directory that gets cleaned up automatically
    with tempfile.TemporaryDirectory() as temp_dir:
        source_dir = Path(temp_dir) / "source"
        source_dir.mkdir()

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

        # --- CRITICAL FIX: Create the zip file *inside* the temporary directory block ---
        with zipfile.ZipFile(zip_path_obj, 'w', zipfile.ZIP_DEFLATED) as zipf:
            for root, _, files in os.walk(source_dir):
                for file in files:
                    file_path = Path(root) / file
                    archive_path = file_path.relative_to(source_dir)
                    zipf.write(file_path, archive_path)
    
    # The source_dir is now automatically deleted, but the zip file remains.
    return str(zip_path_obj)