# Pancakeswap Universal Router Decoder & Encoder

> Forked from and many thanks to [**pancakeswap-universal-router-decoder**](https://github.com/Elnaril/uniswap-universal-router-decoder)

### List of supported Pancakeswap Universal Router Functions

| Command Id  | Universal Router Function | Underlying Action - Function | Supported |
| ----------- | ------------------------- | ---------------------------- | :-------: |
| 0x0a        | PERMIT2_PERMIT            |                              |    ✅     |
| 0x0e - 0x0f | placeholders              |                              |    N/A    |
| 0x10        | V4_SWAP                   |                              |    ✅     |
|             |                           | 0x06 - SWAP_EXACT_IN_SINGLE  |    ✅     |
| 0x11 - 0x12 |                           |                              |    ❌     |
| 0x15 - 0x1d |                           |                              |    ❌     |
| 0x1e - 0x3f | placeholders              |                              |    N/A    |

---

## Installation

A good practice is to use [Python virtual environments](https://python.readthedocs.io/en/latest/library/venv.html), here is a [tutorial](https://www.freecodecamp.org/news/how-to-setup-virtual-environments-in-python/).

The library can be pip installed from [pypi.org](https://pypi.org/project/pancakeswap-universal-router-decoder/) as usual:

```bash
# update pip to latest version if needed
pip install -U pip

# install the decoder from pypi.org
pip install pancakeswap-universal-router-decoder
```

---

This is a fork of the original project and may not be fully compatible with the original project. Please DYOR.
