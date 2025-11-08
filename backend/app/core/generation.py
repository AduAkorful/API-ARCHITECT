import os
import shutil
import zipfile
from pathlib import Path
from typing import Dict, Any
from jinja2 import Environment, FileSystemLoader
import logging

logging.basicConfig(level=logging.INFO)

template_dir = Path(__file__).parent.parent.parent / "templates"
env = Environment(loader=FileSystemLoader(str(template_dir)))

def generate_flask_service(spec: Dict[str, Any], gcp_config: Dict[str, str]) -> str:
    service_name = spec["service_name"]
    logging.info(f"Starting generation for service: {service_name}")
    
    unique_id = os.urandom(4).hex()
    build_dir = Path("/tmp") / f"{service_name}_{unique_id}"
    source_dir = build_dir / "source"
    
    source_dir.mkdir(parents=True, exist_ok=True)
    
    flask_template_dir = template_dir / "flask_template"
    
    context = {
        "endpoint": spec["endpoint"],
        "storage": spec.get("storage"),
        "service": {"name": service_name},
        "gcp": gcp_config
    }

    try:
        for template_file in flask_template_dir.rglob("*.j2"):
            relative_path = template_file.relative_to(flask_template_dir)
            output_file = source_dir / relative_path.with_suffix("")

            
            output_file.parent.mkdir(parents=True, exist_ok=True)
            
            template_name = template_file.relative_to(template_dir).as_posix()
            template = env.get_template(template_name)
            rendered_content = template.render(context)
            
            with open(output_file, "w") as f:
                f.write(rendered_content)
    
    except Exception as e:
        logging.error(f"FATAL: An error occurred during template rendering: {e}", exc_info=True)
        raise

    zip_path = build_dir / f"{service_name}.zip"
    
    with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
        for root, _, files in os.walk(source_dir):
            for file in files:
                file_path = Path(root) / file
                archive_path = file_path.relative_to(source_dir)
                zipf.write(file_path, archive_path)
    
    shutil.rmtree(source_dir)

    logging.info(f"Successfully created zip file for {service_name} at {zip_path}")
    return str(zip_path)