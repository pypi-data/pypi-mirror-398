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

/// Wrapper for Python enum.Enum
pub fn PyEnum(comptime root: type) type {
    return extern struct {
        obj: py.PyObject, // This will be the Enum *type*

        const Self = @This();
        pub const from = PyObjectMixin("Enum", "PyEnum", Self);

        fn enumModule() !py.PyObject {
            return py.import(root, "enum");
        }

        /// Create a new Enum type.
        pub fn new(comptime class_name: []const u8, comptime members: []const []const u8) !Self {
            const enum_mod = try enumModule();
            defer enum_mod.decref();

            const enum_type_builder = try enum_mod.get("Enum");
            defer enum_type_builder.decref();

            const class_name_obj = try py.PyString.create(class_name);
            defer class_name_obj.obj.decref();

            const joined_members = try std.mem.join(py.allocator, " ", members);
            defer py.allocator.free(joined_members);
            const members_obj = try py.PyString.create(joined_members);
            defer members_obj.obj.decref();

            const enum_type = try py.call(root, py.PyObject, enum_type_builder, .{ class_name_obj.obj, members_obj.obj }, .{});
            return .{ .obj = enum_type };
        }

        /// Get an enum member by name.
        pub fn getMember(self: Self, name: []const u8) !py.PyObject {
            return self.obj.get(name);
        }

        /// Get the name of an enum member.
        pub fn getMemberName(member: py.PyObject) ![]const u8 {
            const name_obj = try member.get("name");
            defer name_obj.decref();
            const name_str = try py.PyString.from.checked(root, name_obj);
            return name_str.asSlice();
        }

        /// Get the value of an enum member.
        pub fn getMemberValue(member: py.PyObject, comptime T: type) !T {
            const value_obj = try member.get("value");
            defer value_obj.decref();
            return py.as(root, T, value_obj);
        }
    };
}

test "PyEnum" {
    py.initialize();
    defer py.finalize();

    const root = @This();

    // Create an Enum type
    const Color = try py.PyEnum(root).new("Color", &.{ "RED", "GREEN", "BLUE" });
    defer Color.obj.decref();

    // Get members
    const RED = try Color.getMember("RED");
    defer RED.decref();
    const GREEN = try Color.getMember("GREEN");
    defer GREEN.decref();

    // Check member names
    try std.testing.expectEqualStrings("RED", try py.PyEnum(root).getMemberName(RED));
    try std.testing.expectEqualStrings("GREEN", try py.PyEnum(root).getMemberName(GREEN));

    // Check member values (auto-assigned by Enum)
    try std.testing.expectEqual(@as(i64, 1), try py.PyEnum(root).getMemberValue(RED, i64));
    try std.testing.expectEqual(@as(i64, 2), try py.PyEnum(root).getMemberValue(GREEN, i64));

    // Check equality
    const RED2 = try Color.getMember("RED");
    defer RED2.decref();
    try std.testing.expect(try py.eq(root, RED, RED2));
    try std.testing.expect(try py.ne(root, RED, GREEN));

    // Iterating over an enum
    const iter = try py.iter(root, Color.obj);
    var count: usize = 0;
    while (try iter.next(py.PyObject)) |member| {
        defer member.decref();
        count += 1;
    }
    try std.testing.expectEqual(@as(usize, 3), count);
}