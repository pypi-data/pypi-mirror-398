# Recipes SDK

Python SDK for working with recipes from JSON file.

## Installation

```bash
pip install -r requirements.txt
```

## Usage

```python
from recipes_sdk import RecipesSDK

# Create SDK instance
sdk = RecipesSDK(language="en")  # or "ru"

# Random recipe
recipe = sdk.get_random_recipe()

# With allergens and calories filtering
recipe = sdk.get_random_recipe(
    user_allergens=["nuts", "gluten"], 
    max_calories=300
)

# By category
breakfast = sdk.get_recipes_by_category("breakfast")
```

## API

- `get_random_recipe()` - random recipe (returns JSON)
- `get_recipes_by_category(category)` - all recipes from category (returns JSON)
- `get_random_recipe_by_category(category)` - random recipe from category (returns JSON)
- `get_all_categories()` - list of categories (returns JSON)
- `get_all_recipes()` - all recipes (returns JSON)

All methods support filtering by allergens and calories.