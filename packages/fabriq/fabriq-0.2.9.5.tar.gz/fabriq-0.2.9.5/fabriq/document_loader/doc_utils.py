import re
import subprocess
import os
import platform
from typing import Any
import whisper

def convert_to_pdf(source_path, pdf_path) -> bool:
    try:
        libreoffice_path = get_office_path()
        subprocess.run([libreoffice_path, '--headless', '--convert-to', 'pdf', source_path, '--outdir', os.path.dirname(pdf_path)])
        return True
    except Exception as e:
        print("Error while converting to PDF:",e)
        return False
    
def get_office_path() -> str:
    platform_name = platform.system().lower()
    if platform_name == 'linux':
        return '/opt/libreoffice7.1/program/soffice'
    elif platform_name == 'darwin':
        return '/Applications/LibreOffice.app/Contents/MacOS/soffice'

def generate_description(image: str, llm: Any) -> str:
    system_prompt = "You are an expert in analyzing visual content."
    prompt = f"generate a detailed description to be part of a document for the following image:"
    description = llm.generate(prompt=prompt,system_prompt=system_prompt,image=image)
    return description

def replace_image(markdown_text: str = "",llm: Any = None) -> str:
    regex_pattern = r'!\[[^\]]*\]\(data:image/[a-zA-Z0-9+\-]+;base64,[a-zA-Z0-9+/]+={0,2}\)'
    match = re.search(regex_pattern, markdown_text)

    def replacer(match):
        full_markdown_tag = match.group(0)
        image = "data:image/png;base64,"+full_markdown_tag.split("base64,")[-1]
        description = generate_description(image, llm)
        return "\n[**IMAGE**:\n"+description+"]"
    
    if match:
        return re.sub(regex_pattern, replacer, markdown_text)
    else:
        return markdown_text
    
def transcribe_audio(file_path: str) -> str:
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"The file {file_path} does not exist.")
    
    model = whisper.load_model("small",download_root="assets/model/whisper")
    result = model.transcribe(file_path)
    metadata = {"segments": [{"start": segment["start"], "end": segment["end"], "text": segment["text"].strip()} for segment in result["segments"]]}
    return result["text"].strip(), metadata