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

/// PySequence mixin - provides Python sequence protocol operations
///
/// This mixin can be added to any Zig type that wraps a Python sequence object
/// (list, tuple, range, etc.) to provide convenient sequence operations.
///
/// Usage:
/// ```zig
/// pub const MySeq = extern struct {
///     obj: py.PyObject,
///
///     pub usingnamespace PySequenceMixin(@This());
/// };
/// ```

const std = @import("std");
const ffi = @import("ffi");
const py = @import("../pyz3.zig");
const PyError = @import("../errors.zig").PyError;
const PyObject = @import("obj.zig").PyObject;

/// PySequence mixin - provides all Python sequence protocol operations
///
/// This mixin implements the full Python sequence protocol as defined in:
/// https://docs.python.org/3/c-api/sequence.html
///
/// Type parameter:
///   - Self: The type that has an `obj: PyObject` field
pub fn PySequenceMixin(comptime Self: type) type {
    return struct {
        // ============================================================
        // Core Sequence Protocol Operations
        // ============================================================

        /// Get the length of the sequence
        /// Equivalent to Python: len(seq)
        pub fn len(self: Self) !usize {
            const size = ffi.PySequence_Size(self.obj.py);
            if (size < 0) return PyError.PyRaised;
            return @intCast(size);
        }

        /// Get the length of the sequence (alias for len)
        pub fn length(self: Self) !usize {
            return self.len();
        }

        /// Check if sequence is empty
        pub fn isEmpty(self: Self) !bool {
            return (try self.len()) == 0;
        }

        /// Get item at index
        /// Equivalent to Python: seq[index]
        ///
        /// Supports negative indices (Python-style: -1 is last element)
        /// Returns a new reference
        pub fn getItem(self: Self, comptime T: type, idx: isize) !T {
            const item = ffi.PySequence_GetItem(self.obj.py, idx) orelse return PyError.PyRaised;
            return py.as(@import("../pyz3.zig"), T, PyObject{ .py = item });
        }

        /// Get item at index, returning PyObject
        /// Returns a new reference
        pub fn getItemObj(self: Self, idx: isize) !PyObject {
            const item = ffi.PySequence_GetItem(self.obj.py, idx) orelse return PyError.PyRaised;
            return PyObject{ .py = item };
        }

        /// Set item at index
        /// Equivalent to Python: seq[index] = value
        ///
        /// Note: Only works for mutable sequences (list, bytearray)
        /// Tuples will raise TypeError
        pub fn setItem(self: Self, idx: isize, value: anytype) !void {
            const py_value = py.object(@import("../pyz3.zig"), value);
            if (ffi.PySequence_SetItem(self.obj.py, idx, py_value.py) < 0) {
                return PyError.PyRaised;
            }
        }

        /// Delete item at index
        /// Equivalent to Python: del seq[index]
        ///
        /// Note: Only works for mutable sequences
        pub fn delItem(self: Self, idx: isize) !void {
            if (ffi.PySequence_DelItem(self.obj.py, idx) < 0) {
                return PyError.PyRaised;
            }
        }

        /// Get slice of sequence
        /// Equivalent to Python: seq[start:end]
        ///
        /// Returns a new reference
        pub fn getSlice(self: Self, start: isize, end: isize) !Self {
            const slice = ffi.PySequence_GetSlice(self.obj.py, start, end) orelse return PyError.PyRaised;
            return Self{ .obj = .{ .py = slice } };
        }

        /// Set slice of sequence
        /// Equivalent to Python: seq[start:end] = values
        ///
        /// Note: Only works for mutable sequences
        pub fn setSlice(self: Self, start: isize, end: isize, values: anytype) !void {
            const py_values = py.object(@import("../pyz3.zig"), values);
            if (ffi.PySequence_SetSlice(self.obj.py, start, end, py_values.py) < 0) {
                return PyError.PyRaised;
            }
        }

        /// Delete slice of sequence
        /// Equivalent to Python: del seq[start:end]
        ///
        /// Note: Only works for mutable sequences
        pub fn delSlice(self: Self, start: isize, end: isize) !void {
            if (ffi.PySequence_DelSlice(self.obj.py, start, end) < 0) {
                return PyError.PyRaised;
            }
        }

        // ============================================================
        // Search and Membership Operations
        // ============================================================

        /// Check if sequence contains value
        /// Equivalent to Python: value in seq
        pub fn contains(self: Self, value: anytype) !bool {
            const py_value = py.object(@import("../pyz3.zig"), value);
            const result = ffi.PySequence_Contains(self.obj.py, py_value.py);
            if (result < 0) return PyError.PyRaised;
            return result == 1;
        }

        /// Find index of first occurrence of value
        /// Equivalent to Python: seq.index(value)
        ///
        /// Raises ValueError if value is not found
        pub fn index(self: Self, value: anytype) !usize {
            const py_value = py.object(@import("../pyz3.zig"), value);
            const idx = ffi.PySequence_Index(self.obj.py, py_value.py);
            if (idx < 0) return PyError.PyRaised;
            return @intCast(idx);
        }

        /// Count occurrences of value in sequence
        /// Equivalent to Python: seq.count(value)
        pub fn count(self: Self, value: anytype) !usize {
            const py_value = py.object(@import("../pyz3.zig"), value);
            const cnt = ffi.PySequence_Count(self.obj.py, py_value.py);
            if (cnt < 0) return PyError.PyRaised;
            return @intCast(cnt);
        }

        // ============================================================
        // Concatenation and Repetition
        // ============================================================

        /// Concatenate two sequences
        /// Equivalent to Python: seq1 + seq2
        ///
        /// Returns a new reference
        pub fn concat(self: Self, other: Self) !Self {
            const result = ffi.PySequence_Concat(self.obj.py, other.obj.py) orelse return PyError.PyRaised;
            return Self{ .obj = .{ .py = result } };
        }

        /// Concatenate with any sequence-like object
        pub fn concatObj(self: Self, other: PyObject) !Self {
            const result = ffi.PySequence_Concat(self.obj.py, other.py) orelse return PyError.PyRaised;
            return Self{ .obj = .{ .py = result } };
        }

        /// Repeat sequence n times
        /// Equivalent to Python: seq * n
        ///
        /// Returns a new reference
        pub fn repeat(self: Self, n: usize) !Self {
            const result = ffi.PySequence_Repeat(self.obj.py, @intCast(n)) orelse return PyError.PyRaised;
            return Self{ .obj = .{ .py = result } };
        }

        /// In-place concatenation (for mutable sequences)
        /// Equivalent to Python: seq += other
        ///
        /// Note: Only works for mutable sequences like list
        pub fn inplaceConcat(self: *Self, other: Self) !void {
            const result = ffi.PySequence_InPlaceConcat(self.obj.py, other.obj.py) orelse return PyError.PyRaised;
            // Update self with the result
            self.obj.decref();
            self.obj.py = result;
        }

        /// In-place repeat (for mutable sequences)
        /// Equivalent to Python: seq *= n
        ///
        /// Note: Only works for mutable sequences like list
        pub fn inplaceRepeat(self: *Self, n: usize) !void {
            const result = ffi.PySequence_InPlaceRepeat(self.obj.py, @intCast(n)) orelse return PyError.PyRaised;
            // Update self with the result
            self.obj.decref();
            self.obj.py = result;
        }

        // ============================================================
        // Conversion and Iteration
        // ============================================================

        /// Convert sequence to a list
        /// Returns a new reference
        pub fn toList(self: Self) !py.PyList(@import("../pyz3.zig")) {
            const list = ffi.PySequence_List(self.obj.py) orelse return PyError.PyRaised;
            return py.PyList(@import("../pyz3.zig")){ .obj = .{ .py = list } };
        }

        /// Convert sequence to a tuple
        /// Returns a new reference
        pub fn toTuple(self: Self) !py.PyTuple(@import("../pyz3.zig")) {
            const tuple = ffi.PySequence_Tuple(self.obj.py) orelse return PyError.PyRaised;
            return py.PyTuple(@import("../pyz3.zig")){ .obj = .{ .py = tuple } };
        }

        /// Get fast sequence access (for iteration)
        /// Returns PySequence_Fast object which can be indexed efficiently
        ///
        /// This is an optimization for iteration - use this for tight loops
        pub fn fast(self: Self, error_msg: [:0]const u8) !PyObject {
            const fast_seq = ffi.PySequence_Fast(self.obj.py, error_msg.ptr) orelse return PyError.PyRaised;
            return PyObject{ .py = fast_seq };
        }

        // ============================================================
        // Utility Operations
        // ============================================================

        /// Get the first item
        /// Equivalent to Python: seq[0]
        pub fn first(self: Self, comptime T: type) !T {
            return self.getItem(T, 0);
        }

        /// Get the last item
        /// Equivalent to Python: seq[-1]
        pub fn last(self: Self, comptime T: type) !T {
            return self.getItem(T, -1);
        }

        /// Check if index is valid for this sequence
        pub fn isValidIndex(self: Self, idx: isize) !bool {
            const len_val: isize = @intCast(try self.len());
            if (idx >= 0) {
                return idx < len_val;
            } else {
                return -idx <= len_val;
            }
        }

        /// Iterate over sequence items
        /// Usage:
        /// ```zig
        /// var iter = seq.iterator();
        /// while (try iter.next()) |item| {
        ///     // Use item...
        ///     defer item.decref();
        /// }
        /// ```
        pub fn iterator(self: Self) SequenceIterator {
            return SequenceIterator{
                .seq = self.obj,
                .index = 0,
                .length = self.len() catch 0,
            };
        }

        // ============================================================
        // Advanced Operations
        // ============================================================

        /// Apply a function to each element (map)
        /// Returns a new list with transformed elements
        pub fn map(self: Self, comptime func: anytype) !py.PyList(@import("../pyz3.zig")) {
            const len_val = try self.len();
            var result_list = try py.PyList(@import("../pyz3.zig")).new(len_val);
            errdefer result_list.obj.decref();

            var i: usize = 0;
            while (i < len_val) : (i += 1) {
                const item = try self.getItemObj(@intCast(i));
                defer item.decref();

                const transformed = func(item);
                try result_list.setItem(i, transformed);
            }

            return result_list;
        }

        /// Filter sequence by predicate
        /// Returns a new list containing only elements where predicate returns true
        pub fn filter(self: Self, comptime predicate: anytype) !py.PyList(@import("../pyz3.zig")) {
            const len_val = try self.len();
            var result_list = try py.PyList(@import("../pyz3.zig")).new(0);
            errdefer result_list.obj.decref();

            var i: usize = 0;
            while (i < len_val) : (i += 1) {
                const item = try self.getItemObj(@intCast(i));
                errdefer item.decref();

                if (try predicate(item)) {
                    try result_list.append(item);
                } else {
                    item.decref();
                }
            }

            return result_list;
        }

        /// Reverse the sequence (returns new reversed sequence)
        /// Equivalent to Python: reversed(seq)
        pub fn reversed(self: Self) !Self {
            _ = try self.len();
            const rev_obj = ffi.PySequence_InPlaceConcat(
                self.obj.py,
                ffi.PyList_New(0) orelse return PyError.PyRaised,
            ) orelse return PyError.PyRaised;

            if (ffi.PyList_Reverse(rev_obj) < 0) {
                ffi.Py_DecRef(rev_obj);
                return PyError.PyRaised;
            }

            return Self{ .obj = .{ .py = rev_obj } };
        }
    };
}

/// Iterator for sequence objects
pub const SequenceIterator = struct {
    seq: PyObject,
    index: usize,
    length: usize,

    /// Get the next item in the sequence
    /// Returns null when iteration is complete
    /// Caller owns the returned reference
    pub fn next(self: *SequenceIterator) !?PyObject {
        if (self.index >= self.length) {
            return null;
        }

        const item = ffi.PySequence_GetItem(self.seq.py, @intCast(self.index)) orelse return PyError.PyRaised;
        self.index += 1;

        return PyObject{ .py = item };
    }

    /// Reset iterator to beginning
    pub fn reset(self: *SequenceIterator) void {
        self.index = 0;
    }

    /// Get remaining item count
    pub fn remaining(self: SequenceIterator) usize {
        return self.length - self.index;
    }
};

// ============================================================
// Tests
// ============================================================

test "PySequenceMixin - basic operations" {
    py.initialize();
    defer py.finalize();

    const root = @import("../pyz3.zig");

    // Create a list to test with
    var list = try py.PyList(root).new(3);
    defer list.obj.decref();

    // Test length
    try std.testing.expectEqual(@as(usize, 3), try list.len());
    try std.testing.expectEqual(false, try list.isEmpty());

    // Test setItem and getItem
    try list.setItem(0, 10);
    try list.setItem(1, 20);
    try list.setItem(2, 30);

    try std.testing.expectEqual(@as(i64, 10), try list.getItem(i64, 0));
    try std.testing.expectEqual(@as(i64, 30), try list.getItem(i64, -1));
}

test "PySequenceMixin - search operations" {
    py.initialize();
    defer py.finalize();

    const root = @import("../pyz3.zig");

    var list = try py.PyList(root).new(5);
    defer list.obj.decref();

    try list.setItem(0, 10);
    try list.setItem(1, 20);
    try list.setItem(2, 10);
    try list.setItem(3, 30);
    try list.setItem(4, 10);

    // Test contains
    try std.testing.expect(try list.contains(10));
    try std.testing.expect(try list.contains(20));
    try std.testing.expect(!try list.contains(999));

    // Test index
    try std.testing.expectEqual(@as(usize, 0), try list.index(10));
    try std.testing.expectEqual(@as(usize, 1), try list.index(20));

    // Test count
    try std.testing.expectEqual(@as(usize, 3), try list.count(10));
    try std.testing.expectEqual(@as(usize, 1), try list.count(20));
}

test "PySequenceMixin - slice operations" {
    py.initialize();
    defer py.finalize();

    const root = @import("../pyz3.zig");

    var list = try py.PyList(root).new(5);
    defer list.obj.decref();

    try list.setItem(0, 0);
    try list.setItem(1, 1);
    try list.setItem(2, 2);
    try list.setItem(3, 3);
    try list.setItem(4, 4);

    // Test getSlice
    var slice = try list.getSlice(1, 4);
    defer slice.obj.decref();

    try std.testing.expectEqual(@as(usize, 3), try slice.len());
    try std.testing.expectEqual(@as(i64, 1), try slice.getItem(i64, 0));
    try std.testing.expectEqual(@as(i64, 3), try slice.getItem(i64, 2));
}

test "PySequenceMixin - concatenation and repetition" {
    py.initialize();
    defer py.finalize();

    const root = @import("../pyz3.zig");

    var list1 = try py.PyList(root).new(2);
    defer list1.obj.decref();
    try list1.setItem(0, 1);
    try list1.setItem(1, 2);

    var list2 = try py.PyList(root).new(2);
    defer list2.obj.decref();
    try list2.setItem(0, 3);
    try list2.setItem(1, 4);

    // Test concat
    var concatenated = try list1.concat(list2);
    defer concatenated.obj.decref();
    try std.testing.expectEqual(@as(usize, 4), try concatenated.len());

    // Test repeat
    var repeated = try list1.repeat(3);
    defer repeated.obj.decref();
    try std.testing.expectEqual(@as(usize, 6), try repeated.len());
}

test "PySequenceMixin - iterator" {
    py.initialize();
    defer py.finalize();

    const root = @import("../pyz3.zig");

    var list = try py.PyList(root).new(3);
    defer list.obj.decref();
    try list.setItem(0, 10);
    try list.setItem(1, 20);
    try list.setItem(2, 30);

    var iter = list.iterator();
    var sum: i64 = 0;
    var count: usize = 0;

    while (try iter.next()) |item| {
        defer item.decref();
        const val = try py.as(root, i64, item);
        sum += val;
        count += 1;
    }

    try std.testing.expectEqual(@as(i64, 60), sum);
    try std.testing.expectEqual(@as(usize, 3), count);
}
