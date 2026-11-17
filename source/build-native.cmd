@echo off
call "C:\Program Files (x86)\Microsoft Visual Studio\2022\BuildTools\VC\Auxiliary\Build\vcvars32.bat" >nul
cl /nologo /LD /O2 /MT /W3 ta_cn.c gdi32.lib /link /DEF:ta_cn.def /OUT:ta_cn.dll
