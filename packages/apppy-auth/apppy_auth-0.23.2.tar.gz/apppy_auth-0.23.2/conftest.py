def pytest_configure(config):
    config.pluginmanager.import_plugin("apppy.auth.fixtures")
    config.pluginmanager.import_plugin("apppy.env.fixtures")
    config.pluginmanager.import_plugin("apppy.fs.fixtures")
