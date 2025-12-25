#include "native_array.h"
#include "utarray.h"
#include <stdlib.h>
#include <string.h>

// Array structure
struct NativeArray {
    UT_array* array;
};

// ICD (init, copy, dtor) for void* elements
static UT_icd void_ptr_icd = {
    sizeof(void*),  // size
    NULL,           // init
    NULL,           // copy
    NULL            // dtor
};

// Create a new array
NativeArray* native_array_create(void) {
    NativeArray* arr = (NativeArray*)malloc(sizeof(NativeArray));
    if (!arr) return NULL;

    utarray_new(arr->array, &void_ptr_icd);
    if (!arr->array) {
        free(arr);
        return NULL;
    }

    return arr;
}

// Destroy array
void native_array_destroy(NativeArray* array) {
    if (!array) return;

    if (array->array) {
        utarray_free(array->array);
    }

    free(array);
}

// Push element to end
bool native_array_push(NativeArray* array, void* value) {
    if (!array || !array->array) return false;

    utarray_push_back(array->array, &value);
    return true;
}

// Pop element from end
void* native_array_pop(NativeArray* array) {
    if (!array || !array->array) return NULL;

    size_t len = utarray_len(array->array);
    if (len == 0) return NULL;

    void** elem = (void**)utarray_back(array->array);
    void* value = elem ? *elem : NULL;

    utarray_pop_back(array->array);

    return value;
}

// Get element at index
void* native_array_get(NativeArray* array, size_t index) {
    if (!array || !array->array) return NULL;

    if (index >= utarray_len(array->array)) return NULL;

    void** elem = (void**)utarray_eltptr(array->array, index);
    return elem ? *elem : NULL;
}

// Set element at index
bool native_array_set(NativeArray* array, size_t index, void* value) {
    if (!array || !array->array) return false;

    if (index >= utarray_len(array->array)) return false;

    void** elem = (void**)utarray_eltptr(array->array, index);
    if (!elem) return false;

    *elem = value;
    return true;
}

// Insert element at index
bool native_array_insert(NativeArray* array, size_t index, void* value) {
    if (!array || !array->array) return false;

    size_t len = utarray_len(array->array);
    if (index > len) return false;

    utarray_insert(array->array, &value, index);
    return true;
}

// Remove element at index
bool native_array_remove(NativeArray* array, size_t index) {
    if (!array || !array->array) return false;

    if (index >= utarray_len(array->array)) return false;

    utarray_erase(array->array, index, 1);
    return true;
}

// Get array size
size_t native_array_size(NativeArray* array) {
    if (!array || !array->array) return 0;

    return utarray_len(array->array);
}

// Clear all elements
void native_array_clear(NativeArray* array) {
    if (!array || !array->array) return;

    utarray_clear(array->array);
}

// Reserve capacity
bool native_array_reserve(NativeArray* array, size_t capacity) {
    if (!array || !array->array) return false;

    utarray_reserve(array->array, capacity);
    return true;
}

// Convert to pointer array
void** native_array_to_ptr_array(NativeArray* array, size_t* count) {
    if (!array || !array->array || !count) return NULL;

    size_t len = utarray_len(array->array);
    *count = len;

    if (len == 0) return NULL;

    void** ptr_array = (void**)malloc(sizeof(void*) * len);
    if (!ptr_array) return NULL;

    for (size_t i = 0; i < len; i++) {
        void** elem = (void**)utarray_eltptr(array->array, i);
        ptr_array[i] = elem ? *elem : NULL;
    }

    return ptr_array;
}

// Free pointer array
void native_array_free_ptr_array(void** ptr_array) {
    free(ptr_array);
}
