
#!/usr/bin/env python
#
# -----------------------------------------------------------------------------

from .basic_io              import BasicIO
from .value_io              import ValueIO

from .transportable         import Transportable
from .transport_descriptor  import TransportDescriptor

from .marshal_stream        import MarshalStream
from .unmarshal_stream      import UnmarshalStream

from .deep_clone            import DeepClone


# -----------------------------------------------------------------------------
"""
Quick design note (important):

Right now BasicIO.insert(...) writes directly into a provided bytearray. With this MarshalStream, the intended usage is:

* call reserve(n)
* write into stream.get_buffer()[pos:pos+n]
* call deliver(n)

When we port real transport code, we can add helper methods like write_int, write_double, etc., but I’d keep this minimal for now to match Java’s surface API.
"""