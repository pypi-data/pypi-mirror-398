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

/// Python complex number object wrapper
pub const PyComplex = extern struct {
    obj: py.PyObject,

    const Self = @This();

    /// Create a complex number from real and imaginary parts
    pub fn create(real_part: f64, imag_part: f64) !Self {
        const complex_obj = ffi.PyComplex_FromDoubles(real_part, imag_part) orelse return PyError.PyRaised;
        return .{ .obj = .{ .py = complex_obj } };
    }

    /// Check if object is a complex number
    pub fn check(obj: py.PyObject) bool {
        return ffi.PyComplex_Check(obj.py) != 0;
    }

    /// Get the real part of the complex number
    pub fn real(self: Self) !f64 {
        const r = ffi.PyComplex_RealAsDouble(self.obj.py);
        if (r == -1.0 and ffi.PyErr_Occurred() != null) {
            return PyError.PyRaised;
        }
        return r;
    }

    /// Get the imaginary part of the complex number
    pub fn imag(self: Self) !f64 {
        const i = ffi.PyComplex_ImagAsDouble(self.obj.py);
        if (i == -1.0 and ffi.PyErr_Occurred() != null) {
            return PyError.PyRaised;
        }
        return i;
    }

    /// Get both real and imaginary parts as a tuple
    pub fn asTuple(self: Self) !struct { real: f64, imag: f64 } {
        return .{
            .real = try self.real(),
            .imag = try self.imag(),
        };
    }

    /// Create from std.math.Complex
    pub fn fromStdComplex(c: std.math.Complex(f64)) !Self {
        return try Self.create(c.re, c.im);
    }

    /// Convert to std.math.Complex
    pub fn toStdComplex(self: Self) !std.math.Complex(f64) {
        const parts = try self.asTuple();
        return std.math.Complex(f64).init(parts.real, parts.imag);
    }

    /// Add two complex numbers
    pub fn add(self: Self, other: Self) !Self {
        const a = try self.asTuple();
        const b = try other.asTuple();
        return try Self.create(a.real + b.real, a.imag + b.imag);
    }

    /// Subtract two complex numbers
    pub fn sub(self: Self, other: Self) !Self {
        const a = try self.asTuple();
        const b = try other.asTuple();
        return try Self.create(a.real - b.real, a.imag - b.imag);
    }

    /// Multiply two complex numbers
    pub fn mul(self: Self, other: Self) !Self {
        const a = try self.asTuple();
        const b = try other.asTuple();
        const real_part = a.real * b.real - a.imag * b.imag;
        const imag_part = a.real * b.imag + a.imag * b.real;
        return try Self.create(real_part, imag_part);
    }

    /// Divide two complex numbers
    pub fn div(self: Self, other: Self) !Self {
        const a = try self.asTuple();
        const b = try other.asTuple();

        const denominator = b.real * b.real + b.imag * b.imag;
        if (denominator == 0.0) {
            return py.ZeroDivisionError(@import("../pyz3.zig")).raise("complex division by zero");
        }

        const real_part = (a.real * b.real + a.imag * b.imag) / denominator;
        const imag_part = (a.imag * b.real - a.real * b.imag) / denominator;
        return try Self.create(real_part, imag_part);
    }

    /// Get the absolute value (magnitude) of the complex number
    pub fn abs(self: Self) !f64 {
        const parts = try self.asTuple();
        return @sqrt(parts.real * parts.real + parts.imag * parts.imag);
    }

    /// Get the conjugate of the complex number
    pub fn conjugate(self: Self) !Self {
        const parts = try self.asTuple();
        return try Self.create(parts.real, -parts.imag);
    }

    /// Get the phase (argument) of the complex number in radians
    pub fn phase(self: Self) !f64 {
        const parts = try self.asTuple();
        return std.math.atan2(f64, parts.imag, parts.real);
    }

    /// Create from polar coordinates (r * e^(i*phi))
    pub fn fromPolar(r: f64, phi: f64) !Self {
        const real_part = r * @cos(phi);
        const imag_part = r * @sin(phi);
        return try Self.create(real_part, imag_part);
    }

    /// Convert to polar coordinates
    pub fn toPolar(self: Self) !struct { r: f64, phi: f64 } {
        return .{
            .r = try self.abs(),
            .phi = try self.phase(),
        };
    }
};
