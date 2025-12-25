import os, sys, random

##lists
race_list=["Dragonborn","Dwarf","Elf","Gnome","HalfElf","HalfOrc","Halfling","Human","Tiefling"]
class_list=["Barbarian","Bard","Cleric","Druid","Fighter","Monk","Paladin","Ranger","Rogue","Sorcerer","Warlock","Wizard"]
align_list=["LawfulGood","NeutralGood","ChaoticGood","LawfulNeutral","TrueNeutral","ChaoticNeutral","LawfulEvil","NeutralEvil","ChaoticEvil"]
bg_list=["Acolyte","Charlatan","Criminal","Entertainer","FolkHero","GuildArtisan","Hermit","Noble","Outlander","Sage","Sailor","Soldier","Urchin"]
dwarf_list=["HillDwarf","MountainDwarf"]
elf_list=["HighElf","WoodElf","DarkElf"]
halfling_list=["LightfootHalfling","StoutHalfling"]

##races
dragonborn="""Born of dragons, as their name proclaims,
the dragonborn walk proudly through a world that greets them with fearful incomprehension.
Shaped by draconic gods or the dragons themselves,
dragonborn originally hatched from dragon eggs as a unique race, combining the best attributes of dragons and humanoids.
Some dragonborn are faithful servants to true dragons, others form the ranks of soldiers in great wars,
and still others find themselves adrift, with no clear calling in life."""
dwarf="""Kingdoms rich in ancient grandeur, halls carved into the roots of mountains,
the echoing of picks and hammers in deep mines and blazing forges, a commitment to clan and tradition,
and a burning hatred of goblins and orcs – these common threads unite all dwarves."""

elf="""Elves are a magical people of otherworldly grace, living in places of ethereal beauty,
in the midst of ancient forests or in silvery spires glittering with faerie light,
where soft music drifts through the air and gentle fragrances waft on the breeze.
Elves love nature and magic, art and artistry, music and poetry."""

halfling="""The comforts of home are the goals of most halflings' lives:
a place to settle in peace and quiet, far from marauding monsters and clashing armies.
Others form nomadic bands that travel constantly,
lured by the open road and the wide horizon to discover the wonders of new lands and peoples.
Halflings work readily with others, and they are loyal to their friends, whether halfling or otherwise.
They can display remarkable ferocity when their friends, families, or communities are threatened."""

human="""In the reckonings of most worlds, humans are the youngest of the common races,
late to arrive on the world scene and short-lived in comparison to dwarves, elves, and dragons.
Perhaps it is because of their shorter lives that they strive to achieve as much as they can in the years they are given.
Or maybe they feel they have something to prove to the elder races,
and that's why they build their mighty empires on the foundation of conquest and trade.
Whatever drives them, humans are the innovators, the achievers, and the pioneers of the worlds."""

gnome="""A constant hum of busy activity pervades the warrens and neighborhoods where gnomes form their close-knit communities.
Louder sounds punctuate the hum: a crunch of grinding gears here, a minor explosion there,
a yelp of surprise or triumph, and especially bursts of laughter. Gnomes take delight in life,
enjoying every moment of invention, exploration, investigation, creation, and play."""

halfelf="""Walking in two worlds but truly belonging to neither,
half-elves combine what some say are the best qualities of their elf and human parents:
human curiosity, inventiveness, and ambition tempered by the refined senses, love of nature, and artistic tastes of the elves."""

halforc="""When alliances between humans and orcs are sealed by marriages, half-orcs are born.
Some half-orcs rise to become proud chiefs of orc tribes, their human blood giving them an edge over their full-blooded orc rivals.
Some venture into the world to prove their worth among humans and other more civilized races.
Many of these become adventurers, achieving greatness for their mighty deeds and notoriety for their barbaric customs and savage fury."""

tiefling="""To be greeted with stares and whispers, to suffer violence and insult on the street, to see mistrust and fear in every eye:
this is the lot of the tiefling. And to twist the knife,
tieflings know that this is because a pact struck generations ago infused the essence of Asmodeus,
overlord of the Nine Hells (and many of the other powerful devils serving under him) into their bloodline.
Their appearance and their nature are not their fault but the result of an ancient sin,
for which they and their children and their children's children will always be held accountable."""

##classes
barbarian = """For some, their rage springs from a communion with fierce animal spirits.
Others draw from a roiling reservoir of anger at a world full of pain.
For every barbarian, rage is a power that fuels not just a battle frenzy but also uncanny reflexes, resilience, and feats of strength."""

bard = """Whether scholar, skald, or scoundrel, a bard weaves magic through words and music to inspire allies,
demoralize foes, manipulate minds, create illusions, and even heal wounds.
The bard is a master of song, speech, and the magic they contain."""

cleric = """Clerics are intermediaries between the mortal world and the distant planes of the gods.
As varied as the gods they serve, clerics strive to embody the handiwork of their deities.
No ordinary priest, a cleric is imbued with divine magic."""

druid = """Whether calling on the elemental forces of nature or emulating the creatures of the animal world,
druids are an embodiment of nature's resilience, cunning, and fury.
They claim no mastery over nature, but see themselves as extensions of nature's indomitable will."""

fighter = """Fighters share an unparalleled mastery with weapons and armor, and a thorough knowledge of the skills of combat.
They are well acquainted with death, both meting it out and staring it defiantly in the face."""

monk = """Monks are united in their ability to magically harness the energy that flows in their bodies.
Whether channeled as a striking display of combat prowess or a subtler focus of defensive ability and speed,
this energy infuses all that a monk does."""

paladin = """Whether sworn before a god's altar and the witness of a priest,
in a sacred glade before nature spirits and fey beings,
or in a moment of desperation and grief with the dead as the only witness, a paladin's oath is a powerful bond."""

ranger = """Far from the bustle of cities and towns, past the hedges that shelter the most distant farms from the terrors of the wild,
amid the dense-packed trees of trackless forests and across wide and empty plains, rangers keep their unending watch."""

rogue = """Rogues rely on skill, stealth, and their foes' vulnerabilities to get the upper hand in any situation.
They have a knack for finding the solution to just about any problem,
demonstrating a resourcefulness and versatility that is the cornerstone of any successful adventuring party."""

sorcerer = """Sorcerers carry a magical birthright conferred upon them by an exotic bloodline,
some otherworldly influence, or exposure to unknown cosmic forces. No one chooses sorcery; the power chooses the sorcerer."""

warlock = """Warlocks are seekers of the knowledge that lies hidden in the fabric of the multiverse.
Through pacts made with mysterious beings of supernatural power, warlocks unlock magical effects both subtle and spectacular."""

wizard = """Wizards are supreme magic-users, defined and united as a class by the spells they cast.
Drawing on the subtle weave of magic that permeates the cosmos, wizards cast spells of explosive fire,
arcing lightning, subtle deception, brute-force mind control, and much more."""

##Alignments
lawfulgood="""A lawful good character typically acts with compassion and always with honor and a sense of duty.
However, lawful good characters will often regret taking any action they fear would violate their code,
even if they recognize such action as being good. Such characters include gold dragons, righteous knights, paladins, and most dwarves."""

neutralgood="""A neutral good character typically acts altruistically, without regard for or against lawful precepts such as rules or tradition.
A neutral good character has no problems with cooperating with lawful officials, but does not feel beholden to them.
In the event that doing the right thing requires the bending or breaking of rules,
they do not suffer the same inner conflict that a lawful good character would.
Examples of this alignment include many celestials, some cloud giants, and most gnomes."""

chaoticgood="""A chaotic good character does whatever is necessary to bring about change for the better,
disdains bureaucratic organizations that get in the way of social improvement,
and places a high value on personal freedom, not only for oneself but for others as well.
Chaotic good characters usually intend to do the right thing,
but their methods are generally disorganized and often out of sync with the rest of society.
Examples of this alignment include copper dragons, many elves, and unicorns."""

lawfulneutral="""A lawful neutral character typically believes strongly in lawful concepts such as honor, order, rules, and tradition,
but often follows a personal code in addition to, or even in preference to, one set down by a benevolent authority.
Examples of this alignment include a soldier who always follows orders,
a judge or enforcer who adheres mercilessly to the letter of the law, a disciplined monk, and some wizards."""

trueneutral="""A neutral character is neutral on both axes and tends not to feel strongly towards any alignment, or actively seeks their balance.
Druids frequently follow this dedication to balance. In an example given in the 2nd Edition Player's Handbook,
a typical druid might fight against a band of marauding gnolls, only to switch sides to save the gnolls' clan from being totally exterminated.
Examples of this alignment include lizardfolk, most druids, and many humans."""

chaoticneutral="""A chaotic neutral character is an individualist who follows their own heart and generally shirks rules and traditions.
Although chaotic neutral characters promote the ideals of freedom, it is their own freedom that comes first;
good and evil come second to their need to be free. Examples of this alignment include many barbarians and rogues, and some bards."""

lawfulevil="""A lawful evil character sees a well-ordered system as being necessary to fulfill their own personal wants and needs,
using these systems to further their power and influence. Examples of this alignment include tyrants, devils, corrupt officials,
undiscriminating mercenary types who have a strict code of conduct, blue dragons, and hobgoblins."""

neutralevil="""A neutral evil character is typically selfish and has no qualms about turning on allies-of-the-moment,
and usually makes allies primarily to further their own goals.
A neutral evil character has no compunctions about harming others to get what they want,
but neither will they go out of their way to cause carnage or mayhem when they see no direct benefit for themselves.
Another valid interpretation of neutral evil holds up evil as an ideal, doing evil for evil's sake and trying to spread its influence.
Examples of the first type are an assassin who has little regard for formal laws but does not needlessly kill,
a henchman who plots behind their superior's back, or a mercenary who readily switches sides if made a better offer.
An example of the second type would be a masked killer who strikes only for the sake of causing fear and distrust in the community.
Examples of this alignment include many drow, some cloud giants, and yugoloths."""

chaoticevil="""A chaotic evil character tends to have no respect for rules, other people's lives, or anything but their own desires,
which are typically selfish and cruel. They set a high value on personal freedom,
but do not have much regard for the lives or freedom of other people.
Chaotic evil characters do not work well in groups because they resent being given orders
and usually do not behave themselves unless there is no alternative.
Examples of this alignment include higher forms of undead (such as liches),
violent killers who strike for pleasure rather than profit, demons, red dragons, and orcs."""

##background
acolyte = """You have spent your life in the service of a temple to a specific god or pantheon of gods.
You act as an intermediary between the realm of the holy and the mortal world,
performing sacred rites and offering sacrifices in order to conduct worshipers into the presence of the divine.
You are not necessarily a cleric – performing sacred rites is not the same thing as channeling divine power.
Choose a god, a pantheon of gods, or some other quasi-divine being, and work with your DM to detail the nature of your religious service.
Were you a lesser functionary in a temple, raised from childhood to assist the priests in the sacred rites?
Or were you a high priest who suddenly experienced a call to serve your god in a different way?
Perhaps you were the leader of a small cult outside of any established temple structure,
or even an occult group that served a fiendish master that you now deny."""

charlatan = """You have always had a way with people. You know what makes them tick,
you can tease out their hearts' desires after a few minutes of conversation,
and with a few leading questions you can read them like they were children's books.
It's a useful talent, and one that you're perfectly willing to use for your advantage.
You know what people want and you deliver, or rather, you promise to deliver.
Common sense should steer people away from things that sound too good to be true,
but common sense seems to be in short supply when you're around.
The bottle of pink colored liquid will surely cure that unseemly rash,
this ointment – nothing more than a bit of fat with a sprinkle of silver dust can restore youth and vigor,
and there's a bridge in the city that just happens to be for sale. These marvels sound implausible, but you make them sound like the real deal."""

criminal = """You are an experienced criminal with a history of breaking the law.
You have spent a lot of time among other criminals and still have contacts within the criminal underworld.
You're far closer than most people to the world of murder, theft, and violence that pervades the underbelly of civilization,
and you have survived up to this point by flouting the rules and regulations of society."""

entertainer = """You thrive in front of an audience. You know how to entrance them, entertain them, and even inspire them.
Your poetics can stir the hearts of those who hear you, awakening grief or joy, laughter or anger.
Your music raises their spirits or captures their sorrow. Your dance steps captivate, your humor cuts to the quick.
Whatever techniques you use, your art is your life."""

folkhero = """You come from a humble social rank, but you are destined for so much more.
Already the people of your home village regard you as their champion,
and your destiny calls you to stand against the tyrants and monsters that threaten the common folk everywhere."""

guildartisan = """You are a member of an artisan's guild, skilled in a particular field and closely associated with other artisans.
You are a well-established part of the mercantile world, freed by talent and wealth from the constraints of a feudal social order.
You learned your skills as an apprentice to a master artisan, under the sponsorship of your guild, until you became a master in your own right."""

hermit = """You lived in seclusion – either in a sheltered community such as a monastery,
or entirely alone – for a formative part of your life. In your time apart from the clamor of society,
you found quiet, solitude, and perhaps some of the answers you were looking for."""

noble = """You understand wealth, power, and privilege.
You carry a noble title, and your family owns land, collects taxes, and wields significant political influence.
You might be a pampered aristocrat unfamiliar with work or discomfort, a former merchant just elevated to the nobility,
or a disinherited scoundrel with a disproportionate sense of entitlement.
Or you could be an honest, hard-working landowner who cares deeply about the people who live and work on your land,
keenly aware of your responsibility to them.
Work with your DM to come up with an appropriate title and determine how much authority that title carries.
A noble title doesn't stand on its own-it's connected to an entire family,
and whatever title you hold, you will pass it down to your own children.
Not only do you need to determine your noble title, but you should also work with the DM to describe your family and their influence on you.
Is your family old and established, or was your title only recently bestowed?
How much influence do they wield, and over what area?
What kind of reputation does your family have among the other aristocrats of the region?
How do the common people regard them? What's your position in the family?
Are you the heir to the head of the family? Have you already inherited the title? How do you feel about that responsibility?
Or are you so far down the line of inheritance that no one cares what you do, as long as you don't embarrass the family?
How does the head of your family feel about your adventuring career?
Are you in your family's good graces, or shunned by the rest of your family?
Does your family have a coat of arms? An insignia you might wear on a signet ring?
Particular colors you wear all the time? An animal you regard as a symbol of your line or even a spiritual member of the family?
These details help establish your family and your title as features of the world of the campaign."""

outlander = """You grew up in the wilds, far from civilization and the comforts of town and technology.
You've witnessed the migration of herds larger than forests,
survived weather more extreme than any city-dweller could comprehend,
and enjoyed the solitude of being the only thinking creature for miles in any direction.
The wilds are in your blood, whether you were a nomad, an explorer, a recluse, a hunter-gatherer, or even a marauder.
Even in places where you don't know the specific features of the terrain, you know the ways of the wild."""

sage = """You spent years learning the lore of the multiverse.
You scoured manuscripts, studied scrolls, and listened to the greatest experts on the subjects that interest you.
Your efforts have made you a master in your fields of study."""

sailor = """You sailed on a seagoing vessel for years. In that time, you faced down mighty storms,
monsters of the deep, and those who wanted to sink your craft to the bottomless depths.
Your first love is the distant line of the horizon, but the time has come to try your hand at something new.
Discuss the nature of the ship you previously sailed with your DM. Was it a merchant ship, a naval vessel,
a ship of discovery, or a pirate ship? How famous (or infamous) is it? Is it widely traveled?
Is it still sailing, or is it missing and presumed lost with all hands?
What were your duties on board – boatswain, captain, navigator, cook, or some other position?
Who were the captain and first mate? Did you leave your ship on good terms with your fellows, or on the run?"""

soldier = """War has been your life for as long as you care to remember. You trained as a youth,
studied the use of weapons and armor, learned basic survival techniques,
including how to stay alive on the battlefield.
You might have been part of a standing national army or a mercenary company,
or perhaps a member of a local militia who rose to prominence during a recent war.
When you choose this background, work with your DM to determine which military organization you were a part of,
how far through its ranks you progressed, and what kind of experiences you had during your military career.
Was it a standing army, a town guard, or a village militia?
Or it might have been a noble's or merchant's private army, or a mercenary company."""

urchin = """You grew up on the streets alone, orphaned, and poor.
You had no one to watch over you or to provide for you, so you learned to provide for yourself.
You fought fiercely over food and kept a constant watch out for other desperate souls who might steal from you.
You slept on rooftops and in alleyways, exposed to the elements,
and endured sickness without the advantage of medicine or a place to recuperate.
You've survived despite all odds, and did so through cunning, strength, speed, or some combination of each.
You begin your adventuring career with enough money to live modestly but securely for at least ten days.
How did you come by that money? What allowed you to break free of your desperate circumstances and embark on a better life?"""

##subspecies list
hilldwarf = """As a hill dwarf, you have keen senses, deep intuition, and remarkable resilience.
The gold dwarves of Faerun in their mighty southern kingdom are hill dwarves,
as are the exiled Neidar and the debased Klar of Krynn in the Dragonlance setting."""

mountaindwarf = """As a mountain dwarf, you're strong and hardy, accustomed to a difficult life in rugged terrain.
You're probably on the tall side (for a dwarf), and tend toward lighter coloration,
The shield dwarves of northern Faerun,
as well as the ruling Hylar clan and the noble Daewar clan of Dragonlance, are mountain dwarves."""

highelf = """As a high elf, you have a keen mind and a mastery of at least the basics of magic.
In many of the worlds of D&D, there are two kinds of high elves.
One type (which includes the gray elves and valley elves of Greyhawk, the Silvanesti of Dragonlance,
and the sun elves of the Forgotten Realms) is haughty and reclusive,
believing themselves to be superior to non-elves and even other elves.
The other type (including the high elves of Greyhawk. the Qualinesti of Dragonlance,
and the moon elves of the Forgotten Realms) are more common and more friendly, and often encountered among humans and other races.
The sun elves of Faerun (also called gold elves or sunrise elves) have bronze skin and hair of copper, black, or golden blood.
Their eyes are golden, silver, or black. Moon elves (also called silver elves or gray elves) are much paler,
with alabaster skin sometimes tinged with blue.
They often have hair of silver-while, black, or blue, but various shades of blond, brown, and red are not uncommon.
Their eyes are blue or green and flecked with gold."""

woodelf = """As a wood elf, you have keen senses and intuition, and your fleet feet carry you quickly
and stealthily through your native forests. This category includes the wild elves (grugach) of Greyhawk and the Kagonesti of Dragonlance,
as well as the races called wood elves in Greyhawk and the Forgotten Realms.
In Faerun, wood elves (also called wild elves. green elves, or forest elves) are reclusive and distrusting of non-elves.
Wood elves' skin tends to be copperish in hue, sometimes with traces of green. Their hair tends toward browns and blacks,
but it is occasionally blond or copper-colored. Their eyes are green, brown, or hazel."""

darkelf = """Descended from an earlier subrace of dark-skinned elves,
the drow were banished from the surface world for following the goddess Lolth down the path to evil and corruption.
Now they have built their own civilization in the depths of the Underdark, patterned after the Way of Lolth.
Also called dark elves. The drow have black skin that resembles polished obsidian and stark white or pale yellow hair.
They commonly have very pale eyes (so pale as to be mistaken for white) in shades of lilac, silver, pink, red, and blue.
They tend to be smaller and thinner than most elves. Drow adventurers are rare, and the race does not exist in all worlds.
Check with your Dungeon Master to see if you can play a drow character."""

lightfoothalfling = """As a lightfoot halfling, you can easily hide from notice, even using other people as cover.
You're inclined to be affable and get along well with others.
In the Forgotten Realms, lightfoot halflings have spread the farthest and thus are the most common variety.
Lightfoots are more prone to wanderlust than other halflings, and often dwell alongside other races or take up a nomadic life.
In the world of Grayhawk, these halflings are called hairfeet or tallfellows."""

stoutfoothalfling = """As a stout halfling, you're hardier than average and have some resistance to poison.
Some say that stouts have dwarven blood.
In the Forgotten Realms, these halflings are called stronghearts, and they're most common in the south."""


##-------gen-functions-------
def selector(name_list):
    for i in name_list:
        print(i)
    while 1:
        inp = input('Type "s <name>" to choose. Type "i <name>" to get more info: ')
        if inp != "":
            inp = inp.lower()
            inp_spli=inp.split()
            if inp_spli[0] == "s":
                choice = inp_spli[1]
                if choice.capitalize() in name_list or choice.lower() in [n.lower() for n in name_list]:
                    return choice.lower()
                else:
                    print("Not found")
            elif inp_spli[0] == "i":
                print("-----"+inp_spli[1]+"-------")
                print(globals().get(inp_spli[1],"Not found"))
                print("---------------------------")
        else:
            print("Please enter a value")
def subrace(race):
    race=race.lower()
    if race in ("dwarf","elf","halfling"):
        if race == "dwarf":
            return selector(dwarf_list)
        elif race == "elf":
            return selector(elf_list)
        elif race == "halfling":
            return selector(halfling_list)
    else:
        return race
def point_rep(name,points):
    while 1:
        val = input("Points for "+name+": ")
        val = int(val)
        if((points - val) >= 0 and val >= 0):
            points = points-val
            print("Points left: "+str(points))
            val = val + 8
            break
        else:
            print("Choose a proper value")
    return val, points
def point_chooser():
    print("You have 5 abilities and 27 points. You will have to choose how to spend them")
    print("Each ability starts at 8, with a -1 modifier. To increase your modifier by 1, you must spend 2 points")
    points=27
    stg, points=point_rep("strength",points)
    dex, points=point_rep("dexterity",points)
    con, points=point_rep("constitution",points)
    inl, points=point_rep("intelligence",points)
    wis, points=point_rep("wisdom",points)
    cha, points=point_rep("charisma",points)
    return stg,dex,con,inl,wis,cha
def save_dict_as_txt(data: dict, path: str):
    with open(path, "w") as f:
        for key, value in data.items():
            f.write(f"{key} = {value}\n")
def load_txt_as_dict(path:str):
    dic = {}
    with open(path, 'r') as file:
        for line in file:
            try:
                key, value = line.strip().split(' = ', 1)
                dic[key] = value
            except ValueError:
                continue
    return dic
##-------chr-functions-------
def corechr():
    plrName= input("Your name: ")
    print("--About--")
    name = input("Name: ")
    align = selector(align_list)
    print("--Class--")
    clas = selector(class_list)
    print(clas)
    print("--Background--")
    bkgn = selector(bg_list)
    print("--Race--")
    race = selector(race_list)
    race = subrace(race)
    gender = input("Gender: ")
    height = input("Height: ")
    weight = input("Weight: ")
    hair = input("Hair: ")
    age = input("Age: ")
    eyecolor = input("Eye Color: ")
    skin = input("Skin: ")
    while 1:
        stg,dex,con,inl,wis,cha = point_chooser()
        abil_list= [stg,dex,con,inl,wis,cha]
        confirm = input("Y/N: Would you like keep these stats?")
        confirm = confirm.lower()
        if confirm == "y":
            break
    starter=input("Would you rather have equipment or gold? Type E or G: ")
    starter = starter.lower()
    print("That's all! Additional features may be added in the future! Time to compile!")
    character = {
        "name" : name,
        "alignment" : align,
        "background" : bkgn,
        "class" : clas,
        "race" : race,
        "gender" : gender,
        "height" : height,
        "weight" : weight,
        "hair" : hair,
        "eye color" : eyecolor,
        "skin" : skin,
        "strength" : stg,
        "dexterity" : dex,
        "constitution" : con,
        "intelligence" : inl,
        "age":age,
        "wisdom" : wis,
        "charisma" : cha,
        "starter" : starter,
        "player name": plrName
        }
    return character
    


    
