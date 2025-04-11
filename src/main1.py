from dotenv import load_dotenv
from portia import (
    Config,
    LogLevel,
    Portia,
    StorageClass,
)
from portia.open_source_tools.registry import example_tool_registry


load_dotenv()

my_config = Config.from_default(
    storage_class=StorageClass.DISK,
    storage_dir="demo_runs",
    default_log_level=LogLevel.DEBUG,
)

portia = Portia(config=my_config, tools=example_tool_registry)

output = portia.run('Which stock price grew faster in 2024, Amazon or Google?')

print(output.model_dump_json(indent=2))

