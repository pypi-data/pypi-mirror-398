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
const py = @import("./pyz3.zig");
const builtin = @import("builtin");

/// Debug logging levels
pub const LogLevel = enum(u8) {
    trace = 0,
    debug = 1,
    info = 2,
    warn = 3,
    err = 4,

    pub fn toString(self: LogLevel) []const u8 {
        return switch (self) {
            .trace => "TRACE",
            .debug => "DEBUG",
            .info => "INFO",
            .warn => "WARN",
            .err => "ERROR",
        };
    }
};

/// Global debug state
var debug_enabled: bool = false;
var debug_level: LogLevel = .info;

/// Enable debug mode
pub fn enableDebug() void {
    debug_enabled = true;
}

/// Disable debug mode
pub fn disableDebug() void {
    debug_enabled = false;
}

/// Check if debug mode is enabled
pub fn isDebugEnabled() bool {
    return debug_enabled;
}

/// Set debug log level
pub fn setLogLevel(level: LogLevel) void {
    debug_level = level;
}

/// Get current log level
pub fn getLogLevel() LogLevel {
    return debug_level;
}

/// Debug print with level
pub fn log(comptime level: LogLevel, comptime fmt: []const u8, args: anytype) void {
    if (!debug_enabled or @intFromEnum(level) < @intFromEnum(debug_level)) {
        return;
    }

    const level_str = level.toString();
    std.debug.print("[Pydust {s}] ", .{level_str});
    std.debug.print(fmt, args);
    std.debug.print("\n", .{});
}

/// Trace-level logging (most verbose)
pub fn trace(comptime fmt: []const u8, args: anytype) void {
    log(.trace, fmt, args);
}

/// Debug-level logging
pub fn debug(comptime fmt: []const u8, args: anytype) void {
    log(.debug, fmt, args);
}

/// Info-level logging
pub fn info(comptime fmt: []const u8, args: anytype) void {
    log(.info, fmt, args);
}

/// Warning-level logging
pub fn warn(comptime fmt: []const u8, args: anytype) void {
    log(.warn, fmt, args);
}

/// Error-level logging
pub fn err(comptime fmt: []const u8, args: anytype) void {
    log(.err, fmt, args);
}

/// Print Python object for debugging
pub fn printPyObject(obj: py.PyObject) void {
    const repr = py.repr(obj) catch {
        std.debug.print("<failed to get repr>\n", .{});
        return;
    };
    defer repr.decref();

    const str = repr.asSlice() catch {
        std.debug.print("<failed to convert repr to string>\n", .{});
        return;
    };

    std.debug.print("PyObject: {s}\n", .{str});
}

/// Get Python traceback as a string
pub fn getTraceback() !py.PyString {
    const traceback_mod = try py.import("traceback");
    defer traceback_mod.decref();

    const format_exc = try traceback_mod.getAttribute("format_exc");
    defer format_exc.decref();

    const result = try py.call0(@This(), format_exc);
    return py.PyString{ .obj = result };
}

/// Print current Python exception with traceback
pub fn printException() void {
    const traceback = getTraceback() catch {
        std.debug.print("Failed to get traceback\n", .{});
        return;
    };
    defer traceback.obj.decref();

    const str = traceback.asSlice() catch {
        std.debug.print("Failed to format traceback\n", .{});
        return;
    };

    std.debug.print("\n=== Python Exception ===\n{s}\n========================\n", .{str});
}

/// Stack frame information
pub const StackFrame = struct {
    function_name: []const u8,
    file: []const u8,
    line: usize,
};

/// Print current stack trace (both Zig and Python)
pub fn printStackTrace() void {
    std.debug.print("\n=== Stack Trace ===\n", .{});

    // Zig stack trace
    std.debug.print("\n--- Zig Stack ---\n", .{});
    _ = std.debug.getSelfDebugInfo() catch |e| {
        std.debug.print("Failed to get Zig debug info: {}\n", .{e});
        return;
    };
    var it = std.debug.StackIterator.init(@returnAddress(), null);
    var frame_idx: usize = 0;
    while (it.next()) |addr| {
        std.debug.print("#{d}: 0x{x:0>16}\n", .{ frame_idx, addr });
        frame_idx += 1;
        if (frame_idx > 20) break; // Limit to 20 frames
    }

    // Python stack trace
    std.debug.print("\n--- Python Stack ---\n", .{});
    const traceback = getTraceback() catch {
        std.debug.print("No Python stack available\n", .{});
        return;
    };
    defer traceback.obj.decref();

    const str = traceback.asSlice() catch return;
    std.debug.print("{s}\n", .{str});

    std.debug.print("===================\n\n", .{});
}

/// Breakpoint helper - pauses execution if debugger is attached
pub fn breakpoint() void {
    if (builtin.mode == .Debug) {
        std.debug.print("\n🔴 Breakpoint hit! Attach debugger or press Enter to continue...\n", .{});
        // In a real debugger, this would trigger a breakpoint
        // For now, we just pause
        @breakpoint();
    }
}

/// Assert with detailed error message
pub fn assertDebug(condition: bool, comptime fmt: []const u8, args: anytype) void {
    if (!condition) {
        std.debug.print("\n❌ Assertion failed: ", .{});
        std.debug.print(fmt, args);
        std.debug.print("\n", .{});
        printStackTrace();
        @panic("Assertion failed");
    }
}

/// Memory inspection helper
pub fn inspectMemory(ptr: anytype, len: usize) void {
    const bytes: [*]const u8 = @ptrCast(ptr);
    std.debug.print("\nMemory at 0x{x}:\n", .{@intFromPtr(ptr)});

    var i: usize = 0;
    while (i < len) : (i += 16) {
        std.debug.print("  {x:0>8}: ", .{i});

        // Print hex
        var j: usize = 0;
        while (j < 16 and i + j < len) : (j += 1) {
            std.debug.print("{x:0>2} ", .{bytes[i + j]});
        }

        // Padding
        while (j < 16) : (j += 1) {
            std.debug.print("   ", .{});
        }

        // Print ASCII
        std.debug.print(" | ", .{});
        j = 0;
        while (j < 16 and i + j < len) : (j += 1) {
            const c = bytes[i + j];
            if (c >= 32 and c <= 126) {
                std.debug.print("{c}", .{c});
            } else {
                std.debug.print(".", .{});
            }
        }
        std.debug.print("\n", .{});
    }
}

/// Python object reference count inspector
pub fn inspectRefCount(obj: py.PyObject) void {
    const count = py.refcnt(obj);
    std.debug.print("PyObject refcount: {d}\n", .{count});

    if (count == 0) {
        std.debug.print("⚠️  WARNING: Reference count is 0! Object may be freed.\n", .{});
    } else if (count > 1000) {
        std.debug.print("⚠️  WARNING: Very high reference count! Possible leak.\n", .{});
    }
}

/// Timing helper for performance debugging
pub const Timer = struct {
    start_time: i64,
    name: []const u8,

    pub fn start(name: []const u8) Timer {
        return .{
            .start_time = std.time.milliTimestamp(),
            .name = name,
        };
    }

    pub fn stop(self: Timer) void {
        const end = std.time.milliTimestamp();
        const elapsed = end - self.start_time;
        info("{s} took {d}ms", .{ self.name, elapsed });
    }
};

/// Debug context for tracking state
pub const DebugContext = struct {
    name: []const u8,
    values: std.StringHashMap([]const u8),
    allocator: std.mem.Allocator,

    pub fn init(allocator: std.mem.Allocator, name: []const u8) DebugContext {
        return .{
            .name = name,
            .values = std.StringHashMap([]const u8).init(allocator),
            .allocator = allocator,
        };
    }

    pub fn deinit(self: *DebugContext) void {
        self.values.deinit();
    }

    pub fn set(self: *DebugContext, key: []const u8, value: []const u8) !void {
        try self.values.put(key, value);
    }

    pub fn dump(self: *const DebugContext) void {
        std.debug.print("\n=== Debug Context: {s} ===\n", .{self.name});
        var it = self.values.iterator();
        while (it.next()) |entry| {
            std.debug.print("  {s} = {s}\n", .{ entry.key_ptr.*, entry.value_ptr.* });
        }
        std.debug.print("===========================\n\n", .{});
    }
};
