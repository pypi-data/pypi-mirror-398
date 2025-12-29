import json
import random
from typing import List, Dict, Optional, Union
from pathlib import Path


class RecipesSDK:
    def __init__(self, language: str = "en"):
        self.language = language
        self.recipes = self._load_recipes()
        self.breakfast_file_index = 0  # Индекс текущего файла завтраков (0, 1, 2)
    
    def _load_recipes(self) -> Dict:
        """Загружает все рецепты из всех доступных файлов для каждой категории"""
        recipes = {}
        base_path = Path(__file__).parent
        
        # Маппинг категорий на возможные файлы
        category_files = {
            'breakfast': ['breakfast_1.json', 'breakfast_2.json', 'breakfast_3.json', 'breakfast_4.json'],
            'lunch': ['lunch.json', 'lunch_1.json'],
            'dinner': ['dinner.json', 'dinner_1.json'],
            'snack': ['snack.json']
        }
        
        # Загружаем все категории
        for category, file_names in category_files.items():
            category_list = []
            
            # Загружаем все файлы для категории
            for file_name in file_names:
                file_path = base_path / file_name
                if file_path.exists():
                    try:
                        with open(file_path, 'r', encoding='utf-8') as f:
                            data = json.load(f)
                            # Определяем ключ (может быть category или category_1 и т.д.)
                            key = list(data.keys())[0] if data else None
                            if key and category in key.lower():
                                category_list.extend(data.get(key, []))
                    except Exception as e:
                        # Пропускаем файлы с ошибками
                        continue
            
            recipes[category] = category_list
        
        return recipes
    
    def _get_breakfast_from_rotated_file(self) -> List[Dict]:
        """Получает завтраки из текущего файла (ротация по кругу)"""
        base_path = Path(__file__).parent
        breakfast_files = [
            base_path / "breakfast_1.json",
            base_path / "breakfast_2.json",
            base_path / "breakfast_3.json",
            base_path / "breakfast_4.json"
        ]
        
        # Фильтруем только существующие файлы
        existing_files = [f for f in breakfast_files if f.exists()]
        
        if not existing_files:
            # Fallback на старый файл
            file_path = base_path / "breakfast.json"
            if file_path.exists():
                with open(file_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    return data.get('breakfast', [])
            return []
        
        # Загружаем из текущего файла (по ротации)
        num_files = len(existing_files)
        current_file = existing_files[self.breakfast_file_index % num_files]
        
        with open(current_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
            key = list(data.keys())[0] if data else None
            breakfast_list = data.get(key, []) if key else []
        
        # Переключаемся на следующий файл для следующего запроса
        self.breakfast_file_index = (self.breakfast_file_index + 1) % num_files
        
        return breakfast_list
    
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
        """Возвращает случайный рецепт из всех категорий"""
        all_recipes = []
        
        # Добавляем все категории (уже загружены из всех файлов)
        for category in ['breakfast', 'snack', 'lunch', 'dinner']:
            if category in self.recipes:
                all_recipes.extend(self.recipes[category])
        
        filtered = self._filter_by_allergens(all_recipes, user_allergens or [])
        filtered = self._filter_by_calories(filtered, max_calories)
        
        result = random.choice(filtered) if filtered else None
        return json.dumps(result, ensure_ascii=False, indent=2)
    
    def get_recipes_by_category(self, category: str, user_allergens: List[str] = None, max_calories: Optional[int] = None) -> str:
        """Возвращает ВСЕ рецепты категории из всех файлов"""
        if category not in self.recipes:
            return json.dumps([], ensure_ascii=False, indent=2)
        
        # Возвращаем все рецепты категории (из всех файлов)
        recipes = self.recipes[category]
        
        filtered = self._filter_by_allergens(recipes, user_allergens or [])
        filtered = self._filter_by_calories(filtered, max_calories)
        
        return json.dumps(filtered, ensure_ascii=False, indent=2)
    
    def get_random_recipe_by_category(self, category: str, user_allergens: List[str] = None, max_calories: Optional[int] = None) -> str:
        """Возвращает случайный рецепт из категории (из всех файлов)"""
        if category not in self.recipes:
            return json.dumps(None, ensure_ascii=False, indent=2)
        
        # Используем все рецепты категории из всех файлов
        recipes = self.recipes[category]
        
        filtered = self._filter_by_allergens(recipes, user_allergens or [])
        filtered = self._filter_by_calories(filtered, max_calories)
        
        result = random.choice(filtered) if filtered else None
        return json.dumps(result, ensure_ascii=False, indent=2)
    
    def get_all_categories(self) -> str:
        return json.dumps(list(self.recipes.keys()), ensure_ascii=False, indent=2)
    
    def get_all_recipes(self, user_allergens: List[str] = None, max_calories: Optional[int] = None) -> str:
        """Возвращает ВСЕ рецепты из всех категорий и всех файлов"""
        all_recipes = []
        
        # Добавляем все категории (уже загружены из всех файлов)
        for category in ['breakfast', 'snack', 'lunch', 'dinner']:
            if category in self.recipes:
                all_recipes.extend(self.recipes[category])
        
        filtered = self._filter_by_allergens(all_recipes, user_allergens or [])
        filtered = self._filter_by_calories(filtered, max_calories)
        
        return json.dumps(filtered, ensure_ascii=False, indent=2)