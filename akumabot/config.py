from ConfigParser import RawConfigParser, NoSectionError, NoOptionError



REQUIRED = object()


def get(parser, section, option, default):
    return _get(parser.get, section, option, default)


def get_boolean(parser, section, option, default):
    return _get(parser.getboolean, section, option, default)


def get_list(parser, section, option, default):
    value = _get(parser.get, section, option, default)
    return [chunk for chunk in value.split() if chunk]


def get_set(parser, section, option, default):
    return set(get_list(parser, section, option, default))


def _get(getmethod, section, option, default):
    try:
        return getmethod(section, option)
    except (NoSectionError, NoOptionError):
        if default is REQUIRED:
            raise
        else:
            return default

# Map of (section, option) or (section, option, default) tuples to
# get_* functions.
options = {
    ('akumabot', 'nickname'): get,
    ('akumabot', 'password'): get,
    ('akumabot', 'channels'): get_list,
    ('akumabot', 'admins'): get_set,
    ('akumabot', 'debug', False): get_boolean,
    ('commands', 'trigger', '<nick>'): get,
}


def process_config_file(config_file):
    parser = RawConfigParser()
    parser.readfp(config_file)
    config = {}
    for opt_sec_def, getfunc in options.items():
        default = REQUIRED
        if len(opt_sec_def) == 2:
            section, option = opt_sec_def
        else:
            section, option, default = opt_sec_def
        confkey = '{0}.{1}'.format(section, option)
        config[confkey] = getfunc(parser, section, option, default)
    return config
