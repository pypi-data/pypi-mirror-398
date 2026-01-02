//
// Copyright © 2025 Jonatan Nevo.
// Distributed under the MIT license (see LICENSE file).
//

#include <portal/engine/settings.h>
#include <portal/engine/engine.h>

#include <portal/application/application.h>
#include <portal/application/entry_point.h>

using namespace portal;

constexpr auto LOG_LEVEL_ENTRY = "log-level";

void initialize_settings()
{
    Settings::init(SettingsArchiveType::Json, "settings.json");
}

void initialize_logger()
{
    auto log_level_string = Settings::get().get_setting<std::string>(LOG_LEVEL_ENTRY);
    if (log_level_string)
    {
        const auto log_level = portal::from_string<Log::LogLevel>(*log_level_string);
        Log::set_default_log_level(log_level);
    }
    Settings::get().debug_print();
}

ApplicationProperties make_application_properties()
{
    auto& settings = Settings::get();

    const auto name = settings.get_setting<std::string>("name");
    const auto width = settings.get_setting<size_t>("application.window.width");
    const auto height = settings.get_setting<size_t>("application.window.height");

    return ApplicationProperties{
        .name = STRING_ID(name.value()),
        .width = width.value(),
        .height = height.value()
    };
}

std::unique_ptr<Application> portal::create_application(int, char**)
{
    initialize_settings();
    initialize_logger();

    const auto prop = make_application_properties();
    auto engine = std::make_unique<Engine>(prop);

    return engine;
}
