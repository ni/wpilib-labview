#include <extcode.h>
#include <string.h>
#include <wpi/nt/ntcore_c_types.h>
#include <wpi/nt/ntcore_c.h>
#include <wpi/util/string.h>
#include "mrclib/MrcLibTypes.h"
#include "mrclib/DsComms.h"
#include "mrclib/DsCommsControl.h"

#ifdef _WIN32
#define EXPORT_FUNC __declspec(dllexport) __cdecl
#ifndef _WIN64
#pragma pack(push, 1)
#endif
#elif defined(__linux)
#define EXPORT_FUNC
#else
#error "Unsupported platform"
#endif

#define MRC_String struct WPI_String
#define MRC_FreeString WPI_FreeString

extern "C"
{

void EXPORT_FUNC LV_MRCStringToLVString(MRC_String* mrcString, LStrHandle valueHandle);
void EXPORT_FUNC LV_MRCStringToLVString(MRC_String* mrcString, LStrHandle valueHandle)
    {
        // intended for dealing with return values from MRCLib.
        // semantics are that return string is allocated and we need to copy to LV types, and free MRC allocation
        DSSetHandleSize((void*)valueHandle, mrcString->len - 1 + sizeof(LStr));
        (*(valueHandle))->cnt = mrcString->len;
        strncpy((char*)(*(valueHandle))->str, mrcString->str, mrcString->len);
        MRC_FreeString(mrcString);
    }


// Semantics are that we are wanting to share a string with MRC. They will not keep a pointer to it, but will either make
// their own copy which they own or they will reference during the call.
// We can either allocate a temp, and copy LV to temp, then pass it to them and call a cleanup on the temp,
// OR we can point to the LVString with the assumption that our VIs do not branch around and modify it while they are lookingMRC_Status
void EXPORT_FUNC LV_LVStringToMRCString(LStrHandle valueHandle, MRC_String* mrcString);
void EXPORT_FUNC LV_LVStringToMRCString(LStrHandle valueHandle, MRC_String* mrcString)
    {
        if(valueHandle) {
            mrcString->len = (*(valueHandle))->cnt;
            mrcString->str = (const char*)(*(valueHandle))->str;
        }
        else {
            mrcString->len = 0;
            mrcString->str = 0;
        }
    }

static Occurrence gMRCOccurrence = kNonOccurrence;

void MRC_CALLCONV LV_DSCallback(void);
void MRC_CALLCONV LV_DSCallback(void) {

	if(gMRCOccurrence != kNonOccurrence) {
		(void)Occur(gMRCOccurrence);
	}
}

MRC_Status EXPORT_FUNC LV_InstallDSCallback(Occurrence occurrence);
MRC_Status EXPORT_FUNC LV_InstallDSCallback(Occurrence occurrence)
{
	MRC_Status status = MRC_DsComms_SetNewDataCallback(LV_DSCallback);
	gMRCOccurrence = occurrence;
	return status;
}

MgErr EXPORT_FUNC LV_CodeStartCleanupProc(InstanceDataPtr *inst);
MgErr EXPORT_FUNC LV_CodeStartCleanupProc(InstanceDataPtr *inst)
{
	DbgPrintf("cleanup Code Start");
	MRC_Status status = MRC_DsCommsControl_SetHasUserCode(0);
	status = MRC_DsComms_SetNewDataCallback(nullptr);
	return status == MRC_STATUS_SUCCESS ? noErr : status;
}

// this dummy call exists so that we will call the cleanup also in this lib
MgErr EXPORT_FUNC LV_CodeStartMessage();
MgErr EXPORT_FUNC LV_CodeStartMessage()
{
	DbgPrintf("Code Start");
	return noErr;
}


} // extern "C"

#if defined(_WIN32) && !defined(_WIN64)
#pragma pack(pop)
#endif
