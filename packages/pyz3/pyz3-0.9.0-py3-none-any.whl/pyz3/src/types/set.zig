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

/// Python set object wrapper (mutable unordered collection)
pub fn PySet(comptime root: type) type {
    return extern struct {
        obj: py.PyObject,

        const Self = @This();

        /// Create a new empty set
        pub fn new() !Self {
            const set_obj = ffi.PySet_New(null) orelse return PyError.PyRaised;
            return .{ .obj = .{ .py = set_obj } };
        }

        /// Create a set from an iterable
        pub fn fromIterable(iterable: py.PyObject) !Self {
            const set_obj = ffi.PySet_New(iterable.py) orelse return PyError.PyRaised;
            return .{ .obj = .{ .py = set_obj } };
        }

        /// Check if object is a set
        pub fn check(obj: py.PyObject) bool {
            return ffi.PySet_Check(obj.py) != 0;
        }

        /// Get the size of the set
        pub fn len(self: Self) !usize {
            const size = ffi.PySet_Size(self.obj.py);
            if (size < 0) return PyError.PyRaised;
            return @intCast(size);
        }

        /// Add an item to the set
        pub fn add(self: Self, item: py.PyObject) !void {
            if (ffi.PySet_Add(self.obj.py, item.py) < 0) {
                return PyError.PyRaised;
            }
        }

        /// Check if item is in the set
        pub fn contains(self: Self, item: py.PyObject) !bool {
            const result = ffi.PySet_Contains(self.obj.py, item.py);
            if (result < 0) return PyError.PyRaised;
            return result == 1;
        }

        /// Remove an item from the set (raises KeyError if not present)
        pub fn discard(self: Self, item: py.PyObject) !void {
            if (ffi.PySet_Discard(self.obj.py, item.py) < 0) {
                return PyError.PyRaised;
            }
        }

        /// Remove and return an arbitrary item
        pub fn pop(self: Self) !py.PyObject {
            const item = ffi.PySet_Pop(self.obj.py) orelse return PyError.PyRaised;
            return .{ .py = item };
        }

        /// Remove all items from the set
        pub fn clear(self: Self) !void {
            if (ffi.PySet_Clear(self.obj.py) < 0) {
                return PyError.PyRaised;
            }
        }

        /// Get an iterator over the set
        pub fn iter(self: Self) !py.PyIter {
            const iter_obj = ffi.PyObject_GetIter(self.obj.py) orelse return PyError.PyRaised;
            return .{ .obj = .{ .py = iter_obj } };
        }

        /// Create a set from a Zig slice
        pub fn fromSlice(items: anytype) !Self {
            const set = try Self.new();
            for (items) |item| {
                const py_item = try py.create(root, item);
                defer py_item.decref();
                try set.add(py_item);
            }
            return set;
        }

        /// Union of two sets
        pub fn unionWith(self: Self, other: Self) !Self {
            const result = ffi.PySet_New(self.obj.py) orelse return PyError.PyRaised;
            const result_set = Self{ .obj = .{ .py = result } };

            // Add all items from other
            var it = try other.iter();
            while (try it.next()) |item| {
                defer item.decref();
                try result_set.add(item);
            }

            return result_set;
        }

        /// Intersection of two sets
        pub fn intersection(self: Self, other: Self) !Self {
            const result = try Self.new();

            var it = try self.iter();
            while (try it.next()) |item| {
                defer item.decref();
                if (try other.contains(item)) {
                    try result.add(item);
                }
            }

            return result;
        }

        /// Difference of two sets (items in self but not in other)
        pub fn difference(self: Self, other: Self) !Self {
            const result = try Self.new();

            var it = try self.iter();
            while (try it.next()) |item| {
                defer item.decref();
                if (!try other.contains(item)) {
                    try result.add(item);
                }
            }

            return result;
        }
    };
}

/// Python frozenset object wrapper (immutable unordered collection)
pub fn PyFrozenSet(comptime root: type) type {
    return extern struct {
        obj: py.PyObject,

        const Self = @This();

        /// Create a new frozenset from an iterable
        pub fn new(iterable: ?py.PyObject) !Self {
            const iter_ptr = if (iterable) |it| it.py else null;
            const fs_obj = ffi.PyFrozenSet_New(iter_ptr) orelse return PyError.PyRaised;
            return .{ .obj = .{ .py = fs_obj } };
        }

        /// Check if object is a frozenset
        pub fn check(obj: py.PyObject) bool {
            return ffi.PyFrozenSet_Check(obj.py) != 0;
        }

        /// Get the size of the frozenset
        pub fn len(self: Self) !usize {
            const size = ffi.PySet_Size(self.obj.py);
            if (size < 0) return PyError.PyRaised;
            return @intCast(size);
        }

        /// Check if item is in the frozenset
        pub fn contains(self: Self, item: py.PyObject) !bool {
            const result = ffi.PySet_Contains(self.obj.py, item.py);
            if (result < 0) return PyError.PyRaised;
            return result == 1;
        }

        /// Get an iterator over the frozenset
        pub fn iter(self: Self) !py.PyIter {
            const iter_obj = ffi.PyObject_GetIter(self.obj.py) orelse return PyError.PyRaised;
            return .{ .obj = .{ .py = iter_obj } };
        }

        /// Create a frozenset from a Zig slice
        pub fn fromSlice(items: anytype) !Self {
            const list = try py.PyList(root).new();
            defer list.obj.decref();

            for (items) |item| {
                const py_item = try py.create(root, item);
                defer py_item.decref();
                try list.append(py_item);
            }

            return try Self.new(list.obj);
        }

        /// Union of two frozensets
        pub fn unionWith(self: Self, other: Self) !Self {
            // Create a regular set for union, then convert to frozenset
            const temp_set = ffi.PySet_New(self.obj.py) orelse return PyError.PyRaised;
            defer {
                const obj = py.PyObject{ .py = temp_set };
                obj.decref();
            }

            var it = try other.iter();
            while (try it.next()) |item| {
                defer item.decref();
                if (ffi.PySet_Add(temp_set, item.py) < 0) {
                    return PyError.PyRaised;
                }
            }

            return try Self.new(.{ .py = temp_set });
        }

        /// Intersection of two frozensets
        pub fn intersection(self: Self, other: Self) !Self {
            const temp_set = ffi.PySet_New(null) orelse return PyError.PyRaised;
            defer {
                const obj = py.PyObject{ .py = temp_set };
                obj.decref();
            }

            var it = try self.iter();
            while (try it.next()) |item| {
                defer item.decref();
                if (try other.contains(item)) {
                    if (ffi.PySet_Add(temp_set, item.py) < 0) {
                        return PyError.PyRaised;
                    }
                }
            }

            return try Self.new(.{ .py = temp_set });
        }
    };
}
