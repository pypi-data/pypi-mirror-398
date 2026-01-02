from iker.common.utils import logger
from iker.common.utils.config import Config
from iker.common.utils.funcutils import memorized
from iker.common.utils.shutils import expanded_path


@memorized()
def config(config_path: str = "") -> Config:
    default_items: list[tuple[str, str, str]] = [
        ("plexus", "logging.level", "INFO"),
        ("plexus", "logging.format", "%(asctime)s [%(levelname)s] %(name)s: %(message)s"),
    ]

    instance = Config(config_path or expanded_path("~/.plexus.cfg"))
    instance.restore()
    instance.update(default_items, overwrite=False)

    return instance


def config_print_or_set(config: Config, section: str, key: str, value: str):
    if value is not None:
        if section is None or key is None:
            raise ValueError("cannot specify value without section and key")

        old_value = config.get(section, key)
        config.set(section, key, value)
        config.persist()

        print(f"Configuration file '{config.config_path}'", )
        print(f"Section <{section}>")
        print(f"  {key} = {old_value} -> {value}")

    else:
        if section is None and key is None:
            print(f"Configuration file '{config.config_path}'", )
            for section in config.config_parser.sections():
                print(f"Section <{section}>")
                for key, value in config.config_parser.items(section):
                    print(f"  {key} = {value}")

        elif section is not None and key is None:
            if not config.has_section(section):
                logger.warning("Configuration section <%s> not found", section)
                return
            print(f"Configuration file '{config.config_path}'", )
            print(f"Section <{section}>")
            for key, value in config.config_parser.items(section):
                print(f"  {key} = {value}")

        elif section is not None and key is not None:
            value = config.get(section, key)
            if value is None:
                logger.warning("Configuration section <%s> key <%s> not found", section, key)
                return
            print(f"Configuration file '{config.config_path}'", )
            print(f"Section <{section}>")
            print(f"  {key} = {value}")

        else:
            raise ValueError("cannot specify key without section")
