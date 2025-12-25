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
const py = @import("../pyz3.zig");
const PyError = @import("../errors.zig").PyError;

/// Python range object wrapper (immutable sequence)
pub const PyRange = extern struct {
    obj: py.PyObject,

    const Self = @This();

    /// Create a range with stop value: range(stop)
    pub fn new(stop_value: i64) !Self {
        const builtins = try py.import("builtins");
        defer builtins.decref();

        const range_type = try builtins.getAttribute("range");
        defer range_type.decref();

        const stop_obj = try py.PyLong.from(stop_value);
        defer stop_obj.obj.decref();

        const range_obj = try py.call(@import("../pyz3.zig"), range_type, .{stop_obj.obj});
        return .{ .obj = range_obj };
    }

    /// Create a range with start and stop: range(start, stop)
    pub fn fromStartStop(start_value: i64, stop_value: i64) !Self {
        const builtins = try py.import("builtins");
        defer builtins.decref();

        const range_type = try builtins.getAttribute("range");
        defer range_type.decref();

        const start_obj = try py.PyLong.from(start_value);
        defer start_obj.obj.decref();

        const stop_obj = try py.PyLong.from(stop_value);
        defer stop_obj.obj.decref();

        const range_obj = try py.call(@import("../pyz3.zig"), range_type, .{ start_obj.obj, stop_obj.obj });
        return .{ .obj = range_obj };
    }

    /// Create a range with start, stop, and step: range(start, stop, step)
    pub fn fromStartStopStep(start_value: i64, stop_value: i64, step_value: i64) !Self {
        if (step_value == 0) {
            return py.ValueError(@import("../pyz3.zig")).raise("range() arg 3 must not be zero");
        }

        const builtins = try py.import("builtins");
        defer builtins.decref();

        const range_type = try builtins.getAttribute("range");
        defer range_type.decref();

        const start_obj = try py.PyLong.from(start_value);
        defer start_obj.obj.decref();

        const stop_obj = try py.PyLong.from(stop_value);
        defer stop_obj.obj.decref();

        const step_obj = try py.PyLong.from(step_value);
        defer step_obj.obj.decref();

        const range_obj = try py.call(@import("../pyz3.zig"), range_type, .{ start_obj.obj, stop_obj.obj, step_obj.obj });
        return .{ .obj = range_obj };
    }

    /// Check if object is a range
    pub fn check(obj: py.PyObject) bool {
        const builtins = py.import("builtins") catch return false;
        defer builtins.decref();

        const range_type = builtins.getAttribute("range") catch return false;
        defer range_type.decref();

        return py.isinstance(@import("../pyz3.zig"), obj, range_type) catch false;
    }

    /// Get the start value of the range
    pub fn start(self: Self) !i64 {
        const start_obj = try self.obj.getAttribute("start");
        defer start_obj.decref();
        return try py.as(i64, @import("../pyz3.zig"), start_obj);
    }

    /// Get the stop value of the range
    pub fn stop(self: Self) !i64 {
        const stop_obj = try self.obj.getAttribute("stop");
        defer stop_obj.decref();
        return try py.as(i64, @import("../pyz3.zig"), stop_obj);
    }

    /// Get the step value of the range
    pub fn step(self: Self) !i64 {
        const step_obj = try self.obj.getAttribute("step");
        defer step_obj.decref();
        return try py.as(i64, @import("../pyz3.zig"), step_obj);
    }

    /// Get the length of the range
    pub fn len(self: Self) !usize {
        const length = ffi.PyObject_Length(self.obj.py);
        if (length < 0) return PyError.PyRaised;
        return @intCast(length);
    }

    /// Get an iterator over the range
    pub fn iter(self: Self) !py.PyIter {
        const iter_obj = ffi.PyObject_GetIter(self.obj.py) orelse return PyError.PyRaised;
        return .{ .obj = .{ .py = iter_obj } };
    }

    /// Check if a value is in the range
    pub fn contains(self: Self, value: i64) !bool {
        const value_obj = try py.PyLong.from(value);
        defer value_obj.obj.decref();

        const result = ffi.PySequence_Contains(self.obj.py, value_obj.obj.py);
        if (result < 0) return PyError.PyRaised;
        return result == 1;
    }

    /// Get the value at a specific index
    pub fn index(self: Self, idx: isize) !i64 {
        const index_obj = try py.PyLong.from(idx);
        defer index_obj.obj.decref();

        const item = ffi.PyObject_GetItem(self.obj.py, index_obj.obj.py) orelse return PyError.PyRaised;
        defer {
            const obj = py.PyObject{ .py = item };
            obj.decref();
        }

        const item_obj = py.PyObject{ .py = item };
        return try py.as(i64, @import("../pyz3.zig"), item_obj);
    }

    /// Count occurrences of a value in the range (always 0 or 1)
    pub fn count(self: Self, value: i64) !usize {
        const contains_value = try self.contains(value);
        return if (contains_value) 1 else 0;
    }

    /// Convert range to a list
    pub fn toList(self: Self, comptime root: type) !py.PyList(root) {
        const list_type = try py.import("builtins").getAttribute("list");
        defer list_type.decref();

        const list_obj = try py.call(root, list_type, .{self.obj});
        return .{ .obj = list_obj };
    }

    /// Get range parameters as a tuple
    pub fn asTuple(self: Self) !struct { start: i64, stop: i64, step: i64 } {
        return .{
            .start = try self.start(),
            .stop = try self.stop(),
            .step = try self.step(),
        };
    }

    /// Check if the range is empty
    pub fn isEmpty(self: Self) !bool {
        const length = try self.len();
        return length == 0;
    }

    /// Reverse the range (returns a new reversed iterator)
    pub fn reversed(self: Self) !py.PyIter {
        const builtins = try py.import("builtins");
        defer builtins.decref();

        const reversed_fn = try builtins.getAttribute("reversed");
        defer reversed_fn.decref();

        const reversed_obj = try py.call(@import("../pyz3.zig"), reversed_fn, .{self.obj});
        return .{ .obj = reversed_obj };
    }
};
