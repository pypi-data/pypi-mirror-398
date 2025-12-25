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

/// Python bytearray object wrapper (mutable byte sequence)
pub const PyByteArray = extern struct {
    obj: py.PyObject,

    const Self = @This();

    /// Create a bytearray from a byte slice
    pub fn from(bytes: []const u8) !Self {
        const ba_obj = ffi.PyByteArray_FromStringAndSize(
            @ptrCast(bytes.ptr),
            @intCast(bytes.len),
        ) orelse return PyError.PyRaised;
        return .{ .obj = .{ .py = ba_obj } };
    }

    /// Create an empty bytearray with specified size
    pub fn withSize(size: usize) !Self {
        const ba_obj = ffi.PyByteArray_FromStringAndSize(null, @intCast(size)) orelse return PyError.PyRaised;
        return .{ .obj = .{ .py = ba_obj } };
    }

    /// Create a bytearray from an iterable
    pub fn fromIterable(iterable: py.PyObject) !Self {
        const ba_obj = ffi.PyByteArray_FromObject(iterable.py) orelse return PyError.PyRaised;
        return .{ .obj = .{ .py = ba_obj } };
    }

    /// Check if object is a bytearray
    pub fn check(obj: py.PyObject) bool {
        return ffi.PyByteArray_Check(obj.py) != 0;
    }

    /// Get the size of the bytearray
    pub fn len(self: Self) !usize {
        const size = ffi.PyByteArray_Size(self.obj.py);
        if (size < 0) return PyError.PyRaised;
        return @intCast(size);
    }

    /// Get a pointer to the internal buffer (mutable)
    /// Warning: This pointer may be invalidated if the bytearray is resized
    pub fn asSlice(self: Self) ![]u8 {
        const ptr = ffi.PyByteArray_AsString(self.obj.py);
        if (ptr == null) return PyError.PyRaised;
        const size = try self.len();
        return @as([*]u8, @ptrCast(ptr))[0..size];
    }

    /// Resize the bytearray
    pub fn resize(self: Self, new_size: usize) !void {
        if (ffi.PyByteArray_Resize(self.obj.py, @intCast(new_size)) < 0) {
            return PyError.PyRaised;
        }
    }

    /// Concatenate two bytearrays, returning a new bytearray
    pub fn concat(self: Self, other: Self) !Self {
        const result = ffi.PyByteArray_Concat(self.obj.py, other.obj.py) orelse return PyError.PyRaised;
        return .{ .obj = .{ .py = result } };
    }

    /// Append a single byte to the bytearray
    pub fn append(self: Self, byte: u8) !void {
        const current_len = try self.len();
        try self.resize(current_len + 1);
        const slice = try self.asSlice();
        slice[current_len] = byte;
    }

    /// Extend the bytearray with bytes from a slice
    pub fn extend(self: Self, bytes: []const u8) !void {
        const current_len = try self.len();
        try self.resize(current_len + bytes.len);
        const slice = try self.asSlice();
        @memcpy(slice[current_len..], bytes);
    }

    /// Get a byte at a specific index
    pub fn get(self: Self, index: usize) !u8 {
        const slice = try self.asSlice();
        if (index >= slice.len) {
            return py.IndexError(@import("../pyz3.zig")).raise("bytearray index out of range");
        }
        return slice[index];
    }

    /// Set a byte at a specific index
    pub fn set(self: Self, index: usize, byte: u8) !void {
        const slice = try self.asSlice();
        if (index >= slice.len) {
            return py.IndexError(@import("../pyz3.zig")).raise("bytearray index out of range");
        }
        slice[index] = byte;
    }

    /// Clear the bytearray (resize to 0)
    pub fn clear(self: Self) !void {
        try self.resize(0);
    }

    /// Create a copy of the bytearray
    pub fn copy(self: Self) !Self {
        const slice = try self.asSlice();
        return try Self.from(slice);
    }

    /// Convert to immutable bytes object
    pub fn toBytes(self: Self) !py.PyBytes {
        const slice = try self.asSlice();
        return try py.PyBytes.from(slice);
    }

    /// Reverse the bytearray in place
    pub fn reverse(self: Self) !void {
        const slice = try self.asSlice();
        std.mem.reverse(u8, slice);
    }

    /// Remove and return an item at index (default last)
    pub fn pop(self: Self, index: ?isize) !u8 {
        const slice = try self.asSlice();
        const length = slice.len;

        if (length == 0) {
            return py.IndexError(@import("../pyz3.zig")).raise("pop from empty bytearray");
        }

        const idx = if (index) |i| blk: {
            const normalized = if (i < 0) @as(usize, @intCast(@as(isize, @intCast(length)) + i)) else @as(usize, @intCast(i));
            if (normalized >= length) {
                return py.IndexError(@import("../pyz3.zig")).raise("pop index out of range");
            }
            break :blk normalized;
        } else length - 1;

        const value = slice[idx];

        // Shift elements after idx
        if (idx < length - 1) {
            std.mem.copyForwards(u8, slice[idx..], slice[idx + 1 ..]);
        }

        try self.resize(length - 1);
        return value;
    }

    /// Insert a byte at a specific index
    pub fn insert(self: Self, index: usize, byte: u8) !void {
        const current_len = try self.len();
        const idx = @min(index, current_len);

        try self.resize(current_len + 1);
        const slice = try self.asSlice();

        // Shift elements to make room
        if (idx < current_len) {
            std.mem.copyBackwards(u8, slice[idx + 1 ..], slice[idx..current_len]);
        }

        slice[idx] = byte;
    }

    /// Remove first occurrence of a byte value
    pub fn remove(self: Self, byte: u8) !void {
        const slice = try self.asSlice();

        for (slice, 0..) |b, i| {
            if (b == byte) {
                _ = try self.pop(@intCast(i));
                return;
            }
        }

        return py.ValueError(@import("../pyz3.zig")).raise("bytearray.remove(x): x not in bytearray");
    }

    /// Count occurrences of a byte value
    pub fn count(self: Self, byte: u8) !usize {
        const slice = try self.asSlice();
        var cnt: usize = 0;
        for (slice) |b| {
            if (b == byte) cnt += 1;
        }
        return cnt;
    }

    /// Find index of first occurrence of byte value (-1 if not found)
    pub fn indexOf(self: Self, byte: u8) !isize {
        const slice = try self.asSlice();
        for (slice, 0..) |b, i| {
            if (b == byte) return @intCast(i);
        }
        return -1;
    }
};
