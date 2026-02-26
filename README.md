# The Quaker Deliverance
A Quake 1 launcher in Python, Vibe Coded using Google Gemini

Simple up and running for Debian based distros

```bash
git clone https://github.com/yzf750/The-Quaker-Deliverance.git
cd ./The-Quaker-Deliverance
sudo apt update
#sudo apt install python3-tk python3-pil.imagetk
sudo apt install python3-pil
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
