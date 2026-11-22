/*
 * Windows: the LabVIEW functions the shims call, looked up at run time in the LabVIEW process
 * that loaded the shim (LabVIEW.exe, or lvrt.dll in the run-time engine). This replaces linking
 * against cintools' labviewv.lib. Prototypes come from cintools/extcode.h.
 */
#include <stdarg.h>
#include <stdio.h>
#include <string.h>
#include <windows.h>

#include "extcode.h"

static FARPROC lv_function(const char* name)
{
    static const wchar_t* const modules[] = {NULL, L"lvrt.dll"};
    for (size_t i = 0; i < sizeof(modules) / sizeof(modules[0]); i++) {
        HMODULE module = GetModuleHandleW(modules[i]);
        FARPROC f = module ? GetProcAddress(module, name) : NULL;
        if (f) {
            return f;
        }
    }
    return NULL;
}

/* Declares `fn`, LabVIEW's function `name`, of pointer type `type`, resolved on first use. */
#define LV_FUNCTION(type, name)                    \
    static type fn;                                \
    if (!fn) {                                     \
        fn = (type)(void*)lv_function(name);       \
    }

typedef UHandle(_FUNCC* NewHandleFn)(size_t);
typedef UPtr(_FUNCC* NewPtrFn)(size_t);
typedef MgErr(_FUNCC* DisposeFn)(void*);
typedef MgErr(_FUNCC* SetSizeFn)(void*, size_t);
typedef void(_FUNCC* MoveBlockFn)(const void*, void*, size_t);
typedef MgErr(_FUNCC* OccurFn)(Occurrence);
typedef MgErr(_FUNCC* DbgPrintfFn)(const char*, ...);

UHandle _FUNCC DSNewHandle(size_t size)
{
    LV_FUNCTION(NewHandleFn, "DSNewHandle");
    return fn ? fn(size) : NULL;
}

UPtr _FUNCC DSNewPtr(size_t size)
{
    LV_FUNCTION(NewPtrFn, "DSNewPtr");
    return fn ? fn(size) : NULL;
}

MgErr _FUNCC DSDisposeHandle(void* h)
{
    LV_FUNCTION(DisposeFn, "DSDisposeHandle");
    return fn ? fn(h) : mgArgErr;
}

MgErr _FUNCC DSDisposePtr(void* p)
{
    LV_FUNCTION(DisposeFn, "DSDisposePtr");
    return fn ? fn(p) : mgArgErr;
}

MgErr _FUNCC DSSetHandleSize(void* h, size_t size)
{
    LV_FUNCTION(SetSizeFn, "DSSetHandleSize");
    return fn ? fn(h, size) : mFullErr;
}

MgErr _FUNCC DSSetHSzClr(void* h, size_t size)
{
    LV_FUNCTION(SetSizeFn, "DSSetHSzClr");
    return fn ? fn(h, size) : mFullErr;
}

void _FUNCC MoveBlock(const void* src, void* dest, size_t size)
{
    LV_FUNCTION(MoveBlockFn, "MoveBlock");
    if (fn) {
        fn(src, dest, size);
    } else if (size) {
        memmove(dest, src, size);
    }
}

MgErr _FUNCC Occur(Occurrence o)
{
    LV_FUNCTION(OccurFn, "Occur");
    return fn ? fn(o) : mgArgErr;
}

MgErr _FUNCC DbgPrintf(const char* fmt, ...)
{
    LV_FUNCTION(DbgPrintfFn, "DbgPrintf");
    char buf[1024];
    va_list args;
    va_start(args, fmt);
    vsnprintf(buf, sizeof(buf), fmt, args);
    va_end(args);
    return fn ? fn("%s", buf) : noErr;
}
