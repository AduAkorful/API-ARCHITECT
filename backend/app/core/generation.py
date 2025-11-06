import os
import shutil
import zipfile
from pathlib import Path
from typing import Dict, Any
from jinja2 import Environment, FileSystemLoader
import logging

# Set up basic logging
logging.basicConfig(level=logging.INFO)

template_dir = Path(__file__).parent.parent.parent / "templates"
env = Environment(loader=FileSystemLoader(str(template_dir)))
logging.info(f"Template directory set to: {template_dir}")

def generate_flask_service(spec: Dict, gcp_config: Dict) -> str:
    service_name = spec["service_name"]
    logging.info(f"Starting generation for service: {service_name}")
    
    unique_id = os.urandom(4).hex()
    build_dir = Path("/tmp") / f"{service_name}_{unique_id}"
    source_dir = build_dir / "source"
    
    if build_dir.exists():
        shutil.rmtree(build_dir)
    source_dir.mkdir(parents=True, exist_ok=True)
    logging.info(f"Created source directory: {source_dir}")
    
    flask_template_dir = template_dir / "flask_template"
    
    context = {"spec": spec, "gcp": gcp_config} # Simplified context for logging
    logging.info(f"Using context: {context}")
    
    rendered_files_count = 0
    try:
        template_files = list(flask_template_dir.rglob("*.j2"))
        if not template_files:
            logging.error(f"FATAL: No .j2 template files found in {flask_template_dir}")
            raise Exception(f"No .j2 files found in {flask_template_dir}")

        for template_file in template_files:
            logging.info(f"Processing template file: {template_file}")
            
            relative_path = template_file.relative_to(flask_template_dir)
            output_file = source_dir / relative_path.with_suffix("")
            
            template_name = template_file.relative_to(template_dir).as_posix()
            
            logging.info(f"  - Template name for Jinja: {template_name}")
            logging.info(f"  - Output file path: {output_file}")
            
            template = env.get_template(template_name)
            rendered_content = template.render(spec) # Pass spec directly
            
            output_file.parent.mkdir(parents=True, exist_ok=True)
            with open(output_file, "w") as f:
                f.write(rendered_content)
            
            rendered_files_count += 1
            logging.info(f"  - Successfully rendered and wrote file.")
    
    except Exception as e:
        logging.error(f"FATAL: An error occurred during template rendering: {e}", exc_info=True)
        raise

    logging.info(f"Total files rendered: {rendered_files_count}")

    zip_path = build_dir / f"{service_name}.zip"
    logging.info(f"Creating zip file at: {zip_path}")
    
    with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
        files_in_source = list(source_dir.rglob("*"))
        if not files_in_source:
             logging.error(f"FATAL: Source directory {source_dir} is empty before zipping.")
        for file_path in files_in_source:
            if file_path.is_file():
                archive_path = file_path.relative_to(source_dir)
                zipf.write(file_path, archive_path)
                logging.info(f"  - Added to zip: {archive_path}")

    return str(zip_path)