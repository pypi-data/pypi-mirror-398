# Grabpy

Simple respectful web scraper

## INSTALLING

How to install Grabpy.

```bash
pip install grabpy
```

## USING

How to use Grabpy to fetch pages or download content.

```python
from grabpy import Grabber

with Grabber('useragent/0.1', retries=3) as grabber:
    content = grabber.get('https://www.example.org')
    
    if grabber.download('https://www.example.org/music.mp3', 'music.mp3'):
        print('Download successful.')
    else:
        print('Download failed.')
```

## LOGGING

How to enable logging for this package.

```python
import logging

logging.basicConfig(level=logging.DEBUG)
logging.getLogger('grabpy').setLevel(logging.DEBUG)
logging.getLogger().setLevel(logging.WARNING)
```
