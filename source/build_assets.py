from pathlib import Path
import shutil
r=Path('research');src=next(x for x in Path('.').iterdir() if x.is_dir() and x.name.startswith('[Windows]'));pay=Path('Steam整合汉化补丁/payload')
# Keep PC content and its translated graphics; add only missing console graphics.
for group in ['BGM','DAT','G00','GAN','KOE','MOV','WAV']:
 d=src/group
 if not d.exists():continue
 for p in d.rglob('*'):
  if not p.is_file():continue
  q=pay/group/p.relative_to(d);q.parent.mkdir(parents=True,exist_ok=True)
  if not q.exists():shutil.copy2(p,q)
for p in (r/'cn-extracted/G00').rglob('*'):
 if p.is_file():q=pay/'G00'/p.relative_to(r/'cn-extracted/G00');q.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(p,q)
for group in ['G00','KOE']:
 for p in (r/'allages-extracted'/group).rglob('*'):
  if p.is_file():
   q=pay/group/p.relative_to(r/'allages-extracted'/group);q.parent.mkdir(parents=True,exist_ok=True)
   if not q.exists():shutil.copy2(p,q)
shutil.copy2(r/'cn-merged-Seen.txt',pay/'Seen.txt')
# Preserve legacy UI layout, with ASCII system-dialog strings and an isolated profile.
b=(r/'cn-extracted/GAMEEXE.INI').read_bytes()
import re
for key,val in [(b'CAPTION',b'"Tomoyo After - Steam Chinese +18"'),(b'REGNAME',b'"KEY\\TASteamCN18_v1"'),(b'SYSCOM.009',b'U:"Font"'),(b'NAME.A',b'"Okazaki"'),(b'NAME.B',b'"Tomoya"')]:b=re.sub(rb'(?m)^#'+re.escape(key)+rb'\s*=.*$',lambda m:b'#'+key+b'='+val+b'\r',b)
b=b.decode('cp932',errors='replace').encode('cp932',errors='replace')
b+=b'\r\n#ALL_FONT_USE=1\r\n#INIT_FONT_NAME="SimHei"\r\n#DLL.014="ta_cn"\r\n#DLL.015="rlSteam"\r\n'
(pay/'Gameexe.ini').write_bytes(b)
print('Payload',len([p for p in pay.rglob('*') if p.is_file()]),'files',round(sum(p.stat().st_size for p in pay.rglob('*') if p.is_file())/1024**2,1),'MiB')
