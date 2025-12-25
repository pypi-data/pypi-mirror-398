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

const std = @import("std");
const ffi = @import("ffi");
const PyError = @import("../errors.zig").PyError;
const py = @import("../pyz3.zig");

/// Python coroutine object wrapper
/// Represents a Python coroutine created by an async function.
pub const PyCoroutine = extern struct {
    obj: py.PyObject,

    const Self = @This();

    /// Check if a Python object is a coroutine
    pub fn check(obj: py.PyObject) bool {
        return ffi.PyCoro_CheckExact(obj.py) != 0;
    }

    /// Send a value to the coroutine
    pub fn send(self: Self, value: ?py.PyObject) !py.PyObject {
        const val = if (value) |v| v.py else ffi.Py_None();
        const result = ffi.PyIter_Send(self.obj.py, val, null) orelse return PyError.PyRaised;
        return py.PyObject{ .py = result };
    }

    /// Throw an exception into the coroutine
    pub fn throw(self: Self, exception: py.PyObject) !py.PyObject {
        const result = ffi.PyObject_CallMethod(
            self.obj.py,
            "throw",
            "(O)",
            exception.py,
        ) orelse return PyError.PyRaised;
        return py.PyObject{ .py = result };
    }

    /// Close the coroutine
    pub fn close(self: Self) !void {
        const result = ffi.PyObject_CallMethod(self.obj.py, "close", null) orelse return PyError.PyRaised;
        defer {
            const obj = py.PyObject{ .py = result };
            obj.decref();
        }
    }
};

/// Python awaitable object
pub fn PyAwaitable(comptime root: type) type {
    return extern struct {
        obj: py.PyObject,

        const Self = @This();

        /// Get the iterator for this awaitable (for await protocol)
        pub fn iter(self: Self) !py.PyIter(root) {
            const result = ffi.PyObject_GetIter(self.obj.py) orelse return PyError.PyRaised;
            return py.PyIter(root){ .obj = py.PyObject{ .py = result } };
        }

        /// Await this awaitable (blocking)
        /// Warning: This blocks the current thread until the coroutine completes
        pub fn await_(self: Self) !py.PyObject {
            const it = try self.iter();
            while (true) {
                const item = it.next(py.PyObject) catch |err| {
                    if (err == PyError.PyRaised) {
                        // Check if StopIteration was raised (normal completion)
                        if (ffi.PyErr_ExceptionMatches(ffi.PyExc_StopIteration) != 0) {
                            // Get the StopIteration value
                            var ptype: ?*ffi.PyObject = null;
                            var pvalue: ?*ffi.PyObject = null;
                            var ptraceback: ?*ffi.PyObject = null;
                            ffi.PyErr_Fetch(&ptype, &pvalue, &ptraceback);

                            if (pvalue) |value| {
                                const exc = py.PyObject{ .py = value };
                                const result = exc.getAttribute("value") catch {
                                    // No value attribute, return None
                                    return py.None();
                                };
                                return result;
                            }
                        }
                    }
                    return err;
                };
                if (item) |obj| obj.decref();
                // Continue iterating until StopIteration
            }
        }
    };
}

/// Helper to create an async function wrapper
/// This allows Zig functions to be called as Python coroutines
pub fn AsyncFunction(comptime func: anytype) type {
    return struct {
        pub fn call(args: anytype) !PyCoroutine {
            // Create a coroutine that wraps the Zig function
            // For now, this is a simplified implementation
            _ = args;
            _ = func;
            @compileError("AsyncFunction not yet fully implemented. Use manual coroutine creation.");
        }
    };
}
