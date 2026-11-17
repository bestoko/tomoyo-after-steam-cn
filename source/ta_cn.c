#define WIN32_LEAN_AND_MEAN
#include <windows.h>
#include <stdio.h>
#include <string.h>
static int installed;
static HFONT old_fonts[128],new_fonts[128];
static int font_count;
static DWORD WINAPI glyph_gbk(HDC dc,UINT ch,UINT format,LPGLYPHMETRICS metrics,DWORD cb,LPVOID buf,const MAT2 *mat) {
    HFONT prev=(HFONT)GetCurrentObject(dc,OBJ_FONT),font=NULL;
    for(int i=0;i<font_count;i++)if(old_fonts[i]==prev){font=new_fonts[i];break;}
    if(!font){LOGFONTW lf;if(GetObjectW(prev,sizeof(lf),&lf)){
        lf.lfCharSet=GB2312_CHARSET;lstrcpyW(lf.lfFaceName,L"SimHei");font=CreateFontIndirectW(&lf);
        if(font&&font_count<128){old_fonts[font_count]=prev;new_fonts[font_count++]=font;}
    }}
    char text[2];WCHAR w=0;int n;
    if(ch>255){text[0]=(char)(ch>>8);text[1]=(char)ch;n=2;}else{text[0]=(char)ch;n=1;}
    if(!(format&GGO_GLYPH_INDEX))MultiByteToWideChar(936,0,text,n,&w,1);else w=(WCHAR)ch;
    if(font)SelectObject(dc,font);
    DWORD result=GetGlyphOutlineW(dc,w,format,metrics,cb,buf,mat);
    if(font)SelectObject(dc,prev);
    return result;
}
static void hook_glyph(unsigned char *base,IMAGE_NT_HEADERS *nt) {
    IMAGE_IMPORT_DESCRIPTOR *id=(IMAGE_IMPORT_DESCRIPTOR*)(base+nt->OptionalHeader.DataDirectory[IMAGE_DIRECTORY_ENTRY_IMPORT].VirtualAddress);
    for(;id->Name;id++) {
        if(!id->OriginalFirstThunk)continue;
        IMAGE_THUNK_DATA *names=(IMAGE_THUNK_DATA*)(base+id->OriginalFirstThunk),*iat=(IMAGE_THUNK_DATA*)(base+id->FirstThunk);
        for(;names->u1.AddressOfData;names++,iat++){
            if(IMAGE_SNAP_BY_ORDINAL(names->u1.Ordinal))continue;
            IMAGE_IMPORT_BY_NAME *name=(IMAGE_IMPORT_BY_NAME*)(base+names->u1.AddressOfData);
            if(!strcmp((char*)name->Name,"GetGlyphOutlineA")){
                DWORD old;VirtualProtect(&iat->u1.Function,sizeof(void*),PAGE_READWRITE,&old);
                iat->u1.Function=(DWORD_PTR)glyph_gbk;DWORD ignored;VirtualProtect(&iat->u1.Function,sizeof(void*),old,&ignored);
            }
        }
    }
}
static void install(void) {
    if (installed) return;
    installed=1;
    unsigned char *base=(unsigned char*)GetModuleHandleW(NULL);
    IMAGE_NT_HEADERS *nt=(IMAGE_NT_HEADERS*)(base+((IMAGE_DOS_HEADER*)base)->e_lfanew);
    IMAGE_SECTION_HEADER *sec=IMAGE_FIRST_SECTION(nt);
    int count=0;
    for(unsigned s=0;s<nt->FileHeader.NumberOfSections;s++) {
        if(memcmp(sec[s].Name,".text",5)) continue;
        unsigned char *p=base+sec[s].VirtualAddress;
        DWORD size=sec[s].Misc.VirtualSize, old;
        if(!VirtualProtect(p,size,PAGE_EXECUTE_READWRITE,&old)) continue;
        for(DWORD i=0;i+18<size;i++) {
            if(p[i]==0x3c && p[i+1]==0xa0 && p[i+2]==0x72 && p[i+4]==0x3c && p[i+5]==0xdf && (p[i+6]==0x76 || p[i+6]==0x77 || (p[i+6]==0x0f&&(p[i+7]==0x86||p[i+7]==0x87)))) {
                p[i+1]=0xff;
                int tail=p[i+6]==0x0f?12:8;
                if(p[i+tail]==0x3c && p[i+tail+1]==0xfe) p[i+tail+1]=0xff;
                count++;
            }
            if(p[i]==0x80 && p[i+1]>=0xf8 && p[i+2]==0xa0 && p[i+3]==0x72 && p[i+5]==0x80 && p[i+6]==p[i+1] && p[i+7]==0xdf && (p[i+8]==0x76 || p[i+8]==0x77 || (p[i+8]==0x0f&&(p[i+9]==0x86||p[i+9]==0x87)))) {
                p[i+2]=0xff;
                int tail=p[i+8]==0x0f?14:10;
                if(p[i+tail]==0x80 && p[i+tail+1]==p[i+1] && p[i+tail+2]==0xfe) p[i+tail+2]=0xff;
                count++;
            }
        }
        DWORD ignore;VirtualProtect(p,size,old,&ignore);
        FlushInstructionCache(GetCurrentProcess(),p,size);
    }
    hook_glyph(base,nt);
    FILE *f=fopen("ta_cn.log","a");
    if(f){fprintf(f,"GBK character parser installed: %d sites; exe=%p\n",count,base);fclose(f);}
}
__declspec(dllexport) int __stdcall reallive_dll_func_load(void *engine,void *unused){install();return 1;}
__declspec(dllexport) int __stdcall reallive_dll_func_free(void){return 1;}
__declspec(dllexport) int __stdcall reallive_dll_func_init(void){return 1;}
__declspec(dllexport) int __stdcall reallive_dll_func_call(int a,int b,int c,int d,int e){
    install();
    if(a==1){
        HMODULE api=GetModuleHandleA("steam_api.dll"),bridge=GetModuleHandleA("rlSteam.dll");
        typedef BOOL (__cdecl *Running)(void);typedef void *(__cdecl *Stats)(void);
        Running running=api?(Running)GetProcAddress(api,"SteamAPI_IsSteamRunning"):NULL;
        Stats stats=api?(Stats)GetProcAddress(api,"SteamUserStats"):NULL;
        FILE *f=fopen("ta_cn.log","a");
        if(f){fprintf(f,"Steam connection: running=%d; user_stats=%p; official_bridge=%p; bridge_init=%d\n",running?running():0,stats?stats():NULL,bridge,bridge?*((unsigned char*)bridge+0x164ad):0);fclose(f);}
    }
    return 1;
}
BOOL WINAPI DllMain(HINSTANCE h,DWORD why,LPVOID reserved){if(why==DLL_PROCESS_ATTACH)DisableThreadLibraryCalls(h);return TRUE;}
