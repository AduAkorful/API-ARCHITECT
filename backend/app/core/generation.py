import os
import shutil
import zipfile
from pathlib import Path
from typing import Dict, Any
from jinja2 import Environment, FileSystemLoader, TemplateError
import logging

logging.basicConfig(level=logging.INFO)
template_dir = Path(__file__).parent.parent.parent / "templates"
env = Environment(loader=FileSystemLoader(str(template_dir)))

def generate_flask_service(spec: Dict[str, Any], gcp_config: Dict[str, str]) -> str:
    # --- Robustness Fix: Validate the incoming spec ---
    service_name = spec.get("service_name")
    if not service_name:
        raise ValueError("AI-generated spec is missing the required 'service_name' field.")
    
    endpoint_spec = spec.get("endpoint")
    if not endpoint_spec:
        raise ValueError("AI-generated spec is missing the required 'endpoint' field.")
    # ----------------------------------------------------

    unique_id = os.urandom(4).hex()
    build_dir = Path("/tmp") / f"{service_name}_{unique_id}"
    source_dir = build_dir
    
    # --- Robustness Fix: Ensure cleanup happens even if errors occur ---
    try:
        source_dir.mkdir(parents=True, exist_ok=True)
        
        flask_template_dir = template_dir / "flask_template"
        
        context = {
            "endpoint": endpoint_spec,
            "storage": spec.get("storage"),
            "service": {"name": service_name},
            "gcp": gcp_config
        }

        for template_file in flask_template_dir.rglob("*.j2"):
            relative_path = template_file.relative_to(flask_template_dir)
            
            if relative_path.parts and relative_path.parts[0] == 'app':
                output_relative_path = Path(*relative_path.parts[1:])
            else:
                output_relative_path = relative_path
                
            output_file = source_dir / output_relative_path.with_suffix("")
            
            output_file.parent.mkdir(parents=True, exist_ok=True)
            template_name = template_file.relative_to(template_dir).as_posix()
            
            try:
                template = env.get_template(template_name)
                rendered_content = template.render(context)
                with open(output_file, "w") as f:
                    f.write(rendered_content)
            except TemplateError as e:
                raise IOError(f"Failed to render template {template_name}: {e}")

        # Create zip at parent level (not inside source_dir which will be deleted)
        zip_path = Path("/tmp") / f"{service_name}_{unique_id}.zip"
        with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
            for root, _, files in os.walk(source_dir):
                for file in files:
                    file_path = Path(root) / file
                    archive_path = file_path.relative_to(source_dir)
                    zipf.write(file_path, archive_path)
        
        return str(zip_path)
    finally:
        # Clean up the source directory (but not the zip file which is at parent level)
        if source_dir.exists():
            shutil.rmtree(source_dir)
    # -----------------------------------------------------------------