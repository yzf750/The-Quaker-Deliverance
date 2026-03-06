# The Quaker Deliverance
A Quake 1 launcher in Python, Vibe Coded using Google Gemini

![tqd](images/the-quaker-deliverance.png)

Features
--------

- Takes "Real Time" scrrwenshots. 
- Laiches Mods or Maps
- Lunches Saved Games
- Slects Skill Level
- Shows Number fo Mosyrts and Secrets per map (Change skill level to see number per skill level)
- Shows Maps full name
- Supports themes
- Uses mostly pre installed python librarires for most distros (You may need to install the python pillow library for image support)
- Search Mods and Maps (Only maps for the selected Mod, I might add support to search all maps)


Configuration
-------------
- Browse for Quake Engine (Executable)
- Browse for Quake base direcory

Settings
--------
- Select Threme
- Select font size.


Launch Mod or Map
-----------------
- Slect "Skill"
- Add any "Extra CLI Args" such as -heapsize , -startwindowed. CLI Args are saved on a per Mod basis. 
- Click Mod, click map, click laucnh


Launch Saved Game
-----------------
- Saved games are sorted by most recent first
- Load a Saved Game and the app will show you a scrrsnhot of the map from the saved game.
- Click "Load Save" 
- Click Laucnch


Screenshots
-----------
- When you click a Mod Any existing screenshots for that Mod are moved to the "oldscreenshots" direcory.
- Take a scrrenshot using your usual key (default is F12)
- Application monitors Mod direcory for new screenshots, if you take a scrrsnhot it will be renaned to the map name you launched and moved to the "previres" direcory
- Right click a screensjpt fopr an option to delete it or open the "previews" direcory

Filter
------
- You can filter for Mods and Maps by typing in the textbox at the top of each column

Refresh Mods and Maps 
---------------------
- Right click any Mod in the Mods column
- "Force Maps Rescan - (Clear Cache)" will scan for any new maps added to the direcory
- "Refresh Mods List" - Will updated any Mods you have added (saves you from having to restart the app)


Simple up and running for Debian based distros

```bash
git clone https://github.com/yzf750/The-Quaker-Deliverance.git
cd ./The-Quaker-Deliverance
sudo apt update
# From the Pillow docs. Most major Linux distributions, including Fedora, Ubuntu and ArchLinux
# also include Pillow in packages that previously contained PIL e.g. python-imaging.
# Debian splits it into two packages, python3-pil and python3-pil.imagetk.
sudo apt install python3-tk python3-pil.imagetk
#sudo apt install python3-pil
pip install -r requirements.txt
cp the-quaker-deliverence.py thequake.png /path/to/your/quake/directory/
```

Copy or Move the-quaker-deliverance.py and thequaker.png to your Quake directory



cd "YourQuakeDirectory"

```bash
# Make script executable
chmod +x ./the-quaker-deliverence.py
./the-quaker-deliverence.py

# or run using python

python3 ./the-quaker-deliverence.py

```


python3 ./the-quaker-deliverance.py

Configure Engine, Quake Root.

Click a Mod then Map and click launch

While running the app looks for screenshots in the mod or id direcory, once a new screenshot is detcted it will rename the file to the map name and move it to the previews folder.
Caution, previos screenshots will be removed/renamed then moved to the previews folder. Move any screenshots you may have created to avoid lossing them.
Press F12 (or whatever key you use for sreenshots) and the script will create a screenshot for that map in a direcory named "previews"

Under "Mods" in the Mods listing you can search in the textbox
Under "Maps" in the Maps listing you can search in the textbox

Right Click a Mod Name and you can force a rescan that will look for new maps or changes. (Force Maps Rescan (Clear Cache)
Right Click a Mod Name and you can refresh the Mods listings.

Right Click the preview image and you can delete the screenshot.

More instructions and screenshots...... Coming soon.
