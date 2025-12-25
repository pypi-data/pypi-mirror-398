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

/// Wrapper for Python fractions.Fraction
pub fn PyFraction(comptime root: type) type {
    return extern struct {
        obj: py.PyObject,

        const Self = @This();
        pub const from = struct {
            pub fn check(obj: py.PyObject) !bool {
                const fractions_mod = py.import(Self, "fractions") catch return false;
                defer fractions_mod.decref();

                const fraction_type = fractions_mod.get("Fraction") catch return false;
                defer fraction_type.decref();

                return py.isinstance(Self, obj, fraction_type);
            }

            pub fn checked(obj: py.PyObject) !Self {
                if (try Self.from.check(obj) == false) {
                    const typeName = try py.str(root, py.type_(root, obj));
                    defer typeName.obj.decref();
                    return py.TypeError(root).raiseFmt("expected {s}, found {s}", .{ "Fraction", try typeName.asSlice() });
                }
                return .{ .obj = obj };
            }

            pub fn unchecked(obj: py.PyObject) Self {
                return .{ .obj = obj };
            }
        };

        fn fractionType() !py.PyObject {
            const fractions_mod = try py.import(root, "fractions");
            defer fractions_mod.decref();
            return fractions_mod.get("Fraction");
        }

        /// Create a new Fraction from a numerator and a denominator.
        pub fn new(num: i64, den: i64) !Self {
            const fraction_type = try fractionType();
            defer fraction_type.decref();

            const num_obj = try py.PyLong.create(num);
            defer num_obj.obj.decref();
            const den_obj = try py.PyLong.create(den);
            defer den_obj.obj.decref();

            const fraction_obj = try py.call(root, py.PyObject, fraction_type, .{ num_obj.obj, den_obj.obj }, .{});
            return .{ .obj = fraction_obj };
        }

        /// Create a new Fraction from a float.
        pub fn fromFloat(value: f64) !Self {
            const fraction_type = try fractionType();
            defer fraction_type.decref();
            const float_obj = try py.PyFloat.create(value);
            defer float_obj.obj.decref();
            const fraction_obj = try py.call(root, py.PyObject, fraction_type, .{float_obj.obj}, .{});
            return .{ .obj = fraction_obj };
        }

        /// Create a new Fraction from a string.
        pub fn fromString(value: []const u8) !Self {
            const fraction_type = try fractionType();
            defer fraction_type.decref();
            const str_obj = try py.PyString.create(value);
            defer str_obj.obj.decref();
            const fraction_obj = try py.call(root, py.PyObject, fraction_type, .{str_obj.obj}, .{});
            return .{ .obj = fraction_obj };
        }

        pub fn numerator(self: Self) !i64 {
            const num_obj = try self.obj.get("numerator");
            defer num_obj.decref();
            return py.as(root, i64, num_obj);
        }

        pub fn denominator(self: Self) !i64 {
            const den_obj = try self.obj.get("denominator");
            defer den_obj.decref();
            return py.as(root, i64, den_obj);
        }

        pub fn add(self: Self, other: Self) !Self {
            const add_method = try self.obj.get("__add__");
            defer add_method.decref();
            const res = try py.call(root, py.PyObject, add_method, .{other.obj}, .{});
            return Self.from.unchecked(res);
        }

        pub fn sub(self: Self, other: Self) !Self {
            const sub_method = try self.obj.get("__sub__");
            defer sub_method.decref();
            const res = try py.call(root, py.PyObject, sub_method, .{other.obj}, .{});
            return Self.from.unchecked(res);
        }

        pub fn mul(self: Self, other: Self) !Self {
            const mul_method = try self.obj.get("__mul__");
            defer mul_method.decref();
            const res = try py.call(root, py.PyObject, mul_method, .{other.obj}, .{});
            return Self.from.unchecked(res);
        }

        pub fn div(self: Self, other: Self) !Self {
            const truediv_method = try self.obj.get("__truediv__");
            defer truediv_method.decref();
            const res = try py.call(root, py.PyObject, truediv_method, .{other.obj}, .{});
            return Self.from.unchecked(res);
        }

        pub fn asFloat(self: Self) !f64 {
            const builtins = try py.import(root, "builtins");
            defer builtins.decref();
            const float_type = try builtins.get("float");
            defer float_type.decref();
            const float_obj = try py.call(root, py.PyObject, float_type, .{self.obj}, .{});
            defer float_obj.decref();
            return py.as(root, f64, float_obj);
        }

        pub fn check(obj: py.PyObject) !bool {
            const fractions_mod = py.import(root, "fractions") catch return false;
            defer fractions_mod.decref();

            const fraction_type = fractions_mod.get("Fraction") catch return false;
            defer fraction_type.decref();

            return py.isinstance(root, obj, fraction_type);
        }
    };
}

test "PyFraction" {
    py.initialize();
    defer py.finalize();

    const root = @This();

    // Creation
    const f1 = try py.PyFraction(root).new(1, 2);
    defer f1.obj.decref();

    try std.testing.expectEqual(@as(i64, 1), try f1.numerator());
    try std.testing.expectEqual(@as(i64, 2), try f1.denominator());

    const f2 = try py.PyFraction(root).fromFloat(0.25);
    defer f2.obj.decref();
    try std.testing.expectEqual(@as(i64, 1), try f2.numerator());
    try std.testing.expectEqual(@as(i64, 4), try f2.denominator());

    const f3 = try py.PyFraction(root).fromString("3/4");
    defer f3.obj.decref();
    try std.testing.expectEqual(@as(i64, 3), try f3.numerator());
    try std.testing.expectEqual(@as(i64, 4), try f3.denominator());

    // Arithmetic
    // 1/2 + 1/4 = 3/4
    const sum = try f1.add(f2);
    defer sum.obj.decref();
    try std.testing.expectEqual(@as(i64, 3), try sum.numerator());
    try std.testing.expectEqual(@as(i64, 4), try sum.denominator());

    // 3/4 - 1/2 = 1/4
    const diff = try f3.sub(f1);
    defer diff.obj.decref();
    try std.testing.expectEqual(@as(i64, 1), try diff.numerator());
    try std.testing.expectEqual(@as(i64, 4), try diff.denominator());

    // 1/2 * 3/4 = 3/8
    const prod = try f1.mul(f3);
    defer prod.obj.decref();
    try std.testing.expectEqual(@as(i64, 3), try prod.numerator());
    try std.testing.expectEqual(@as(i64, 8), try prod.denominator());

    // (1/2) / (1/4) = 2
    const quot = try f1.div(f2);
    defer quot.obj.decref();
    try std.testing.expectEqual(@as(i64, 2), try quot.numerator());
    try std.testing.expectEqual(@as(i64, 1), try quot.denominator());

    // asFloat
    const float_val = try f1.asFloat();
    try std.testing.expectEqual(@as(f64, 0.5), float_val);
}