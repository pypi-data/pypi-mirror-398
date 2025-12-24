# BlizzardAPI v3

A modern, config-driven Python wrapper for the Blizzard API with full async support, type safety via Pydantic, and comprehensive error handling.

## Table of Contents

- [Features](#features)
- [Installation](#installation)
- [Quick Start](#quick-start)
- [Using Search Endpoints](#using-search-endpoints)
- [Error Handling](#error-handling)
- [Comprehensive Examples](#comprehensive-examples)
- [Supported Games](#supported-games)
- [Documentation](#documentation)
- [Development](#development)
- [Architecture](#architecture)

## Features

- 🚀 **Async/Await Support** - First-class async support with both sync and async methods
- 🔒 **Type Safety** - Full Pydantic models with IDE autocomplete
- 📝 **Config-Driven** - YAML-defined endpoints, easy to extend
- 🎯 **Better Errors** - Specific exception types with detailed context
- ⚡ **Efficient** - Single session management, proper resource cleanup
- 🎮 **Complete Coverage** - Supports WoW, Diablo 3, Hearthstone, and StarCraft 2

## Installation

```bash
pip install blizzardapi3
```

## Quick Start

### Synchronous Usage

```python
from blizzardapi3 import BlizzardAPI

# Use context manager for proper cleanup
with BlizzardAPI(client_id="your_id", client_secret="your_secret") as api:
    # Get WoW achievement
    achievement = api.wow.game_data.get_achievement(
        region="us",
        locale="en_US",
        achievement_id=6
    )
    print(achievement["name"]["en_US"])
```

### Asynchronous Usage

```python
import asyncio
from blizzardapi3 import BlizzardAPI

async def main():
    async with BlizzardAPI(client_id="your_id", client_secret="your_secret") as api:
        # Async methods end with _async
        achievement = await api.wow.game_data.get_achievement_async(
            region="us",
            locale="en_US",
            achievement_id=6
        )
        print(achievement["name"]["en_US"])

asyncio.run(main())
```

## Using Search Endpoints

BlizzardAPI v3 provides powerful search functionality for various game resources. Search methods accept flexible keyword arguments for filtering and pagination.

### Basic Search

```python
from blizzardapi3 import BlizzardAPI, Region, Locale

with BlizzardAPI(client_id, client_secret) as api:
    # Search for decor items containing "wall"
    results = api.wow.game_data.search_decor(
        region=Region.US,
        locale=Locale.EN_US,
        **{"name.en_US": "wall"}
    )

    print(f"Found {len(results['results'])} items")
    for item in results['results']:
        data = item['data']
        print(f"{data['name']['en_US']} (ID: {data['id']})")
```

### Pagination and Ordering

```python
with BlizzardAPI(client_id, client_secret) as api:
    # Get first page, ordered by ID
    results = api.wow.game_data.search_decor(
        region=Region.US,
        locale=Locale.EN_US,
        orderby="id",
        _page=1
    )

    print(f"Page {results['page']} of {results['pageCount']}")
    print(f"Results per page: {results['pageSize']}")
```

### Advanced Filtering

Search endpoints support locale-specific filtering using dot notation:

```python
with BlizzardAPI(client_id, client_secret) as api:
    # Search with multiple filters
    results = api.wow.game_data.search_decor(
        region=Region.US,
        locale=Locale.EN_US,
        **{
            "name.en_US": "mirror",
            "orderby": "id:desc",
            "_page": 1
        }
    )
```

### Available Search Methods

#### World of Warcraft Game Data

- `search_azerite_essence()` - Search azerite essences
- `search_covenant()` - Search covenants
- `search_creature()` - Search creatures
- `search_decor()` - Search housing decor items
- `search_item()` - Search items
- `search_media()` - Search media assets
- `search_mount()` - Search mounts
- `search_pet()` - Search battle pets
- `search_profession()` - Search professions
- `search_spell()` - Search spells

### Common Search Parameters

| Parameter       | Description              | Example              |
| --------------- | ------------------------ | -------------------- |
| `name.{locale}` | Filter by localized name | `name.en_US: "wall"` |
| `orderby`       | Sort results             | `"id"`, `"id:desc"`  |
| `_page`         | Page number (1-indexed)  | `1`, `2`, `3`        |

### Search Response Structure

```python
{
    "page": 1,
    "pageSize": 100,
    "maxPageSize": 100,
    "pageCount": 10,
    "results": [
        {
            "key": {"href": "..."},
            "data": {
                "id": 534,
                "name": {"en_US": "Plain Interior Wall"},
                # ... additional fields
            }
        }
    ]
}
```

## Error Handling

```python
from blizzardapi3 import BlizzardAPI
from blizzardapi3.exceptions import NotFoundError, RateLimitError

with BlizzardAPI(client_id, client_secret) as api:
    try:
        data = api.wow.game_data.get_achievement(
            region="us",
            locale="en_US",
            achievement_id=999999
        )
    except NotFoundError:
        print("Achievement not found")
    except RateLimitError as e:
        print(f"Rate limited. Retry after {e.retry_after} seconds")
```

## Comprehensive Examples

### Character Profile Information

```python
from blizzardapi3 import BlizzardAPI, Region, Locale

with BlizzardAPI(client_id, client_secret) as api:
    # Get character appearance
    appearance = api.wow.profile.get_character_appearance_summary(
        region=Region.US,
        locale=Locale.EN_US,
        realm_slug="illidan",
        character_name="beyloc"
    )

    print(f"Character: {appearance['character']['name']}")
    print(f"Race: {appearance['playable_race']['name']}")
    print(f"Class: {appearance['playable_class']['name']}")
    print(f"Spec: {appearance['active_spec']['name']}")

    # Get character equipment
    equipment = api.wow.profile.get_character_equipment_summary(
        region=Region.US,
        locale=Locale.EN_US,
        realm_slug="illidan",
        character_name="beyloc"
    )

    for item in equipment['equipped_items']:
        print(f"{item['slot']['name']}: {item['name']}")
```

### Building a Decor Browser

```python
from blizzardapi3 import BlizzardAPI, Region, Locale

def search_decor_by_name(api, search_term, page=1):
    """Search for decor items by name with pagination."""
    results = api.wow.game_data.search_decor(
        region=Region.US,
        locale=Locale.EN_US,
        **{
            "name.en_US": search_term,
            "orderby": "id",
            "_page": page
        }
    )

    items = []
    for result in results['results']:
        data = result['data']
        items.append({
            'id': data['id'],
            'name': data['name']['en_US'],
            'href': result['key']['href']
        })

    return {
        'items': items,
        'page': results['page'],
        'total_pages': results['pageCount'],
        'has_more': results['page'] < results['pageCount']
    }

with BlizzardAPI(client_id, client_secret) as api:
    # Search for walls
    result = search_decor_by_name(api, "wall", page=1)

    for item in result['items']:
        print(f"{item['name']} (ID: {item['id']})")

    if result['has_more']:
        print(f"\nShowing page {result['page']} of {result['total_pages']}")
```

### Item Search with Filtering

```python
with BlizzardAPI(client_id, client_secret) as api:
    # Search for epic quality items
    items = api.wow.game_data.search_item(
        region=Region.US,
        locale=Locale.EN_US,
        **{
            "name.en_US": "sword",
            "orderby": "id:desc",
            "_page": 1
        }
    )

    for result in items['results'][:10]:
        item = result['data']
        print(f"{item['name']['en_US']} (ID: {item['id']})")
```

### Async Batch Operations

```python
import asyncio
from blizzardapi3 import BlizzardAPI, Region, Locale

async def get_multiple_achievements(api, achievement_ids):
    """Fetch multiple achievements concurrently."""
    tasks = [
        api.wow.game_data.get_achievement_async(
            region=Region.US,
            locale=Locale.EN_US,
            achievement_id=aid
        )
        for aid in achievement_ids
    ]
    return await asyncio.gather(*tasks)

async def main():
    async with BlizzardAPI(client_id, client_secret) as api:
        achievement_ids = [6, 7, 8, 9, 10]
        achievements = await get_multiple_achievements(api, achievement_ids)

        for ach in achievements:
            print(f"{ach['name']} - {ach['points']} points")

asyncio.run(main())
```

### Guild Information

```python
with BlizzardAPI(client_id, client_secret) as api:
    # Get guild roster
    roster = api.wow.profile.get_guild_roster(
        region=Region.US,
        locale=Locale.EN_US,
        realm_slug="illidan",
        name_slug="your-guild-name"
    )

    for member in roster['members']:
        char = member['character']
        print(f"{char['name']} - Level {char['level']} {char.get('playable_class', {}).get('name', 'Unknown')}")
```

## Supported Games

- **World of Warcraft** - Game Data & Profile APIs (208 endpoints)
  - Game Data: Achievements, Items, Mounts, Pets, Auctions, Housing/Decor, and more
  - Profile: Characters, Guilds, Mythic+, PvP, Collections, Equipment
- **Diablo 3** - Community & Game Data APIs (24 endpoints)
- **Hearthstone** - Game Data API (8 endpoints)
- **StarCraft 2** - Community & Game Data APIs (11 endpoints)

**Total: 242 endpoints**

## Documentation

### Core Documentation

- **[Search Guide](docs/SEARCH_GUIDE.md)** - Comprehensive guide to using search endpoints with real-world examples
- **[Search Quick Reference](docs/SEARCH_QUICK_REFERENCE.md)** - Quick reference for all search methods and parameters
- **[OAuth Guide](docs/OAUTH_GUIDE.md)** - Complete guide to OAuth authorization code flow for user-specific endpoints
- **[Migration Guide](MIGRATION.md)** - Detailed guide for migrating from blizzardapi2

### Additional Resources

- [Blizzard API Official Documentation](https://develop.battle.net/documentation)
- [GitHub Repository](https://github.com/lostcol0ny/blizzardapi3)
- [Issue Tracker](https://github.com/lostcol0ny/blizzardapi3/issues)

## Migration from v2

See [MIGRATION.md](MIGRATION.md) for a detailed guide on migrating from blizzardapi2.

## Development

```bash
# Clone the repository
git clone https://github.com/lostcol0ny/blizzardapi3.git
cd blizzardapi3

# Install development dependencies
pip install -e ".[dev]"

# Run tests
pytest

# Format code
black .
ruff check .
```

## Architecture

BlizzardAPI v3 uses a config-driven architecture:

- **YAML Endpoint Definitions** - All API endpoints defined in YAML configs
- **Dynamic Method Generation** - Methods generated at runtime from configs
- **Pydantic Models** - Type-safe response models
- **Custom Exceptions** - Detailed error hierarchy
- **Single Session** - Efficient session management with proper cleanup

## License

MIT License - see [LICENSE](LICENSE) for details
