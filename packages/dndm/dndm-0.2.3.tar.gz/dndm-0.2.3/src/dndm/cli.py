# src/dndm/cli.py
import sys, click, random, json
import os
from . import __version__
from .defi import *
from importlib.resources import files
from .dnd_sheet_generator import *
CONFIG_PATH = os.path.expanduser("~/.config/dndm/config.json")
def load_config():
    if os.path.exists(CONFIG_PATH):
        with open(CONFIG_PATH, "r") as f:
            return json.load(f)
    return {"save_dir": os.getcwd()}

def save_config(config):
    os.makedirs(os.path.dirname(CONFIG_PATH), exist_ok=True)
    with open(CONFIG_PATH, "w") as f:
        json.dump(config, f, indent=2)
config = load_config()

command_list=["Rolls a chosen dice: roll <dice_number> [repeat]", "Creates a character: chr", "Changes the save path for created files: svc </preferred/path","Sends a character to the dev: sendchr </path/to/file>"]

@click.group()
@click.version_option(__version__)
def main():
    """Dungeons and Dragons tools. Use 'dndm --help' for details."""
    pass

@main.command()
@click.argument("dice_number", required=True)
@click.argument("repeat", required=False, default=0)
def roll(dice_number, repeat):
    """Rolls a dice. Usage: roll <dice_number> [repeat]"""
    d = int(dice_number)
    r = int(repeat)
    while (r >=0):
        click.echo(random.randint(1,d))
        r = r-1
@main.command()
@click.argument("name")
def regen(name):
    """Regenerates the completed pdf with the given character. Usage: regen <name>"""
    name = name.strip()
    path = config["save_dir"]+"/"+ str(name)+".txt"
    if os.path.exists(path):
        character = load_txt_as_dict(path)
        save_path = os.path.join(config["save_dir"],name)
        save_path = save_path+"_sheet.pdf"
        fill_sheet(character,save_path)
    else:
        print(f"File: {path} not found")
        
@main.command()
@click.argument("path")
def svc(path):
    """Set the default save directory."""
    path = os.path.abspath(path)
    if not os.path.isdir(path):
        click.echo("Invalid directory")
        return
    
    config["save_dir"] = path
    save_config(config)
    click.echo(f"Default save directory set to: {path}")

@main.command()
def chr():
    """Creates a character"""
    character=corechr()
    name = "".join((character["name"]).split())
    save_path = os.path.join(config["save_dir"],name)
    save_path_pdf= save_path+"_sheet.pdf"
    fill_sheet(character,save_path_pdf)
    save_path = save_path+".txt"
    save_dict_as_txt(character, save_path)
    click.echo(f"Completed at {save_path_pdf}")
if __name__ == "__main__":
    main()
