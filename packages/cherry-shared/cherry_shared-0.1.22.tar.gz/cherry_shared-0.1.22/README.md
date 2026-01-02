# Cherry Shared

Cherry Bot shared utilities package.

## Installation

This is a private package. Install it directly from the Git repository:

### Using HTTPS (requires authentication)

```bash
pip install git+https://github.com/YOUR_USERNAME/cherry_shared.git@main#egg=cherry_shared
```

For private repositories, you'll need to authenticate. You can use a personal access token:

```bash
pip install git+https://YOUR_TOKEN@github.com/YOUR_USERNAME/cherry_shared.git@main#egg=cherry_shared
```

### Using SSH (recommended for private repos)

```bash
pip install git+ssh://git@github.com/YOUR_USERNAME/cherry_shared.git@main#egg=cherry_shared
```

### Installing a specific version/tag

```bash
pip install git+ssh://git@github.com/YOUR_USERNAME/cherry_shared.git@v0.1.1#egg=cherry_shared
```

### Installing from a requirements.txt

Add this line to your `requirements.txt`:

```
git+ssh://git@github.com/YOUR_USERNAME/cherry_shared.git@main#egg=cherry_shared
```

Then install with:

```bash
pip install -r requirements.txt
```

## Development Installation

For development, install in editable mode:

```bash
pip install -e git+ssh://git@github.com/YOUR_USERNAME/cherry_shared.git@main#egg=cherry_shared
```

Or clone the repository and install locally:

```bash
git clone git@github.com:YOUR_USERNAME/cherry_shared.git
cd cherry_shared
pip install -e .
```

## Usage

```python
from cherry_shared import Blockchains, BotStrings, Constants, Emojis, LaunchPads
```

