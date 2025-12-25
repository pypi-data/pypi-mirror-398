#include "nanobind/nanobind.h"
#include "nanobind/stl/string.h"
#include "nanobind/stl/vector.h"
#include "nanobind/stl/shared_ptr.h"
#include "nanobind/stl/function.h"

#include "spdlog/spdlog.h"
#include "spdlog/sinks/sink.h"
#include "spdlog/sinks/base_sink.h"
#include "spdlog/sinks/stdout_color_sinks.h"
#include "spdlog/sinks/stdout_sinks.h"
#include "spdlog/sinks/basic_file_sink.h"
#include "spdlog/sinks/rotating_file_sink.h"
#include "spdlog/sinks/daily_file_sink.h"
#include "spdlog/sinks/null_sink.h"
#include "spdlog/async.h"
#include "spdlog/async_logger.h"
#include "spdlog/common.h"

#include <chrono>
#include <memory>

namespace nb = nanobind;
using namespace nb::literals;

static spdlog::details::thread_pool g_thread_pool(spdlog::details::default_async_q_size, 1);
static std::shared_ptr<spdlog::details::thread_pool> g_thread_pool_ptr{ &g_thread_pool, [](spdlog::details::thread_pool*){} };

NB_MODULE(spydlog, m) {
    // Log level enum
    nb::enum_<spdlog::level::level_enum>(m, "level")
        .value("trace", spdlog::level::trace)
        .value("debug", spdlog::level::debug)
        .value("info", spdlog::level::info)
        .value("warn", spdlog::level::warn)
        .value("err", spdlog::level::err)
        .value("critical", spdlog::level::critical)
        .value("off", spdlog::level::off)
        .def("__lt__", [](const spdlog::level::level_enum& self, spdlog::level::level_enum other) { return self < other; })
        .def("__le__", [](const spdlog::level::level_enum& self, spdlog::level::level_enum other) { return self <= other; })
        .def("__gt__", [](const spdlog::level::level_enum& self, spdlog::level::level_enum other) { return self > other; })
        .def("__ge__", [](const spdlog::level::level_enum& self, spdlog::level::level_enum other) { return self >= other; });

    // Color mode enum
    nb::enum_<spdlog::color_mode>(m, "color_mode")
        .value("always", spdlog::color_mode::always)
        .value("automatic", spdlog::color_mode::automatic)
        .value("never", spdlog::color_mode::never);

    // Pattern time enum
    nb::enum_<spdlog::pattern_time_type>(m, "pattern_time_type")
        .value("local", spdlog::pattern_time_type::local)
        .value("utc", spdlog::pattern_time_type::utc);

    // Sink base class
    nb::class_<spdlog::sinks::sink>(m, "sink")
        .def("log", [](spdlog::sinks::sink& self, spdlog::level::level_enum lvl, const std::string& msg) {
            spdlog::details::log_msg log_msg(spdlog::source_loc{}, "", lvl, msg);
            self.log(log_msg);
        })
        .def("set_level", &spdlog::sinks::sink::set_level)
        .def("level", &spdlog::sinks::sink::level)
        .def("set_pattern", &spdlog::sinks::sink::set_pattern);

    // Console sinks
    nb::class_<spdlog::sinks::stdout_color_sink_mt, spdlog::sinks::sink>(m, "stdout_color_sink_mt")
        .def(nb::init<>())
        .def(nb::init<spdlog::color_mode>(), "mode"_a);

    nb::class_<spdlog::sinks::stdout_color_sink_st, spdlog::sinks::sink>(m, "stdout_color_sink_st")
        .def(nb::init<>())
        .def(nb::init<spdlog::color_mode>(), "mode"_a);

    nb::class_<spdlog::sinks::stderr_color_sink_mt, spdlog::sinks::sink>(m, "stderr_color_sink_mt")
        .def(nb::init<>())
        .def(nb::init<spdlog::color_mode>(), "mode"_a);

    nb::class_<spdlog::sinks::stderr_color_sink_st, spdlog::sinks::sink>(m, "stderr_color_sink_st")
        .def(nb::init<>())
        .def(nb::init<spdlog::color_mode>(), "mode"_a);

    nb::class_<spdlog::sinks::stdout_sink_mt, spdlog::sinks::sink>(m, "stdout_sink_mt")
        .def(nb::init<>());

    nb::class_<spdlog::sinks::stdout_sink_st, spdlog::sinks::sink>(m, "stdout_sink_st")
        .def(nb::init<>());

    nb::class_<spdlog::sinks::stderr_sink_mt, spdlog::sinks::sink>(m, "stderr_sink_mt")
        .def(nb::init<>());

    nb::class_<spdlog::sinks::stderr_sink_st, spdlog::sinks::sink>(m, "stderr_sink_st")
        .def(nb::init<>());

    // Basic file sink
    nb::class_<spdlog::sinks::basic_file_sink_mt, spdlog::sinks::sink>(m, "basic_file_sink_mt")
        .def(nb::init<const std::string&, bool>(),
             "filename"_a, "truncate"_a = false)
        .def("filename", &spdlog::sinks::basic_file_sink_mt::filename);

    nb::class_<spdlog::sinks::basic_file_sink_st, spdlog::sinks::sink>(m, "basic_file_sink_st")
        .def(nb::init<const std::string&, bool>(),
             "filename"_a, "truncate"_a = false)
        .def("filename", &spdlog::sinks::basic_file_sink_st::filename);

    // Rotating file sink
    nb::class_<spdlog::sinks::rotating_file_sink_mt, spdlog::sinks::sink>(m, "rotating_file_sink_mt")
        .def(nb::init<const std::string&, size_t, size_t>(),
             "filename"_a, "max_size"_a, "max_files"_a);

    nb::class_<spdlog::sinks::rotating_file_sink_st, spdlog::sinks::sink>(m, "rotating_file_sink_st")
        .def(nb::init<const std::string&, size_t, size_t>(),
             "filename"_a, "max_size"_a, "max_files"_a);

    // Daily file sink
    nb::class_<spdlog::sinks::daily_file_sink_mt, spdlog::sinks::sink>(m, "daily_file_sink_mt")
        .def(nb::init<const std::string&, int, int>(),
             "filename"_a, "hour"_a = 0, "minute"_a = 0)
        .def("filename", [](spdlog::sinks::daily_file_sink_mt& self) {return self.filename(); });

    nb::class_<spdlog::sinks::daily_file_sink_st, spdlog::sinks::sink>(m, "daily_file_sink_st")
        .def(nb::init<const std::string&, int, int>(),
             "filename"_a, "hour"_a = 0, "minute"_a = 0)
    .def("filename", [](spdlog::sinks::daily_file_sink_st& self) {return self.filename(); });

    // Null sink (no need to register null_sink_mt since they are the same sink)
    nb::class_<spdlog::sinks::null_sink_st, spdlog::sinks::sink>(m, "null_sink_st")
        .def(nb::init<>());

    // Logger class
    nb::class_<spdlog::logger>(m, "logger")
        .def(nb::init<const std::string&>())
        .def(nb::init<const std::string&, spdlog::sink_ptr>(),
             "name"_a, "sink"_a)
        .def("__init__", [](spdlog::logger* logger, const std::string& name, const std::vector<spdlog::sink_ptr>& sinks) {
            new (logger) spdlog::logger(name, sinks.begin(), sinks.end());
        }, "name"_a, "sinks"_a)
        .def("trace", [](spdlog::logger& self, const std::string& msg) { self.trace(msg); })
        .def("debug", [](spdlog::logger& self, const std::string& msg) { self.debug(msg); })
        .def("info", [](spdlog::logger& self, const std::string& msg) { self.info(msg); })
        .def("warn", [](spdlog::logger& self, const std::string& msg) { self.warn(msg); })
        .def("error", [](spdlog::logger& self, const std::string& msg) { self.error(msg); })
        .def("critical", [](spdlog::logger& self, const std::string& msg) { self.critical(msg); })
        .def("log", [](spdlog::logger& self, spdlog::level::level_enum lvl, const std::string& msg) {
            self.log(lvl, msg);
        })
        .def("set_level", &spdlog::logger::set_level)
        .def("level", &spdlog::logger::level)
        .def("name", &spdlog::logger::name)
        .def("set_pattern", &spdlog::logger::set_pattern, "pattern"_a, "time_type"_a = spdlog::pattern_time_type::local)
        .def("flush", &spdlog::logger::flush)
        .def("flush_on", &spdlog::logger::flush_on)
        .def("sinks", [](spdlog::logger& self) { return self.sinks(); }, nb::rv_policy::reference_internal)
        .def("should_log", &spdlog::logger::should_log)
        .def("clone", &spdlog::logger::clone);

    // Async logger
    nb::class_<spdlog::async_logger, spdlog::logger>(m, "_async_logger");

    m.def("async_logger", [](const std::string& name, spdlog::sink_ptr& sink) {
        return std::make_shared<spdlog::async_logger>(name, sink, g_thread_pool_ptr, spdlog::async_overflow_policy::block);
    }, "name"_a, "sink"_a);

    m.def("async_logger", [](const std::string& name,
                             const std::vector<spdlog::sink_ptr>& sinks) {
        return std::make_shared<spdlog::async_logger>(name, sinks.begin(), sinks.end(), g_thread_pool_ptr, spdlog::async_overflow_policy::block);
    }, "name"_a, "sinks"_a);

    // Global logger functions
    m.def("set_level", &spdlog::set_level);
    m.def("get_level", &spdlog::get_level);
    m.def("flush_on", &spdlog::flush_on);
    m.def("flush_every", [](int milliseconds) {
        spdlog::flush_every(std::chrono::milliseconds(milliseconds));
    }, "milliseconds"_a);
    m.def("set_pattern", &spdlog::set_pattern, "pattern"_a, "time_type"_a = spdlog::pattern_time_type::local);

    // Global logging functions
    m.def("trace", [](const std::string& msg) { spdlog::trace(msg); });
    m.def("debug", [](const std::string& msg) { spdlog::debug(msg); });
    m.def("info", [](const std::string& msg) { spdlog::info(msg); });
    m.def("warn", [](const std::string& msg) { spdlog::warn(msg); });
    m.def("error", [](const std::string& msg) { spdlog::error(msg); });
    m.def("critical", [](const std::string& msg) { spdlog::critical(msg); });

    // Logger registry
    m.def("set_default_logger", &spdlog::set_default_logger);
    m.def("default_logger", &spdlog::default_logger);
    m.def("get", &spdlog::get, "name"_a);
    m.def("drop", &spdlog::drop, "name"_a);
    m.def("drop_all", &spdlog::drop_all);
    m.def("register_logger", &spdlog::register_logger);
    m.def("apply_all", [](const std::function<void(std::shared_ptr<spdlog::logger>)>& fun) {
        spdlog::apply_all(fun);
    });

    // Async overflow policy enum
    nb::enum_<spdlog::async_overflow_policy>(m, "async_overflow_policy")
        .value("block", spdlog::async_overflow_policy::block)
        .value("overrun_oldest", spdlog::async_overflow_policy::overrun_oldest);

    // Factory functions for common logger types
    m.def("stdout_color_mt", [](const std::string& logger_name, spdlog::color_mode mode) {
        return spdlog::stdout_color_mt(logger_name, mode);
    }, "logger_name"_a, "mode"_a = spdlog::color_mode::automatic);

    m.def("stdout_color_st", [](const std::string& logger_name, spdlog::color_mode mode) {
        return spdlog::stdout_color_st(logger_name, mode);
    }, "logger_name"_a, "mode"_a = spdlog::color_mode::automatic);

    m.def("stderr_color_mt", [](const std::string& logger_name, spdlog::color_mode mode) {
        return spdlog::stderr_color_mt(logger_name, mode);
    }, "logger_name"_a, "mode"_a = spdlog::color_mode::automatic);

    m.def("stderr_color_st", [](const std::string& logger_name, spdlog::color_mode mode) {
        return spdlog::stderr_color_st(logger_name, mode);
    }, "logger_name"_a, "mode"_a = spdlog::color_mode::automatic);

    m.def("stdout_logger_mt", [](const std::string& logger_name) { return spdlog::stdout_logger_mt(logger_name); });
    m.def("stdout_logger_st", [](const std::string& logger_name) { return spdlog::stdout_logger_st(logger_name); });
    m.def("stderr_logger_mt", [](const std::string& logger_name) { return spdlog::stderr_logger_mt(logger_name); });
    m.def("stderr_logger_st", [](const std::string& logger_name) { return spdlog::stderr_logger_st(logger_name); });

    m.def("basic_logger_mt", [](const std::string& logger_name, const std::string& filename, bool truncate) {
        return spdlog::basic_logger_mt(logger_name, filename, truncate);
    }, "logger_name"_a, "filename"_a, "truncate"_a = false);

    m.def("basic_logger_st", [](const std::string& logger_name, const std::string& filename, bool truncate) {
        return spdlog::basic_logger_st(logger_name, filename, truncate);
    }, "logger_name"_a, "filename"_a, "truncate"_a = false);

    m.def("rotating_logger_mt", [](const std::string& logger_name, const std::string& filename,
                                    size_t max_size, size_t max_files) {
        return spdlog::rotating_logger_mt(logger_name, filename, max_size, max_files);
    }, "logger_name"_a, "filename"_a, "max_size"_a, "max_files"_a);

    m.def("rotating_logger_st", [](const std::string& logger_name, const std::string& filename,
                                    size_t max_size, size_t max_files) {
        return spdlog::rotating_logger_st(logger_name, filename, max_size, max_files);
    }, "logger_name"_a, "filename"_a, "max_size"_a, "max_files"_a);

    m.def("daily_logger_mt", [](const std::string& logger_name, const std::string& filename,
                                 int hour, int minute) {
        return spdlog::daily_logger_mt(logger_name, filename, hour, minute);
    }, "logger_name"_a, "filename"_a, "hour"_a = 0, "minute"_a = 0);

    m.def("daily_logger_st", [](const std::string& logger_name, const std::string& filename,
                                 int hour, int minute) {
        return spdlog::daily_logger_st(logger_name, filename, hour, minute);
    }, "logger_name"_a, "filename"_a, "hour"_a = 0, "minute"_a = 0);
}
