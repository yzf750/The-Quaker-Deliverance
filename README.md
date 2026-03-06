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
- When you click a Mod a random screenshot will appear.
- Saves the last Mod and Map used when closed.

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
----------------------------------------------

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

More instructions and screenshots...... Coming soon.
