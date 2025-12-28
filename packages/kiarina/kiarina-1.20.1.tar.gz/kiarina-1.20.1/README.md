# kiarina

[![Python](https://img.shields.io/badge/python-3.12%2B-blue.svg)](https://www.python.org/downloads/)
[![PyPI version](https://badge.fury.io/py/kiarina.svg)](https://badge.fury.io/py/kiarina)
[![License](https://img.shields.io/badge/license-MIT-blue.svg)](https://github.com/kiarina/kiarina-python/blob/main/LICENSE)

> 🐍 **kiarina's Python utility collection** - A comprehensive namespace package collection providing essential utilities for modern Python development.

## 🚀 Quick Install

Install all kiarina packages with a single command:

```bash
pip install kiarina
```

This meta-package installs all kiarina utilities:

- **kiarina-i18n** - Simple internationalization (i18n) utilities
- **kiarina-utils-common** - Common utilities and helper functions
- **kiarina-utils-file** - Advanced file I/O operations with encoding detection
- **kiarina-lib-anthropic** - Anthropic API integration utilities
- **kiarina-lib-cloudflare-auth** - Cloudflare authentication utilities
- **kiarina-lib-cloudflare-d1** - Cloudflare D1 database integration
- **kiarina-lib-falkordb** - FalkorDB integration utilities
- **kiarina-lib-google-auth** - Google Cloud authentication utilities
- **kiarina-lib-google-cloud-storage** - Google Cloud Storage integration
- **kiarina-lib-openai** - OpenAI API integration utilities
- **kiarina-lib-redis** - Redis integration with configuration management
- **kiarina-lib-redisearch** - RediSearch integration and query builders
- **kiarina-llm** - LLM integration utilities

## 📖 Usage

After installation, you can use any kiarina package:

```python
# Configuration parsing
from kiarina.utils.common import parse_config_string
config = parse_config_string("app.debug:true,db.port:5432")

# File operations with encoding detection
import kiarina.utils.file as kf
blob = kf.read_file("document.txt")  # Auto-detects encoding
data = kf.read_json_dict("config.json", default={})

# Async file operations
import kiarina.utils.file.asyncio as kfa
blob = await kfa.read_file("large_file.dat")

# Redis integration
from kiarina.lib.redis import create_redis_client
redis = create_redis_client("redis://localhost:6379")
```

## 🎯 Individual Package Installation

If you only need specific functionality, you can install individual packages:

```bash
# Core utilities only
pip install kiarina-utils-common kiarina-utils-file

# Database libraries
pip install kiarina-lib-redis kiarina-lib-falkordb kiarina-lib-redisearch

# LLM utilities
pip install kiarina-llm
```

## 📚 Documentation

For detailed documentation, examples, and API reference, visit the main repository:

**[📖 Full Documentation](https://github.com/kiarina/kiarina-python#readme)**

## 🤝 Contributing

This is primarily a personal project, but contributions are welcome! Visit the [main repository](https://github.com/kiarina/kiarina-python) for contribution guidelines.

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](https://github.com/kiarina/kiarina-python/blob/main/LICENSE) file for details.

---

<div align="center">

**Made with ❤️ by [kiarina](https://github.com/kiarina)**

*Building better Python utilities, one package at a time.*

</div>
