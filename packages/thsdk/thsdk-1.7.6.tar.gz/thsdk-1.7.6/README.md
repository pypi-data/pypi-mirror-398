## Installation

```bash
pip install --upgrade thsdk
```

## Quick Start

```python
from thsdk import THS

with THS() as ths:
    print(ths.klines("USZA300033", count=100).df)
```

