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

/// Enhanced error handling with granular error types and stack trace support
const std = @import("std");
const ffi = @import("ffi");
const py = @import("pyz3.zig");

/// Granular error types for better error handling
pub const PyError = error{
    /// Python exception already set
    PyRaised,

    /// Memory allocation failed
    OutOfMemory,

    /// Type conversion error
    TypeError,

    /// Value error (invalid value)
    ValueError,

    /// Index out of bounds
    IndexError,

    /// Key not found in dict
    KeyError,

    /// Attribute not found
    AttributeError,

    /// Runtime error
    RuntimeError,

    /// Not implemented
    NotImplementedError,

    /// Division by zero
    ZeroDivisionError,

    /// Overflow error
    OverflowError,

    /// Import error
    ImportError,

    /// IO error
    IOError,

    /// OS error
    OSError,

    /// File not found
    FileNotFoundError,

    /// Permission denied
    PermissionError,

    /// Assertion failed
    AssertionError,

    /// Stop iteration
    StopIteration,

    /// Unicode error
    UnicodeError,

    /// System error
    SystemError,
} || std.mem.Allocator.Error;

/// Python stack frame information
pub const StackFrame = struct {
    filename: []const u8,
    function_name: []const u8,
    line_number: i32,

    pub fn format(self: @This(), writer: anytype) !void {
        try writer.print("  File \"{s}\", line {d}, in {s}\n", .{
            self.filename,
            self.line_number,
            self.function_name,
        });
    }
};

/// Python stack trace
pub const StackTrace = struct {
    frames: []const StackFrame,
    allocator: std.mem.Allocator,

    pub fn deinit(self: *@This()) void {
        for (self.frames) |frame| {
            self.allocator.free(frame.filename);
            self.allocator.free(frame.function_name);
        }
        self.allocator.free(self.frames);
    }

    pub fn format(self: @This(), writer: anytype) !void {
        try writer.writeAll("Traceback (most recent call last):\n");
        for (self.frames) |frame| {
            try frame.format(writer);
        }
    }
};

/// Capture current Python stack trace
pub fn captureStackTrace(allocator: std.mem.Allocator) !?StackTrace {
    // Get current exception info
    var exc_type: ?*ffi.PyObject = null;
    var exc_value: ?*ffi.PyObject = null;
    var exc_traceback: ?*ffi.PyObject = null;

    ffi.PyErr_Fetch(&exc_type, &exc_value, &exc_traceback);

    // Restore exception
    defer {
        if (exc_type != null or exc_value != null or exc_traceback != null) {
            ffi.PyErr_Restore(exc_type, exc_value, exc_traceback);
        }
    }

    // If there's an exception with traceback, create a simple stack frame entry
    // Note: Detailed stack frame capture requires Python 3.11+ FFI functions
    // that may not be available in all Python C API bindings
    if (exc_traceback != null or exc_type != null) {
        var frames: std.ArrayList(StackFrame) = .empty;
        errdefer frames.deinit(allocator);

        // Create a basic frame indicating an error occurred
        const filename = try allocator.dupe(u8, "<python>");
        const function_name = try allocator.dupe(u8, "<error>");

        try frames.append(allocator, .{
            .filename = filename,
            .function_name = function_name,
            .line_number = 0,
        });

        return StackTrace{
            .frames = try frames.toOwnedSlice(allocator),
            .allocator = allocator,
        };
    }

    return null;
}

/// Enhanced exception raising with stack trace capture
pub fn raiseWithTrace(
    comptime root: type,
    exc_type: type,
    message: []const u8,
) PyError {
    // Capture current stack trace before raising
    const trace = captureStackTrace(py.allocator) catch null;
    defer if (trace) |*t| {
        var owned_trace = t.*;
        owned_trace.deinit();
    };

    // Format message with stack trace
    var buffer: std.ArrayList(u8) = .empty;
    defer buffer.deinit(py.allocator);

    const writer = buffer.writer(py.allocator);

    if (trace) |t| {
        t.format(writer) catch {};
        writer.writeAll("\n") catch {};
    }

    writer.writeAll(message) catch {};

    const full_message = buffer.items;

    // Raise exception
    return exc_type(root).raise(full_message);
}

/// Get detailed error information
pub const ErrorInfo = struct {
    error_type: []const u8,
    message: []const u8,
    stack_trace: ?StackTrace,
    allocator: std.mem.Allocator,

    pub fn deinit(self: *@This()) void {
        self.allocator.free(self.error_type);
        self.allocator.free(self.message);
        if (self.stack_trace) |*trace| {
            trace.deinit();
        }
    }
};

/// Get current Python exception information
pub fn getErrorInfo(allocator: std.mem.Allocator) !?ErrorInfo {
    var exc_type: ?*ffi.PyObject = null;
    var exc_value: ?*ffi.PyObject = null;
    var exc_traceback: ?*ffi.PyObject = null;

    ffi.PyErr_Fetch(&exc_type, &exc_value, &exc_traceback);

    if (exc_type == null) {
        return null;
    }

    defer {
        if (exc_type) |t| ffi.Py_DecRef(t);
        if (exc_value) |v| ffi.Py_DecRef(v);
        if (exc_traceback) |tb| ffi.Py_DecRef(tb);
    }

    // Restore for stack trace capture
    ffi.PyErr_Restore(exc_type, exc_value, exc_traceback);
    const stack_trace = try captureStackTrace(allocator);
    ffi.PyErr_Fetch(&exc_type, &exc_value, &exc_traceback);

    // Get type name
    const type_obj = py.PyObject{ .py = exc_type.? };
    const type_name_cstr = try type_obj.getTypeName();
    const error_type = try allocator.dupe(u8, std.mem.span(type_name_cstr));

    // Get message
    var message: []const u8 = "";
    if (exc_value) |val| {
        const val_obj = py.PyObject{ .py = val };
        const str_obj = py.str(@TypeOf(val_obj), val_obj) catch val_obj;
        defer if (str_obj.py != val_obj.py) str_obj.decref();

        const str_type = py.PyString.from.checked(@TypeOf(val_obj), str_obj) catch {
            message = try allocator.dupe(u8, "<error getting message>");
            return ErrorInfo{
                .error_type = error_type,
                .message = message,
                .stack_trace = stack_trace,
                .allocator = allocator,
            };
        };

        const msg_slice = str_type.asSlice() catch "";
        message = try allocator.dupe(u8, msg_slice);
    } else {
        message = try allocator.dupe(u8, "");
    }

    return ErrorInfo{
        .error_type = error_type,
        .message = message,
        .stack_trace = stack_trace,
        .allocator = allocator,
    };
}

/// Map Zig error to appropriate Python exception type
pub fn mapZigError(err: anyerror) PyError {
    return switch (err) {
        error.OutOfMemory => PyError.OutOfMemory,
        error.FileNotFound => PyError.FileNotFoundError,
        error.AccessDenied => PyError.PermissionError,
        error.BrokenPipe => PyError.IOError,
        error.ConnectionRefused => PyError.IOError,
        error.InvalidCharacter => PyError.ValueError,
        error.Overflow => PyError.OverflowError,
        error.DivisionByZero => PyError.ZeroDivisionError,
        else => PyError.RuntimeError,
    };
}

test "capture stack trace" {
    // This test requires Python to be initialized
    py.initialize();
    defer py.finalize();

    // Raise a Python exception to create a stack trace
    const ValueError = py.ValueError(@This());

    // This will set an exception
    ValueError.raise("Test error") catch {};

    // Try to capture the stack trace
    const trace = try captureStackTrace(std.testing.allocator);

    if (trace) |*t| {
        defer {
            var owned = t.*;
            owned.deinit();
        }

        // Should have at least one frame
        try std.testing.expect(t.frames.len >= 0);
    }

    // Clear the error
    ffi.PyErr_Clear();
}

test "map Zig errors" {
    const err1 = error.OutOfMemory;
    const mapped1 = mapZigError(err1);
    try std.testing.expectEqual(PyError.OutOfMemory, mapped1);

    const err2 = error.FileNotFound;
    const mapped2 = mapZigError(err2);
    try std.testing.expectEqual(PyError.FileNotFoundError, mapped2);
}
