from pathlib import Path
import json,hashlib
p=Path('Steam整合汉化补丁');pay=p/'payload';st=Path(r"E:\SteamLibrary\steamapps\common\Tomoyo After ~It's a Wonderful Life~ English Edition")
h=lambda x:hashlib.sha256(x.read_bytes()).hexdigest()
spec={'version':'0.1-personal-experimental','originals':[{'path':n,'sha256':h(st/n)} for n in ['RealLiveEn.exe','rlSteam.dll','steam_api.dll']], 'files':[{'path':str(f.relative_to(pay)), 'sha256':h(f),'size':f.stat().st_size} for f in sorted(pay.rglob('*')) if f.is_file()]}
(p/'manifest.json').write_text(json.dumps(spec,ensure_ascii=False,indent=2),encoding='utf8')
f=p/'Manage-Patch.ps1';f.write_text(f.read_text(encoding='utf-8-sig').lstrip('\ufeff'),encoding='utf-8-sig')
print('Manifest files',len(spec['files']))
