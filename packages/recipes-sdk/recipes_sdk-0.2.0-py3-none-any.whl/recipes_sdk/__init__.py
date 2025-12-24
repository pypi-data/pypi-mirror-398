import json
import random
from typing import List, Dict, Optional, Union
from pathlib import Path


class RecipesSDK:
    def __init__(self, language: str = "en"):
        self.language = language
        self.recipes = self._load_recipes()
    
    def _load_recipes(self) -> Dict:
        categories = ['breakfast', 'snack', 'lunch', 'dinner']
        recipes = {}
        base_path = Path(__file__).parent
        for category in categories:
            file_path = base_path / f"{category}.json"
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                recipes[category] = data[category]
        return recipes
    
    def _filter_by_allergens(self, recipes: List[Dict], user_allergens: List[str]) -> List[Dict]:
        if not user_allergens:
            return recipes
        
        filtered = []
        for recipe in recipes:
            recipe_allergens = recipe.get('allergens', {}).get(self.language, [])
            if not any(allergen in recipe_allergens for allergen in user_allergens):
                filtered.append(recipe)
        return filtered
    
    def _filter_by_calories(self, recipes: List[Dict], max_calories: Optional[int]) -> List[Dict]:
        if max_calories is None:
            return recipes
        return [recipe for recipe in recipes if recipe['calories'] <= max_calories]
    
    def get_random_recipe(self, user_allergens: List[str] = None, max_calories: Optional[int] = None) -> str:
        all_recipes = []
        for category in self.recipes.values():
            all_recipes.extend(category)
        
        filtered = self._filter_by_allergens(all_recipes, user_allergens or [])
        filtered = self._filter_by_calories(filtered, max_calories)
        
        result = random.choice(filtered) if filtered else None
        return json.dumps(result, ensure_ascii=False, indent=2)
    
    def get_recipes_by_category(self, category: str, user_allergens: List[str] = None, max_calories: Optional[int] = None) -> str:
        if category not in self.recipes:
            return json.dumps([], ensure_ascii=False, indent=2)
        
        recipes = self.recipes[category]
        filtered = self._filter_by_allergens(recipes, user_allergens or [])
        filtered = self._filter_by_calories(filtered, max_calories)
        
        return json.dumps(filtered, ensure_ascii=False, indent=2)
    
    def get_random_recipe_by_category(self, category: str, user_allergens: List[str] = None, max_calories: Optional[int] = None) -> str:
        if category not in self.recipes:
            return json.dumps(None, ensure_ascii=False, indent=2)
        
        recipes = self.recipes[category]
        filtered = self._filter_by_allergens(recipes, user_allergens or [])
        filtered = self._filter_by_calories(filtered, max_calories)
        
        result = random.choice(filtered) if filtered else None
        return json.dumps(result, ensure_ascii=False, indent=2)
    
    def get_all_categories(self) -> str:
        return json.dumps(list(self.recipes.keys()), ensure_ascii=False, indent=2)
    
    def get_all_recipes(self, user_allergens: List[str] = None, max_calories: Optional[int] = None) -> str:
        all_recipes = []
        for category in self.recipes.values():
            all_recipes.extend(category)
        
        filtered = self._filter_by_allergens(all_recipes, user_allergens or [])
        filtered = self._filter_by_calories(filtered, max_calories)
        
        return json.dumps(filtered, ensure_ascii=False, indent=2)