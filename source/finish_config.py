from pathlib import Path
import re,shutil
p=Path('Steam整合汉化补丁/payload/Gameexe.ini');b=p.read_bytes()
labels={'SYSTEM_SAVELOADMESSAGE_STR':'Ask before saving or loading.','SAVEMESSAGE_TITLE_STR':'Save','SAVEMESSAGE_MESS_STR':'Save your progress?','SAVEMESSAGE_MESS2_STR':'This confirmation can be changed in settings.','LOADMESSAGE_TITLE_STR':'Load','LOADMESSAGE_MESS_STR':'Load this saved game?','LOADMESSAGE_MESS2_STR':'Unsaved progress will be lost.','DLGSAVEMESSAGE_TITLE_STR':'Save','DLGSAVEMESSAGE_OK_BUTTON_STR':'Save','DLGLOADMESSAGE_TITLE_STR':'Load','DLGLOADMESSAGE_OK_BUTTON_STR':'Load','SYSTEM_ANIME_STR':'Skip transition animations.','SELPOINT_RETURN_MESS_STR':'Return to the previous choice?','MENU_RETURN_MESS_STR':'Return to the title menu?','GAME_END_MESS_STR':'Exit the game?','SAVE_NODATA':'Empty slot'}
for k,v in labels.items():b=re.sub(rb'(?m)^#'+re.escape(k.encode())+rb'\s*=.*$',lambda m:b'#'+k.encode()+b'="'+v.encode()+b'"\r',b)
p.write_bytes(b)
st=Path(r"E:\SteamLibrary\steamapps\common\Tomoyo After ~It's a Wonderful Life~ English Edition");shutil.copy2(p,st/'Gameexe.ini')
src=Path('Steam整合汉化补丁/source');src.mkdir(exist_ok=True)
for n in ['ta_cn.c','ta_cn.def','build-native.cmd','patch_bytecode.py','build_patch.py','build_assets.py','manifest_patch.py']:
 shutil.copy2(Path('research')/n,src/n)
