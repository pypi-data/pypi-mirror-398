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

/// Python pathlib.Path object wrapper
pub const PyPath = extern struct {
    obj: py.PyObject,

    const Self = @This();

    /// Create a Path from a string
    pub fn create(path: []const u8) !Self {
        const pathlib = try py.import("pathlib");
        defer pathlib.decref();

        const path_class = try pathlib.getAttribute("Path");
        defer path_class.decref();

        const path_str = try py.PyString.create(path);
        defer path_str.obj.decref();

        const path_obj = try py.call(@import("../pyz3.zig"), path_class, .{path_str.obj});
        return .{ .obj = path_obj };
    }

    /// Get current working directory
    pub fn cwd() !Self {
        const pathlib = try py.import("pathlib");
        defer pathlib.decref();

        const path_class = try pathlib.getAttribute("Path");
        defer path_class.decref();

        const cwd_method = try path_class.getAttribute("cwd");
        defer cwd_method.decref();

        const path_obj = try py.call0(@import("../pyz3.zig"), cwd_method);
        return .{ .obj = path_obj };
    }

    /// Get home directory
    pub fn home() !Self {
        const pathlib = try py.import("pathlib");
        defer pathlib.decref();

        const path_class = try pathlib.getAttribute("Path");
        defer path_class.decref();

        const home_method = try path_class.getAttribute("home");
        defer home_method.decref();

        const path_obj = try py.call0(@import("../pyz3.zig"), home_method);
        return .{ .obj = path_obj };
    }

    /// Check if object is a Path
    pub fn check(obj: py.PyObject) bool {
        const pathlib = py.import("pathlib") catch return false;
        defer pathlib.decref();

        const path_class = pathlib.getAttribute("Path") catch return false;
        defer path_class.decref();

        return py.isinstance(@import("../pyz3.zig"), obj, path_class) catch false;
    }

    /// Convert path to string
    pub fn toString(self: Self) !py.PyString {
        const str_fn = try py.import("builtins").getAttribute("str");
        defer str_fn.decref();

        const result = try py.call(@import("../pyz3.zig"), str_fn, .{self.obj});
        return .{ .obj = result };
    }

    /// Check if path exists
    pub fn exists(self: Self) !bool {
        const method = try self.obj.getAttribute("exists");
        defer method.decref();

        const result = try py.call0(@import("../pyz3.zig"), method);
        defer result.decref();

        return try py.as(bool, @import("../pyz3.zig"), result);
    }

    /// Check if path is a file
    pub fn isFile(self: Self) !bool {
        const method = try self.obj.getAttribute("is_file");
        defer method.decref();

        const result = try py.call0(@import("../pyz3.zig"), method);
        defer result.decref();

        return try py.as(bool, @import("../pyz3.zig"), result);
    }

    /// Check if path is a directory
    pub fn isDir(self: Self) !bool {
        const method = try self.obj.getAttribute("is_dir");
        defer method.decref();

        const result = try py.call0(@import("../pyz3.zig"), method);
        defer result.decref();

        return try py.as(bool, @import("../pyz3.zig"), result);
    }

    /// Check if path is absolute
    pub fn isAbsolute(self: Self) !bool {
        const method = try self.obj.getAttribute("is_absolute");
        defer method.decref();

        const result = try py.call0(@import("../pyz3.zig"), method);
        defer result.decref();

        return try py.as(bool, @import("../pyz3.zig"), result);
    }

    /// Get absolute path
    pub fn absolute(self: Self) !Self {
        const method = try self.obj.getAttribute("absolute");
        defer method.decref();

        const result = try py.call0(@import("../pyz3.zig"), method);
        return .{ .obj = result };
    }

    /// Resolve path (make absolute and resolve symlinks)
    pub fn resolve(self: Self) !Self {
        const method = try self.obj.getAttribute("resolve");
        defer method.decref();

        const result = try py.call0(@import("../pyz3.zig"), method);
        return .{ .obj = result };
    }

    /// Join path with another path or string
    pub fn joinPath(self: Self, other: []const u8) !Self {
        const other_str = try py.PyString.create(other);
        defer other_str.obj.decref();

        const div_method = try self.obj.getAttribute("__truediv__");
        defer div_method.decref();

        const result = try py.call(@import("../pyz3.zig"), div_method, .{other_str.obj});
        return .{ .obj = result };
    }

    /// Get parent directory
    pub fn parent(self: Self) !Self {
        const parent_attr = try self.obj.getAttribute("parent");
        return .{ .obj = parent_attr };
    }

    /// Get file name (last component)
    pub fn name(self: Self) !py.PyString {
        const name_attr = try self.obj.getAttribute("name");
        return .{ .obj = name_attr };
    }

    /// Get file stem (name without extension)
    pub fn stem(self: Self) !py.PyString {
        const stem_attr = try self.obj.getAttribute("stem");
        return .{ .obj = stem_attr };
    }

    /// Get file extension
    pub fn suffix(self: Self) !py.PyString {
        const suffix_attr = try self.obj.getAttribute("suffix");
        return .{ .obj = suffix_attr };
    }

    /// Create directory (with parents if needed)
    pub fn mkdir(self: Self, parents: bool, exist_ok: bool) !void {
        const method = try self.obj.getAttribute("mkdir");
        defer method.decref();

        const parents_obj = try py.create(@import("../pyz3.zig"), parents);
        defer parents_obj.decref();

        const exist_ok_obj = try py.create(@import("../pyz3.zig"), exist_ok);
        defer exist_ok_obj.decref();

        // Call mkdir(parents=..., exist_ok=...)
        const kwargs = try py.import("builtins").getAttribute("dict");
        defer kwargs.decref();

        const kw = try py.call0(@import("../pyz3.zig"), kwargs);
        defer kw.decref();

        // Set kwargs
        _ = try kw.callMethod("__setitem__", .{ try py.PyString.create("parents"), parents_obj });
        _ = try kw.callMethod("__setitem__", .{ try py.PyString.create("exist_ok"), exist_ok_obj });

        const result = ffi.PyObject_Call(method.py, ffi.PyTuple_New(0), kw.py) orelse return PyError.PyRaised;
        defer {
            const r = py.PyObject{ .py = result };
            r.decref();
        }
    }

    /// Remove file
    pub fn unlink(self: Self) !void {
        const method = try self.obj.getAttribute("unlink");
        defer method.decref();

        const result = try py.call0(@import("../pyz3.zig"), method);
        defer result.decref();
    }

    /// Remove directory
    pub fn rmdir(self: Self) !void {
        const method = try self.obj.getAttribute("rmdir");
        defer method.decref();

        const result = try py.call0(@import("../pyz3.zig"), method);
        defer result.decref();
    }

    /// Rename/move file
    pub fn rename(self: Self, target: []const u8) !Self {
        const method = try self.obj.getAttribute("rename");
        defer method.decref();

        const target_str = try py.PyString.create(target);
        defer target_str.obj.decref();

        const result = try py.call(@import("../pyz3.zig"), method, .{target_str.obj});
        return .{ .obj = result };
    }

    /// Read file as text
    pub fn readText(self: Self) !py.PyString {
        const method = try self.obj.getAttribute("read_text");
        defer method.decref();

        const result = try py.call0(@import("../pyz3.zig"), method);
        return .{ .obj = result };
    }

    /// Read file as bytes
    pub fn readBytes(self: Self) !py.PyBytes {
        const method = try self.obj.getAttribute("read_bytes");
        defer method.decref();

        const result = try py.call0(@import("../pyz3.zig"), method);
        return .{ .obj = result };
    }

    /// Write text to file
    pub fn writeText(self: Self, text: []const u8) !void {
        const method = try self.obj.getAttribute("write_text");
        defer method.decref();

        const text_str = try py.PyString.create(text);
        defer text_str.obj.decref();

        const result = try py.call(@import("../pyz3.zig"), method, .{text_str.obj});
        defer result.decref();
    }

    /// Write bytes to file
    pub fn writeBytes(self: Self, bytes: []const u8) !void {
        const method = try self.obj.getAttribute("write_bytes");
        defer method.decref();

        const bytes_obj = try py.PyBytes.from(bytes);
        defer bytes_obj.obj.decref();

        const result = try py.call(@import("../pyz3.zig"), method, .{bytes_obj.obj});
        defer result.decref();
    }

    /// List directory contents (returns iterator)
    pub fn iterdir(self: Self) !py.PyIter {
        const method = try self.obj.getAttribute("iterdir");
        defer method.decref();

        const result = try py.call0(@import("../pyz3.zig"), method);
        const iter_obj = ffi.PyObject_GetIter(result.py) orelse {
            result.decref();
            return PyError.PyRaised;
        };
        result.decref();

        return .{ .obj = .{ .py = iter_obj } };
    }

    /// Glob pattern matching
    pub fn glob(self: Self, pattern: []const u8) !py.PyIter {
        const method = try self.obj.getAttribute("glob");
        defer method.decref();

        const pattern_str = try py.PyString.create(pattern);
        defer pattern_str.obj.decref();

        const result = try py.call(@import("../pyz3.zig"), method, .{pattern_str.obj});
        const iter_obj = ffi.PyObject_GetIter(result.py) orelse {
            result.decref();
            return PyError.PyRaised;
        };
        result.decref();

        return .{ .obj = .{ .py = iter_obj } };
    }

    /// Recursive glob pattern matching
    pub fn rglob(self: Self, pattern: []const u8) !py.PyIter {
        const method = try self.obj.getAttribute("rglob");
        defer method.decref();

        const pattern_str = try py.PyString.create(pattern);
        defer pattern_str.obj.decref();

        const result = try py.call(@import("../pyz3.zig"), method, .{pattern_str.obj});
        const iter_obj = ffi.PyObject_GetIter(result.py) orelse {
            result.decref();
            return PyError.PyRaised;
        };
        result.decref();

        return .{ .obj = .{ .py = iter_obj } };
    }

    /// Get file size in bytes
    pub fn stat(self: Self) !py.PyObject {
        const method = try self.obj.getAttribute("stat");
        defer method.decref();

        return try py.call0(@import("../pyz3.zig"), method);
    }
};
