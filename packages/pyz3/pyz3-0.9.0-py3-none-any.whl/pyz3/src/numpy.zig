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

/// NumPy integration for pyz3
///
/// This module provides basic NumPy interoperability.
/// Full NumPy functionality is available through standard Python object calls.
///
/// Example:
/// ```zig
/// const np = try py.import(@This(), "numpy");
/// defer np.decref();
///
/// // Create array
/// const arr = try py.call(@This(), np, "array", .{&[_]f64{1, 2, 3}});
/// defer arr.decref();
///
/// // Call NumPy functions
/// const sum = try py.call(@This(), arr, "sum", .{});
/// ```

const std = @import("std");
const py = @import("pyz3.zig");
const PyError = @import("errors.zig").PyError;
const PyObject = py.PyObject;

/// Initialize NumPy module
/// Returns the numpy module as a PyObject for direct method calls
pub fn getModule(comptime root: type) !PyObject {
    return try py.import(root, "numpy");
}

/// Check if an object is a NumPy array
pub fn isArray(obj: PyObject) bool {
    // Try to get the __array_interface__ attribute
    const attr = obj.getAttribute("__array_interface__") catch return false;
    defer attr.decref();
    return true;
}
