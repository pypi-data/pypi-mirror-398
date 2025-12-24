# Spotify Backup Helper

[![PyPI version](https://badge.fury.io/py/spotify-backup-helper.svg)](https://badge.fury.io/py/spotify-backup-helper)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Downloads](https://static.pepy.tech/static/bash-version-badge.svg)](https://pepy.tech/project/spotify-backup-helper)
[![LinkedIn](https://img.shields.io/badge/LinkedIn-Eugene%20Evstafev-blue)](https://www.linkedin.com/in/eugene-evstafev-417196146/)

A package that helps Spotify users securely back up their music library.

## Overview

By accepting simple text inputs that describe a user's playlists, liked tracks, and saved albums, the tool generates a clean, structured response—such as a JSON-formatted backup plan—detailing what data should be exported, how to organize it, and step-by-step instructions for safely storing the information.

## Installation

```bash
pip install spotify-backup-helper
```

## Usage

```python
from spotify-backup-helper import spotify_backup_helper

user_input = "Backup my favorite artists and albums"
response = spotify_backup_helper(user_input)
print(response)
```

You can also pass your own LLM instance (e.g. OpenAI, Anthropic, Google GenAI) by passing it to the function:

```python
from langchain_openai import ChatOpenAI
from spotify-backup-helper import spotify_backup_helper

llm = ChatOpenAI()
response = spotify_backup_helper(user_input, llm=llm)
print(response)
```

If you want to use higher rate limits for LLM7, you can pass your own API key via environment variable `LLM7_API_KEY` or directly to the function:

```python
os.environ['LLM7_API_KEY'] = 'your_api_key'
response = spotify_backup_helper(user_input)
```

or

```python
response = spotify_backup_helper(user_input, api_key='your_api_key')
```

You can get a free API key by registering at [https://token.llm7.io/](https://token.llm7.io/)

## Developer Info

Author: Eugene Evstafev
Author email: hi@eugene.plus
GitHub: https://github.com/chigwell

## License

MIT License

Copyright (c) 2023 Eugene Evstafev

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.

[![GitHub issues](https://img.shields.io/github/issues/chigwell/spotify-backup-helper)](https://github.com/chigwell/spotify-backup-helper/issues)