#!/usr/bin/env python
"""
Примеры использования cursor-rag-tools как библиотеки Python
"""

from pathlib import Path

from cursor_rag import Indexer, auto_detect_project_name, get_db_path


def example_basic_indexing():
    """Базовый пример индексации проекта"""
    print("=" * 60)
    print("Пример 1: Базовая индексация")
    print("=" * 60)

    # Создаем индексатор (использует дефолтные настройки)
    indexer = Indexer()

    # Индексируем текущий проект
    project_path = Path.cwd()

    # Автоопределение имени
    project_name = auto_detect_project_name(project_path)
    print(f"Автоопределенное имя: {project_name}")

    # Индексация
    files_count, chunks_count = indexer.index_project(
        project_path=project_path,
        project_name=project_name,
        force=True,  # Перезаписать если существует
    )

    print(f"✅ Проиндексировано: {files_count} файлов, {chunks_count} чанков")


def example_custom_db():
    """Пример с кастомной базой данных"""
    print("\n" + "=" * 60)
    print("Пример 2: Кастомная база данных")
    print("=" * 60)

    # Создаем индексатор с кастомной БД
    custom_db = Path.home() / "my_custom_rag_db"
    indexer = Indexer(db_path=custom_db)

    print(f"База данных: {custom_db}")

    # Индексируем проект
    project_path = Path("/path/to/your/project")  # Измените на свой путь

    if project_path.exists():
        files_count, chunks_count = indexer.index_project(
            project_path=project_path, project_name="my_awesome_project", force=True
        )
        print(f"✅ Проиндексировано: {files_count} файлов, {chunks_count} чанков")
    else:
        print(f"⚠️  Путь {project_path} не существует")


def example_list_projects():
    """Пример получения списка проектов"""
    print("\n" + "=" * 60)
    print("Пример 3: Список проектов")
    print("=" * 60)

    indexer = Indexer()
    projects = indexer.list_projects()

    if not projects:
        print("Проектов не найдено")
        return

    print(f"Найдено проектов: {len(projects)}")
    for name, count in projects:
        print(f"  • {name}: {count} чанков")


def example_delete_project():
    """Пример удаления проекта"""
    print("\n" + "=" * 60)
    print("Пример 4: Удаление проекта")
    print("=" * 60)

    indexer = Indexer()

    # Удаляем проект
    project_to_delete = "test_project"

    if indexer.delete_project(project_to_delete):
        print(f"✅ Проект '{project_to_delete}' удален")
    else:
        print(f"⚠️  Проект '{project_to_delete}' не найден")


def example_multiple_projects():
    """Пример индексации нескольких проектов"""
    print("\n" + "=" * 60)
    print("Пример 5: Индексация нескольких проектов")
    print("=" * 60)

    indexer = Indexer()

    # Список проектов для индексации
    projects_to_index = [
        ("/path/to/project1", "backend_api"),
        ("/path/to/project2", "frontend_app"),
        ("/path/to/project3", "ml_models"),
    ]

    for project_path, project_name in projects_to_index:
        path = Path(project_path)
        if not path.exists():
            print(f"⚠️  Пропускаем {project_name}: путь не существует")
            continue

        try:
            files_count, chunks_count = indexer.index_project(
                project_path=path, project_name=project_name, force=True
            )
            print(f"✅ {project_name}: {files_count} файлов, {chunks_count} чанков")
        except Exception as e:
            print(f"❌ Ошибка при индексации {project_name}: {e}")


def example_with_env_vars():
    """Пример использования с переменными окружения"""
    print("\n" + "=" * 60)
    print("Пример 6: Использование env vars")
    print("=" * 60)

    import os

    # Устанавливаем кастомные переменные окружения
    os.environ["CURSOR_RAG_DB_PATH"] = str(Path.home() / "work_projects_db")
    os.environ["CURSOR_RAG_CHUNK_SIZE"] = "1000"

    # Теперь get_db_path() вернет значение из env var
    print(f"DB Path: {get_db_path()}")

    # Создаем индексатор (автоматически использует env vars)
    indexer = Indexer()

    # Индексация с новыми настройками
    # ...


def example_error_handling():
    """Пример обработки ошибок"""
    print("\n" + "=" * 60)
    print("Пример 7: Обработка ошибок")
    print("=" * 60)

    indexer = Indexer()

    try:
        # Попытка индексации несуществующего пути
        indexer.index_project(project_path="/nonexistent/path", project_name="test")
    except ValueError as e:
        print(f"✅ Поймана ошибка ValueError: {e}")

    try:
        # Попытка индексации без force (если проект существует)
        indexer.index_project(
            project_path=Path.cwd(),
            project_name="existing_project",
            force=False,  # Выбросит ошибку если проект уже есть
        )
    except RuntimeError as e:
        print(f"✅ Поймана ошибка RuntimeError: {e}")


def example_transliteration():
    """Пример автоматической транслитерации"""
    print("\n" + "=" * 60)
    print("Пример 8: Транслитерация кириллицы")
    print("=" * 60)

    # Проекты с кириллическими именами
    test_paths = [
        Path("/проекты/мой_сайт"),
        Path("/projects/содержимое_фабрика"),
        Path("/код/тестовый-проект"),
    ]

    for path in test_paths:
        name = auto_detect_project_name(path)
        print(f"{path.name} → {name}")


def main():
    """Запуск всех примеров"""
    print("\n🚀 Примеры использования cursor-rag-tools\n")

    # Запускаем безопасные примеры (без реальной индексации)
    example_transliteration()
    example_list_projects()

    # Раскомментируйте для запуска примеров с индексацией
    # example_basic_indexing()
    # example_custom_db()
    # example_delete_project()
    # example_multiple_projects()
    # example_with_env_vars()
    # example_error_handling()

    print("\n✅ Примеры завершены!")
    print("\n💡 Подсказка: Раскомментируйте нужные примеры в функции main()")


if __name__ == "__main__":
    main()
