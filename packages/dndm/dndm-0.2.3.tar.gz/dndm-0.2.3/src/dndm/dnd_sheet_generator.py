from PIL import Image, ImageDraw, ImageFont
import math
from importlib.resources import files
from .datcalc import*
def modify(num):
    num = int(num)
    if num % 2 != 0:
        num = num -1
    modifier = (num-10)/2
    modifier = round(modifier)
    return modifier

def fill_sheet(character_data,savepath):
    # 1. Open the blank Character Sheet
    # .convert("RGBA") is best if using transparent PNGs
    img = files("dndm").joinpath("Blank1.png")
    img2 = files("dndm").joinpath("Blank2.png")
    img3 = files("dndm").joinpath("Blank3.png")
    sheet = Image.open(img).convert("RGBA")
    sheet2 = Image.open(img2).convert("RGBA")
    sheet3 = Image.open(img3).convert("RGBA")
    font = files("dndm").joinpath("PlayfairDisplay-Black.ttf")
    # 2. Create a "Draw" object to manipulate the image
    draw = ImageDraw.Draw(sheet)
    draw2 = ImageDraw.Draw(sheet2)
    draw3 = ImageDraw.Draw(sheet3)
    # 3. Load your Fonts (You can download cool ones from Google Fonts)
    # Format: ImageFont.truetype("Filename.ttf", Size)
    name_font = ImageFont.truetype(font, 30)
    sub_font = ImageFont.truetype(font, 25)
    #stat_font = ImageFont.truetype("Handwriting.ttf", 30)
    stat_font=name_font
    mod_font=ImageFont.truetype(font, 55)
    # 4. Define text color (RGB tuple or Hex code)
    text_color = (0, 0, 0) # Black
    # 5. Draw the Text
    # Syntax: draw.text((x, y), "Text", font=font_variable, fill=color)
    # Name (Top Left)
    draw.text((130, 135), character_data["name"], font=name_font, fill=text_color)
    # Class (Below Name)
    draw.text((620, 115), character_data["class"].captalize(), font=sub_font, fill=text_color)
    draw.text((620, 175), character_data["race"].capitalize(), font=sub_font, fill=text_color)
    draw.text((865, 115), character_data["background"].capitalize(), font=sub_font, fill=text_color)
    draw.text((865, 175), character_data["alignment"].capitalize(), font=sub_font, fill=text_color)
    draw.text((1110,115),str(character_data["player name"]),font=sub_font,fill=text_color)
    # Strength Score (Specific Box)
    draw.text((112, 415), str(character_data["strength"]), font=stat_font, fill=text_color)
    draw.text((112, 575), str(character_data["dexterity"]), font=stat_font, fill=text_color)
    draw.text((112, 740), str(character_data["constitution"]), font=stat_font, fill=text_color)
    draw.text((112, 900), str(character_data["intelligence"]), font=stat_font, fill=text_color)
    draw.text((112, 1065), str(character_data["wisdom"]), font=stat_font, fill=text_color)
    draw.text((112, 1225), str(character_data["charisma"]), font=stat_font, fill=text_color)
    ##
    draw.text((112, 1150), str(modify(character_data["charisma"])), font=mod_font, fill=text_color)
    draw.text((112, 990), str(modify(character_data["wisdom"])), font=mod_font, fill=text_color)
    draw.text((112, 825), str(modify(character_data["intelligence"])), font=mod_font, fill=text_color)
    draw.text((112, 665), str(modify(character_data["constitution"])), font=mod_font, fill=text_color)
    draw.text((112, 500), str(modify(character_data["dexterity"])), font=mod_font, fill=text_color)
    draw.text((112, 340), str(modify(character_data["strength"])), font=mod_font, fill=text_color)
    ## Second page
    draw2.text((130,135),str(character_data["name"]),font=name_font,fill=text_color)
    draw2.text((620, 115), str(character_data["age"]), font=sub_font, fill=text_color)
    draw2.text((620, 175), str(character_data["eye color"]).capitalize(), font=sub_font, fill=text_color)
    draw2.text((865, 115), str(character_data["height"]), font=sub_font, fill=text_color)
    draw2.text((865, 175), str(character_data["skin"]).capitalize(), font=sub_font, fill=text_color)
    draw2.text((1110,175),str(character_data["hair"]).capitalize(),font=sub_font,fill=text_color)
    draw2.text((1110,115),str(character_data["weight"]),font=sub_font,fill=text_color)
    save_list = [sheet2,sheet3]
    sheet.save(
        savepath, 
        save_all=True, 
        append_images=save_list
    )
    # 6. Save the final artifact
    #sheet.save(savepath)
    


# --- THE DATA FEED ---

# This is where your generator logic would plug in.

# For now, here is a dummy character.

hero = {

    "name": "Valen the Bold",
    "alignment": "Chaotic Good",
    "class": "Paladin",
    "background": "Folk Hero",
    "race":"Elf",
    "strength": 10,
    "gender" : "Male",
    "height": "510",
    "weight": "110",
    "hair": "Blonde",
    "eye color":"green",
    "skin":"fair",
    "dexterity":14,
    "constitution":12,
    "intelligence":12,
    "wisdom":14,
    "age":113,
    "charisma":15,
    "player name":"Mark"

}



#fill_sheet(hero,"/Users/ophelia/Desktop/dev/dndm/src/dndm/Blank1.png","/Users/ophelia/Downloads/test.pdf","/Users/ophelia/Desktop/dev/dndm/src/dndm/Blank2.png")
