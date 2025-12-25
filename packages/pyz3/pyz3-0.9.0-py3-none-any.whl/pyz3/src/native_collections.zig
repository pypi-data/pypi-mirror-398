/// Native high-performance collections using uthash and utarray
/// Provides fast dict and array implementations with C-level performance
const std = @import("std");
const py = @import("pyz3.zig");
const PyError = @import("errors.zig").PyError;

// C bindings for native dict
pub const NativeDict = opaque {};
pub const NativeDictIterator = opaque {};

extern fn native_dict_create() ?*NativeDict;
extern fn native_dict_destroy(dict: *NativeDict) void;
extern fn native_dict_set(dict: *NativeDict, key: [*:0]const u8, value: ?*anyopaque) bool;
extern fn native_dict_get(dict: *NativeDict, key: [*:0]const u8) ?*anyopaque;
extern fn native_dict_delete(dict: *NativeDict, key: [*:0]const u8) bool;
extern fn native_dict_contains(dict: *NativeDict, key: [*:0]const u8) bool;
extern fn native_dict_size(dict: *NativeDict) usize;
extern fn native_dict_clear(dict: *NativeDict) void;
extern fn native_dict_iter_create(dict: *NativeDict) ?*NativeDictIterator;
extern fn native_dict_iter_destroy(iter: *NativeDictIterator) void;
extern fn native_dict_iter_next(iter: *NativeDictIterator, key: *?[*:0]const u8, value: *?*anyopaque) bool;
extern fn native_dict_keys(dict: *NativeDict, count: *usize) ?[*]?[*:0]const u8;
extern fn native_dict_values(dict: *NativeDict, count: *usize) ?[*]?*anyopaque;
extern fn native_dict_free_keys(keys: [*]?[*:0]const u8) void;
extern fn native_dict_free_values(values: [*]?*anyopaque) void;

// C bindings for native array
pub const NativeArray = opaque {};

extern fn native_array_create() ?*NativeArray;
extern fn native_array_destroy(array: *NativeArray) void;
extern fn native_array_push(array: *NativeArray, value: ?*anyopaque) bool;
extern fn native_array_pop(array: *NativeArray) ?*anyopaque;
extern fn native_array_get(array: *NativeArray, index: usize) ?*anyopaque;
extern fn native_array_set(array: *NativeArray, index: usize, value: ?*anyopaque) bool;
extern fn native_array_insert(array: *NativeArray, index: usize, value: ?*anyopaque) bool;
extern fn native_array_remove(array: *NativeArray, index: usize) bool;
extern fn native_array_size(array: *NativeArray) usize;
extern fn native_array_clear(array: *NativeArray) void;
extern fn native_array_reserve(array: *NativeArray, capacity: usize) bool;
extern fn native_array_to_ptr_array(array: *NativeArray, count: *usize) ?[*]?*anyopaque;
extern fn native_array_free_ptr_array(ptr_array: [*]?*anyopaque) void;

/// High-performance hash table using uthash
pub const FastDict = struct {
    dict: *NativeDict,

    pub fn init() !FastDict {
        const dict = native_dict_create() orelse return error.OutOfMemory;
        return FastDict{ .dict = dict };
    }

    pub fn deinit(self: *FastDict) void {
        native_dict_destroy(self.dict);
    }

    pub fn set(self: *FastDict, key: []const u8, value: ?*anyopaque) !void {
        const key_z = try std.heap.c_allocator.dupeZ(u8, key);
        defer std.heap.c_allocator.free(key_z);

        if (!native_dict_set(self.dict, key_z.ptr, value)) {
            return error.OutOfMemory;
        }
    }

    pub fn get(self: *FastDict, key: []const u8) ?*anyopaque {
        const key_z = std.heap.c_allocator.dupeZ(u8, key) catch return null;
        defer std.heap.c_allocator.free(key_z);

        return native_dict_get(self.dict, key_z.ptr);
    }

    pub fn delete(self: *FastDict, key: []const u8) bool {
        const key_z = std.heap.c_allocator.dupeZ(u8, key) catch return false;
        defer std.heap.c_allocator.free(key_z);

        return native_dict_delete(self.dict, key_z.ptr);
    }

    pub fn contains(self: *FastDict, key: []const u8) bool {
        const key_z = std.heap.c_allocator.dupeZ(u8, key) catch return false;
        defer std.heap.c_allocator.free(key_z);

        return native_dict_contains(self.dict, key_z.ptr);
    }

    pub fn size(self: *FastDict) usize {
        return native_dict_size(self.dict);
    }

    pub fn clear(self: *FastDict) void {
        native_dict_clear(self.dict);
    }

    pub fn keys(self: *FastDict, allocator: std.mem.Allocator) ![][]const u8 {
        var count: usize = 0;
        const keys_ptr = native_dict_keys(self.dict, &count) orelse return &[_][]const u8{};
        defer native_dict_free_keys(keys_ptr);

        var result = try allocator.alloc([]const u8, count);
        for (0..count) |i| {
            const key_ptr = keys_ptr[i] orelse continue;
            const key_len = std.mem.len(key_ptr);
            result[i] = try allocator.dupe(u8, key_ptr[0..key_len]);
        }

        return result;
    }
};

/// High-performance dynamic array using utarray
pub const FastArray = struct {
    array: *NativeArray,

    pub fn init() !FastArray {
        const array = native_array_create() orelse return error.OutOfMemory;
        return FastArray{ .array = array };
    }

    pub fn deinit(self: *FastArray) void {
        native_array_destroy(self.array);
    }

    pub fn push(self: *FastArray, value: ?*anyopaque) !void {
        if (!native_array_push(self.array, value)) {
            return error.OutOfMemory;
        }
    }

    pub fn pop(self: *FastArray) ?*anyopaque {
        return native_array_pop(self.array);
    }

    pub fn get(self: *FastArray, index: usize) ?*anyopaque {
        return native_array_get(self.array, index);
    }

    pub fn set(self: *FastArray, index: usize, value: ?*anyopaque) !void {
        if (!native_array_set(self.array, index, value)) {
            return error.IndexOutOfBounds;
        }
    }

    pub fn insert(self: *FastArray, index: usize, value: ?*anyopaque) !void {
        if (!native_array_insert(self.array, index, value)) {
            return error.IndexOutOfBounds;
        }
    }

    pub fn remove(self: *FastArray, index: usize) !void {
        if (!native_array_remove(self.array, index)) {
            return error.IndexOutOfBounds;
        }
    }

    pub fn size(self: *FastArray) usize {
        return native_array_size(self.array);
    }

    pub fn clear(self: *FastArray) void {
        native_array_clear(self.array);
    }

    pub fn reserve(self: *FastArray, capacity: usize) !void {
        if (!native_array_reserve(self.array, capacity)) {
            return error.OutOfMemory;
        }
    }
};

// Tests
test "FastDict basic operations" {
    var dict = try FastDict.init();
    defer dict.deinit();

    // Test set and get
    const value1: usize = 42;
    const value2: usize = 100;

    try dict.set("key1", @ptrFromInt(value1));
    try dict.set("key2", @ptrFromInt(value2));

    try std.testing.expectEqual(@as(usize, 2), dict.size());

    const retrieved1 = dict.get("key1");
    try std.testing.expect(retrieved1 != null);
    try std.testing.expectEqual(value1, @intFromPtr(retrieved1.?));

    // Test contains
    try std.testing.expect(dict.contains("key1"));
    try std.testing.expect(!dict.contains("nonexistent"));

    // Test delete
    try std.testing.expect(dict.delete("key1"));
    try std.testing.expectEqual(@as(usize, 1), dict.size());
    try std.testing.expect(!dict.contains("key1"));

    // Test clear
    dict.clear();
    try std.testing.expectEqual(@as(usize, 0), dict.size());
}

test "FastArray basic operations" {
    var array = try FastArray.init();
    defer array.deinit();

    // Test push and size
    const value1: usize = 42;
    const value2: usize = 100;
    const value3: usize = 200;

    try array.push(@ptrFromInt(value1));
    try array.push(@ptrFromInt(value2));
    try array.push(@ptrFromInt(value3));

    try std.testing.expectEqual(@as(usize, 3), array.size());

    // Test get
    const retrieved1 = array.get(0);
    try std.testing.expect(retrieved1 != null);
    try std.testing.expectEqual(value1, @intFromPtr(retrieved1.?));

    const retrieved2 = array.get(1);
    try std.testing.expect(retrieved2 != null);
    try std.testing.expectEqual(value2, @intFromPtr(retrieved2.?));

    // Test set
    const new_value: usize = 999;
    try array.set(1, @ptrFromInt(new_value));

    const retrieved_new = array.get(1);
    try std.testing.expect(retrieved_new != null);
    try std.testing.expectEqual(new_value, @intFromPtr(retrieved_new.?));

    // Test pop
    const popped = array.pop();
    try std.testing.expect(popped != null);
    try std.testing.expectEqual(value3, @intFromPtr(popped.?));
    try std.testing.expectEqual(@as(usize, 2), array.size());

    // Test insert
    const insert_value: usize = 500;
    try array.insert(1, @ptrFromInt(insert_value));
    try std.testing.expectEqual(@as(usize, 3), array.size());

    const retrieved_inserted = array.get(1);
    try std.testing.expect(retrieved_inserted != null);
    try std.testing.expectEqual(insert_value, @intFromPtr(retrieved_inserted.?));

    // Test remove
    try array.remove(1);
    try std.testing.expectEqual(@as(usize, 2), array.size());

    // Test clear
    array.clear();
    try std.testing.expectEqual(@as(usize, 0), array.size());
}

test "FastDict stress test" {
    var dict = try FastDict.init();
    defer dict.deinit();

    // Insert 1000 entries (use offset to avoid null pointer)
    const offset: usize = 0x10000;
    for (0..1000) |i| {
        const key = try std.fmt.allocPrint(std.heap.c_allocator, "key{d}", .{i});
        defer std.heap.c_allocator.free(key);

        try dict.set(key, @ptrFromInt(offset + i));
    }

    try std.testing.expectEqual(@as(usize, 1000), dict.size());

    // Verify all entries
    for (0..1000) |i| {
        const key = try std.fmt.allocPrint(std.heap.c_allocator, "key{d}", .{i});
        defer std.heap.c_allocator.free(key);

        const value = dict.get(key);
        try std.testing.expect(value != null);
        try std.testing.expectEqual(offset + i, @intFromPtr(value.?));
    }

    // Delete half
    for (0..500) |i| {
        const key = try std.fmt.allocPrint(std.heap.c_allocator, "key{d}", .{i});
        defer std.heap.c_allocator.free(key);

        try std.testing.expect(dict.delete(key));
    }

    try std.testing.expectEqual(@as(usize, 500), dict.size());
}

test "FastArray stress test" {
    var array = try FastArray.init();
    defer array.deinit();

    // Push 1000 elements (use offset to avoid null pointer)
    const offset: usize = 0x10000;
    for (0..1000) |i| {
        try array.push(@ptrFromInt(offset + i));
    }

    try std.testing.expectEqual(@as(usize, 1000), array.size());

    // Verify all elements
    for (0..1000) |i| {
        const value = array.get(i);
        try std.testing.expect(value != null);
        try std.testing.expectEqual(offset + i, @intFromPtr(value.?));
    }

    // Remove elements from back (where indices are stable)
    for (0..500) |_| {
        const current_size = array.size();
        if (current_size > 0) {
            try array.remove(current_size - 1);
        }
    }

    try std.testing.expectEqual(@as(usize, 500), array.size());
}
