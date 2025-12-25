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

/// SIMD datatype support for pyz3
/// Provides efficient vectorized operations with Python integration
const std = @import("std");
const py = @import("pyz3.zig");
const ffi = @import("ffi");
const PyError = @import("errors.zig").PyError;

/// SIMD vector types for common sizes
pub fn SimdVec(comptime T: type, comptime len: comptime_int) type {
    return @Vector(len, T);
}

/// Common SIMD vector types
pub const SimdF32x4 = SimdVec(f32, 4);
pub const SimdF32x8 = SimdVec(f32, 8);
pub const SimdF64x2 = SimdVec(f64, 2);
pub const SimdF64x4 = SimdVec(f64, 4);
pub const SimdI32x4 = SimdVec(i32, 4);
pub const SimdI32x8 = SimdVec(i32, 8);
pub const SimdI64x2 = SimdVec(i64, 2);
pub const SimdI64x4 = SimdVec(i64, 4);

/// Convert Python list/tuple to SIMD vector
pub fn fromPython(comptime T: type, comptime len: comptime_int, obj: py.PyObject) PyError!SimdVec(T, len) {
    var result: SimdVec(T, len) = undefined;

    // Try to get as list
    if (ffi.PyList_Check(obj.py) != 0) {
        const list = py.PyList(@This()){ .obj = obj };
        if (list.length() != len) {
            return py.ValueError(@This()).raiseFmt(
                "Expected list of length {d}, got {d}",
                .{ len, list.length() }
            );
        }

        for (0..len) |i| {
            const item = try list.getItem(py.PyObject, @intCast(i));
            const value = try py.as(@This(), T, item);
            result[i] = value;
        }
        return result;
    }

    // Try to get as tuple
    if (ffi.PyTuple_Check(obj.py) != 0) {
        const tuple = py.PyTuple(@This()){ .obj = obj };
        if (tuple.length() != len) {
            return py.ValueError(@This()).raiseFmt(
                "Expected tuple of length {d}, got {d}",
                .{ len, tuple.length() }
            );
        }

        for (0..len) |i| {
            const item = try tuple.getItem(py.PyObject, @intCast(i));
            const value = try py.as(@This(), T, item);
            result[i] = value;
        }
        return result;
    }

    return py.TypeError(@This()).raise("Expected list or tuple for SIMD vector");
}

/// Convert SIMD vector to Python list
pub fn toPython(comptime root: type, comptime T: type, comptime len: comptime_int, vec: SimdVec(T, len)) PyError!py.PyList(root) {
    const list = try py.PyList(root).new(0);

    for (0..len) |i| {
        const item = try py.create(@This(), vec[i]);
        try list.append(item);
        item.decref();
    }

    return list;
}

/// SIMD operations
pub const SimdOps = struct {
    /// Add two SIMD vectors
    pub fn add(comptime T: type, comptime len: comptime_int, a: SimdVec(T, len), b: SimdVec(T, len)) SimdVec(T, len) {
        return a + b;
    }

    /// Subtract two SIMD vectors
    pub fn sub(comptime T: type, comptime len: comptime_int, a: SimdVec(T, len), b: SimdVec(T, len)) SimdVec(T, len) {
        return a - b;
    }

    /// Multiply two SIMD vectors
    pub fn mul(comptime T: type, comptime len: comptime_int, a: SimdVec(T, len), b: SimdVec(T, len)) SimdVec(T, len) {
        return a * b;
    }

    /// Divide two SIMD vectors
    pub fn div(comptime T: type, comptime len: comptime_int, a: SimdVec(T, len), b: SimdVec(T, len)) SimdVec(T, len) {
        return a / b;
    }

    /// Multiply vector by scalar
    pub fn scale(comptime T: type, comptime len: comptime_int, vec: SimdVec(T, len), scalar: T) SimdVec(T, len) {
        return vec * @as(SimdVec(T, len), @splat(scalar));
    }

    /// Dot product of two vectors
    pub fn dot(comptime T: type, comptime len: comptime_int, a: SimdVec(T, len), b: SimdVec(T, len)) T {
        const product = a * b;
        return @reduce(.Add, product);
    }

    /// Sum of all elements in vector
    pub fn sum(comptime T: type, comptime len: comptime_int, vec: SimdVec(T, len)) T {
        return @reduce(.Add, vec);
    }

    /// Minimum element in vector
    pub fn min(comptime T: type, comptime len: comptime_int, vec: SimdVec(T, len)) T {
        return @reduce(.Min, vec);
    }

    /// Maximum element in vector
    pub fn max(comptime T: type, comptime len: comptime_int, vec: SimdVec(T, len)) T {
        return @reduce(.Max, vec);
    }

    /// Fused multiply-add: a * b + c
    pub fn fma(comptime T: type, comptime len: comptime_int, a: SimdVec(T, len), b: SimdVec(T, len), c: SimdVec(T, len)) SimdVec(T, len) {
        return @mulAdd(SimdVec(T, len), a, b, c);
    }
};

/// Helper struct for SIMD operations with Python integration
pub fn SimdWrapper(comptime T: type, comptime len: comptime_int) type {
    return struct {
        const Vec = SimdVec(T, len);

        /// Create from Python object
        pub fn from(obj: py.PyObject) PyError!Vec {
            return fromPython(T, len, obj);
        }

        /// Convert to Python object
        pub fn to(vec: Vec) PyError!py.PyList {
            return toPython(T, len, vec);
        }

        /// Add two vectors
        pub fn add(a: Vec, b: Vec) Vec {
            return SimdOps.add(T, len, a, b);
        }

        /// Subtract two vectors
        pub fn sub(a: Vec, b: Vec) Vec {
            return SimdOps.sub(T, len, a, b);
        }

        /// Multiply two vectors (element-wise)
        pub fn mul(a: Vec, b: Vec) Vec {
            return SimdOps.mul(T, len, a, b);
        }

        /// Divide two vectors (element-wise)
        pub fn div(a: Vec, b: Vec) Vec {
            return SimdOps.div(T, len, a, b);
        }

        /// Multiply by scalar
        pub fn scale(vec: Vec, scalar: T) Vec {
            return SimdOps.scale(T, len, vec, scalar);
        }

        /// Dot product
        pub fn dot(a: Vec, b: Vec) T {
            return SimdOps.dot(T, len, a, b);
        }

        /// Sum all elements
        pub fn sum(vec: Vec) T {
            return SimdOps.sum(T, len, vec);
        }

        /// Get minimum element
        pub fn min(vec: Vec) T {
            return SimdOps.min(T, len, vec);
        }

        /// Get maximum element
        pub fn max(vec: Vec) T {
            return SimdOps.max(T, len, vec);
        }
    };
}

/// Batch SIMD operations on arrays
pub fn batchOp(
    comptime T: type,
    comptime len: comptime_int,
    comptime op: fn (SimdVec(T, len), SimdVec(T, len)) SimdVec(T, len),
    a: []const T,
    b: []const T,
    result: []T,
) void {
    std.debug.assert(a.len == b.len);
    std.debug.assert(a.len == result.len);

    const vec_count = a.len / len;
    const remainder = a.len % len;

    // Process full vectors
    var i: usize = 0;
    while (i < vec_count) : (i += 1) {
        const start = i * len;
        const vec_a: SimdVec(T, len) = a[start..][0..len].*;
        const vec_b: SimdVec(T, len) = b[start..][0..len].*;
        const vec_result = op(vec_a, vec_b);

        for (0..len) |j| {
            result[start + j] = vec_result[j];
        }
    }

    // Process remainder using scalar operations
    // Note: We can't use the SIMD op for remainder since it expects vectors of length 'len'
    const remainder_start = vec_count * len;
    if (remainder > 0) {
        // For remainder, create a partial vector and extract results
        var temp_a: SimdVec(T, len) = @splat(0);
        var temp_b: SimdVec(T, len) = @splat(0);

        for (0..remainder) |j| {
            temp_a[j] = a[remainder_start + j];
            temp_b[j] = b[remainder_start + j];
        }

        const temp_result = op(temp_a, temp_b);

        for (0..remainder) |j| {
            result[remainder_start + j] = temp_result[j];
        }
    }
}

test "SIMD vector creation" {
    const vec: SimdF32x4 = .{ 1.0, 2.0, 3.0, 4.0 };
    try std.testing.expectEqual(@as(f32, 1.0), vec[0]);
    try std.testing.expectEqual(@as(f32, 4.0), vec[3]);
}

test "SIMD addition" {
    const a: SimdF32x4 = .{ 1.0, 2.0, 3.0, 4.0 };
    const b: SimdF32x4 = .{ 5.0, 6.0, 7.0, 8.0 };
    const c = SimdOps.add(f32, 4, a, b);

    try std.testing.expectEqual(@as(f32, 6.0), c[0]);
    try std.testing.expectEqual(@as(f32, 12.0), c[3]);
}

test "SIMD dot product" {
    const a: SimdF32x4 = .{ 1.0, 2.0, 3.0, 4.0 };
    const b: SimdF32x4 = .{ 5.0, 6.0, 7.0, 8.0 };
    const result = SimdOps.dot(f32, 4, a, b);

    // 1*5 + 2*6 + 3*7 + 4*8 = 5 + 12 + 21 + 32 = 70
    try std.testing.expectEqual(@as(f32, 70.0), result);
}

test "SIMD sum" {
    const vec: SimdF32x4 = .{ 1.0, 2.0, 3.0, 4.0 };
    const result = SimdOps.sum(f32, 4, vec);

    try std.testing.expectEqual(@as(f32, 10.0), result);
}

test "SIMD min/max" {
    const vec: SimdF32x4 = .{ 3.0, 1.0, 4.0, 2.0 };

    try std.testing.expectEqual(@as(f32, 1.0), SimdOps.min(f32, 4, vec));
    try std.testing.expectEqual(@as(f32, 4.0), SimdOps.max(f32, 4, vec));
}

test "SIMD scale" {
    const vec: SimdF32x4 = .{ 1.0, 2.0, 3.0, 4.0 };
    const scaled = SimdOps.scale(f32, 4, vec, 2.0);

    try std.testing.expectEqual(@as(f32, 2.0), scaled[0]);
    try std.testing.expectEqual(@as(f32, 8.0), scaled[3]);
}
