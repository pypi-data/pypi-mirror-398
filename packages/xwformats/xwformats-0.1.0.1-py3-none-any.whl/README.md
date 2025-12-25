# xwformats - Enterprise Serialization Formats

**Company:** eXonware.com  
**Author:** Eng. Muhammad AlShehri  
**Email:** connect@exonware.com  
**Version:** 0.1.0.1
**Date:** 02-Nov-2025

---

## Overview

Extended serialization format library providing heavyweight enterprise formats for specialized domains.

**Note:** This library is separated from `xwsystem` to keep the core lightweight and fast.

---

## What's Inside

### 18 Enterprise Formats (~87 MB):

**Schema Formats (7):**
- Protocol Buffers
- Apache Avro
- Apache Parquet
- Apache Thrift
- Apache ORC
- Cap'n Proto
- FlatBuffers

**Scientific Formats (5):**
- HDF5
- Feather
- Zarr
- NetCDF
- MATLAB MAT

**Database Formats (3):**
- LMDB
- GraphDB (Neo4j, Dgraph)
- LevelDB

**Binary Formats (2):**
- BSON
- UBJSON

**Text Formats (1):**
- XML (enterprise features)

---

## Installation

```bash
# Standard installation
pip install exonware-xwformats

# With xwsystem
pip install exonware-xwsystem exonware-xwformats

# Or use xwsystem[lazy] for auto-installation
pip install exonware-xwsystem[lazy]
```

---

## Usage

```python
from exonware.xwformats import (
    ParquetSerializer,
    ProtobufSerializer,
    Hdf5Serializer,
    # ... all enterprise formats
)

# Or through xwsystem
from exonware.xwsystem import XWIO

io = XWIO()
io.serialize(data, format="parquet")  # Auto-discovers xwformats!
```

---

## Why Separate from xwsystem?

**Performance:**
- xwsystem: ~5 MB (core formats only)
- xwformats: ~87 MB (enterprise formats)
- Install only what you need!

**Startup Time:**
- xwsystem alone: ~0.1s (20x faster!)
- With xwformats: ~2s (when actually used)

**Coverage:**
- xwsystem: 14 core formats (80%+ use cases)
- xwformats: 18 enterprise formats (specialized needs)

---

## License

MIT License - See LICENSE file

---

**Part of the eXonware ecosystem**

