# LabVIEW cintools headers

`extcode.h`, `platdefines.h`, `fundtypes.h`, `lv_prolog.h`, and `lv_epilog.h` from LabVIEW 2026 Q3
(26.3.0f541) `cintools`, unmodified. They declare LabVIEW's C API (data types, the memory manager,
occurrences) that the shim libraries in [`src/`](..) call.

NI's guidance for building C code against LabVIEW without LabVIEW installed is to copy these
headers from `cintools`
([Calling a LabVIEW DLL from a LabWindows/CVI or C Project](https://knowledge.ni.com/KnowledgeArticleDetails?id=kA03q000000YIIQCA4)).
They keep NI's copyright notice and are not covered by this repository's BSD-3-Clause license.

On Windows the shims don't link against `labviewv.lib`; [`lvapi_win.c`](../common/lvapi_win.c)
looks the functions up in the LabVIEW process at run time instead.
