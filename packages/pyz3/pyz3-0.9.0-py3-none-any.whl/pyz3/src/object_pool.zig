// Licensed under the Apache License, Version 2.0 (the "License");
// you may not use this file except in compliance with the License.
// You may obtain a copy of the License at
//
//         http://www.apache.org/licenses/LICENSE-2.0
//
// Unless required by applicable law or agreed to in writing, software
// distributed under the License is distributed on an "AS IS" BASIS,
// WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
// See the License for the specific language governing permissions and
// limitations under the License.

/// Object pooling for frequently used Python objects
/// This reduces allocation overhead for common objects like empty tuples,
/// small integers, and boolean values
const std = @import("std");
const ffi = @import("ffi");
const py = @import("pyz3.zig");

/// Pool of commonly used Python objects
pub const ObjectPool = struct {
    /// Cached empty tuple (frequently used for function calls with no args)
    empty_tuple: ?*ffi.PyObject = null,

    /// Cached empty dict
    empty_dict: ?*ffi.PyObject = null,

    /// Cached empty list
    empty_list: ?*ffi.PyObject = null,

    /// Cached small integers (-5 to 256, same as CPython's optimization)
    /// Note: CPython already caches these internally, but we cache the
    /// references to avoid repeated lookups
    small_ints: [262]?*ffi.PyObject = [_]?*ffi.PyObject{null} ** 262,

    /// Cached common floats (0.0, 1.0, -1.0, 0.5)
    float_zero: ?*ffi.PyObject = null,
    float_one: ?*ffi.PyObject = null,
    float_neg_one: ?*ffi.PyObject = null,
    float_half: ?*ffi.PyObject = null,

    /// Cached common strings
    str_empty: ?*ffi.PyObject = null,
    str_none: ?*ffi.PyObject = null,
    str_true: ?*ffi.PyObject = null,
    str_false: ?*ffi.PyObject = null,

    /// Initialize the object pool
    pub fn init(self: *ObjectPool) void {
        // Create and cache empty tuple
        self.empty_tuple = ffi.PyTuple_New(0);
        if (self.empty_tuple) |t| {
            // Keep a permanent reference
            _ = ffi.Py_IncRef(t);
        }

        // Create and cache empty dict
        self.empty_dict = ffi.PyDict_New();
        if (self.empty_dict) |d| {
            _ = ffi.Py_IncRef(d);
        }

        // Create and cache empty list
        self.empty_list = ffi.PyList_New(0);
        if (self.empty_list) |l| {
            _ = ffi.Py_IncRef(l);
        }

        // Cache small integers (-5 to 256)
        var i: i64 = -5;
        while (i <= 256) : (i += 1) {
            const idx = @as(usize, @intCast(i + 5));
            self.small_ints[idx] = ffi.PyLong_FromLongLong(i);
            if (self.small_ints[idx]) |obj| {
                _ = ffi.Py_IncRef(obj);
            }
        }

        // Cache common floats
        self.float_zero = ffi.PyFloat_FromDouble(0.0);
        if (self.float_zero) |f| _ = ffi.Py_IncRef(f);

        self.float_one = ffi.PyFloat_FromDouble(1.0);
        if (self.float_one) |f| _ = ffi.Py_IncRef(f);

        self.float_neg_one = ffi.PyFloat_FromDouble(-1.0);
        if (self.float_neg_one) |f| _ = ffi.Py_IncRef(f);

        self.float_half = ffi.PyFloat_FromDouble(0.5);
        if (self.float_half) |f| _ = ffi.Py_IncRef(f);

        // Cache common strings
        self.str_empty = ffi.PyUnicode_FromString("");
        if (self.str_empty) |s| _ = ffi.Py_IncRef(s);

        self.str_none = ffi.PyUnicode_FromString("None");
        if (self.str_none) |s| _ = ffi.Py_IncRef(s);

        self.str_true = ffi.PyUnicode_FromString("True");
        if (self.str_true) |s| _ = ffi.Py_IncRef(s);

        self.str_false = ffi.PyUnicode_FromString("False");
        if (self.str_false) |s| _ = ffi.Py_IncRef(s);
    }

    /// Cleanup the object pool
    pub fn deinit(self: *ObjectPool) void {
        // Release cached objects
        if (self.empty_tuple) |t| {
            ffi.Py_DecRef(t);
        }
        if (self.empty_dict) |d| {
            ffi.Py_DecRef(d);
        }
        if (self.empty_list) |l| {
            ffi.Py_DecRef(l);
        }

        // Release small integers
        for (self.small_ints) |maybe_obj| {
            if (maybe_obj) |obj| {
                ffi.Py_DecRef(obj);
            }
        }

        // Release common floats
        if (self.float_zero) |f| ffi.Py_DecRef(f);
        if (self.float_one) |f| ffi.Py_DecRef(f);
        if (self.float_neg_one) |f| ffi.Py_DecRef(f);
        if (self.float_half) |f| ffi.Py_DecRef(f);

        // Release common strings
        if (self.str_empty) |s| ffi.Py_DecRef(s);
        if (self.str_none) |s| ffi.Py_DecRef(s);
        if (self.str_true) |s| ffi.Py_DecRef(s);
        if (self.str_false) |s| ffi.Py_DecRef(s);
    }

    /// Get a cached empty tuple (returns a borrowed reference)
    pub fn getEmptyTuple(self: *const ObjectPool) ?*ffi.PyObject {
        if (self.empty_tuple) |t| {
            _ = ffi.Py_IncRef(t);
            return t;
        }
        return null;
    }

    /// Get a cached empty dict (returns a new reference)
    pub fn getEmptyDict(self: *const ObjectPool) ?*ffi.PyObject {
        if (self.empty_dict) |d| {
            // Return a copy to avoid mutations affecting the pool
            return ffi.PyDict_Copy(d);
        }
        return null;
    }

    /// Get a cached empty list (returns a new reference to a new list)
    pub fn getEmptyList(self: *const ObjectPool) ?*ffi.PyObject {
        _ = self; // Intentionally unused - always creates new list
        // Always return a new list to avoid mutations
        return ffi.PyList_New(0);
    }

    /// Get a cached small integer (returns a new reference)
    /// Returns null if value is outside cached range
    pub fn getSmallInt(self: *const ObjectPool, value: i64) ?*ffi.PyObject {
        if (value < -5 or value > 256) {
            return null;
        }

        const idx = @as(usize, @intCast(value + 5));
        if (self.small_ints[idx]) |obj| {
            _ = ffi.Py_IncRef(obj);
            return obj;
        }
        return null;
    }

    /// Check if a value is in the small int cache range
    pub inline fn isSmallInt(value: i64) bool {
        return value >= -5 and value <= 256;
    }

    /// Get a cached common float (returns a new reference)
    /// Returns null if value is not in the cached set
    pub fn getCommonFloat(self: *const ObjectPool, value: f64) ?*ffi.PyObject {
        const obj = if (value == 0.0)
            self.float_zero
        else if (value == 1.0)
            self.float_one
        else if (value == -1.0)
            self.float_neg_one
        else if (value == 0.5)
            self.float_half
        else
            null;

        if (obj) |o| {
            _ = ffi.Py_IncRef(o);
            return o;
        }
        return null;
    }

    /// Get a cached common string (returns a new reference)
    /// Supported strings: "", "None", "True", "False"
    pub fn getCommonString(self: *const ObjectPool, str: []const u8) ?*ffi.PyObject {
        const obj = if (std.mem.eql(u8, str, ""))
            self.str_empty
        else if (std.mem.eql(u8, str, "None"))
            self.str_none
        else if (std.mem.eql(u8, str, "True"))
            self.str_true
        else if (std.mem.eql(u8, str, "False"))
            self.str_false
        else
            null;

        if (obj) |o| {
            _ = ffi.Py_IncRef(o);
            return o;
        }
        return null;
    }
};

/// Global object pool instance
/// This is initialized when the first Python module loads
/// Note: Python's GIL protects access to this, so no additional locking needed
/// All Python extension calls happen under the GIL
var global_pool: ObjectPool = .{};
var pool_initialized: bool = false;

/// Initialize the global object pool
/// SAFETY: Must be called with GIL held (guaranteed during module initialization)
pub fn initGlobalPool() void {
    // Double-check to prevent re-initialization
    // GIL ensures this check-then-act is atomic
    if (!pool_initialized) {
        global_pool.init();
        pool_initialized = true;
    }
}

/// Cleanup the global object pool
/// SAFETY: Must be called with GIL held (guaranteed during module cleanup)
pub fn deinitGlobalPool() void {
    if (pool_initialized) {
        global_pool.deinit();
        pool_initialized = false;
    }
}

/// Get the global object pool
/// SAFETY: Must be called with GIL held
pub fn getGlobalPool() *const ObjectPool {
    // GIL protects this check-then-act pattern
    if (!pool_initialized) {
        initGlobalPool();
    }
    return &global_pool;
}

/// Get a cached small integer from the global pool
pub fn getCachedInt(value: i64) ?*ffi.PyObject {
    const pool = getGlobalPool();
    return pool.getSmallInt(value);
}

/// Get a cached empty tuple from the global pool
pub fn getCachedEmptyTuple() ?*ffi.PyObject {
    const pool = getGlobalPool();
    return pool.getEmptyTuple();
}

/// Get a cached empty dict from the global pool
pub fn getCachedEmptyDict() ?*ffi.PyObject {
    const pool = getGlobalPool();
    return pool.getEmptyDict();
}

/// Get a cached empty list from the global pool
pub fn getCachedEmptyList() ?*ffi.PyObject {
    const pool = getGlobalPool();
    return pool.getEmptyList();
}

/// Get a cached common float from the global pool
pub fn getCachedFloat(value: f64) ?*ffi.PyObject {
    const pool = getGlobalPool();
    return pool.getCommonFloat(value);
}

/// Get a cached common string from the global pool
pub fn getCachedString(str: []const u8) ?*ffi.PyObject {
    const pool = getGlobalPool();
    return pool.getCommonString(str);
}
