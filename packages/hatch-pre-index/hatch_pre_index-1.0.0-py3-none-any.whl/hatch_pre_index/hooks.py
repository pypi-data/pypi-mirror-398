from hatchling.plugin import hookimpl
from hatch_pre_index.pre_index_publisher import PreIndexPublisher

@hookimpl
def hatch_register_publisher():
    return PreIndexPublisher
