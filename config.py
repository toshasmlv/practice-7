from configparser import ConfigParser


def load_config(filename='database.ini', section='postgresql'):
    """Read database configuration from a .ini file."""
    parser = ConfigParser()
    parser.read(filename)

    config = {}
    if parser.has_section(section):
        for param in parser.items(section):
            config[param[0]] = param[1]
    else:
        raise Exception(
            f'Section [{section}] not found in {filename}.\n'
            'Please create database.ini with your PostgreSQL credentials.'
        )
    return config


if __name__ == '__main__':
    cfg = load_config()
    print('Loaded config:', cfg)