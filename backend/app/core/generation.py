import os
import shutil
import zipfile
from pathlib import Path
from typing import Dict, Any
from jinja2 import Environment, FileSystemLoader

# Setup Jinja2 environment
template_dir = Path(__file__).parent.parent.parent / "templates"
env = Environment(loader=FileSystemLoader(str(template_dir)))

def generate_flask_service(spec: Dict[str, Any], gcp_config: Dict[str, str]) -> str:
    """
    Generates a Flask service source code from a spec, zips it, and returns the path.
    """
    service_name = spec["service_name"]
    output_dir = Path("/tmp") / service_name
    source_dir = output_dir / "source"
    
    if output_dir.exists():
        shutil.rmtree(output_dir)
    source_dir.mkdir(parents=True, exist_ok=True)
    
    flask_template_dir = template_dir / "flask_template"
    
    context = {
        "endpoint": spec["endpoint"],
        "storage": spec.get("storage"),
        "service": {"name": service_name},
        "gcp": gcp_config
    }

    # --- SIMPLIFIED AND CORRECTED LOGIC ---
    # Iterate through all .j2 templates.
    for template_file in flask_template_dir.rglob("*.j2"):
        # Get the path of the template relative to its own root directory.
        # e.g., 'cloudbuild.yaml.j2' or 'app/main.py.j2'
        relative_path = template_file.relative_to(flask_template_dir)
        
        # Determine the final output path in the 'source' directory.
        # e.g., 'source/cloudbuild.yaml' or 'source/app/main.py'
        output_file = source_dir / relative_path.with_suffix("") # Remove .j2
        
        # Ensure the destination directory exists (e.g., create the 'app' subfolder).
        output_file.parent.mkdir(parents=True, exist_ok=True)
        
        # Load the template using its full path relative to the main 'templates' dir.
        template_name = template_file.relative_to(template_dir).as_posix()
        template = env.get_template(template_name)
        
        # Render and write the file.
        with open(output_file, "w") as f:
            f.write(template.render(context))

    # Create a zip file of the generated source code.
    zip_path = output_dir / f"{service_name}.zip"
    with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
        for root, _, files in os.walk(source_dir):
            for file in files:
                file_path = Path(root) / file
                archive_path = file_path.relative_to(source_dir)
                zipf.write(file_path, archive_path)

    shutil.rmtree(source_dir)

    return str(zip_path)