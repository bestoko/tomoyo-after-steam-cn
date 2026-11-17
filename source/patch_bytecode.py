from pathlib import Path
import struct,json,re
ROOT=Path(__file__).resolve().parent
def u32(b,p):return struct.unpack_from('<I',b,p)[0]
def compressed(raw):
    start=u32(raw,0x20);code=raw[start:];payload=bytearray()
    for i in range(0,len(code),8):payload.append(255);payload.extend(code[i:i+8])
    payload=bytearray(struct.pack('<II',len(payload)+8,len(code)))+payload
    go=(ROOT/'rldev-go/common/pkg/compression/compression.go').read_text(encoding='utf8')
    part=go.split('var xorMask = [256]byte{',1)[1].split('}',1)[0]
    mask=bytes(int(s,16) for s in re.findall(r'0x([0-9a-fA-F]{2})',part))
    payload=bytes(v^mask[i%256] for i,v in enumerate(payload))
    out=bytearray(raw[:start]);out[:4]=struct.pack('<I',464)
    struct.pack_into('<II',out,0x24,len(code),len(payload))
    return out+payload
def insert(raw,info,insertions):
    raw=bytearray(raw);start=u32(raw,0x20)
    # Branches to an insertion boundary must execute the inserted calls.
    def newpos(p):return p+sum(len(s) for at,s in insertions if at<p)
    for pos,target in (info['relocations'] or {}).items():struct.pack_into('<I',raw,int(pos),newpos(target))
    for i in range(100):
        pos=u32(raw,0x34+i*4)
        if pos:struct.pack_into('<I',raw,0x34+i*4,newpos(pos))
    code=raw[start:]
    for at,s in sorted(insertions,reverse=True):code[at:at]=s
    raw=raw[:start]+code;struct.pack_into('<I',raw,0x24,len(code))
    return raw
if __name__=='__main__':
    raw=(ROOT/'cn-raw/SEEN9030.TXT.rl').read_bytes()
    info=json.loads((ROOT/'cn-json/SEEN9030.TXT.rl.json').read_text(encoding='utf8'))
    # RealLive CallDLL(14), inserted after the entrypoint marker.
    call=bytes.fromhex('2302010c000100002824ff0e00000029')
    out=compressed(insert(raw,info,[(3,call)]))
    (ROOT/'bootstrap-SEEN9030.TXT').write_bytes(out)
    print('Bootstrap script:',len(out),'bytes')
