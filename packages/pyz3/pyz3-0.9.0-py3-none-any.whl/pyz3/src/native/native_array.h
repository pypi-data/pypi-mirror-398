#ifndef NATIVE_ARRAY_H
#define NATIVE_ARRAY_H

#include <stddef.h>
#include <stdint.h>
#include <stdbool.h>

#ifdef __cplusplus
extern "C" {
#endif

// Forward declaration
typedef struct NativeArray NativeArray;

// Array operations
NativeArray* native_array_create(void);
void native_array_destroy(NativeArray* array);
bool native_array_push(NativeArray* array, void* value);
void* native_array_pop(NativeArray* array);
void* native_array_get(NativeArray* array, size_t index);
bool native_array_set(NativeArray* array, size_t index, void* value);
bool native_array_insert(NativeArray* array, size_t index, void* value);
bool native_array_remove(NativeArray* array, size_t index);
size_t native_array_size(NativeArray* array);
void native_array_clear(NativeArray* array);
bool native_array_reserve(NativeArray* array, size_t capacity);

// Utility operations
void** native_array_to_ptr_array(NativeArray* array, size_t* count);
void native_array_free_ptr_array(void** ptr_array);

#ifdef __cplusplus
}
#endif

#endif // NATIVE_ARRAY_H
