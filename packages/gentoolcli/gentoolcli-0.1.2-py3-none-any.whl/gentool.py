import click
import pyrebase
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from commands.comfyui import comfyui
from commands.auth import get_session, save_session, get_valid_user, SESSION_FILE

def get_firebase():
    config_path = os.path.join(os.path.dirname(__file__), "commands", "firebase_config.json")
    with open(config_path) as f:
        config = json.load(f)
    return pyrebase.initialize_app(config)

@click.group()
def main():
    pass

@main.command()
@click.option("--email", prompt=True)
@click.option("--password", prompt=True, hide_input=True)
def login(email, password):
    firebase = get_firebase()
    auth = firebase.auth()
    try:
        user = auth.sign_in_with_email_and_password(email, password)
        save_session(user)
        click.echo("Connecté !")
    except Exception as e:
        click.echo(f"Erreur : {e}")

@main.command()
def logout():
    if os.path.exists(SESSION_FILE):
        os.remove(SESSION_FILE)
        click.echo("Déconnecté !")
    else:
        click.echo("Aucune session active.")

@main.command()
def status():
    user = get_valid_user(get_firebase())
    if user:
        click.echo(f"Connecté : {user['email']}")
    else:
        click.echo("Non connecté.")

main.add_command(comfyui)

if __name__ == "__main__":
    main()