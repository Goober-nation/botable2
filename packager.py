import json
import os
from datetime import datetime
from typing import Dict, Any, Set
import requests


class Packager:
    def __init__(self, api_endpoint: str = None):
        """
        Инициализация упаковщика данных пользователей

        Args:
            api_endpoint: URL API для отправки данных
        """
        self.api_endpoint = api_endpoint or os.getenv("USER_DATA_API_ENDPOINT")

    def convert_sets_to_lists(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Конвертирует set объекты в списки для JSON сериализации

        Args:
            data: Словарь с данными пользователя

        Returns:
            Словарь с конвертированными данными
        """
        converted_data = {}
        for key, value in data.items():
            if isinstance(value, set):
                converted_data[key] = list(value)
            else:
                converted_data[key] = value
        return converted_data

    def export_user_filters_to_json(self, user_filters: Dict[int, Dict[str, Any]],
                                    filename: str = None) -> str:
        """
        Экспортирует фильтры пользователей в JSON файл

        Args:
            user_filters: Словарь с фильтрами пользователей
            filename: Имя файла для сохранения (опционально)

        Returns:
            Путь к созданному JSON файлу
        """
        if filename is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"exports/user_filters_{timestamp}.json"

        # Создаем папку exports если её нет
        os.makedirs(os.path.dirname(filename) if os.path.dirname(filename) else "exports", exist_ok=True)

        # Конвертируем данные для JSON сериализации
        json_data = {
            "export_timestamp": datetime.now().isoformat(),
            "total_users": len(user_filters),
            "export_type": "filter_save",
            "users": {}
        }

        for user_id, user_data in user_filters.items():
            converted_data = self.convert_sets_to_lists(user_data)
            json_data["users"][str(user_id)] = converted_data

        # Сохраняем в файл
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(json_data, f, ensure_ascii=False, indent=2)

        print(f"Данные пользователей упакованы в файл: {filename}")
        return filename

    def send_to_api(self, user_filters: Dict[int, Dict[str, Any]],
                    headers: Dict[str, str] = None) -> bool:
        """
        Отправляет данные пользователей в API

        Args:
            user_filters: Словарь с фильтрами пользователей
            headers: Дополнительные заголовки для запроса

        Returns:
            True если отправка успешна, False в противном случае
        """
        if not self.api_endpoint:
            print("Предупреждение: API endpoint не настроен, пропускаем отправку в API")
            return False

        # Подготавливаем данные
        json_data = {
            "export_timestamp": datetime.now().isoformat(),
            "total_users": len(user_filters),
            "export_type": "filter_save",
            "users": {}
        }

        for user_id, user_data in user_filters.items():
            converted_data = self.convert_sets_to_lists(user_data)
            json_data["users"][str(user_id)] = converted_data

        # Устанавливаем заголовки по умолчанию
        default_headers = {
            "Content-Type": "application/json",
            "User-Agent": "DAHA-Bot-Packager/1.0"
        }

        if headers:
            default_headers.update(headers)

        try:
            response = requests.post(
                self.api_endpoint,
                json=json_data,
                headers=default_headers,
                timeout=30
            )

            if response.status_code in [200, 201]:
                print(f"Данные успешно отправлены в API: {self.api_endpoint}")
                return True
            else:
                print(f"Ошибка при отправке в API: {response.status_code} - {response.text}")
                return False

        except requests.exceptions.RequestException as e:
            print(f"Ошибка при отправке запроса в API: {e}")
            return False

    def package_and_send(self, user_filters: Dict[int, Dict[str, Any]],
                         save_local: bool = True, send_api: bool = True,
                         filename: str = None, headers: Dict[str, str] = None) -> Dict[str, Any]:
        """
        Упаковывает данные локально и отправляет в API

        Args:
            user_filters: Словарь с фильтрами пользователей
            save_local: Сохранить локально в JSON файл
            send_api: Отправить в API
            filename: Имя файла для локального сохранения
            headers: Заголовки для API запроса

        Returns:
            Словарь с результатами операций
        """
        results = {
            "local_export": {"success": False, "filename": None},
            "api_export": {"success": False, "endpoint": self.api_endpoint}
        }

        if save_local:
            try:
                saved_filename = self.export_user_filters_to_json(user_filters, filename)
                results["local_export"]["success"] = True
                results["local_export"]["filename"] = saved_filename
            except Exception as e:
                print(f"Ошибка при локальном сохранении: {e}")

        if send_api and self.api_endpoint:
            try:
                api_success = self.send_to_api(user_filters, headers)
                results["api_export"]["success"] = api_success
            except Exception as e:
                print(f"Ошибка при отправке в API: {e}")

        return results
