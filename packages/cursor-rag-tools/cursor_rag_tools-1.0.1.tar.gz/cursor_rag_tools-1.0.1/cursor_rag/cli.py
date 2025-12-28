"""
CLI интерфейс для cursor-rag-tools.
"""

import argparse
import json
import sys
from pathlib import Path

from .config import get_db_path, get_model_info, get_saved_model, print_config_info, set_saved_model
from .indexer import Indexer


def cmd_index(args):
    """Команда индексации проекта"""
    project_path = Path(args.path).resolve()

    if not project_path.exists():
        print(f"❌ Путь не найден: {project_path}")
        sys.exit(1)

    # Определяем путь к БД
    db_path = Path(args.db).resolve() if args.db else get_db_path()

    try:
        indexer = Indexer(db_path=db_path)
        files_count, chunks_count = indexer.index_project(
            project_path=project_path,
            project_name=args.name,
            force=args.force,
        )

        print(f"\n{'=' * 60}")
        print("✅ Индексация успешно завершена!")
        print(f"📊 Файлов: {files_count}, чанков: {chunks_count}")
        print(f"{'=' * 60}")

    except Exception as e:
        print(f"\n❌ Ошибка при индексации: {e}")
        sys.exit(1)


def cmd_list(args):
    """Команда вывода списка проектов"""
    db_path = Path(args.db).resolve() if args.db else get_db_path()

    try:
        indexer = Indexer(db_path=db_path)
        projects = indexer.list_projects()

        if not projects:
            print(f"\n📚 В базе данных {db_path} нет проектов.")
            print("   Используйте 'cursor-rag index' для индексации проекта.")
            return

        print(f"\n📚 Проиндексированные проекты в {db_path}:")
        print(f"{'=' * 60}")
        for name, count in projects:
            print(f"  • {name:<30} ({count:>6} чанков)")
        print(f"{'=' * 60}")
        print(f"Всего проектов: {len(projects)}")

    except Exception as e:
        print(f"\n❌ Ошибка: {e}")
        sys.exit(1)


def cmd_delete(args):
    """Команда удаления проекта"""
    db_path = Path(args.db).resolve() if args.db else get_db_path()

    try:
        indexer = Indexer(db_path=db_path)

        if indexer.delete_project(args.name):
            print(f"✅ Проект '{args.name}' успешно удален из {db_path}")
        else:
            print(f"❌ Проект '{args.name}' не найден в {db_path}")
            print("\nИспользуйте 'cursor-rag list' для просмотра доступных проектов.")
            sys.exit(1)

    except Exception as e:
        print(f"\n❌ Ошибка: {e}")
        sys.exit(1)


def cmd_serve(args):
    """Команда запуска MCP сервера"""
    from .mcp_server import run_server

    # Устанавливаем переменные окружения если заданы
    if args.db:
        import os

        os.environ["CURSOR_RAG_DB_PATH"] = str(Path(args.db).resolve())

    run_server()


def cmd_config(args):
    """Команда генерации конфигурации для Cursor"""
    output_path = Path(args.output) if args.output else Path.cwd() / "mcp-config.json"

    # Получаем путь к python интерпретатору
    python_path = sys.executable

    # Определяем путь к БД
    db_path = Path(args.db).resolve() if args.db else get_db_path()

    # Генерируем конфигурацию
    config = {
        "mcpServers": {
            "cursor-rag": {
                "command": python_path,
                "args": ["-m", "cursor_rag.mcp_server"],
                "env": {"CURSOR_RAG_DB_PATH": str(db_path)},
            }
        }
    }

    # Сохраняем конфигурацию
    try:
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(config, f, indent=2, ensure_ascii=False)

        print(f"✅ Конфигурация сохранена: {output_path}")
        print("\n📋 Содержимое конфигурации:")
        print("=" * 60)
        print(json.dumps(config, indent=2, ensure_ascii=False))
        print("=" * 60)
        print("\n💡 Как использовать:")
        print("   1. Откройте Cursor IDE")
        print("   2. Settings -> Features -> MCP Servers")
        print(f"   3. Добавьте содержимое {output_path}")
        print("   4. Перезапустите Cursor")

    except Exception as e:
        print(f"❌ Ошибка при сохранении конфигурации: {e}")
        sys.exit(1)


def cmd_info(args):
    """Команда вывода информации о конфигурации"""
    print_config_info()


def cmd_help(args, *, root_parser: argparse.ArgumentParser, command_parsers: dict[str, argparse.ArgumentParser]):
    """
    Команда help: печатает справку по CLI или по конкретной подкоманде.
    """
    if not getattr(args, "command_name", None):
        root_parser.print_help()
        return

    cmd = args.command_name
    parser = command_parsers.get(cmd)
    if parser is None:
        root_parser.print_help()
        return
    parser.print_help()


def main():
    """Главная функция CLI"""
    parser = argparse.ArgumentParser(
        prog="cursor-rag",
        description="RAG индексация и поиск для Cursor IDE",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Примеры использования:
  cursor-rag index .                      # Индексировать текущий проект (автоимя)
  cursor-rag index /path/to/project       # Индексировать с автоопределением имени
  cursor-rag index . --name myproject     # Индексировать с указанным именем
  cursor-rag index . --force              # Переиндексировать проект
  cursor-rag index . --db ~/my_db         # Использовать кастомную БД
  
  cursor-rag model list                   # Список пресетов моделей
  cursor-rag model show                   # Текущая модель и источник (env/config/default)
  cursor-rag model set bge-base           # Сохранить модель в ~/.cursor_rag/config.json
  
  cursor-rag list                         # Список проектов
  cursor-rag list --db ~/my_db            # Список в кастомной БД
  
  cursor-rag delete myproject             # Удалить проект
  
  cursor-rag serve                        # Запустить MCP сервер
  cursor-rag serve --db ~/my_db           # Сервер с кастомной БД
  
  cursor-rag config                       # Создать mcp-config.json для Cursor
  cursor-rag config --output ~/config.json # С кастомным путем
  
  cursor-rag info                         # Показать текущую конфигурацию

Переменные окружения:
  CURSOR_RAG_DB_PATH        Путь к базе данных
  CURSOR_RAG_MODEL          Модель для эмбеддингов
  CURSOR_RAG_CHUNK_SIZE     Размер чанка
  CURSOR_RAG_CHUNK_OVERLAP  Размер перекрытия
  CURSOR_RAG_MIN_CHUNK_SIZE Минимальный размер чанка (маленькие чанки будут объединяться)
  CURSOR_RAG_SEMANTIC_CHUNKING  Включить семантический чанкинг кода (true/false)
  CURSOR_RAG_IGNORE_DIRS    Доп. игнорируемые папки (через запятую)
  CURSOR_RAG_IGNORE_EXT     Доп. игнорируемые расширения (через запятую)
  CURSOR_RAG_ALLOWED_EXT    Кастомные разрешенные расширения (через запятую)
        """,
    )

    subparsers = parser.add_subparsers(dest="command", help="Доступные команды")

    # Храним подкоманды, чтобы реализовать `cursor-rag help <command>`
    command_parsers: dict[str, argparse.ArgumentParser] = {}

    # Команда: index
    parser_index = subparsers.add_parser(
        "index",
        help="Индексировать проект",
        description="Индексирует код проекта в векторную базу данных",
    )
    command_parsers["index"] = parser_index
    parser_index.add_argument(
        "path",
        nargs="?",
        default=".",
        help="Путь к проекту (по умолчанию текущая директория)",
    )
    parser_index.add_argument(
        "--name",
        "-n",
        help="Имя проекта (если не указано, определяется автоматически)",
    )
    parser_index.add_argument(
        "--db",
        help="Путь к базе данных (по умолчанию ~/.cursor_rag)",
    )
    parser_index.add_argument(
        "--force",
        "-f",
        action="store_true",
        help="Перезаписать существующий индекс",
    )
    parser_index.set_defaults(func=cmd_index)

    # Команда: list
    parser_list = subparsers.add_parser(
        "list",
        help="Список проектов",
        description="Показывает список проиндексированных проектов",
    )
    command_parsers["list"] = parser_list
    parser_list.add_argument(
        "--db",
        help="Путь к базе данных (по умолчанию ~/.cursor_rag)",
    )
    parser_list.set_defaults(func=cmd_list)

    # Команда: delete
    parser_delete = subparsers.add_parser(
        "delete",
        help="Удалить проект",
        description="Удаляет проект из индекса",
    )
    command_parsers["delete"] = parser_delete
    parser_delete.add_argument(
        "name",
        help="Имя проекта для удаления",
    )
    parser_delete.add_argument(
        "--db",
        help="Путь к базе данных (по умолчанию ~/.cursor_rag)",
    )
    parser_delete.set_defaults(func=cmd_delete)

    # Команда: serve
    parser_serve = subparsers.add_parser(
        "serve",
        help="Запустить MCP сервер",
        description="Запускает MCP сервер для Cursor IDE",
    )
    command_parsers["serve"] = parser_serve
    parser_serve.add_argument(
        "--db",
        help="Путь к базе данных (по умолчанию ~/.cursor_rag)",
    )
    parser_serve.set_defaults(func=cmd_serve)

    # Команда: config
    parser_config = subparsers.add_parser(
        "config",
        help="Создать конфигурацию для Cursor",
        description="Генерирует mcp-config.json для настройки Cursor IDE",
    )
    command_parsers["config"] = parser_config
    parser_config.add_argument(
        "--output",
        "-o",
        help="Путь для сохранения конфига (по умолчанию ./mcp-config.json)",
    )
    parser_config.add_argument(
        "--db",
        help="Путь к базе данных (по умолчанию ~/.cursor_rag)",
    )
    parser_config.set_defaults(func=cmd_config)

    # Команда: info
    parser_info = subparsers.add_parser(
        "info",
        help="Информация о конфигурации",
        description="Показывает текущую конфигурацию",
    )
    command_parsers["info"] = parser_info
    parser_info.set_defaults(func=cmd_info)

    # Команда: model
    parser_model = subparsers.add_parser(
        "model",
        help="Управление моделью эмбеддингов (глобально)",
        description="Показывает/переключает модель эмбеддингов, сохраненную в ~/.cursor_rag/config.json",
    )
    command_parsers["model"] = parser_model
    model_sub = parser_model.add_subparsers(dest="model_cmd", help="Подкоманды model")

    presets = {
        "mini": "sentence-transformers/all-MiniLM-L6-v2",
        "bge-base": "BAAI/bge-base-en-v1.5",
        "bge-large": "BAAI/bge-large-en-v1.5",
    }

    def _cmd_model_list(_args: argparse.Namespace):
        print("📚 Доступные пресеты моделей:")
        for key, val in presets.items():
            print(f"  - {key:<9} -> {val}")

    def _cmd_model_show(_args: argparse.Namespace):
        model, source = get_model_info()
        saved = get_saved_model()
        print(f"✅ Активная модель: {model} (source: {source})")
        if saved:
            print(f"💾 Сохранено в config: {saved}")
        else:
            print("💾 Сохранено в config: (нет)")
        print("ℹ️  Примечание: CURSOR_RAG_MODEL (env) имеет приоритет над config.")

    def _cmd_model_set(_args: argparse.Namespace):
        preset = _args.preset
        model_name = presets[preset]
        set_saved_model(model_name)
        print(f"✅ Сохранено: {preset} -> {model_name}")
        print("⚠️  Чтобы изменения влияли на поиск, переиндексируйте проект: cursor-rag index ... --force")

    model_list = model_sub.add_parser("list", help="Показать доступные пресеты моделей")
    model_list.set_defaults(func=_cmd_model_list)

    model_show = model_sub.add_parser("show", help="Показать активную модель и источник")
    model_show.set_defaults(func=_cmd_model_show)

    model_set = model_sub.add_parser("set", help="Выбрать модель из пресетов и сохранить в config")
    model_set.add_argument("preset", choices=sorted(presets.keys()), help="Имя пресета модели")
    model_set.set_defaults(func=_cmd_model_set)

    # Команда: help
    parser_help = subparsers.add_parser(
        "help",
        help="Показать справку по командам",
        description="Показывает справку по CLI или по конкретной команде",
    )
    parser_help.add_argument(
        "command_name",
        nargs="?",
        choices=sorted(command_parsers.keys()),
        help="Команда, по которой нужна справка (например: index, serve)",
    )
    parser_help.set_defaults(func=lambda a: cmd_help(a, root_parser=parser, command_parsers=command_parsers))

    # Парсинг аргументов
    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        sys.exit(1)

    # Выполнение команды
    args.func(args)


if __name__ == "__main__":
    main()
