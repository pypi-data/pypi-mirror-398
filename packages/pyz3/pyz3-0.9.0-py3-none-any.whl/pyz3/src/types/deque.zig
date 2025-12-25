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
const py = @import("../pyz3.zig");
const PyObjectMixin = @import("./obj.zig").PyObjectMixin;
const ffi = py.ffi;
const PyError = @import("../errors.zig").PyError;

/// Wrapper for Python collections.deque
pub fn PyDeque(comptime root: type) type {
    return extern struct {
        obj: py.PyObject,

        const Self = @This();
        pub const from = PyObjectMixin("deque", "PyDeque", Self);

        fn dequeType() !py.PyObject {
            const collections = try py.import(root, "collections");
            defer collections.decref();
            return collections.get("deque");
        }

        /// Create a new empty deque.
        pub fn new() !Self {
            const deque_type = try dequeType();
            defer deque_type.decref();
            const deque_obj = try py.call0(root, py.PyObject, deque_type);
            return .{ .obj = deque_obj };
        }

        /// Create a new deque from an iterable.
        pub fn fromIterable(iterable: py.PyObject) !Self {
            const deque_type = try dequeType();
            defer deque_type.decref();
            const deque_obj = try py.call(root, py.PyObject, deque_type, .{iterable}, .{});
            return .{ .obj = deque_obj };
        }

        pub fn len(self: Self) !usize {
            const l = ffi.PyObject_Length(self.obj.py);
            if (l < 0) return PyError.PyRaised;
            return @intCast(l);
        }

        pub fn getItem(self: Self, comptime T: type, index: isize) !T {
            const index_obj = try py.PyLong.create(index);
            defer index_obj.obj.decref();
            const item = ffi.PyObject_GetItem(self.obj.py, index_obj.obj.py) orelse return PyError.PyRaised;
            return py.as(root, T, item);
        }

        pub fn append(self: Self, item: py.PyObject) !void {
            const append_method = try self.obj.get("append");
            defer append_method.decref();
            const res = try py.call(root, py.PyObject, append_method, .{item}, .{});
            res.decref();
        }

        pub fn appendLeft(self: Self, item: py.PyObject) !void {
            const appendleft_method = try self.obj.get("appendleft");
            defer appendleft_method.decref();
            const res = try py.call(root, py.PyObject, appendleft_method, .{item}, .{});
            res.decref();
        }

        pub fn pop(self: Self) !py.PyObject {
            const pop_method = try self.obj.get("pop");
            defer pop_method.decref();
            return py.call0(root, py.PyObject, pop_method);
        }

        pub fn popLeft(self: Self) !py.PyObject {
            const popleft_method = try self.obj.get("popleft");
            defer popleft_method.decref();
            return py.call0(root, py.PyObject, popleft_method);
        }

        pub fn extend(self: Self, iterable: py.PyObject) !void {
            const extend_method = try self.obj.get("extend");
            defer extend_method.decref();
            const res = try py.call(root, py.PyObject, extend_method, .{iterable}, .{});
            res.decref();
        }

        pub fn extendLeft(self: Self, iterable: py.PyObject) !void {
            const extendleft_method = try self.obj.get("extendleft");
            defer extendleft_method.decref();
            const res = try py.call(root, py.PyObject, extendleft_method, .{iterable}, .{});
            res.decref();
        }

        pub fn rotate(self: Self, n: isize) !void {
            const rotate_method = try self.obj.get("rotate");
            defer rotate_method.decref();
            const n_obj = try py.PyLong.create(n);
            defer n_obj.obj.decref();
            const res = try py.call(root, py.PyObject, rotate_method, .{n_obj}, .{});
            res.decref();
        }

        pub fn clear(self: Self) !void {
            const clear_method = try self.obj.get("clear");
            defer clear_method.decref();
            const res = try py.call0(root, py.PyObject, clear_method);
            res.decref();
        }
    };
}

test "PyDeque" {
    py.initialize();
    defer py.finalize();

    const root = @This();

    const d = try py.PyDeque(root).new();
    defer d.obj.decref();

    // append and appendLeft
    const one = try py.PyLong.create(1);
    defer one.obj.decref();
    const two = try py.PyLong.create(2);
    defer two.obj.decref();
    const zero = try py.PyLong.create(0);
    defer zero.obj.decref();

    try d.append(one.obj); // [1]
    try d.append(two.obj); // [1, 2]
    try d.appendLeft(zero.obj); // [0, 1, 2]

    try std.testing.expectEqual(@as(usize, 3), try d.len());
    try std.testing.expectEqual(@as(i64, 0), try d.getItem(i64, 0));
    try std.testing.expectEqual(@as(i64, 1), try d.getItem(i64, 1));
    try std.testing.expectEqual(@as(i64, 2), try d.getItem(i64, 2));

    // pop and popLeft
    const popped_right = try d.pop();
    defer popped_right.decref();
    try std.testing.expectEqual(@as(i64, 2), try py.as(root, i64, popped_right));
    try std.testing.expectEqual(@as(usize, 2), try d.len());

    const popped_left = try d.popLeft();
    defer popped_left.decref();
    try std.testing.expectEqual(@as(i64, 0), try py.as(root, i64, popped_left));
    try std.testing.expectEqual(@as(usize, 1), try d.len());

    // extend and extendLeft
    const list1 = try py.PyList(root).new(0);
    try list1.append(py.PyLong.create(3) catch unreachable);
    try list1.append(py.PyLong.create(4) catch unreachable);
    try d.extend(list1.obj); // [1, 3, 4]
    list1.obj.decref();

    try std.testing.expectEqual(@as(i64, 4), try d.getItem(i64, 2));

    const list2 = try py.PyList(root).new(0);
    try list2.append(py.PyLong.create(-1) catch unreachable);
    try list2.append(py.PyLong.create(-2) catch unreachable);
    try d.extendLeft(list2.obj); // [-2, -1, 1, 3, 4]
    list2.obj.decref();

    try std.testing.expectEqual(@as(usize, 5), try d.len());
    try std.testing.expectEqual(@as(i64, -2), try d.getItem(i64, 0));

    // rotate
    try d.rotate(2); // [3, 4, -2, -1, 1]
    try std.testing.expectEqual(@as(i64, 3), try d.getItem(i64, 0));
    try std.testing.expectEqual(@as(i64, 1), try d.getItem(i64, 4));

    try d.rotate(-1); // [4, -2, -1, 1, 3]
    try std.testing.expectEqual(@as(i64, 4), try d.getItem(i64, 0));

    // clear
    try d.clear();
    try std.testing.expectEqual(@as(usize, 0), try d.len());
}