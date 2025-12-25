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

/// Python UUID object wrapper
pub const PyUUID = extern struct {
    obj: py.PyObject,

    const Self = @This();

    /// Create a UUID from a string
    pub fn fromString(uuid_str: []const u8) !Self {
        const uuid_mod = try py.import("uuid");
        defer uuid_mod.decref();

        const uuid_class = try uuid_mod.getAttribute("UUID");
        defer uuid_class.decref();

        const str_obj = try py.PyString.create(uuid_str);
        defer str_obj.obj.decref();

        const uuid_obj = try py.call(@import("../pyz3.zig"), uuid_class, .{str_obj.obj});
        return .{ .obj = uuid_obj };
    }

    /// Create a UUID from bytes (16 bytes)
    pub fn fromBytes(bytes: []const u8) !Self {
        if (bytes.len != 16) {
            return py.ValueError(@import("../pyz3.zig")).raise("UUID bytes must be exactly 16 bytes");
        }

        const uuid_mod = try py.import("uuid");
        defer uuid_mod.decref();

        const uuid_class = try uuid_mod.getAttribute("UUID");
        defer uuid_class.decref();

        const bytes_obj = try py.PyBytes.from(bytes);
        defer bytes_obj.obj.decref();

        // Create kwargs dict with bytes=...
        const kwargs = std.StringHashMap(py.PyObject).init(py.allocator);
        defer kwargs.deinit();

        const bytes_key = try py.PyString.create("bytes");
        defer bytes_key.obj.decref();

        // Call UUID(bytes=...)
        const uuid_obj = ffi.PyObject_Call(uuid_class.py, ffi.PyTuple_New(0), null) orelse {
            // Fallback: use keyword argument
            const kw_dict = ffi.PyDict_New() orelse return PyError.PyRaised;
            defer {
                const d = py.PyObject{ .py = kw_dict };
                d.decref();
            }

            _ = ffi.PyDict_SetItemString(kw_dict, "bytes", bytes_obj.obj.py);

            const result = ffi.PyObject_Call(uuid_class.py, ffi.PyTuple_New(0), kw_dict) orelse return PyError.PyRaised;
            return .{ .obj = .{ .py = result } };
        };

        const obj = py.PyObject{ .py = uuid_obj };
        obj.decref();
        return try Self.fromString("00000000-0000-0000-0000-000000000000");
    }

    /// Create a UUID from fields
    pub fn fromFields(time_low: u32, time_mid: u16, time_hi_version: u16, clock_seq_hi_variant: u8, clock_seq_low: u8, node: u48) !Self {
        const uuid_mod = try py.import("uuid");
        defer uuid_mod.decref();

        const uuid_class = try uuid_mod.getAttribute("UUID");
        defer uuid_class.decref();

        // Create kwargs
        const kw_dict = ffi.PyDict_New() orelse return PyError.PyRaised;
        defer {
            const d = py.PyObject{ .py = kw_dict };
            d.decref();
        }

        const time_low_obj = try py.PyLong.from(@as(i64, time_low));
        defer time_low_obj.obj.decref();
        _ = ffi.PyDict_SetItemString(kw_dict, "time_low", time_low_obj.obj.py);

        const time_mid_obj = try py.PyLong.from(@as(i64, time_mid));
        defer time_mid_obj.obj.decref();
        _ = ffi.PyDict_SetItemString(kw_dict, "time_mid", time_mid_obj.obj.py);

        const time_hi_obj = try py.PyLong.from(@as(i64, time_hi_version));
        defer time_hi_obj.obj.decref();
        _ = ffi.PyDict_SetItemString(kw_dict, "time_hi_version", time_hi_obj.obj.py);

        const clock_hi_obj = try py.PyLong.from(@as(i64, clock_seq_hi_variant));
        defer clock_hi_obj.obj.decref();
        _ = ffi.PyDict_SetItemString(kw_dict, "clock_seq_hi_variant", clock_hi_obj.obj.py);

        const clock_low_obj = try py.PyLong.from(@as(i64, clock_seq_low));
        defer clock_low_obj.obj.decref();
        _ = ffi.PyDict_SetItemString(kw_dict, "clock_seq_low", clock_low_obj.obj.py);

        const node_obj = try py.PyLong.from(@as(i64, node));
        defer node_obj.obj.decref();
        _ = ffi.PyDict_SetItemString(kw_dict, "node", node_obj.obj.py);

        const uuid_obj = ffi.PyObject_Call(uuid_class.py, ffi.PyTuple_New(0), kw_dict) orelse return PyError.PyRaised;
        return .{ .obj = .{ .py = uuid_obj } };
    }

    /// Generate a random UUID (UUID4)
    pub fn uuid4() !Self {
        const uuid_mod = try py.import("uuid");
        defer uuid_mod.decref();

        const uuid4_fn = try uuid_mod.getAttribute("uuid4");
        defer uuid4_fn.decref();

        const uuid_obj = try py.call0(@import("../pyz3.zig"), uuid4_fn);
        return .{ .obj = uuid_obj };
    }

    /// Generate a UUID based on a namespace and name (UUID5 - SHA1)
    pub fn uuid5(namespace: Self, name: []const u8) !Self {
        const uuid_mod = try py.import("uuid");
        defer uuid_mod.decref();

        const uuid5_fn = try uuid_mod.getAttribute("uuid5");
        defer uuid5_fn.decref();

        const name_str = try py.PyString.create(name);
        defer name_str.obj.decref();

        const uuid_obj = try py.call(@import("../pyz3.zig"), uuid5_fn, .{ namespace.obj, name_str.obj });
        return .{ .obj = uuid_obj };
    }

    /// Generate a UUID based on a namespace and name (UUID3 - MD5)
    pub fn uuid3(namespace: Self, name: []const u8) !Self {
        const uuid_mod = try py.import("uuid");
        defer uuid_mod.decref();

        const uuid3_fn = try uuid_mod.getAttribute("uuid3");
        defer uuid3_fn.decref();

        const name_str = try py.PyString.create(name);
        defer name_str.obj.decref();

        const uuid_obj = try py.call(@import("../pyz3.zig"), uuid3_fn, .{ namespace.obj, name_str.obj });
        return .{ .obj = uuid_obj };
    }

    /// Get predefined DNS namespace UUID
    pub fn namespaceDNS() !Self {
        const uuid_mod = try py.import("uuid");
        defer uuid_mod.decref();

        const namespace = try uuid_mod.getAttribute("NAMESPACE_DNS");
        return .{ .obj = namespace };
    }

    /// Get predefined URL namespace UUID
    pub fn namespaceURL() !Self {
        const uuid_mod = try py.import("uuid");
        defer uuid_mod.decref();

        const namespace = try uuid_mod.getAttribute("NAMESPACE_URL");
        return .{ .obj = namespace };
    }

    /// Get predefined OID namespace UUID
    pub fn namespaceOID() !Self {
        const uuid_mod = try py.import("uuid");
        defer uuid_mod.decref();

        const namespace = try uuid_mod.getAttribute("NAMESPACE_OID");
        return .{ .obj = namespace };
    }

    /// Get predefined X.500 namespace UUID
    pub fn namespaceX500() !Self {
        const uuid_mod = try py.import("uuid");
        defer uuid_mod.decref();

        const namespace = try uuid_mod.getAttribute("NAMESPACE_X500");
        return .{ .obj = namespace };
    }

    /// Check if object is a UUID
    pub fn check(obj: py.PyObject) bool {
        const uuid_mod = py.import("uuid") catch return false;
        defer uuid_mod.decref();

        const uuid_class = uuid_mod.getAttribute("UUID") catch return false;
        defer uuid_class.decref();

        return py.isinstance(@import("../pyz3.zig"), obj, uuid_class) catch false;
    }

    /// Convert UUID to string
    pub fn toString(self: Self) !py.PyString {
        const str_fn = try py.import("builtins").getAttribute("str");
        defer str_fn.decref();

        const result = try py.call(@import("../pyz3.zig"), str_fn, .{self.obj});
        return .{ .obj = result };
    }

    /// Get UUID as bytes (16 bytes)
    pub fn toBytes(self: Self) !py.PyBytes {
        const bytes_attr = try self.obj.getAttribute("bytes");
        return .{ .obj = bytes_attr };
    }

    /// Get UUID as hex string (32 hex digits)
    pub fn toHex(self: Self) !py.PyString {
        const hex_attr = try self.obj.getAttribute("hex");
        return .{ .obj = hex_attr };
    }

    /// Get UUID as URN string
    pub fn toURN(self: Self) !py.PyString {
        const urn_attr = try self.obj.getAttribute("urn");
        return .{ .obj = urn_attr };
    }

    /// Get UUID variant
    pub fn variant(self: Self) !py.PyString {
        const variant_attr = try self.obj.getAttribute("variant");
        return .{ .obj = variant_attr };
    }

    /// Get UUID version (or None if not applicable)
    pub fn version(self: Self) !?i64 {
        const version_attr = try self.obj.getAttribute("version");
        defer version_attr.decref();

        if (py.is_none(version_attr)) {
            return null;
        }

        return try py.as(i64, @import("../pyz3.zig"), version_attr);
    }

    /// Get the 128-bit integer value
    pub fn toInt(self: Self) !i128 {
        const int_attr = try self.obj.getAttribute("int");
        defer int_attr.decref();

        // Python's int can be arbitrarily large, but UUID is 128-bit
        // We'll convert via string to handle the large number
        const str_fn = try py.import("builtins").getAttribute("str");
        defer str_fn.decref();

        const str_obj = try py.call(@import("../pyz3.zig"), str_fn, .{int_attr});
        defer str_obj.decref();

        const str_val = try py.PyString.asSlice(str_obj);
        defer str_val.decref();

        // Parse the string as i128
        return std.fmt.parseInt(i128, str_val.buf, 10) catch {
            return py.ValueError(@import("../pyz3.zig")).raise("UUID int value too large for i128");
        };
    }

    /// Compare for equality
    pub fn eq(self: Self, other: Self) !bool {
        const eq_method = try self.obj.getAttribute("__eq__");
        defer eq_method.decref();

        const result = try py.call(@import("../pyz3.zig"), eq_method, .{other.obj});
        defer result.decref();

        return try py.as(bool, @import("../pyz3.zig"), result);
    }
};
