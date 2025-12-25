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

/// Python datetime object wrapper
pub const PyDateTime = extern struct {
    obj: py.PyObject,

    const Self = @This();

    /// Create a datetime from components
    pub fn create(year: i32, month: i32, day: i32, hour: i32, minute: i32, second: i32, microsecond: i32) !Self {
        const datetime_mod = try py.import("datetime");
        defer datetime_mod.decref();

        const datetime_class = try datetime_mod.getAttribute("datetime");
        defer datetime_class.decref();

        const y = try py.PyLong.from(@as(i64, year));
        defer y.obj.decref();
        const mo = try py.PyLong.from(@as(i64, month));
        defer mo.obj.decref();
        const d = try py.PyLong.from(@as(i64, day));
        defer d.obj.decref();
        const h = try py.PyLong.from(@as(i64, hour));
        defer h.obj.decref();
        const mi = try py.PyLong.from(@as(i64, minute));
        defer mi.obj.decref();
        const s = try py.PyLong.from(@as(i64, second));
        defer s.obj.decref();
        const us = try py.PyLong.from(@as(i64, microsecond));
        defer us.obj.decref();

        const dt_obj = try py.call(@import("../pyz3.zig"), datetime_class, .{ y.obj, mo.obj, d.obj, h.obj, mi.obj, s.obj, us.obj });
        return .{ .obj = dt_obj };
    }

    /// Get current datetime (now)
    pub fn now() !Self {
        const datetime_mod = try py.import("datetime");
        defer datetime_mod.decref();

        const datetime_class = try datetime_mod.getAttribute("datetime");
        defer datetime_class.decref();

        const now_method = try datetime_class.getAttribute("now");
        defer now_method.decref();

        const dt_obj = try py.call0(@import("../pyz3.zig"), now_method);
        return .{ .obj = dt_obj };
    }

    /// Get current UTC datetime
    pub fn utcnow() !Self {
        const datetime_mod = try py.import("datetime");
        defer datetime_mod.decref();

        const datetime_class = try datetime_mod.getAttribute("datetime");
        defer datetime_class.decref();

        const utcnow_method = try datetime_class.getAttribute("utcnow");
        defer utcnow_method.decref();

        const dt_obj = try py.call0(@import("../pyz3.zig"), utcnow_method);
        return .{ .obj = dt_obj };
    }

    /// Get datetime components as a struct
    pub fn components(self: Self) !struct { year: i32, month: i32, day: i32, hour: i32, minute: i32, second: i32, microsecond: i32 } {
        const year_obj = try self.obj.getAttribute("year");
        defer year_obj.decref();
        const month_obj = try self.obj.getAttribute("month");
        defer month_obj.decref();
        const day_obj = try self.obj.getAttribute("day");
        defer day_obj.decref();
        const hour_obj = try self.obj.getAttribute("hour");
        defer hour_obj.decref();
        const minute_obj = try self.obj.getAttribute("minute");
        defer minute_obj.decref();
        const second_obj = try self.obj.getAttribute("second");
        defer second_obj.decref();
        const microsecond_obj = try self.obj.getAttribute("microsecond");
        defer microsecond_obj.decref();

        return .{
            .year = @intCast(try py.as(i64, @import("../pyz3.zig"), year_obj)),
            .month = @intCast(try py.as(i64, @import("../pyz3.zig"), month_obj)),
            .day = @intCast(try py.as(i64, @import("../pyz3.zig"), day_obj)),
            .hour = @intCast(try py.as(i64, @import("../pyz3.zig"), hour_obj)),
            .minute = @intCast(try py.as(i64, @import("../pyz3.zig"), minute_obj)),
            .second = @intCast(try py.as(i64, @import("../pyz3.zig"), second_obj)),
            .microsecond = @intCast(try py.as(i64, @import("../pyz3.zig"), microsecond_obj)),
        };
    }

    /// Convert to ISO format string
    pub fn isoformat(self: Self) !py.PyString {
        const method = try self.obj.getAttribute("isoformat");
        defer method.decref();

        const result = try py.call0(@import("../pyz3.zig"), method);
        return .{ .obj = result };
    }

    /// Format datetime using strftime
    pub fn strftime(self: Self, format: []const u8) !py.PyString {
        const method = try self.obj.getAttribute("strftime");
        defer method.decref();

        const fmt = try py.PyString.create(format);
        defer fmt.obj.decref();

        const result = try py.call(@import("../pyz3.zig"), method, .{fmt.obj});
        return .{ .obj = result };
    }
};

/// Python date object wrapper
pub const PyDate = extern struct {
    obj: py.PyObject,

    const Self = @This();

    /// Create a date from components
    pub fn create(year: i32, month: i32, day: i32) !Self {
        const datetime_mod = try py.import("datetime");
        defer datetime_mod.decref();

        const date_class = try datetime_mod.getAttribute("date");
        defer date_class.decref();

        const y = try py.PyLong.from(@as(i64, year));
        defer y.obj.decref();
        const mo = try py.PyLong.from(@as(i64, month));
        defer mo.obj.decref();
        const d = try py.PyLong.from(@as(i64, day));
        defer d.obj.decref();

        const date_obj = try py.call(@import("../pyz3.zig"), date_class, .{ y.obj, mo.obj, d.obj });
        return .{ .obj = date_obj };
    }

    /// Get today's date
    pub fn today() !Self {
        const datetime_mod = try py.import("datetime");
        defer datetime_mod.decref();

        const date_class = try datetime_mod.getAttribute("date");
        defer date_class.decref();

        const today_method = try date_class.getAttribute("today");
        defer today_method.decref();

        const date_obj = try py.call0(@import("../pyz3.zig"), today_method);
        return .{ .obj = date_obj };
    }

    /// Get date components as a struct
    pub fn components(self: Self) !struct { year: i32, month: i32, day: i32 } {
        const year_obj = try self.obj.getAttribute("year");
        defer year_obj.decref();
        const month_obj = try self.obj.getAttribute("month");
        defer month_obj.decref();
        const day_obj = try self.obj.getAttribute("day");
        defer day_obj.decref();

        return .{
            .year = @intCast(try py.as(i64, @import("../pyz3.zig"), year_obj)),
            .month = @intCast(try py.as(i64, @import("../pyz3.zig"), month_obj)),
            .day = @intCast(try py.as(i64, @import("../pyz3.zig"), day_obj)),
        };
    }

    /// Convert to ISO format string (YYYY-MM-DD)
    pub fn isoformat(self: Self) !py.PyString {
        const method = try self.obj.getAttribute("isoformat");
        defer method.decref();

        const result = try py.call0(@import("../pyz3.zig"), method);
        return .{ .obj = result };
    }
};

/// Python time object wrapper
pub const PyTime = extern struct {
    obj: py.PyObject,

    const Self = @This();

    /// Create a time from components
    pub fn create(hour: i32, minute: i32, second: i32, microsecond: i32) !Self {
        const datetime_mod = try py.import("datetime");
        defer datetime_mod.decref();

        const time_class = try datetime_mod.getAttribute("time");
        defer time_class.decref();

        const h = try py.PyLong.from(@as(i64, hour));
        defer h.obj.decref();
        const mi = try py.PyLong.from(@as(i64, minute));
        defer mi.obj.decref();
        const s = try py.PyLong.from(@as(i64, second));
        defer s.obj.decref();
        const us = try py.PyLong.from(@as(i64, microsecond));
        defer us.obj.decref();

        const time_obj = try py.call(@import("../pyz3.zig"), time_class, .{ h.obj, mi.obj, s.obj, us.obj });
        return .{ .obj = time_obj };
    }

    /// Get time components as a struct
    pub fn components(self: Self) !struct { hour: i32, minute: i32, second: i32, microsecond: i32 } {
        const hour_obj = try self.obj.getAttribute("hour");
        defer hour_obj.decref();
        const minute_obj = try self.obj.getAttribute("minute");
        defer minute_obj.decref();
        const second_obj = try self.obj.getAttribute("second");
        defer second_obj.decref();
        const microsecond_obj = try self.obj.getAttribute("microsecond");
        defer microsecond_obj.decref();

        return .{
            .hour = @intCast(try py.as(i64, @import("../pyz3.zig"), hour_obj)),
            .minute = @intCast(try py.as(i64, @import("../pyz3.zig"), minute_obj)),
            .second = @intCast(try py.as(i64, @import("../pyz3.zig"), second_obj)),
            .microsecond = @intCast(try py.as(i64, @import("../pyz3.zig"), microsecond_obj)),
        };
    }

    /// Convert to ISO format string (HH:MM:SS.mmmmmm)
    pub fn isoformat(self: Self) !py.PyString {
        const method = try self.obj.getAttribute("isoformat");
        defer method.decref();

        const result = try py.call0(@import("../pyz3.zig"), method);
        return .{ .obj = result };
    }
};

/// Python timedelta object wrapper
pub const PyTimeDelta = extern struct {
    obj: py.PyObject,

    const Self = @This();

    /// Create a timedelta from components (days, seconds, microseconds)
    pub fn create(days: i64, seconds: i64, microseconds: i64) !Self {
        const datetime_mod = try py.import("datetime");
        defer datetime_mod.decref();

        const timedelta_class = try datetime_mod.getAttribute("timedelta");
        defer timedelta_class.decref();

        const d = try py.PyLong.from(days);
        defer d.obj.decref();
        const s = try py.PyLong.from(seconds);
        defer s.obj.decref();
        const us = try py.PyLong.from(microseconds);
        defer us.obj.decref();

        const td_obj = try py.call(@import("../pyz3.zig"), timedelta_class, .{ d.obj, s.obj, us.obj });
        return .{ .obj = td_obj };
    }

    /// Create from total seconds
    pub fn fromSeconds(seconds: f64) !Self {
        const datetime_mod = try py.import("datetime");
        defer datetime_mod.decref();

        const timedelta_class = try datetime_mod.getAttribute("timedelta");
        defer timedelta_class.decref();

        const s = try py.PyFloat.from(seconds);
        defer s.obj.decref();

        const td_obj = try py.call(@import("../pyz3.zig"), timedelta_class, .{s.obj});
        return .{ .obj = td_obj };
    }

    /// Get timedelta components
    pub fn components(self: Self) !struct { days: i64, seconds: i64, microseconds: i64 } {
        const days_obj = try self.obj.getAttribute("days");
        defer days_obj.decref();
        const seconds_obj = try self.obj.getAttribute("seconds");
        defer seconds_obj.decref();
        const microseconds_obj = try self.obj.getAttribute("microseconds");
        defer microseconds_obj.decref();

        return .{
            .days = try py.as(i64, @import("../pyz3.zig"), days_obj),
            .seconds = try py.as(i64, @import("../pyz3.zig"), seconds_obj),
            .microseconds = try py.as(i64, @import("../pyz3.zig"), microseconds_obj),
        };
    }

    /// Get total seconds as float
    pub fn totalSeconds(self: Self) !f64 {
        const method = try self.obj.getAttribute("total_seconds");
        defer method.decref();

        const result = try py.call0(@import("../pyz3.zig"), method);
        defer result.decref();

        return try py.as(f64, @import("../pyz3.zig"), result);
    }

    /// Add two timedeltas
    pub fn add(self: Self, other: Self) !Self {
        const add_method = try self.obj.getAttribute("__add__");
        defer add_method.decref();

        const result = try py.call(@import("../pyz3.zig"), add_method, .{other.obj});
        return .{ .obj = result };
    }

    /// Subtract two timedeltas
    pub fn sub(self: Self, other: Self) !Self {
        const sub_method = try self.obj.getAttribute("__sub__");
        defer sub_method.decref();

        const result = try py.call(@import("../pyz3.zig"), sub_method, .{other.obj});
        return .{ .obj = result };
    }

    /// Multiply timedelta by a scalar
    pub fn mul(self: Self, scalar: f64) !Self {
        const mul_method = try self.obj.getAttribute("__mul__");
        defer mul_method.decref();

        const s = try py.PyFloat.from(scalar);
        defer s.obj.decref();

        const result = try py.call(@import("../pyz3.zig"), mul_method, .{s.obj});
        return .{ .obj = result };
    }

    /// Get absolute value of timedelta
    pub fn abs(self: Self) !Self {
        const abs_method = try self.obj.getAttribute("__abs__");
        defer abs_method.decref();

        const result = try py.call0(@import("../pyz3.zig"), abs_method);
        return .{ .obj = result };
    }
};
