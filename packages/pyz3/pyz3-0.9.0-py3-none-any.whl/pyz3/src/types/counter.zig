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

/// Wrapper for Python collections.Counter
pub fn PyCounter(comptime root: type) type {
    return extern struct {
        obj: py.PyObject,

        const Self = @This();
        pub const from = PyObjectMixin("Counter", "PyCounter", Self);

        fn counterType() !py.PyObject {
            const collections = try py.import(root, "collections");
            defer collections.decref();
            return collections.get("Counter");
        }

        /// Create a new empty Counter.
        pub fn new() !Self {
            const counter_type = try counterType();
            defer counter_type.decref();
            const counter_obj = try py.call0(root, py.PyObject, counter_type);
            return .{ .obj = counter_obj };
        }

        /// Create a new Counter from an iterable.
        pub fn fromIterable(iterable: py.PyObject) !Self {
            const counter_type = try counterType();
            defer counter_type.decref();
            const counter_obj = try py.call(root, py.PyObject, counter_type, .{iterable}, .{});
            return .{ .obj = counter_obj };
        }

        /// Delegate to PyDict methods
        pub fn asDict(self: Self) py.PyDict(root) {
            return .{ .obj = self.obj };
        }

        /// Return an iterator over elements repeating each as many times as its count.
        pub fn elements(self: Self) !py.PyIter(root) {
            const elements_method = try self.obj.get("elements");
            defer elements_method.decref();
            const iter_obj = try py.call0(root, py.PyObject, elements_method);
            return py.PyIter(root).from.unchecked(iter_obj);
        }

        /// Return a list of the n most common elements and their counts from the most common to the least.
        pub fn mostCommon(self: Self, n: usize) !py.PyList(root) {
            const most_common_method = try self.obj.get("most_common");
            defer most_common_method.decref();
            const n_obj = try py.PyLong.create(n);
            defer n_obj.obj.decref();
            const list_obj = try py.call(root, py.PyObject, most_common_method, .{n_obj}, .{});
            return py.PyList(root).from.unchecked(list_obj);
        }

        /// Subtract elements from an iterable or from another mapping.
        pub fn subtract(self: Self, iterable: py.PyObject) !void {
            const subtract_method = try self.obj.get("subtract");
            defer subtract_method.decref();
            const result = try py.call(root, py.PyObject, subtract_method, .{iterable}, .{});
            result.decref();
        }

        /// Add counts from an iterable or from another mapping.
        pub fn update(self: Self, iterable: py.PyObject) !void {
            const update_method = try self.obj.get("update");
            defer update_method.decref();
            const result = try py.call(root, py.PyObject, update_method, .{iterable}, .{});
            result.decref();
        }
    };
}

test "PyCounter" {
    py.initialize();
    defer py.finalize();

    const root = @This();

    // Create from a string
    const iterable = try py.PyString.create("abracadabra");
    defer iterable.obj.decref();
    const counter = try py.PyCounter(root).fromIterable(iterable.obj);
    defer counter.obj.decref();

    const counter_dict = counter.asDict();

    // Check counts
    var count_a = try counter_dict.getItem(py.PyLong, "a");
    try std.testing.expect(count_a != null);
    try std.testing.expectEqual(@as(i64, 5), try count_a.?.as(i64));
    count_a.?.obj.decref();

    var count_b = try counter_dict.getItem(py.PyLong, "b");
    try std.testing.expect(count_b != null);
    try std.testing.expectEqual(@as(i64, 2), try count_b.?.as(i64));
    count_b.?.obj.decref();

    // most_common
    const common = try counter.mostCommon(2);
    defer common.obj.decref();
    try std.testing.expectEqual(@as(usize, 2), common.length());

    const first_common = try common.getItem(py.PyTuple(root), 0);
    defer first_common.obj.decref();
    try std.testing.expectEqualStrings("a", try (try first_common.getItem(py.PyString, 0)).asSlice());
    try std.testing.expectEqual(@as(i64, 5), try (try first_common.getItem(py.PyLong, 1)).as(i64));

    // update
    const update_iterable = try py.PyString.create("aazz");
    defer update_iterable.obj.decref();
    try counter.update(update_iterable.obj);

    count_a = try counter_dict.getItem(py.PyLong, "a");
    try std.testing.expectEqual(@as(i64, 7), try count_a.?.as(i64));
    count_a.?.obj.decref();
    var count_z = try counter_dict.getItem(py.PyLong, "z");
    try std.testing.expectEqual(@as(i64, 2), try count_z.?.as(i64));
    count_z.?.obj.decref();

    // subtract
    const subtract_iterable = try py.PyString.create("abr");
    defer subtract_iterable.obj.decref();
    try counter.subtract(subtract_iterable.obj);

    count_a = try counter_dict.getItem(py.PyLong, "a");
    try std.testing.expectEqual(@as(i64, 6), try count_a.?.as(i64));
    count_a.?.obj.decref();

    // elements
    const elements = try counter.elements();
    var elements_count: usize = 0;
    while (try elements.next(py.PyObject)) |elem| {
        elem.decref();
        elements_count += 1;
    }
    // 6*a + 1*b + 1*r + 1*c + 1*d + 2*z = 12
    try std.testing.expectEqual(@as(usize, 12), elements_count);
}