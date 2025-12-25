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

//! NumPy Array Integration
//!
//! This module provides type-safe access to NumPy arrays from Zig code.
//! It supports zero-copy data access, type-safe dtype mapping, and
//! seamless conversion between Zig slices and NumPy arrays.

const std = @import("std");
const ffi = @import("ffi");
const py = @import("../pyz3.zig");
const PyError = @import("../errors.zig").PyError;

/// NumPy data type enumeration
/// Maps to NumPy's dtype system
pub const DType = enum(c_int) {
    bool = 0,
    int8 = 1,
    uint8 = 2,
    int16 = 3,
    uint16 = 4,
    int32 = 5,
    uint32 = 6,
    int64 = 7,
    uint64 = 8,
    float32 = 11,
    float64 = 12,
    complex64 = 14,
    complex128 = 15,

    /// Get dtype from Zig type at compile time
    pub fn fromType(comptime T: type) DType {
        return switch (T) {
            bool => .bool,
            i8 => .int8,
            u8 => .uint8,
            i16 => .int16,
            u16 => .uint16,
            i32, c_int => .int32,
            u32, c_uint => .uint32,
            i64, c_long, isize => .int64,
            u64, c_ulong, usize => .uint64,
            f32 => .float32,
            f64 => .float64,
            else => @compileError("Unsupported NumPy dtype for type: " ++ @typeName(T)),
        };
    }

    /// Get the size in bytes of this dtype
    pub fn size(self: DType) usize {
        return switch (self) {
            .bool, .int8, .uint8 => 1,
            .int16, .uint16 => 2,
            .int32, .uint32, .float32 => 4,
            .int64, .uint64, .float64 => 8,
            .complex64 => 8,
            .complex128 => 16,
        };
    }
};

/// NumPy array flags
pub const ArrayFlags = packed struct(c_int) {
    c_contiguous: bool = false,
    f_contiguous: bool = false,
    owndata: bool = false,
    forcecast: bool = false,
    ensurecopy: bool = false,
    ensurearray: bool = false,
    elementstrides: bool = false,
    aligned: bool = false,
    notswapped: bool = false,
    writeable: bool = false,
    updateifcopy: bool = false,
    _padding: u21 = 0,
};

/// NumPy Array wrapper
/// Provides type-safe access to NumPy arrays
pub fn PyArray(comptime root: type) type {
    return struct {
        obj: py.PyObject,

        const Self = @This();

        /// Get PyArray from checked PyObject
        pub const from = struct {
            pub fn checked(comptime rt: type, obj: py.PyObject) PyError!PyArray(rt) {
                // Import numpy to ensure it's available
                const np = try importNumPy(rt);
                defer np.decref();

                // Check if object is an ndarray
                const ndarray_type = try np.get("ndarray");
                defer ndarray_type.decref();

                if (!try py.isinstance(rt, obj, ndarray_type)) {
                    return py.TypeError(rt).raise("Expected numpy.ndarray");
                }

                return PyArray(rt){ .obj = obj };
            }

            pub fn unchecked(obj: py.PyObject) PyArray(root) {
                return PyArray(root){ .obj = obj };
            }
        };

        /// Create a new array from a Zig slice (copies data)
        pub fn fromSlice(comptime T: type, data: []const T) PyError!Self {
            const np = try importNumPy(root);
            defer np.decref();

            const array_func = try np.get("array");
            defer array_func.decref();

            // Create Python list from Zig slice
            const list = try py.PyList(root).new();
            defer list.obj.decref();

            for (data) |item| {
                const py_item = try py.create(root, item);
                defer py_item.decref();
                try list.append(py_item);
            }

            // Call numpy.array(list)
            const result = try array_func.call(.{list.obj}, .{});
            return Self.from.unchecked(result);
        }

        /// Create a new array from a Zig slice with specified dtype
        pub fn fromSliceTyped(comptime T: type, data: []const T, array_dtype: DType) PyError!Self {
            const np = try importNumPy(root);
            defer np.decref();

            const array_func = try np.get("array");
            defer array_func.decref();

            // Create Python list from Zig slice
            const list = try py.PyList(root).new();
            defer list.obj.decref();

            for (data) |item| {
                const py_item = try py.create(root, item);
                defer py_item.decref();
                try list.append(py_item);
            }

            // Get dtype object
            const dtype_str = try getDTypeName(array_dtype);
            const dtype_obj = try createDType(root, dtype_str);
            defer dtype_obj.decref();

            // Call numpy.array(list, dtype=dtype)
            var kwargs = py.Kwargs().init(py.allocator);
            defer kwargs.deinit();
            try kwargs.put("dtype", dtype_obj);

            const result = try array_func.call(.{list.obj}, kwargs);
            return Self.from.unchecked(result);
        }

        /// Create array from multidimensional Zig data
        pub fn fromSlice2D(comptime T: type, data: []const []const T) PyError!Self {
            const np = try importNumPy(root);
            defer np.decref();

            const array_func = try np.get("array");
            defer array_func.decref();

            // Create nested Python list
            const outer_list = try py.PyList(root).new();
            defer outer_list.obj.decref();

            for (data) |row| {
                const inner_list = try py.PyList(root).new();
                defer inner_list.obj.decref();

                for (row) |item| {
                    const py_item = try py.create(root, item);
                    defer py_item.decref();
                    try inner_list.append(py_item);
                }

                try outer_list.append(inner_list.obj);
            }

            const result = try array_func.call(.{outer_list.obj}, .{});
            return Self.from.unchecked(result);
        }

        /// Create a zero-filled array
        pub fn zeros(comptime T: type, array_shape: []const usize) PyError!Self {
            const np = try importNumPy(root);
            defer np.decref();

            const zeros_func = try np.get("zeros");
            defer zeros_func.decref();

            // Create shape tuple
            const shape_tuple = try shapeToTuple(root, array_shape);
            defer shape_tuple.decref();

            // Get dtype
            const array_dtype = DType.fromType(T);
            const dtype_str = try getDTypeName(array_dtype);
            const dtype_obj = try createDType(root, dtype_str);
            defer dtype_obj.decref();

            // Call numpy.zeros(shape, dtype=dtype)
            var kwargs = py.Kwargs().init(py.allocator);
            defer kwargs.deinit();
            try kwargs.put("dtype", dtype_obj);

            const result = try zeros_func.call(.{shape_tuple}, kwargs);
            return Self.from.unchecked(result);
        }

        /// Create a ones-filled array
        pub fn ones(comptime T: type, array_shape: []const usize) PyError!Self {
            const np = try importNumPy(root);
            defer np.decref();

            const ones_func = try np.get("ones");
            defer ones_func.decref();

            const shape_tuple = try shapeToTuple(root, array_shape);
            defer shape_tuple.decref();

            const array_dtype = DType.fromType(T);
            const dtype_str = try getDTypeName(array_dtype);
            const dtype_obj = try createDType(root, dtype_str);
            defer dtype_obj.decref();

            var kwargs = py.Kwargs().init(py.allocator);
            defer kwargs.deinit();
            try kwargs.put("dtype", dtype_obj);

            const result = try ones_func.call(.{shape_tuple}, kwargs);
            return Self.from.unchecked(result);
        }

        /// Create an array filled with a specific value
        pub fn full(comptime T: type, array_shape: []const usize, fill_value: T) PyError!Self {
            const np = try importNumPy(root);
            defer np.decref();

            const full_func = try np.get("full");
            defer full_func.decref();

            const shape_tuple = try shapeToTuple(root, array_shape);
            defer shape_tuple.decref();

            const fill_obj = try py.create(root, fill_value);
            defer fill_obj.decref();

            const result = try full_func.call(.{ shape_tuple, fill_obj }, .{});
            return Self.from.unchecked(result);
        }

        /// Get array as Zig slice (zero-copy, borrows data)
        /// WARNING: The returned slice is only valid while the array is alive
        /// and the data hasn't been reallocated
        pub fn asSlice(self: Self, comptime T: type) PyError![]T {
            // Verify dtype matches
            const expected_dtype = DType.fromType(T);
            const actual_dtype = try self.dtype();

            if (expected_dtype != actual_dtype) {
                return py.TypeError(root).raiseFmt(
                    "Type mismatch: array has dtype {s}, requested {s}",
                    .{ @tagName(actual_dtype), @tagName(expected_dtype) },
                );
            }

            // Get data pointer via __array_interface__
            const array_interface = try self.obj.get("__array_interface__");
            defer array_interface.decref();

            const data_tuple = try array_interface.get("data");
            defer data_tuple.decref();

            const data_list = try py.PyTuple(root).from.checked(root, data_tuple);
            const data_addr = try data_list.getItem(py.PyLong, 0);
            const addr = try data_addr.as(usize);

            const len = try self.size();
            const ptr: [*]T = @ptrFromInt(addr);

            return ptr[0..len];
        }

        /// Get array as mutable Zig slice (zero-copy, borrows data)
        /// WARNING: The returned slice is only valid while the array is alive
        pub fn asSliceMut(self: Self, comptime T: type) PyError![]T {
            if (!try self.isWriteable()) {
                return py.ValueError(root).raise("Array is not writeable");
            }
            return self.asSlice(T);
        }

        /// Get the shape of the array
        pub fn shape(self: Self) PyError![]usize {
            const shape_obj = try self.obj.get("shape");
            defer shape_obj.decref();

            const shape_tuple = try py.PyTuple(root).from.checked(root, shape_obj);
            const num_dims = shape_tuple.length();

            const result = try py.allocator.alloc(usize, num_dims);
            errdefer py.allocator.free(result);

            for (0..num_dims) |i| {
                const dim = try shape_tuple.getItem(py.PyLong, i);
                result[i] = try dim.as(usize);
            }

            return result;
        }

        /// Get the number of dimensions
        pub fn ndim(self: Self) PyError!usize {
            const ndim_obj = try self.obj.get("ndim");
            defer ndim_obj.decref();

            const ndim_long = try py.PyLong.from.checked(root, ndim_obj);
            return try ndim_long.as(usize);
        }

        /// Get the total number of elements
        pub fn size(self: Self) PyError!usize {
            const size_obj = try self.obj.get("size");
            defer size_obj.decref();

            const size_long = try py.PyLong.from.checked(root, size_obj);
            return try size_long.as(usize);
        }

        /// Get the data type
        pub fn dtype(self: Self) PyError!DType {
            const dtype_obj = try self.obj.get("dtype");
            defer dtype_obj.decref();

            const dtype_name_obj = try dtype_obj.get("name");
            defer dtype_name_obj.decref();

            const dtype_str = try py.PyString.from.checked(root, dtype_name_obj);
            const name = try dtype_str.asSlice();

            return dtypeFromName(name);
        }

        /// Check if array is C-contiguous
        pub fn isCContiguous(self: Self) PyError!bool {
            const flags_obj = try self.obj.get("flags");
            defer flags_obj.decref();

            const c_cont = try flags_obj.get("c_contiguous");
            defer c_cont.decref();

            const c_cont_bool = try py.PyBool.from.checked(root, c_cont);
            return c_cont_bool.asbool();
        }

        /// Check if array is writeable
        pub fn isWriteable(self: Self) PyError!bool {
            const flags_obj = try self.obj.get("flags");
            defer flags_obj.decref();

            const writeable = try flags_obj.get("writeable");
            defer writeable.decref();

            const writeable_bool = try py.PyBool.from.checked(root, writeable);
            return writeable_bool.asbool();
        }

        /// Reshape the array
        pub fn reshape(self: Self, new_shape: []const usize) PyError!Self {
            const reshape_func = try self.obj.get("reshape");
            defer reshape_func.decref();

            const shape_tuple = try shapeToTuple(root, new_shape);
            defer shape_tuple.decref();

            const result = try reshape_func.call(.{shape_tuple}, .{});
            return Self.from.unchecked(result);
        }

        /// Transpose the array
        pub fn transpose(self: Self) PyError!Self {
            const transpose_func = try self.obj.get("transpose");
            defer transpose_func.decref();

            const result = try transpose_func.call(.{}, .{});
            return Self.from.unchecked(result);
        }

        /// Flatten the array to 1D
        pub fn flatten(self: Self) PyError!Self {
            const flatten_func = try self.obj.get("flatten");
            defer flatten_func.decref();

            const result = try flatten_func.call(.{}, .{});
            return Self.from.unchecked(result);
        }

        /// Copy the array
        pub fn copy(self: Self) PyError!Self {
            const copy_func = try self.obj.get("copy");
            defer copy_func.decref();

            const result = try copy_func.call(.{}, .{});
            return Self.from.unchecked(result);
        }

        /// Sum all elements
        pub fn sum(self: Self, comptime T: type) PyError!T {
            const sum_func = try self.obj.get("sum");
            defer sum_func.decref();

            const result = try sum_func.call(.{}, .{});
            defer result.decref();

            return try py.as(root, T, result);
        }

        /// Get mean of all elements
        pub fn mean(self: Self, comptime T: type) PyError!T {
            const mean_func = try self.obj.get("mean");
            defer mean_func.decref();

            const result = try mean_func.call(.{}, .{});
            defer result.decref();

            return try py.as(root, T, result);
        }

        /// Get minimum value
        pub fn min(self: Self, comptime T: type) PyError!T {
            const min_func = try self.obj.get("min");
            defer min_func.decref();

            const result = try min_func.call(.{}, .{});
            defer result.decref();

            return try py.as(root, T, result);
        }

        /// Get maximum value
        pub fn max(self: Self, comptime T: type) PyError!T {
            const max_func = try self.obj.get("max");
            defer max_func.decref();

            const result = try max_func.call(.{}, .{});
            defer result.decref();

            return try py.as(root, T, result);
        }
    };
}

/// Import numpy module (cached)
fn importNumPy(comptime root: type) PyError!py.PyObject {
    const np = try py.import(root, "numpy");
    return np;
}

/// Create dtype object from name
fn createDType(comptime root: type, name: []const u8) PyError!py.PyObject {
    const np = try importNumPy(root);
    defer np.decref();

    const dtype_class = try np.get("dtype");
    defer dtype_class.decref();

    const name_str = try py.create(root, name);
    defer name_str.decref();

    return try dtype_class.call(.{name_str}, .{});
}

/// Get dtype name string
fn getDTypeName(dtype: DType) PyError![]const u8 {
    return switch (dtype) {
        .bool => "bool",
        .int8 => "int8",
        .uint8 => "uint8",
        .int16 => "int16",
        .uint16 => "uint16",
        .int32 => "int32",
        .uint32 => "uint32",
        .int64 => "int64",
        .uint64 => "uint64",
        .float32 => "float32",
        .float64 => "float64",
        .complex64 => "complex64",
        .complex128 => "complex128",
    };
}

/// Parse dtype from name string
fn dtypeFromName(name: []const u8) PyError!DType {
    if (std.mem.eql(u8, name, "bool")) return .bool;
    if (std.mem.eql(u8, name, "int8")) return .int8;
    if (std.mem.eql(u8, name, "uint8")) return .uint8;
    if (std.mem.eql(u8, name, "int16")) return .int16;
    if (std.mem.eql(u8, name, "uint16")) return .uint16;
    if (std.mem.eql(u8, name, "int32")) return .int32;
    if (std.mem.eql(u8, name, "uint32")) return .uint32;
    if (std.mem.eql(u8, name, "int64")) return .int64;
    if (std.mem.eql(u8, name, "uint64")) return .uint64;
    if (std.mem.eql(u8, name, "float32")) return .float32;
    if (std.mem.eql(u8, name, "float64")) return .float64;
    if (std.mem.eql(u8, name, "complex64")) return .complex64;
    if (std.mem.eql(u8, name, "complex128")) return .complex128;

    return PyError.PyRaised;
}

/// Convert shape slice to Python tuple
fn shapeToTuple(comptime root: type, shape: []const usize) PyError!py.PyObject {
    const list = try py.PyList(root).new();
    defer list.obj.decref();

    for (shape) |dim| {
        const dim_obj = try py.create(root, @as(i64, @intCast(dim)));
        defer dim_obj.decref();
        try list.append(dim_obj);
    }

    return try py.tuple(root, list.obj);
}

// Tests
const testing = std.testing;

test "dtype from type" {
    try testing.expectEqual(DType.int32, DType.fromType(i32));
    try testing.expectEqual(DType.float64, DType.fromType(f64));
    try testing.expectEqual(DType.uint8, DType.fromType(u8));
}

test "dtype size" {
    try testing.expectEqual(@as(usize, 1), DType.int8.size());
    try testing.expectEqual(@as(usize, 4), DType.int32.size());
    try testing.expectEqual(@as(usize, 8), DType.float64.size());
}
