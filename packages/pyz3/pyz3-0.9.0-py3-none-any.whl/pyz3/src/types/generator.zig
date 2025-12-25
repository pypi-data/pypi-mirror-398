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

/// Python generator object wrapper
pub const PyGenerator = extern struct {
    obj: py.PyObject,

    const Self = @This();

    /// Check if object is a generator
    pub fn check(obj: py.PyObject) bool {
        return ffi.PyGen_Check(obj.py) != 0;
    }

    /// Get the next value from the generator
    pub fn next(self: Self) !?py.PyObject {
        const result = ffi.PyIter_Next(self.obj.py);
        if (result) |obj| {
            return py.PyObject{ .py = obj };
        }

        // Check if StopIteration was raised (which is normal for generator exhaustion)
        if (ffi.PyErr_Occurred()) |err_type| {
            const stop_iteration = ffi.PyExc_StopIteration;
            if (ffi.PyErr_GivenExceptionMatches(err_type, stop_iteration) != 0) {
                ffi.PyErr_Clear();
                return null;
            }
            return PyError.PyRaised;
        }

        return null;
    }

    /// Send a value into the generator
    pub fn send(self: Self, value: ?py.PyObject) !py.PyObject {
        const val = if (value) |v| v.py else ffi.Py_None();
        const result = ffi.PyIter_Send(self.obj.py, val, null) orelse return PyError.PyRaised;
        return .{ .py = result };
    }

    /// Throw an exception into the generator
    pub fn throw(self: Self, exception: py.PyObject) !py.PyObject {
        const throw_method = try self.obj.getAttribute("throw");
        defer throw_method.decref();

        const result = try py.call(@import("../pyz3.zig"), throw_method, .{exception});
        return result;
    }

    /// Close the generator
    pub fn close(self: Self) !void {
        const close_method = try self.obj.getAttribute("close");
        defer close_method.decref();

        const result = try py.call0(@import("../pyz3.zig"), close_method);
        defer result.decref();
    }

    /// Get the generator's code object
    pub fn getCode(self: Self) !py.PyCode {
        const gi_code = try self.obj.getAttribute("gi_code");
        return .{ .obj = gi_code };
    }

    /// Get the generator's frame
    pub fn getFrame(self: Self) !?py.PyFrame {
        const gi_frame = try self.obj.getAttribute("gi_frame");

        // gi_frame can be None if the generator has finished
        if (py.is_none(gi_frame)) {
            gi_frame.decref();
            return null;
        }

        return .{ .obj = gi_frame };
    }

    /// Check if the generator is running
    pub fn isRunning(self: Self) !bool {
        const gi_running = try self.obj.getAttribute("gi_running");
        defer gi_running.decref();
        return try py.as(bool, @import("../pyz3.zig"), gi_running);
    }

    /// Check if the generator has been exhausted
    pub fn isExhausted(self: Self) !bool {
        const frame = try self.getFrame();
        return frame == null;
    }

    /// Get an iterator (generators are their own iterators)
    pub fn iter(self: Self) py.PyIter {
        self.obj.incref();
        return .{ .obj = self.obj };
    }

    /// Consume the entire generator and collect results into a list
    pub fn toList(self: Self, comptime root: type) !py.PyList(root) {
        const list = try py.PyList(root).new();

        while (try self.next()) |item| {
            defer item.decref();
            try list.append(item);
        }

        return list;
    }

    /// Consume the generator and execute a callback for each item
    pub fn forEach(self: Self, comptime callback: fn (py.PyObject) anyerror!void) !void {
        while (try self.next()) |item| {
            defer item.decref();
            try callback(item);
        }
    }

    /// Take the first N items from the generator
    pub fn take(self: Self, n: usize, comptime root: type) !py.PyList(root) {
        const list = try py.PyList(root).new();

        var count: usize = 0;
        while (count < n) : (count += 1) {
            if (try self.next()) |item| {
                defer item.decref();
                try list.append(item);
            } else {
                break;
            }
        }

        return list;
    }

    /// Skip the first N items from the generator
    pub fn skip(self: Self, n: usize) !void {
        var count: usize = 0;
        while (count < n) : (count += 1) {
            if (try self.next()) |item| {
                item.decref();
            } else {
                break;
            }
        }
    }

    /// Check if any element satisfies a Python predicate function
    pub fn any(self: Self, predicate: py.PyObject) !bool {
        while (try self.next()) |item| {
            defer item.decref();

            const result = try py.call(@import("../pyz3.zig"), predicate, .{item});
            defer result.decref();

            const is_true = try py.as(bool, @import("../pyz3.zig"), result);
            if (is_true) return true;
        }
        return false;
    }

    /// Check if all elements satisfy a Python predicate function
    pub fn all(self: Self, predicate: py.PyObject) !bool {
        while (try self.next()) |item| {
            defer item.decref();

            const result = try py.call(@import("../pyz3.zig"), predicate, .{item});
            defer result.decref();

            const is_true = try py.as(bool, @import("../pyz3.zig"), result);
            if (!is_true) return false;
        }
        return true;
    }
};
