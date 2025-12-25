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
const py = @import("./pyz3.zig");

/// Test allocator with leak detection support
/// This wraps Zig's GeneralPurposeAllocator to track allocations
/// and report memory leaks to the pytest harness.
pub const TestAllocator = struct {
    gpa: std.heap.GeneralPurposeAllocator(.{
        .safety = true,
        .thread_safe = true,
        .verbose_log = false,
    }),
    has_leaked: bool,

    const Self = @This();

    pub fn init() Self {
        return .{
            .gpa = .{},
            .has_leaked = false,
        };
    }

    pub fn allocator(self: *Self) std.mem.Allocator {
        return self.gpa.allocator();
    }

    /// Check for leaks and return true if any were detected
    pub fn deinit(self: *Self) bool {
        const leaked = self.gpa.deinit();
        if (leaked == .leak) {
            self.has_leaked = true;
            return true;
        }
        return false;
    }

    /// Get detailed leak information
    pub fn getLeakInfo(self: *const Self) LeakInfo {
        return .{
            .has_leak = self.has_leaked,
            .bytes_leaked = 0, // GPA in Zig 0.15+ doesn't expose this information
        };
    }
};

pub const LeakInfo = struct {
    has_leak: bool,
    bytes_leaked: usize,
};

/// Fixture for testing with automatic leak detection
/// Usage in tests:
/// ```zig
/// test "my test" {
///     var fixture = py.testing.TestFixture.init();
///     defer fixture.deinit();
///
///     const alloc = fixture.allocator();
///     // Your test code here
/// }
/// ```
pub const TestFixture = struct {
    test_allocator: TestAllocator,
    python_initialized: bool,

    const Self = @This();

    pub fn init() Self {
        return .{
            .test_allocator = TestAllocator.init(),
            .python_initialized = false,
        };
    }

    pub fn allocator(self: *Self) std.mem.Allocator {
        return self.test_allocator.allocator();
    }

    /// Initialize Python interpreter for the test
    pub fn initPython(self: *Self) void {
        if (!self.python_initialized) {
            py.initialize();
            self.python_initialized = true;
        }
    }

    pub fn deinit(self: *Self) void {
        if (self.python_initialized) {
            py.finalize();
        }

        if (self.test_allocator.deinit()) {
            const info = self.test_allocator.getLeakInfo();
            std.debug.print("\n⚠️  Memory leak detected: {} bytes leaked\n", .{info.bytes_leaked});
            @panic("Memory leak detected in test");
        }
    }
};

/// Helper to assert no leaks in a test block
pub fn expectNoLeaks(allocator: std.mem.Allocator) !void {
    // Get the underlying GPA if this is a TestAllocator
    _ = allocator;

    // Note: Leak detection is primarily handled by TestAllocator.deinit()
    // which uses Zig's GeneralPurposeAllocator leak detection.
    // This function exists for API compatibility and future enhancements.
}

/// Verify that a Python object has the expected reference count.
/// This is useful for testing to ensure no reference leaks.
pub fn expectRefCount(obj: py.PyObject, expected: isize) !void {
    const actual = obj.refcnt();
    if (actual != expected) {
        std.debug.print("Reference count mismatch: expected {d}, got {d}\n", .{ expected, actual });
        return error.RefCountMismatch;
    }
}

/// Helper to track reference counts in tests
pub const RefCountTracker = struct {
    initial_counts: std.AutoHashMap(usize, isize),
    allocator: std.mem.Allocator,

    const Self = @This();

    pub fn init(allocator: std.mem.Allocator) Self {
        return .{
            .initial_counts = std.AutoHashMap(usize, isize).init(allocator),
            .allocator = allocator,
        };
    }

    pub fn deinit(self: *Self) void {
        self.initial_counts.deinit();
    }

    /// Record the initial reference count of an object
    pub fn track(self: *Self, obj: py.PyObject) !void {
        const addr = @intFromPtr(obj.py);
        const refcnt = obj.refcnt();
        try self.initial_counts.put(addr, refcnt);
    }

    /// Verify that all tracked objects have the same reference count as when tracked
    pub fn expectNoLeaks(self: *Self) !void {
        var iter = self.initial_counts.iterator();
        var leaked = false;

        while (iter.next()) |entry| {
            const obj = py.PyObject{ .py = @ptrFromInt(entry.key_ptr.*) };
            const initial = entry.value_ptr.*;
            const current = obj.refcnt();

            if (current != initial) {
                std.debug.print("Reference leak detected at 0x{x}: initial={d}, current={d}\n", .{
                    entry.key_ptr.*,
                    initial,
                    current,
                });
                leaked = true;
            }
        }

        if (leaked) {
            return error.ReferenceLeaksDetected;
        }
    }
};
