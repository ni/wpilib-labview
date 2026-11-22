#include <extcode.h>
#include <string.h>

#include <wpi/nt/ntcore_c_types.h>
#include <wpi/nt/ntcore_c.h>
#include <wpi/util/string.h>

// DataLogManager decls must follow <wpi/util/string.h> so struct WPI_String is the complete type.
void DLM_Start(const struct WPI_String* dir, const struct WPI_String* filename, double period);
void DLM_Stop(void);
void DLM_Log(const struct WPI_String* message);

#ifdef _WIN32
#define EXPORT_FUNC __declspec(dllexport) __cdecl
#ifndef _WIN64
#pragma pack(push, 1)
#endif
#elif defined(__linux__) || defined(__APPLE__)
#define EXPORT_FUNC
#endif

//extern "C"
//{
    static NT_Inst gNT_InstanceHandle = 0;
    void EXPORT_FUNC RegisterInstance(NT_Inst handle);
    void EXPORT_FUNC RegisterInstance(NT_Inst handle)
    {
        gNT_InstanceHandle = handle; // store this so that abort and unregister can do cleanup
    }

    NT_Inst EXPORT_FUNC GetInstance();
    NT_Inst EXPORT_FUNC GetInstance()
    {
        return gNT_InstanceHandle; // Use this to figure if the instance is created or not
    }

    void EXPORT_FUNC CleanUpServer(InstanceDataPtr* inst);
    void EXPORT_FUNC CleanUpServer(InstanceDataPtr* inst)
    {
        (void)inst;
        DLM_Stop();
        if (gNT_InstanceHandle) {
            NT_StopClient(gNT_InstanceHandle);
            NT_StopServer(gNT_InstanceHandle);
            gNT_InstanceHandle = 0;
        }
    }

    void EXPORT_FUNC LV_GetBooleanWrapper(NT_Handle subentry, NT_Bool defaultValue, LVBoolean* value, int64* time, int64* serverTime);
    void EXPORT_FUNC LV_GetBooleanWrapper(NT_Handle subentry, NT_Bool defaultValue, LVBoolean* value, int64* time, int64* serverTime)
    {
        // call AtomicRead, copy to LV types, free NT memory
        struct NT_TimestampedBoolean timestampedValue;
        NT_GetAtomicBoolean(subentry, defaultValue, &timestampedValue);
        *value = timestampedValue.value;
        *time = timestampedValue.time;
        *serverTime = timestampedValue.serverTime;
        NT_DisposeTimestampedBoolean(&timestampedValue);
    }

    void EXPORT_FUNC LV_GetDoubleWrapper(NT_Handle subentry, double defaultValue, double* value, int64* time, int64* serverTime);
    void EXPORT_FUNC LV_GetDoubleWrapper(NT_Handle subentry, double defaultValue, double* value, int64* time, int64* serverTime)
    {
        // call AtomicRead, copy to LV types, free NT memory
        struct NT_TimestampedDouble timestampedValue;
        NT_GetAtomicDouble(subentry, defaultValue, &timestampedValue);
        *value = timestampedValue.value;
        *time = timestampedValue.time;
        *serverTime = timestampedValue.serverTime;
        NT_DisposeTimestampedDouble(&timestampedValue);
    }

    void EXPORT_FUNC LV_GetFloatWrapper(NT_Handle subentry, float defaultValue, float* value, int64* time, int64* serverTime);
    void EXPORT_FUNC LV_GetFloatWrapper(NT_Handle subentry, float defaultValue, float* value, int64* time, int64* serverTime)
    {
        // call AtomicRead, copy to LV types, free NT memory
        struct NT_TimestampedFloat timestampedValue;
        NT_GetAtomicFloat(subentry, defaultValue, &timestampedValue);
        *value = timestampedValue.value;
        *time = timestampedValue.time;
        *serverTime = timestampedValue.serverTime;
        NT_DisposeTimestampedFloat(&timestampedValue);
    }

    void EXPORT_FUNC LV_GetIntWrapper(NT_Handle subentry, int64 defaultValue, int64* value, int64* time, int64* serverTime);
    void EXPORT_FUNC LV_GetIntWrapper(NT_Handle subentry, int64 defaultValue, int64* value, int64* time, int64* serverTime)
    {
        // call AtomicRead, copy to LV types, free NT memory
        struct NT_TimestampedInteger timestampedValue;
        NT_GetAtomicInteger(subentry, defaultValue, &timestampedValue);
        *value = timestampedValue.value;
        *time = timestampedValue.time;
        *serverTime = timestampedValue.serverTime;
        NT_DisposeTimestampedInteger(&timestampedValue);
    }

    // pass the pointer directly to the string and the length
    void CopyLVStrFromNTStr(const char* str, size_t len, LStrHandle strHandle);
    void CopyLVStrFromNTStr(const char* str, size_t len, LStrHandle strHandle)
    {
        MgErr err;
        // len and str are network-derived (NT values / topic names); treat as
        // untrusted: reject lengths the int32 cnt field cannot represent, and
        // never write more bytes than the handle actually holds.
        if (!strHandle || (str == NULL && len > 0) || len > (size_t)0x7FFFFFFF) {
            if (strHandle && *strHandle)
                (*strHandle)->cnt = 0;
            return;
        }
        err = DSSetHandleSize((void*)strHandle, len - 1 + sizeof(LStr));
        if (err) {
            // Allocation failed: the handle keeps its old (smaller) size.
            // Leave a valid empty string instead of overflowing it.
            if (*strHandle)
                (*strHandle)->cnt = 0;
            return;
        }
        (*(strHandle))->cnt = (int32)len;
        if (len > 0)
            strncpy((char*)(*(strHandle))->str, str, len);
    }

    void EXPORT_FUNC LV_GetStringWrapper(NT_Handle subentry, char* defaultValue, LStrHandle valueHandle, int64* time, int64* serverTime);
    void EXPORT_FUNC LV_GetStringWrapper(NT_Handle subentry, char* defaultValue, LStrHandle valueHandle, int64* time, int64* serverTime)
    {
        // call AtomicRead, copy to LV types, free NT memory
        struct NT_TimestampedString timestampedValue;
        struct WPI_String defaultValueStruct;
        WPI_InitString(&defaultValueStruct, defaultValue);
        NT_GetAtomicString(subentry, &defaultValueStruct, &timestampedValue);
        CopyLVStrFromNTStr(timestampedValue.value.str, timestampedValue.value.len, valueHandle);
        *time = timestampedValue.time;
        *serverTime = timestampedValue.serverTime;
        NT_DisposeTimestampedString(&timestampedValue);
    }

    struct RawType
    {
        int32 dimSize;
        uInt8 elt[1];
    };
    typedef struct RawType** RawHdl;

    void EXPORT_FUNC LV_GetRawWrapper(NT_Handle subentry, RawHdl defaultValue, RawHdl valueHandle, int64* time, int64* serverTime);
    void EXPORT_FUNC LV_GetRawWrapper(NT_Handle subentry, RawHdl defaultValue, RawHdl valueHandle, int64* time, int64* serverTime)
    {
        // call AtomicRead, copy to LV types, free NT memory
        struct NT_TimestampedRaw timestampedValue;
        MgErr err;
        NT_GetAtomicRaw(subentry, (*defaultValue)->elt, (*defaultValue)->dimSize, &timestampedValue);
        // timestampedValue.len is network-derived; copy only after the resize
        // is confirmed and the length fits the int32 dimSize field.
        if (timestampedValue.len > (size_t)0x7FFFFFFF) {
            (*valueHandle)->dimSize = 0;
        } else {
            err = DSSetHandleSize((void*)valueHandle, timestampedValue.len - 1 + sizeof(LStr));
            if (err) {
                (*valueHandle)->dimSize = 0;
            } else {
                (*valueHandle)->dimSize = (int32)timestampedValue.len;
                MoveBlock(timestampedValue.value, (*valueHandle)->elt, timestampedValue.len * sizeof(uInt8));
            }
        }
        *time = timestampedValue.time;
        *serverTime = timestampedValue.serverTime;
        NT_DisposeTimestampedRaw(&timestampedValue);
    }

    struct ArrayStringType
    {
        int32 dimSize;
        LStrHandle elt[1];
    };
    typedef struct ArrayStringType** ArrStrHdl;

    void MakeNTPtrsFromStringHandle(int32 arraySize, ArrStrHdl valueHandle, struct WPI_String* NTPtr);
    void MakeNTPtrsFromStringHandle(int32 arraySize, ArrStrHdl valueHandle, struct WPI_String* NTPtr)
    {
        for (int i = 0; i < arraySize; i++) {
            LStrHandle strHandle = (*valueHandle)->elt[i];
            NTPtr[i].len = (*strHandle)->cnt;
            NTPtr[i].str = (char*)(*strHandle)->str;
        }
    }

    // LabVIEW only disposes element handles in [0, dimSize), so any handle left in a
    // slot past the published dimSize is leaked. Dispose and clear [first, end).
    static void DisposeStringElements(ArrStrHdl valueHandle, int32 first, int32 end)
    {
        for (int32 i = first; i < end; i++) {
            if ((*valueHandle)->elt[i]) {
                DSDisposeHandle((*valueHandle)->elt[i]);
                (*valueHandle)->elt[i] = NULL;
            }
        }
    }

    void CopyArrStringHandleFromNTPtrs(size_t count, ArrStrHdl valueHandle, struct WPI_String* NTPtr);
    void CopyArrStringHandleFromNTPtrs(size_t count, ArrStrHdl valueHandle, struct WPI_String* NTPtr)
    {
        // count and the element strings are network-derived; every length must fit
        // the int32 dimSize/cnt fields, and nothing is written through a handle
        // whose resize was not confirmed.
        int32 oldSize = (*valueHandle)->dimSize;
        int32 arraySize = count > (size_t)0x7FFFFFFF ? 0 : (int32)count;
        MgErr err;

        DisposeStringElements(valueHandle, arraySize, oldSize);
        err = DSSetHSzClr(valueHandle, sizeof(struct ArrayStringType) + (arraySize - 1) * sizeof(LStrHandle));
        if (err) {
            // The handle keeps its old size; release what it still holds and
            // publish an empty array.
            DisposeStringElements(valueHandle, 0, arraySize < oldSize ? arraySize : oldSize);
            (*valueHandle)->dimSize = 0;
            return;
        }
        // Slots past the old dimSize are not owned by LabVIEW; never treat their
        // contents as handles to resize.
        for (int32 i = oldSize; i < arraySize; i++)
            (*valueHandle)->elt[i] = NULL;

        for (int32 i = 0; i < arraySize; i++) {
            size_t len = NTPtr[i].len;
            if (len > (size_t)0x7FFFFFFF - sizeof(LStr)) {
                err = mFullErr;
            } else if ((*valueHandle)->elt[i]) {
                err = DSSetHandleSize((*valueHandle)->elt[i], len - 1 + sizeof(LStr));
            } else {
                (*valueHandle)->elt[i] = (LStrHandle)DSNewHandle(len - 1 + sizeof(LStr));
                err = (*valueHandle)->elt[i] ? mgNoErr : mFullErr;
            }
            if (err) {
                // Truncate to the elements already written; release the rest.
                DisposeStringElements(valueHandle, i, arraySize);
                (*valueHandle)->dimSize = i;
                return;
            }
            (*(*valueHandle)->elt[i])->cnt = (int32)len;
            if (len > 0)
                strncpy((char*)(*(*valueHandle)->elt[i])->str, NTPtr[i].str, len);
        }
        (*valueHandle)->dimSize = arraySize;
    }

    NT_Bool EXPORT_FUNC LV_SetStringArrayWrapper(NT_Handle pubentry, int64 time, ArrStrHdl valueHandle);
    NT_Bool EXPORT_FUNC LV_SetStringArrayWrapper(NT_Handle pubentry, int64 time, ArrStrHdl valueHandle)
    {
        int arraySize = (*valueHandle)->dimSize;
        struct WPI_String* NTPtr = (struct WPI_String*)DSNewPtr(arraySize * sizeof(struct WPI_String));
        if (!NTPtr) return 0;
        // fill in with pointers into our handles
        MakeNTPtrsFromStringHandle(arraySize, valueHandle, NTPtr);
        NT_Bool returnVal = NT_SetStringArray(pubentry, time, NTPtr, arraySize);
        DSDisposePtr(NTPtr);
        return returnVal;
    }

    void EXPORT_FUNC LV_GetStringArrayWrapper(NT_Handle subentry, ArrStrHdl defaultValue, ArrStrHdl valueHandle, int64* time, int64* serverTime);
    void EXPORT_FUNC LV_GetStringArrayWrapper(NT_Handle subentry, ArrStrHdl defaultValue, ArrStrHdl valueHandle, int64* time, int64* serverTime)
    {
        // call AtomicRead, copy to LV types, free NT memory
        struct NT_TimestampedStringArray timestampedValue;
        struct WPI_String* defData = NULL;
        int defaultArraySize = (*defaultValue)->dimSize;
        if (defaultArraySize) {
            defData = (struct WPI_String*)DSNewPtr(defaultArraySize * sizeof(struct WPI_String));
            if (defData)
                MakeNTPtrsFromStringHandle(defaultArraySize, defaultValue, defData);
            else
                defaultArraySize = 0; // out of memory: fall back to an empty default
        }
        NT_GetAtomicStringArray(subentry, defData, defaultArraySize, &timestampedValue);
        CopyArrStringHandleFromNTPtrs(timestampedValue.len, valueHandle, timestampedValue.value);
        *time = timestampedValue.time;
        *serverTime = timestampedValue.serverTime;
        if (defData) DSDisposePtr(defData);
        NT_DisposeTimestampedStringArray(&timestampedValue);
    }

    struct ArrayDoubleType
    {
        int32 dimSize;
        double elt[1];
    };
    typedef struct ArrayDoubleType** ArrDblHdl;

    struct ArrayFloatType
    {
        int32 dimSize;
        float elt[1];
    };
    typedef struct ArrayFloatType** ArrFloatHdl;

    struct ArrayIntType
    {
        int32 dimSize;
        int64 elt[1];
    };
    typedef struct ArrayIntType** ArrIntHdl;

    void CopyLVNumericArray(void* value, size_t len, size_t eltSize, size_t singleEltSize, ArrDblHdl valueHandle);
    void CopyLVNumericArray(void* value, size_t len, size_t eltSize, size_t singleEltSize, ArrDblHdl valueHandle)
    {
        MgErr err;
        if (len > (size_t)0x7FFFFFFF) { // network-derived length; int32 dimSize
            (*valueHandle)->dimSize = 0;
            return;
        }
        err = DSSetHandleSize((void*)valueHandle, (len - 1) * eltSize + singleEltSize);
        if (err) {
            // Allocation failed: handle keeps its old size; do not copy.
            (*valueHandle)->dimSize = 0;
            return;
        }
        (*valueHandle)->dimSize = (int32)len;
        MoveBlock(value, (*valueHandle)->elt, len * eltSize);
    }

    void CopyLVFloatArray(void* value, size_t len, size_t eltSize, size_t singleEltSize, ArrFloatHdl valueHandle);
    void CopyLVFloatArray(void* value, size_t len, size_t eltSize, size_t singleEltSize, ArrFloatHdl valueHandle)
    {
        MgErr err;
        if (len > (size_t)0x7FFFFFFF) { // network-derived length; int32 dimSize
            (*valueHandle)->dimSize = 0;
            return;
        }
        err = DSSetHandleSize((void*)valueHandle, (len - 1) * eltSize + singleEltSize);
        if (err) {
            // Allocation failed: handle keeps its old size; do not copy.
            (*valueHandle)->dimSize = 0;
            return;
        }
        (*valueHandle)->dimSize = (int32)len;
        MoveBlock(value, (*valueHandle)->elt, len * eltSize);
    }

    void CopyLVIntArray(void* value, size_t len, size_t eltSize, size_t singleEltSize, ArrIntHdl valueHandle);
    void CopyLVIntArray(void* value, size_t len, size_t eltSize, size_t singleEltSize, ArrIntHdl valueHandle)
    {
        MgErr err;
        if (len > (size_t)0x7FFFFFFF) { // network-derived length; int32 dimSize
            (*valueHandle)->dimSize = 0;
            return;
        }
        err = DSSetHandleSize((void*)valueHandle, (len - 1) * eltSize + singleEltSize);
        if (err) {
            // Allocation failed: handle keeps its old size; do not copy.
            (*valueHandle)->dimSize = 0;
            return;
        }
        (*valueHandle)->dimSize = (int32)len;
        MoveBlock(value, (*valueHandle)->elt, len * eltSize);
    }

    void EXPORT_FUNC LV_GetDoubleArrayWrapper(NT_Handle subentry, ArrDblHdl defaultValue, ArrDblHdl valueHandle, int64* time, int64* serverTime);
    void EXPORT_FUNC LV_GetDoubleArrayWrapper(NT_Handle subentry, ArrDblHdl defaultValue, ArrDblHdl valueHandle, int64* time, int64* serverTime)
    {
        // call AtomicRead, copy to LV types, free NT memory
        struct NT_TimestampedDoubleArray timestampedValue;
        NT_GetAtomicDoubleArray(subentry, (*defaultValue)->elt, (*defaultValue)->dimSize, &timestampedValue);
        CopyLVNumericArray(timestampedValue.value, timestampedValue.len, sizeof(double), sizeof(struct ArrayDoubleType), valueHandle);
        *time = timestampedValue.time;
        *serverTime = timestampedValue.serverTime;
        NT_DisposeTimestampedDoubleArray(&timestampedValue);
    }

    void EXPORT_FUNC LV_GetFloatArrayWrapper(NT_Handle subentry, ArrFloatHdl defaultValue, ArrFloatHdl valueHandle, int64* time, int64* serverTime);
    void EXPORT_FUNC LV_GetFloatArrayWrapper(NT_Handle subentry, ArrFloatHdl defaultValue, ArrFloatHdl valueHandle, int64* time, int64* serverTime)
    {
        // call AtomicRead, copy to LV types, free NT memory
        struct NT_TimestampedFloatArray timestampedValue;
        NT_GetAtomicFloatArray(subentry, (*defaultValue)->elt, (*defaultValue)->dimSize, &timestampedValue);
        CopyLVFloatArray(timestampedValue.value, timestampedValue.len, sizeof(float), sizeof(struct ArrayFloatType), valueHandle);
        *time = timestampedValue.time;
        *serverTime = timestampedValue.serverTime;
        NT_DisposeTimestampedFloatArray(&timestampedValue);
    }

    void EXPORT_FUNC LV_GetIntegerArrayWrapper(NT_Handle subentry, ArrIntHdl defaultValue, ArrIntHdl valueHandle, int64* time, int64* serverTime);
    void EXPORT_FUNC LV_GetIntegerArrayWrapper(NT_Handle subentry, ArrIntHdl defaultValue, ArrIntHdl valueHandle, int64* time, int64* serverTime)
    {
        // call AtomicRead, copy to LV types, free NT memory
        struct NT_TimestampedIntegerArray timestampedValue;
        NT_GetAtomicIntegerArray(subentry, (const int64_t*)(*defaultValue)->elt, (*defaultValue)->dimSize, &timestampedValue);
        CopyLVIntArray(timestampedValue.value, timestampedValue.len, sizeof(int64), sizeof(struct ArrayIntType), valueHandle);
        *time = timestampedValue.time;
        *serverTime = timestampedValue.serverTime;
        NT_DisposeTimestampedIntegerArray(&timestampedValue);
    }

    struct ArrayBooleanType
    {
        int32 dimSize;
        LVBoolean elt[1];
    };
    typedef struct ArrayBooleanType** ArrBoolHdl;

    void CopyLVBooleanArray(NT_Bool* value, size_t len, ArrBoolHdl valueHandle);
    void CopyLVBooleanArray(NT_Bool* value, size_t len, ArrBoolHdl valueHandle)
    {
        MgErr err;
        if (len > (size_t)0x7FFFFFFF) { // network-derived length; int32 dimSize
            (*valueHandle)->dimSize = 0;
            return;
        }
        err = DSSetHandleSize((void*)valueHandle, (len - 1) * sizeof(LVBoolean) + sizeof(struct ArrayBooleanType));
        if (err) {
            // Allocation failed: handle keeps its old size; do not write.
            (*valueHandle)->dimSize = 0;
            return;
        }
        (*valueHandle)->dimSize = (int32)len;
        for (size_t i = 0; i < len; i++)
            (*valueHandle)->elt[i] = value[i]; // two different size ints
    }

    void EXPORT_FUNC LV_GetBooleanArrayWrapper(NT_Handle subentry, ArrBoolHdl defaultValue, ArrBoolHdl valueHandle, int64* time, int64* serverTime);
    void EXPORT_FUNC LV_GetBooleanArrayWrapper(NT_Handle subentry, ArrBoolHdl defaultValue, ArrBoolHdl valueHandle, int64* time, int64* serverTime)
    {
        // call AtomicRead, copy to LV types, free NT memory
        struct NT_TimestampedBooleanArray timestampedValue;
        NT_Bool* defaultCopy = NULL;
        size_t len = (*defaultValue)->dimSize;
        if (len) {
            // allocate, copy, and remember to delete
            defaultCopy = (NT_Bool*)DSNewPtr(sizeof(NT_Bool) * len);
            for (size_t i = 0; i < len; i++)
                defaultCopy[i] = (*defaultValue)->elt[i];
        }
        NT_GetAtomicBooleanArray(subentry, defaultCopy, (*defaultValue)->dimSize, &timestampedValue);
        CopyLVBooleanArray(timestampedValue.value, timestampedValue.len, valueHandle);
        *time = timestampedValue.time;
        *serverTime = timestampedValue.serverTime;
        if (defaultCopy) {
            DSDisposePtr(defaultCopy);
            defaultCopy = NULL;
        }
        NT_DisposeTimestampedBooleanArray(&timestampedValue);
    }

    struct ArrayHandleType
    {
        int32 dimSize;
        int32 elt[1];
    };
    typedef struct ArrayHandleType** ArrHandleHdl;

    void EXPORT_FUNC LV_GetTopics(NT_Inst inst, const char* prefix, uInt32 typeMask, ArrHandleHdl topicArray);
    void EXPORT_FUNC LV_GetTopics(NT_Inst inst, const char* prefix, uInt32 typeMask, ArrHandleHdl topicArray)
    {
        size_t count = 0;
        struct WPI_String prefixStruct;
        WPI_InitString(&prefixStruct, prefix);
        NT_Topic* topics = NT_GetTopics(inst, &prefixStruct, typeMask, &count);
        // count is driven by peer-published topics; copy only after the resize
        // succeeds and the count fits the int32 dimSize field.
        if (!topics || count > (size_t)0x7FFFFFFF
            || DSSetHandleSize((void*)topicArray, (count - 1) * sizeof(int32) + sizeof(struct ArrayHandleType))) {
            (*topicArray)->dimSize = 0;
        } else {
            (*topicArray)->dimSize = (int32)count;
            MoveBlock(topics, (*topicArray)->elt, count * sizeof(int32));
        }
        // ntcore allocates the array with malloc in its own runtime and has no
        // dedicated dispose for it; all NT_Free*Array functions are std::free in
        // that same runtime, so use one rather than this module's free().
        NT_FreeCharArray((char*)topics);
    }

    struct LVClustOutput
    {
        double numVal;
        float floatVal;
        int64 intVal;
        LStrHandle strVal;
        ArrBoolHdl boolArray;
        ArrDblHdl numArray;
        ArrFloatHdl floatArray;
        ArrIntHdl intArray;
        ArrStrHdl strArray;
        LVBoolean boolVal;
    };

    // called for each element of the valueNotification array with head and index and output cluster for just that element's type
    // LV will retrieve from cluster and put into variant because we can't access variant API from C
    int32 EXPORT_FUNC LV_TranslateValueNotifications(struct NT_Event* arr, size_t index, struct LVClustOutput* output, int64* time, int64* serverTime, LStrHandle nameHdl);
    int32 EXPORT_FUNC LV_TranslateValueNotifications(struct NT_Event* arr, size_t index, struct LVClustOutput* output, int64* time, int64* serverTime, LStrHandle nameHdl)
    {
        if (!(arr[index].flags & (NT_EVENT_VALUE_ALL)))
            return NT_UNASSIGNED;
        int32 topic = arr[index].data.valueData.topic;
        enum NT_Type datatype = arr[index].data.valueData.value.type;
        *time = arr[index].data.valueData.value.last_change;
        *serverTime = arr[index].data.valueData.value.server_time;
        struct NT_Value* value = &arr[index].data.valueData.value;
        if (topic) {
            struct WPI_String name;
            NT_GetTopicName(topic, &name);
            CopyLVStrFromNTStr(name.str, name.len, nameHdl);
            // NT_GetTopicName allocates the string; the caller must free it.
            WPI_FreeString(&name);
        }

        switch (datatype) {
            default:
                break;
            case NT_UNASSIGNED:
                break;
            case NT_BOOLEAN:
                output->boolVal = value->data.v_boolean;
                break;
            case NT_DOUBLE:
                output->numVal = value->data.v_double;
                break;
            case NT_STRING:
                CopyLVStrFromNTStr(value->data.v_string.str, value->data.v_string.len, output->strVal);
                break;
            case NT_RAW:
                CopyLVStrFromNTStr((char*)value->data.v_raw.data, value->data.v_raw.size, output->strVal);
                break;
            case NT_BOOLEAN_ARRAY:
                CopyLVBooleanArray(value->data.arr_boolean.arr, value->data.arr_boolean.size, output->boolArray);
                break;
            case NT_DOUBLE_ARRAY:
                CopyLVNumericArray(value->data.arr_double.arr, value->data.arr_double.size, sizeof(double), sizeof(struct ArrayDoubleType), output->numArray);
                break;
            case NT_STRING_ARRAY:
                CopyArrStringHandleFromNTPtrs(value->data.arr_string.size, output->strArray, value->data.arr_string.arr);
            case NT_RPC:
                break;
            case NT_INTEGER:
                output->intVal = value->data.v_int;
                break;
            case NT_FLOAT:
                output->floatVal = value->data.v_float;
                break;
            case NT_INTEGER_ARRAY:
                CopyLVIntArray(value->data.arr_float.arr, value->data.arr_float.size, sizeof(int64), sizeof(struct ArrayIntType), output->intArray);
                break;
            case NT_FLOAT_ARRAY:
                CopyLVFloatArray(value->data.arr_int.arr, value->data.arr_int.size, sizeof(float), sizeof(struct ArrayFloatType), output->floatArray);
                break;
        }
        return datatype;
    }

    // called to access a notification about topics
    int32 EXPORT_FUNC LV_ProcessTopicNotifications(struct NT_Event* arr, size_t index, LStrHandle nameHdl, LVBoolean* add);
    int32 EXPORT_FUNC LV_ProcessTopicNotifications(struct NT_Event* arr, size_t index, LStrHandle nameHdl, LVBoolean* add)
    {
        if (arr[index].flags & (NT_EVENT_PUBLISH | NT_EVENT_UNPUBLISH)) {
            *add = (arr[index].flags & NT_EVENT_PUBLISH) ? LVBooleanTrue : LVBooleanFalse;
            struct WPI_String* name = &(arr[index].data.topicInfo.name);
            CopyLVStrFromNTStr(name->str, name->len, nameHdl);
            return 1;
        }
        return 0;
    }

    void EXPORT_FUNC DoNothingCallback(void* data, const struct NT_Event* event);
    void EXPORT_FUNC DoNothingCallback(void* data, const struct NT_Event* event)
    {
        (void)data;
        (void)event;
        // could put a breakpoint to verify or do stats here, but this was added to early-register so first read works
    }

    int32 EXPORT_FUNC LV_AddSubscriber(NT_Inst inst, LStrHandle nameHdl);
    int32 EXPORT_FUNC LV_AddSubscriber(NT_Inst inst, LStrHandle nameHdl)
    {
        struct WPI_String prefix;
        prefix.str = (char *)LHStrBuf(nameHdl);
        prefix.len = LHStrLen(nameHdl);
        return NT_AddListenerSingle(inst, &prefix, 0xC0, NULL, &DoNothingCallback);
    }


    void EXPORT_FUNC LV_GetTopicName(NT_Topic topic, LStrHandle nameHdl);
    void EXPORT_FUNC LV_GetTopicName(NT_Topic topic, LStrHandle nameHdl) {
        struct WPI_String name;
        NT_GetTopicName(topic, &name);
        CopyLVStrFromNTStr(name.str, name.len, nameHdl);
        // NT_GetTopicName allocates the string; the caller must free it.
        WPI_FreeString(&name);
    }



    int32 EXPORT_FUNC LV_AddPolledListenerSingle(NT_ListenerPoller poller, LStrHandle prefixHdl, unsigned int mask);
    int32 EXPORT_FUNC LV_AddPolledListenerSingle(NT_ListenerPoller poller, LStrHandle prefixHdl, unsigned int mask) {
        struct WPI_String prefix;
        prefix.str = (char *)LHStrBuf(prefixHdl);
        prefix.len = LHStrLen(prefixHdl);
        return NT_AddPolledListenerSingle(poller, &prefix, mask);
    }

     void EXPORT_FUNC LV_StartDfltServer();

    // This was added so I can test very basic NT stuff, no param packing, nothing to make things more complicated
    void EXPORT_FUNC LV_StartDfltServer() {
        struct WPI_String WPIDirName;
        struct WPI_String WPIAddr;
        struct WPI_String WPImDNS;
        WPI_InitString(&WPIDirName, "");
        WPI_InitString(&WPIAddr, "");
        WPI_InitString(&WPImDNS, "");
        NT_StartServer(NT_GetDefaultInstance(), &WPIDirName, &WPIAddr, &WPImDNS, 5810);
    }

    // other routines to wrap
    void EXPORT_FUNC LV_StartServer2(NT_Inst inst, LStrHandle persistName, LStrHandle address, LStrHandle mdnsService, unsigned int port4);
    void EXPORT_FUNC LV_StartServer2(NT_Inst inst, LStrHandle persistName, LStrHandle address, LStrHandle mdnsService, unsigned int port4)
    {
        struct WPI_String WPIDirName;
        struct WPI_String WPIAddr;
        struct WPI_String WPImDNSService;

        WPIDirName.str = (char *)LHStrBuf(persistName);
        WPIDirName.len = LHStrLen(persistName);
        WPIAddr.str = (char *)LHStrBuf(address);
        WPIAddr.len = LHStrLen(address);
        WPImDNSService.str = (char *)LHStrBuf(mdnsService);
        WPImDNSService.len = LHStrLen(mdnsService);

        NT_StartServer(inst, &WPIDirName, &WPIAddr, &WPImDNSService, port4);
    }

    void EXPORT_FUNC LV_DLM_Start(LStrHandle dir, LStrHandle name, double period);
    void EXPORT_FUNC LV_DLM_Start(LStrHandle dir, LStrHandle name, double period)
    {
        struct WPI_String WPIDirName;
        WPIDirName.str = (char *)LHStrBuf(dir);
        WPIDirName.len = LHStrLen(dir);
        struct WPI_String WPIName;
        WPIName.str = (char *)LHStrBuf(name);
        WPIName.len = LHStrLen(name);
        DLM_Start(&WPIDirName, &WPIName, period);
    }

    NT_Publisher EXPORT_FUNC LV_Publish(NT_Topic topic, enum NT_Type type, LStrHandle typeStr, const struct NT_PubSubOptions *options);
    NT_Publisher EXPORT_FUNC LV_Publish(NT_Topic topic, enum NT_Type type, LStrHandle typeStr, const struct NT_PubSubOptions *options)
    {
        struct WPI_String WPITypeStr;
        WPITypeStr.str = (char *)LHStrBuf(typeStr);
        WPITypeStr.len = LHStrLen(typeStr);
        return NT_Publish(topic, type, &WPITypeStr, options);
    }

    NT_Subscriber EXPORT_FUNC LV_Subscribe(NT_Topic topic, enum NT_Type type, LStrHandle typeStr, const struct NT_PubSubOptions *options);
    NT_Subscriber EXPORT_FUNC LV_Subscribe(NT_Topic topic, enum NT_Type type, LStrHandle typeStr, const struct NT_PubSubOptions *options)
    {
        struct WPI_String WPITypeStr;
        WPITypeStr.str = (char *)LHStrBuf(typeStr);
        WPITypeStr.len = LHStrLen(typeStr);
        return NT_Subscribe(topic, type, &WPITypeStr, options);
    }

    NT_Topic EXPORT_FUNC LV_GetTopic(NT_Inst inst, LStrHandle name);
    NT_Topic EXPORT_FUNC LV_GetTopic(NT_Inst inst, LStrHandle name)
    {
        struct WPI_String WPIName;
        WPIName.str = (char *)LHStrBuf(name);
        WPIName.len = LHStrLen(name);
        return NT_GetTopic(inst, &WPIName);
    }

    NT_Bool EXPORT_FUNC LV_SetString(NT_Handle pubentry, int64 time, LStrHandle valueHandle);
    NT_Bool EXPORT_FUNC LV_SetString(NT_Handle pubentry, int64 time, LStrHandle valueHandle)
    {
        struct WPI_String WPIStrValue;
        WPIStrValue.str = (char *)LHStrBuf(valueHandle);
        WPIStrValue.len = LHStrLen(valueHandle);
        return NT_SetString(pubentry, time, &WPIStrValue);
    }

    void EXPORT_FUNC LV_StartClient4(NT_Inst inst, LStrHandle identity);
    void EXPORT_FUNC LV_StartClient4(NT_Inst inst, LStrHandle identity)
    {
        struct WPI_String WPIStrValue;
        WPIStrValue.str = (char *)LHStrBuf(identity);
        WPIStrValue.len = LHStrLen(identity);
        NT_StartClient(inst, &WPIStrValue);
    }

    void EXPORT_FUNC LV_DLM_Log(LStrHandle message);
    void EXPORT_FUNC LV_DLM_Log(LStrHandle message)
    {
        struct WPI_String WPIMsg;
        WPIMsg.str = (char *)LHStrBuf(message);
        WPIMsg.len = LHStrLen(message);
        DLM_Log(&WPIMsg);
    }
//} // extern "C"

#if defined(_WIN32) && !defined(_WIN64)
#pragma pack(pop)
#endif
