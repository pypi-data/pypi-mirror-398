#ifndef NATIVE_DICT_H
#define NATIVE_DICT_H

#include <stddef.h>
#include <stdint.h>
#include <stdbool.h>

#ifdef __cplusplus
extern "C" {
#endif

// Forward declarations
typedef struct NativeDict NativeDict;
typedef struct NativeDictEntry NativeDictEntry;
typedef struct NativeDictIterator NativeDictIterator;

// Dict operations
NativeDict* native_dict_create(void);
void native_dict_destroy(NativeDict* dict);
bool native_dict_set(NativeDict* dict, const char* key, void* value);
void* native_dict_get(NativeDict* dict, const char* key);
bool native_dict_delete(NativeDict* dict, const char* key);
bool native_dict_contains(NativeDict* dict, const char* key);
size_t native_dict_size(NativeDict* dict);
void native_dict_clear(NativeDict* dict);

// Iterator operations
NativeDictIterator* native_dict_iter_create(NativeDict* dict);
void native_dict_iter_destroy(NativeDictIterator* iter);
bool native_dict_iter_next(NativeDictIterator* iter, const char** key, void** value);

// Utility operations
const char** native_dict_keys(NativeDict* dict, size_t* count);
void** native_dict_values(NativeDict* dict, size_t* count);
void native_dict_free_keys(const char** keys);
void native_dict_free_values(void** values);

#ifdef __cplusplus
}
#endif

#endif // NATIVE_DICT_H
