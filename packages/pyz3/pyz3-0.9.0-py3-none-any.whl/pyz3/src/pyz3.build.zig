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
const builtin = @import("builtin");
const std = @import("std");
const Step = std.Build.Step;
const LazyPath = std.Build.LazyPath;
const GeneratedFile = std.Build.GeneratedFile;

pub const PyZ3Options = struct {
    // Optionally pass your test_step and we will hook up the pyZ3 Zig tests.
    test_step: ?*Step = null,
};

pub const PythonModuleOptions = struct {
    name: [:0]const u8,
    root_source_file: std.Build.LazyPath,
    limited_api: bool = true,
    target: std.Target.Query,
    optimize: std.builtin.OptimizeMode,
    main_pkg_path: ?std.Build.LazyPath = null,

    // C/C++ integration options
    c_sources: []const []const u8 = &.{},
    c_include_dirs: []const []const u8 = &.{},
    c_libraries: []const []const u8 = &.{},
    c_flags: []const []const u8 = &.{},
    ld_flags: []const []const u8 = &.{},

    pub fn short_name(self: *const PythonModuleOptions) [:0]const u8 {
        if (std.mem.lastIndexOfScalar(u8, self.name, '.')) |short_name_idx| {
            return self.name[short_name_idx + 1 .. :0];
        }
        return self.name;
    }
};

pub const PythonModule = struct {
    library_step: *std.Build.Step.Compile,
    test_step: *std.Build.Step.Compile,
};

/// Configure a pyZ3 step in the build. From this, you can define Python modules.
pub fn addPyZ3(b: *std.Build, options: PyZ3Options) *PyZ3Step {
    return PyZ3Step.add(b, options);
}

pub const PyZ3Step = struct {
    owner: *std.Build,
    allocator: std.mem.Allocator,
    options: PyZ3Options,

    test_build_step: *Step,
    generate_stubs: *Step,
    check_stubs: bool,

    python_exe: []const u8,
    libpython: []const u8,
    hexversion: []const u8,

    pyz3_source_file: []const u8,
    ffi_header_file: []const u8,
    python_include_dir: []const u8,
    python_library_dir: []const u8,

    pub fn add(b: *std.Build, options: PyZ3Options) *PyZ3Step {
        const test_build_step = b.step("pyz3-test-build", "Build pyZ3 test runners");
        const generate_stubs = b.step("generate-stubs", "Generate pyi stubs for the compiled binary");
        const check_stubs = b.option(bool, "check-stubs", "Check that existing stubs are up to date instead of generating new ones") orelse false;

        const python_exe = blk: {
            if (b.option([]const u8, "python-exe", "Python executable to use")) |exe| {
                break :blk exe;
            }
            if (getStdOutput(b.allocator, &.{ "poetry", "env", "info", "--executable" })) |exe| {
                // Strip off the trailing newline
                break :blk exe[0 .. exe.len - 1];
            } else |_| {
                break :blk "python3";
            }
        };

        const libpython = getLibpython(
            b.allocator,
            python_exe,
        ) catch |err| {
            std.debug.print("\n❌ Failed to locate Python library (libpython)\n", .{});
            std.debug.print("   Error: {}\n", .{err});
            std.debug.print("\n   Possible solutions:\n", .{});
            std.debug.print("   - Ensure Python development headers are installed:\n", .{});
            std.debug.print("     • Ubuntu/Debian: sudo apt install python3-dev\n", .{});
            std.debug.print("     • Fedora/RHEL:   sudo dnf install python3-devel\n", .{});
            std.debug.print("     • macOS:         brew install python@3.11\n", .{});
            std.debug.print("   - Verify Python executable: {s}\n", .{python_exe});
            std.debug.print("   - Try specifying Python explicitly: zig build -Dpython-exe=/path/to/python\n", .{});
            std.process.exit(1);
        };
        const hexversion = getPythonOutput(
            b.allocator,
            python_exe,
            "import sys; print(f'{sys.hexversion:#010x}', end='')",
        ) catch |err| {
            std.debug.print("\n❌ Failed to get Python version information\n", .{});
            std.debug.print("   Error: {}\n", .{err});
            std.debug.print("   Python executable: {s}\n", .{python_exe});
            std.debug.print("   Ensure Python is working correctly: {s} --version\n", .{python_exe});
            std.process.exit(1);
        };

        var self = b.allocator.create(PyZ3Step) catch |err| {
            std.debug.print("\n❌ Out of memory creating PyZ3Step\n", .{});
            std.debug.print("   Error: {}\n", .{err});
            std.process.exit(1);
        };

        self.* = .{
            .owner = b,
            .allocator = b.allocator,
            .options = options,
            .test_build_step = test_build_step,
            .generate_stubs = generate_stubs,
            .check_stubs = check_stubs,
            .python_exe = python_exe,
            .libpython = libpython,
            .hexversion = hexversion,
            .pyz3_source_file = "",
            .ffi_header_file = "",
            .python_include_dir = "",
            .python_library_dir = "",
        };
        // Eagerly run path discovery to work around ZLS support.
        self.python_include_dir = self.pythonOutput(
            "import os, sysconfig; print(os.path.relpath(sysconfig.get_path('include')), end='')",
        ) catch |err| {
            std.debug.print("\n❌ Failed to get Python include directory\n", .{});
            std.debug.print("   Error: {}\n", .{err});
            std.debug.print("   Python executable: {s}\n", .{python_exe});
            std.debug.print("   This usually means Python's sysconfig module is not working correctly.\n", .{});
            std.process.exit(1);
        };
        self.python_library_dir = self.pythonOutput(
            "import os, sysconfig; print(os.path.relpath(sysconfig.get_config_var('LIBDIR')), end='')",
        ) catch |err| {
            std.debug.print("\n❌ Failed to get Python library directory\n", .{});
            std.debug.print("   Error: {}\n", .{err});
            std.debug.print("   Python executable: {s}\n", .{python_exe});
            std.process.exit(1);
        };
        self.pyz3_source_file = self.pythonOutput(
            "import pyz3; import os; print(os.path.relpath(os.path.join(os.path.dirname(pyz3.__file__), 'src/pyz3.zig')), end='')",
        ) catch |err| {
            std.debug.print("\n❌ Failed to locate pyz3 source files\n", .{});
            std.debug.print("   Error: {}\n", .{err});
            std.debug.print("   Ensure pyz3 package is installed: pip install pyz3\n", .{});
            std.debug.print("   Or install in development mode: pip install -e .\n", .{});
            std.process.exit(1);
        };
        self.ffi_header_file = self.pythonOutput(
            "import pyz3; import os; print(os.path.abspath(os.path.join(os.path.dirname(pyz3.__file__), 'src/ffi.h')), end='')",
        ) catch |err| {
            std.debug.print("\n❌ Failed to locate pyz3 FFI header file\n", .{});
            std.debug.print("   Error: {}\n", .{err});
            std.debug.print("   Ensure pyz3 package is installed: pip install pyz3\n", .{});
            std.debug.print("   Or install in development mode: pip install -e .\n", .{});
            std.process.exit(1);
        };

        // Option for emitting test binary based on the given root source. This can be helpful for debugging.
        const debugRoot = b.option(
            []const u8,
            "debug-root",
            "The root path of a file emitted as a binary for use with the debugger",
        );
        if (debugRoot) |root| {
            const pyconf = b.addOptions();
            pyconf.addOption([:0]const u8, "module_name", "debug");
            pyconf.addOption(bool, "limited_api", false);
            pyconf.addOption([]const u8, "hexversion", hexversion);

            const testdebug = b.addTest(.{
                .root_module = b.createModule(.{
                    .root_source_file = b.path(root),
                    .target = b.resolveTargetQuery(.{}),
                    .optimize = .Debug,
                }),
            });
            testdebug.root_module.addOptions("pyconf", pyconf);
            const testdebug_module = b.createModule(.{
                .root_source_file = b.path(self.pyz3_source_file),
                .imports = &.{.{ .name = "pyconf", .module = pyconf.createModule() }},
            });
            testdebug_module.addIncludePath(b.path(self.python_include_dir));
            testdebug.root_module.addImport("pyz3", testdebug_module);
            testdebug.linkLibC();
            testdebug.linkSystemLibrary(libpython);
            testdebug.addLibraryPath(b.path(self.python_library_dir));
            // Note: addLibraryPath automatically adds RPATH on macOS in Zig 0.15+
            // Only add explicit RPATH for non-macOS (needed for miniconda on other platforms)
            if (builtin.os.tag != .macos) {
                testdebug.addRPath(b.path(self.python_library_dir));
            }

            const debugBin = b.addInstallBinFile(testdebug.getEmittedBin(), "debug.bin");
            b.getInstallStep().dependOn(&debugBin.step);
        }

        return self;
    }

    /// Adds a pyZ3 Python module. The resulting library and test binaries can be further configured with
    /// additional dependencies or modules.
    pub fn addPythonModule(self: *PyZ3Step, options: PythonModuleOptions) PythonModule {
        const b = self.owner;

        const short_name = options.short_name();

        const pyconf = b.addOptions();
        pyconf.addOption([:0]const u8, "module_name", options.name);
        pyconf.addOption(bool, "limited_api", options.limited_api);
        pyconf.addOption([]const u8, "hexversion", self.hexversion);

        // Configure and install the Python module shared library
        const lib = b.addLibrary(.{
            .name = short_name,
            .linkage = .dynamic,
            .root_module = b.createModule(.{
                .root_source_file = options.root_source_file,
                .target = b.resolveTargetQuery(options.target),
                .optimize = options.optimize,
                //.main_pkg_path = options.main_pkg_path,
            }),
        });
        lib.root_module.addOptions("pyconf", pyconf);
        const translate_c = self.addTranslateC(options);
        translate_c.addIncludePath(b.path(self.python_include_dir));
        const lib_module = b.createModule(.{
            .root_source_file = b.path(self.pyz3_source_file),
            .imports = &.{
                .{ .name = "pyconf", .module = pyconf.createModule() },
                .{ .name = "ffi", .module = translate_c.createModule() },
            },
        });
        lib_module.addIncludePath(b.path(self.python_include_dir));
        lib.root_module.addImport("pyz3", lib_module);
        lib.linkLibC();
        lib.linker_allow_shlib_undefined = true;

        // Apply C/C++ integration configuration
        for (options.c_include_dirs) |include_dir| {
            lib.addIncludePath(b.path(include_dir));
            lib_module.addIncludePath(b.path(include_dir));
        }

        for (options.c_sources) |c_source| {
            lib.addCSourceFile(.{
                .file = b.path(c_source),
                .flags = options.c_flags,
            });
        }

        for (options.c_libraries) |c_lib| {
            lib.linkSystemLibrary(c_lib);
        }

        // Apply linker flags
        for (options.ld_flags) |ld_flag| {
            lib.root_module.addRPathSpecial(ld_flag);
        }

        // Install the shared library within the source tree (not zig-out/).
        // Python's import mechanism expects extension modules to be co-located with
        // Python source files (e.g., package/module.abi3.so), not in a separate build directory.
        //
        // We use .{ .custom = ".." } to install relative to the project root instead of zig-out/.
        // This resolves: zig-out/../package/module.so → package/module.so
        //
        // This is intentional and aligns with Python build system conventions.
        const install = b.addInstallFileWithDir(
            lib.getEmittedBin(),
            .{ .custom = ".." }, // Escape zig-out/ to install in project root
            libraryDestRelPath(self.allocator, options) catch |err| {
                std.debug.print("\n❌ Out of memory computing library destination path\n", .{});
                std.debug.print("   Error: {}\n", .{err});
                std.process.exit(1);
            },
        );
        b.getInstallStep().dependOn(&install.step);

        // Invoke stub generator on the emitted binary
        const workingDir = std.fs.cwd().realpathAlloc(self.allocator, ".") catch |err| {
            std.debug.print("\n❌ Failed to get current working directory\n", .{});
            std.debug.print("   Error: {}\n", .{err});
            std.process.exit(1);
        };
        const genArgs: []const []const u8 = if (self.check_stubs)
            &.{ self.python_exe, "-m", "pyz3.generate_stubs", options.name, workingDir, "--check" }
        else
            &.{ self.python_exe, "-m", "pyz3.generate_stubs", options.name, workingDir };
        const stubs = b.addSystemCommand(genArgs);
        stubs.step.dependOn(&install.step);
        self.generate_stubs.dependOn(&stubs.step);

        // Configure a test runner for the module
        const libtest = b.addTest(.{
            .root_module = b.createModule(.{
                .root_source_file = options.root_source_file,
                // .main_pkg_path = options.main_pkg_path,
                .target = b.resolveTargetQuery(options.target),
                .optimize = options.optimize,
            }),
        });
        libtest.root_module.addOptions("pyconf", pyconf);
        const libtest_module = b.createModule(.{
            .root_source_file = b.path(self.pyz3_source_file),
            .imports = &.{
                .{ .name = "pyconf", .module = pyconf.createModule() },
                .{ .name = "ffi", .module = translate_c.createModule() },
            },
        });
        libtest_module.addIncludePath(b.path(self.python_include_dir));
        libtest.root_module.addImport("pyz3", libtest_module);
        libtest.linkLibC();
        libtest.linkSystemLibrary(self.libpython);
        libtest.addLibraryPath(b.path(self.python_library_dir));
        // Note: addLibraryPath automatically adds RPATH on macOS in Zig 0.15+
        // Only add explicit RPATH for non-macOS (needed for miniconda on other platforms)
        if (builtin.os.tag != .macos) {
            libtest.addRPath(b.path(self.python_library_dir));
        }

        // Apply C/C++ integration configuration to test build
        for (options.c_include_dirs) |include_dir| {
            libtest.addIncludePath(b.path(include_dir));
            libtest_module.addIncludePath(b.path(include_dir));
        }

        for (options.c_sources) |c_source| {
            libtest.addCSourceFile(.{
                .file = b.path(c_source),
                .flags = options.c_flags,
            });
        }

        for (options.c_libraries) |c_lib| {
            libtest.linkSystemLibrary(c_lib);
        }

        for (options.ld_flags) |ld_flag| {
            libtest.root_module.addRPathSpecial(ld_flag);
        }

        // Install the test binary
        const install_libtest = b.addInstallBinFile(
            libtest.getEmittedBin(),
            testDestRelPath(self.allocator, short_name) catch |err| {
                std.debug.print("\n❌ Out of memory computing test destination path\n", .{});
                std.debug.print("   Error: {}\n", .{err});
                std.process.exit(1);
            },
        );
        self.test_build_step.dependOn(&install_libtest.step);

        // Run the tests as part of zig build test.
        if (self.options.test_step) |test_step| {
            const run_libtest = b.addRunArtifact(libtest);
            test_step.dependOn(&run_libtest.step);
        }

        return .{
            .library_step = lib,
            .test_step = libtest,
        };
    }

    fn libraryDestRelPath(allocator: std.mem.Allocator, options: PythonModuleOptions) ![]const u8 {
        const name = options.name;

        if (!options.limited_api) {
            std.debug.print("\n❌ pyz3 currently only supports limited API (PEP 384)\n", .{});
            std.debug.print("   Please set 'limited_api: true' in PythonModuleOptions\n", .{});
            std.debug.print("   Module: {s}\n", .{name});
            std.process.exit(1);
        }

        const suffix = ".abi3.so";
        const destPath = try allocator.alloc(u8, name.len + suffix.len);

        // Take the module name, replace dots for slashes.
        @memcpy(destPath[0..name.len], name);
        std.mem.replaceScalar(u8, destPath[0..name.len], '.', '/');

        // Append the suffix
        @memcpy(destPath[name.len..], suffix);

        return destPath;
    }

    fn testDestRelPath(allocator: std.mem.Allocator, short_name: []const u8) ![]const u8 {
        const suffix = ".test.bin";
        const destPath = try allocator.alloc(u8, short_name.len + suffix.len);

        @memcpy(destPath[0..short_name.len], short_name);
        @memcpy(destPath[short_name.len..], suffix);

        return destPath;
    }

    fn pythonOutput(self: *PyZ3Step, code: []const u8) ![]const u8 {
        return getPythonOutput(self.allocator, self.python_exe, code);
    }

    fn addTranslateC(self: PyZ3Step, options: PythonModuleOptions) *std.Build.Step.TranslateC {
        const b = self.owner;
        const translate_c = b.addTranslateC(.{
            .root_source_file = .{ .cwd_relative = self.ffi_header_file },
            .target = b.resolveTargetQuery(options.target),
            .optimize = options.optimize,
        });
        if (options.limited_api)
            translate_c.defineCMacro("Py_LIMITED_API", self.hexversion);
        return translate_c;
    }
};

fn getLibpython(allocator: std.mem.Allocator, python_exe: []const u8) ![]const u8 {
    const ldlibrary = try getPythonOutput(
        allocator,
        python_exe,
        "import sysconfig; print(sysconfig.get_config_var('LDLIBRARY'), end='')",
    );

    var libname = ldlibrary;

    // Handle macOS Framework Python (e.g., "Python.framework/Versions/3.11/Python" or "Python")
    if (std.mem.indexOf(u8, ldlibrary, ".framework/") != null) {
        // Extract just the library name from framework path
        // Python.framework/Versions/3.11/Python => Python
        if (std.mem.lastIndexOfScalar(u8, ldlibrary, '/')) |last_slash| {
            libname = ldlibrary[last_slash + 1 ..];
        }
        // Remove any extensions
        const lastIdx = std.mem.lastIndexOfScalar(u8, libname, '.') orelse libname.len;
        return libname[0..lastIdx];
    }

    // Strip libpython3.11.a.so => python3.11.a.so
    if (libname.len >= 3 and std.mem.eql(u8, ldlibrary[0..3], "lib")) {
        libname = libname[3..];
    }

    // Strip python3.11.a.so => python3.11.a
    const lastIdx = std.mem.lastIndexOfScalar(u8, libname, '.') orelse libname.len;
    libname = libname[0..lastIdx];

    return libname;
}

fn getPythonOutput(allocator: std.mem.Allocator, python_exe: []const u8, code: []const u8) ![]const u8 {
    const result = try runProcess(.{
        .allocator = allocator,
        .argv = &.{ python_exe, "-c", code },
    });
    if (result.term.Exited != 0) {
        std.debug.print("Failed to execute {s}:\n{s}\n", .{ code, result.stderr });
        std.process.exit(1);
    }
    allocator.free(result.stderr);
    return result.stdout;
}

fn getStdOutput(allocator: std.mem.Allocator, argv: []const []const u8) ![]const u8 {
    const result = try runProcess(.{ .allocator = allocator, .argv = argv });
    if (result.term.Exited != 0) {
        std.debug.print("Failed to execute {any}:\n{s}\n", .{ argv, result.stderr });
        std.process.exit(1);
    }
    allocator.free(result.stderr);
    return result.stdout;
}

const runProcess = if (builtin.zig_version.minor >= 12) std.process.Child.run else std.process.Child.exec;
