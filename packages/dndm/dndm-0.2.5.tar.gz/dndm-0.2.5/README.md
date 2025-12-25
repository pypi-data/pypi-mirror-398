This is an early release of list of dnd tools.
NOTE: This only runs between python versions 3.9 and 3.14. Pillow does not work on more recent builds, so it cannot be used further
These are the following commands:

Roll a dice: roll <dice_number> [repeat]

Change the save path: svc <path>

Create a character: chr

Regenerates a pdf from a previously made character: regen <name>

Please note that the chr command will walk you through the character setup. 

##INSTALL##
Please install via pip:
pip install dndm

## macOS Install Notes

If `pip install dndm` succeeds but `dndm` is not found:

```bash
echo 'export PATH="$HOME/Library/Python/3.9/bin:$PATH"' >> ~/.zshrc
source ~/.zshrc