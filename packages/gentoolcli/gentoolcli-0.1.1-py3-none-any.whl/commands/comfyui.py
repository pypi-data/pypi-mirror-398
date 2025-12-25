import click
import json
import urllib.request
import time
import random
import os

from config import SECRET_TOOL
from commands.auth import get_valid_user

COMFYUI_URL = "https://comfyui.cidplatform.com"

WORKFLOW_PATH = os.path.join(os.path.dirname(__file__), "..", "workflows", "sd15image.json")

def get_firebase():
    import pyrebase
    config_path = os.path.join(os.path.dirname(__file__), "firebase_config.json")
    with open(config_path) as f:
        config = json.load(f)
    return pyrebase.initialize_app(config)

@click.command()
@click.option("-p", "--prompt", required=True, help="Texte du prompt")
def comfyui(prompt):
    user = get_valid_user(get_firebase())
    if not user:
        click.echo("Erreur : vous devez être connecté. Utilisez 'gentool login'.")
        return
    
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {SECRET_TOOL}"
    }
    
    with open(WORKFLOW_PATH, "r") as f:
        workflow = json.load(f)
    
    for node in workflow.values():
        if node.get("class_type") == "KSampler":
            node["inputs"]["seed"] = random.randint(0, 2**53)
        if node.get("class_type") == "CLIPTextEncode" and node["inputs"]["text"] == "":
            node["inputs"]["text"] = prompt
    
    data = json.dumps({"prompt": workflow}).encode("utf-8")
    req = urllib.request.Request(f"{COMFYUI_URL}/prompt", data=data, headers=headers)
    result = json.loads(urllib.request.urlopen(req).read())
    prompt_id = result["prompt_id"]
    click.echo(f"Prompt ID: {prompt_id}")
    
    while True:
        req = urllib.request.Request(f"{COMFYUI_URL}/history/{prompt_id}", headers=headers)
        history = json.loads(urllib.request.urlopen(req).read())
        
        if prompt_id in history and history[prompt_id].get("status", {}).get("completed"):
            outputs = history[prompt_id].get("outputs", {})
            for node_output in outputs.values():
                if "images" in node_output:
                    for img in node_output["images"]:
                        filename = img["filename"]
                        subfolder = img.get("subfolder", "")
                        img_type = img.get("type", "output")
                        
                        url = f"{COMFYUI_URL}/view?filename={filename}&subfolder={subfolder}&type={img_type}"
                        req = urllib.request.Request(url, headers=headers)
                        img_data = urllib.request.urlopen(req).read()
                        
                        with open(filename, "wb") as f:
                            f.write(img_data)
                        
                        click.echo(f"Image sauvegardée : {os.path.abspath(filename)}")
            break
        
        time.sleep(0.5)