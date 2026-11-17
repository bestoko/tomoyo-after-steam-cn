from pathlib import Path
import json,struct,re,shutil,hashlib
from patch_bytecode import compressed,insert,u32
R=Path(__file__).resolve().parent
OUT=R.parent/'Steam整合汉化补丁'
PAY=OUT/'payload';TXT=PAY/'TXT'
TXT.mkdir(parents=True,exist_ok=True)
def info(kind,n):return json.loads((R/(kind+'-json')/f'SEEN{n:04}.TXT.rl.json').read_text(encoding='utf8'))
def raw(kind,n):return (R/(kind+'-raw')/f'SEEN{n:04}.TXT.rl').read_bytes()
def visible(kind,n):return [c for c in info(kind,n)['commands'] if not c['hidden']]
def fragment(kind,n,c):
    data=raw(kind,n);start=u32(data,32);cs=info(kind,n)['commands']
    end=min((x['offset'] for x in cs if x['offset']>c['offset']),default=len(data)-start)
    return data[start+c['offset']:start+end]
def event(n,entry=1):
    pattern=f'(9840, {entry}, special<0>({n}))'
    for p in sorted((R/'steam-json').glob('*.json')):
        sn=int(p.name[4:8])
        for c in info('steam',sn)['commands']:
            if pattern in c['text']:return fragment('steam',sn,c)
    raise ValueError(pattern)
changes={};report=[]
def add(scene,at,code,label):
    changes.setdefault(scene,[]).append((at,code));report.append({'scene':scene,'offset':at,'event':label})
def find(scene,text):
    hits=[c['offset'] for c in visible('cn',scene) if c['text']==text]
    assert len(hits)==1,(scene,text,hits)
    return hits[0]
def after(scene,text):
    cs=visible('cn',scene);hits=[i for i,c in enumerate(cs) if c['text']==text];assert len(hits)==1
    return cs[hits[0]+1]['offset']
# Keep the original translated scenario bytecode; insert only Steam calls.
add(9030,3,bytes.fromhex('2302010c000100002824ff0e00000029')+event(27,0)+bytes.fromhex('2302010c000200012824ff0e00000024ff0100000029'),'GBK initialization; Steam achievement initialization')
add(702,find(702,'jump (707)'),event(1),'ACH_01: opening completed')
add(6000,find(6000,'ReturnMenu'),event(2),'ACH_02: main story completed')
add(712,0x33da,event(10),'ACH_10: internship scene')
add(714,0x22560,event(11),'ACH_11: correct ending of lie game')
add(716,0x463b,event(13),'ACH_13: Tomoyo scene')
add(716,0x13402,event(12),'ACH_12: evening with everyone')
add(1715,after(1715,'intF[31] = 1'),event(13),'ACH_13: alternate scene')
add(1716,after(1716,'intF[32] = 1'),event(15),'ACH_15: alternate scene')
add(1716,after(1716,'intF[33] = 3'),event(14),'ACH_14: alternate scene')
for n in [744,1806,1814,2814,3814,4814]:add(n,find(n,'intG[1012] = 1'),event(16),'ACH_16: bad ending')
add(7910,find(7910,'koePlay (502000055, 1)'),event(3),'ACH_03: D&T introduction')
add(7910,0x16aa,event(20),'ACH_20: D&T story')
for at,n in [(0x3b84,21),(0x5916,22),(0x6d74,23),(0x80d6,24),(0xa319,25)]:add(7930,at,event(n),f'ACH_{n:02}: D&T story')
add(7940,find(7940,'intF[1728] = 1'),event(26),'ACH_26: D&T story')
# Add the console-version quiz as optional bonus after the original June 30.
bonus_comp=(R/'compiled/SEEN9839.TXT').read_bytes()
# Tail transition to the optional bonus menu, using the original jump ABI.
call_bonus=b'\x23\x00\x01\x0b\x00\x01\x00\x01('+b'\x24\xff'+struct.pack('<I',9839)+b')'
add(630,find(630,'jump (701)'),call_bonus,'Optional translated Steam math quiz')
# Baseline: old PC scripts and translated overlays.
for p in (R/'cn-raw').glob('*.TXT.rl'):
    n=int(p.name[4:8]);data=p.read_bytes()
    if n in changes:data=insert(data,info('cn',n),changes[n])
    (TXT/f'SEEN{n:04}.TXT').write_bytes(compressed(data))
# Retain Valve-facing official D&T mechanics and their original conditions.
translated={int(p.stem[4:]) for p in (R/'cn-extracted/TXT').glob('*.TXT')}
official=[]
for p in (R/'steam-raw').glob('*.TXT.rl'):
    n=int(p.name[4:8])
    if 7200<=n<=7900 and n not in translated or n==9840:
        (TXT/f'SEEN{n:04}.TXT').write_bytes(compressed(p.read_bytes()));official.append(n)
# Quiz retains all original branches, including the three-correct-answer check.
q=bytearray(raw('allages',630));qi=info('allages',630);s=u32(q,32)
end=next(c for c in qi['commands'] if c['text']=='jump (701)')
struct.pack_into('<I',q,0x34+50*4,0x45f4)
# Tail transitions avoid introducing an extra scenario-return frame.
old_jump=fragment('allages',630,end)
new_jump=old_jump.replace(struct.pack('<I',701),struct.pack('<I',9841))
assert new_jump!=old_jump and len(new_jump)==len(old_jump)
q[s+end['offset']:s+end['offset']+len(old_jump)]=new_jump
q=insert(q,qi,[(0x7712,event(9))])
(TXT/'SEEN9838.TXT').write_bytes(compressed(q))
# Explicitly terminate generated utility scenes with EOF.
(TXT/'SEEN9839.TXT').write_bytes(compressed(bonus_comp+b'\x00'))
(TXT/'SEEN9841.TXT').write_bytes(compressed((R/'compiled/SEEN9841.TXT').read_bytes()+b'\x00'))
shutil.copy2(R/'ta_cn.dll',PAY/'ta_cn.dll')
(OUT/'成就接入记录.json').write_text(json.dumps({'insertions':report,'official_dt_scenes':official,'quiz':{'entry':50,'correct_answer_trigger':hex(0x7712)}},ensure_ascii=False,indent=2),encoding='utf8')
print('Patched scenes:',len(changes),'official D&T scenes:',len(official),'total scripts:',len(list(TXT.glob('*.TXT'))))
