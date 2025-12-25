// Licensed under the Apache License, Version 2.0 (the "License");
// you may not use this file except in compliance with the License.
// You may obtain a copy of the License.
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

/// Wrapper for Python async generator
pub fn PyAsyncGenerator(comptime root: type) type {
    return extern struct {
        obj: py.PyObject,

        const Self = @This();
        pub const from = struct {
            pub fn check(obj: py.PyObject) !bool {
                const types = try py.import(root, "types");
                defer types.decref();
                const async_gen_type = try types.get("AsyncGeneratorType");
                defer async_gen_type.decref();
                return py.isinstance(root, obj, async_gen_type);
            }

            pub fn checked(obj: py.PyObject) !Self {
                if (try Self.check(obj) == false) {
                    const typeName = try py.str(root, py.type_(root, obj));
                    defer typeName.obj.decref();
                    return py.TypeError(root).raiseFmt("expected {s}, found {s}", .{ "async_generator", try typeName.asSlice() });
                }
                return .{ .obj = obj };
            }

            pub fn unchecked(obj: py.PyObject) Self {
                return .{ .obj = obj };
            }
        };

        /// Check if an object is an async generator.
        pub fn check(obj: py.PyObject) !bool {
            const types = try py.import(root, "types");
            defer types.decref();
            const async_gen_type = try types.get("AsyncGeneratorType");
            defer async_gen_type.decref();
            return py.isinstance(root, obj, async_gen_type);
        }

        /// Returns an awaitable that results in the next value from the generator.
        pub fn anext(self: Self) !py.PyAwaitable(root) {
            const anext_method = try self.obj.get("__anext__");
            defer anext_method.decref();
            const awaitable = try py.call0(root, py.PyObject, anext_method);
            return py.PyAwaitable(root){ .obj = awaitable };
        }

        /// Sends a value into the async generator. Returns an awaitable.
        pub fn asend(self: Self, value: py.PyObject) !py.PyAwaitable(root) {
            const asend_method = try self.obj.get("asend");
            defer asend_method.decref();
            const awaitable = try py.call(root, py.PyObject, asend_method, .{value}, .{});
            return py.PyAwaitable(root){ .obj = awaitable };
        }

        /// Throws an exception into the async generator. Returns an awaitable.
        pub fn athrow(self: Self, exc_type: py.PyObject, value: ?py.PyObject, traceback: ?py.PyObject) !py.PyAwaitable(root) {
            const athrow_method = try self.obj.get("athrow");
            defer athrow_method.decref();

            var args_tuple = try py.PyTuple(root).new(3);
            defer args_tuple.obj.decref();

            try args_tuple.setOwnedItem(0, exc_type);
            exc_type.incref();

            if (value) |v| {
                try args_tuple.setOwnedItem(1, v);
                v.incref();
            } else {
                try args_tuple.setOwnedItem(1, py.None());
            }

            if (traceback) |tb| {
                try args_tuple.setOwnedItem(2, tb);
                tb.incref();
            } else {
                try args_tuple.setOwnedItem(2, py.None());
            }

            const awaitable = try py.call(root, py.PyObject, athrow_method, args_tuple.obj, .{});
            return py.PyAwaitable(root){ .obj = awaitable };
        }
    };
}

test "PyAsyncGenerator" {
    var fixture = py.testing.TestFixture.init();
    defer fixture.deinit();

    fixture.initPython();
    const root = @This();

    const code = "async def my_agen():\n    yield 1\n    yield 2\n\nagen = my_agen()";

    const builtins = try py.import(root, "builtins");
    defer builtins.decref();
    const exec = try builtins.get("exec");
    defer exec.decref();
    const globals = try py.PyDict(root).new();
    defer globals.obj.decref();

    _ = try py.call(root, py.PyObject, exec, .{ try py.PyString.create(code), globals.obj }, .{});

    const agen_obj = try globals.getItem(py.PyObject, "agen") orelse unreachable;
    defer agen_obj.decref();

    const agen = py.PyAsyncGenerator(root).from.unchecked(agen_obj);

    // anext 1
    var awaitable1 = try agen.anext();
    var result1 = awaitable1.await_() catch |err| {
        // Handle StopAsyncIteration
        var ptype: ?*ffi.PyObject = undefined;
        var pvalue: ?*ffi.PyObject = undefined;
        var ptraceback: ?*ffi.PyObject = undefined;
        ffi.PyErr_Fetch(&ptype, &pvalue, &ptraceback);
        const stop_iteration_type = ffi.PyExc_StopAsyncIteration;
        if (ptype != null and ffi.PyErr_GivenExceptionMatches(ptype, stop_iteration_type) != 0) {
            // Error already cleared by PyErr_Fetch
            unreachable; // Should not stop here
        }
        ffi.PyErr_Restore(ptype, pvalue, ptraceback);
        return err;
    };
    defer result1.decref();
    try std.testing.expectEqual(@as(i64, 1), try py.as(root, i64, result1));
    
    // anext 2
    var awaitable2 = try agen.anext();
    var result2 = awaitable2.await_() catch |err| {
        var ptype: ?*ffi.PyObject = undefined;
        var pvalue: ?*ffi.PyObject = undefined;
        var ptraceback: ?*ffi.PyObject = undefined;
        ffi.PyErr_Fetch(&ptype, &pvalue, &ptraceback);
        const stop_iteration_type = ffi.PyExc_StopAsyncIteration;
        if (ptype != null and ffi.PyErr_GivenExceptionMatches(ptype, stop_iteration_type) != 0) {
            // Error already cleared by PyErr_Fetch
            unreachable; // Should not stop here
        }
        ffi.PyErr_Restore(ptype, pvalue, ptraceback);
        return err;
    };
    defer result2.decref();
    try std.testing.expectEqual(@as(i64, 2), try py.as(root, i64, result2));

    // anext 3 - expecting StopAsyncIteration
    var awaitable3 = try agen.anext();
    awaitable3.await_() catch |err| {
        var ptype: ?*ffi.PyObject = undefined;
        var pvalue: ?*ffi.PyObject = undefined;
        var ptraceback: ?*ffi.PyObject = undefined;
        ffi.PyErr_Fetch(&ptype, &pvalue, &ptraceback);
        const stop_iteration_type = ffi.PyExc_StopAsyncIteration;
        if (ptype != null and ffi.PyErr_GivenExceptionMatches(ptype, stop_iteration_type) != 0) {
            // Error already cleared by PyErr_Fetch
        } else {
           ffi.PyErr_Restore(ptype, pvalue, ptraceback);
           return err;
        }
    };
}