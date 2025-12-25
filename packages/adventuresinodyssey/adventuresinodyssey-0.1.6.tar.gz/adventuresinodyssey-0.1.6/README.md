Unofficial Python API clients for the Adventures in Odyssey Club and website. This library allows you to interact with AIO content, including retrieving metadata for albums and episodes.

**Note:** This is an Alpha release. APIs may change.

[Documentation](https://github.com/CATEIN/adventuresinodyssey-py/blob/main/docs/docs.md)

[Github](https://github.com/CATEIN/adventuresinodyssey-py)

### Important: Browser Requirement

`ClubClient`uses Playwright for authentication. Install the required browser binaries (Chromium):

```bash
playwright install chromium
```

## Example Program
```python
import random
from adventuresinodyssey import AIOClient

client = AIOClient()
link_base = "https://app.adventuresinodyssey.com/content/"

print("Caching episodes...")
all_episodes = client.cache_episodes()

if not all_episodes:
    print("Error: Failed to cache episodes.")
    exit()

# Pick a random episode
episode = random.choice(all_episodes)

print(f"Random episode: {episode.get('short_name')}")
print(f"Link: {link_base}{episode.get('id')}")
```
