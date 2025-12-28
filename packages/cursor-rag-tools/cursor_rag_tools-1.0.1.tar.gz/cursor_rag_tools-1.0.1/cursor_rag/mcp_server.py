#!/usr/bin/env python
"""
MCP Server для ChromaDB - позволяет Cursor напрямую обращаться к векторной БД.
Упрощенная версия с поддержкой множественных баз данных через env vars.
"""

import sys
import time
from collections.abc import Sequence
from pathlib import Path
from typing import Any

import chromadb
from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import Resource, TextContent, Tool
from pydantic.networks import AnyUrl
from sentence_transformers import SentenceTransformer

from .config import MAX_RETRIES, RETRY_DELAY, ensure_db_path, get_db_path, get_model

# Глобальные переменные для ленивой инициализации
_chroma_client: Any | None = None
_embedding_model: SentenceTransformer | None = None
_db_path: Path | None = None


def get_chroma_client() -> Any:
    """
    Получить или создать ChromaDB клиента с retry логикой.

    Returns:
        chromadb.PersistentClient: Инициализированный клиент

    Raises:
        RuntimeError: Если не удалось подключиться
    """
    global _chroma_client, _db_path

    if _chroma_client is not None:
        return _chroma_client

    # Получаем путь к БД из конфига (с учетом env vars)
    _db_path = get_db_path()
    _ = ensure_db_path(_db_path)

    for attempt in range(MAX_RETRIES):
        try:
            _chroma_client = chromadb.PersistentClient(path=str(_db_path))
            print(f"✅ Подключено к ChromaDB: {_db_path}", file=sys.stderr)
            return _chroma_client
        except Exception as e:
            error_msg = str(e)
            if "database is locked" in error_msg.lower() or "locked" in error_msg.lower():
                if attempt < MAX_RETRIES - 1:
                    print(
                        f"⚠️  База данных заблокирована, попытка {attempt + 1}/{MAX_RETRIES}...",
                        file=sys.stderr,
                    )
                    time.sleep(RETRY_DELAY)
                else:
                    print(
                        f"❌ Не удалось подключиться к ChromaDB после {MAX_RETRIES} попыток.\n"
                        f"Возможно, другой процесс использует БД: {_db_path}\n"
                        f"Попробуйте остановить все процессы mcp_server или indexer.",
                        file=sys.stderr,
                    )
                    sys.exit(1)
            else:
                print(f"❌ Ошибка инициализации ChromaDB: {e}", file=sys.stderr)
                sys.exit(1)

    raise RuntimeError("❌ Не удалось инициализировать ChromaDB клиент")


def get_embedding(text: str) -> list[float]:
    """
    Получить эмбеддинг текста.

    Args:
        text: Текст для эмбеддинга

    Returns:
        list[float]: Вектор эмбеддинга
    """
    global _embedding_model

    if _embedding_model is None:
        model_name = get_model()
        print(f"🔄 Загрузка модели для эмбеддингов: {model_name}...", file=sys.stderr)
        _embedding_model = SentenceTransformer(model_name)
        print("✅ Модель загружена", file=sys.stderr)

    # Ограничиваем длину текста для эмбеддинга
    embedding = _embedding_model.encode(text[:512], normalize_embeddings=True)
    return embedding.tolist()


# Создание MCP сервера
app = Server("cursor-rag")


@app.list_resources()
async def list_resources() -> list[Resource]:
    """Список всех индексированных проектов (коллекций)"""
    try:
        client = get_chroma_client()
        collections = client.list_collections()
        return [
            Resource(
                uri=AnyUrl(f"chroma://collection/{col.name}"),
                name=col.name,
                description=f"Векторная коллекция проекта {col.name}",
                mimeType="application/json",
            )
            for col in collections
        ]
    except Exception as e:
        print(f"❌ Ошибка при получении коллекций: {e}", file=sys.stderr)
        return []


@app.list_tools()
async def list_tools() -> list[Tool]:
    """Список доступных инструментов"""
    try:
        client = get_chroma_client()
        collections = client.list_collections()
        available_projects = [col.name for col in collections]
    except Exception:
        available_projects = []

    projects_hint = ""
    if available_projects:
        projects_hint = (
            f"\n\nДоступные проекты: {', '.join(available_projects)}\nИспользуйте list_projects для полного списка."
        )

    return [
        Tool(
            name="search_codebase",
            description=(
                f"Поиск кода и документации в проиндексированных проектах через векторную БД. "
                f"Используйте для поиска кода, функций, архитектуры и т.д.{projects_hint}\n\n"
                f"ВАЖНО: project - это имя, которое было указано при индексации (не имя папки!). "
                f"Это имя коллекции в ChromaDB."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "project": {
                        "type": "string",
                        "description": (
                            "Название проекта (имя коллекции в ChromaDB, указанное при индексации). "
                            "НЕ имя папки! Используйте list_projects чтобы увидеть доступные имена."
                        ),
                        "enum": available_projects if available_projects else None,
                    },
                    "query": {
                        "type": "string",
                        "description": "Поисковый запрос на русском или английском",
                    },
                    "top_k": {
                        "type": "integer",
                        "description": "Количество результатов (по умолчанию 3)",
                        "default": 3,
                    },
                },
                "required": ["project", "query"],
            },
        ),
        Tool(
            name="list_rag_projects",
            description=(
                "Получить список всех проиндексированных проектов (имен коллекций в ChromaDB). "
                "Используйте эти имена в search_codebase."
            ),
            inputSchema={"type": "object", "properties": {}},
        ),
    ]


@app.call_tool()
async def call_tool(name: str, arguments: dict[str, Any] | None) -> Sequence[TextContent]:
    """Выполнить инструмент"""
    client = get_chroma_client()

    if name == "search_codebase":
        project_name = arguments.get("project") if arguments else None
        query = arguments.get("query") if arguments else None
        top_k = arguments.get("top_k", 3) if arguments else 3

        if not project_name or not query:
            return [TextContent(type="text", text="❌ Ошибка: требуется project и query")]

        try:
            # Проверяем существование коллекции
            collections = client.list_collections()
            available_names = [col.name for col in collections]

            if project_name not in available_names:
                suggestions = ""
                # Ищем похожие имена
                similar = [
                    name
                    for name in available_names
                    if project_name.lower() in name.lower() or name.lower() in project_name.lower()
                ]
                if similar:
                    suggestions = f"\n\n💡 Возможно, вы имели в виду: {', '.join(similar)}"

                return [
                    TextContent(
                        type="text",
                        text=(
                            f"❌ Проект '{project_name}' не найден в ChromaDB.\n\n"
                            f"📚 Доступные проекты: {', '.join(available_names) if available_names else 'нет'}\n"
                            f"Используйте list_rag_projects для полного списка.{suggestions}\n\n"
                            f"⚠️  Помните: project - это имя, указанное при индексации, а НЕ имя папки!"
                        ),
                    )
                ]

            # Получаем коллекцию
            collection = client.get_collection(name=project_name)

            # Получаем эмбеддинг запроса
            query_embedding = get_embedding(query)

            # Поиск
            results = collection.query(
                query_embeddings=[query_embedding],
                n_results=top_k,
                include=["documents", "metadatas", "distances"],
            )

            if not results["documents"] or not results["documents"][0]:
                return [
                    TextContent(
                        type="text",
                        text=f"❌ В проекте '{project_name}' не найдена релевантная информация для запроса: {query}",
                    )
                ]

            # Форматируем результаты
            context_parts = []
            documents = results["documents"][0]
            metadatas = results["metadatas"][0]
            distances = results["distances"][0]

            for i, (doc, meta, distance) in enumerate(
                zip(documents, metadatas, distances, strict=True),
                start=1,
            ):
                source_file = meta.get("source", "unknown")
                chunk_num = meta.get("chunk", 0)
                start_line = meta.get("start_line")
                end_line = meta.get("end_line")
                symbol_type = meta.get("symbol_type")
                symbol_name = meta.get("symbol_name")
                language = meta.get("language")
                relevance = 1.0 - float(distance)

                lines_info = ""
                if start_line and end_line:
                    lines_info = f"Строки: {start_line}-{end_line}\n"

                symbol_info = ""
                if symbol_type or symbol_name:
                    if symbol_name:
                        symbol_info = f"Сущность: {symbol_type or 'symbol'} {symbol_name}\n"
                    else:
                        symbol_info = f"Сущность: {symbol_type}\n"

                lang_info = f"Язык: {language}\n" if language else ""

                context_parts.append(
                    f"--- Результат {i} (релевантность: {relevance:.2%}) ---\n"
                    f"Файл: {source_file}\n"
                    f"Чанк: {chunk_num}\n"
                    f"{lang_info}"
                    f"{lines_info}"
                    f"{symbol_info}"
                    f"Содержимое:\n{doc}\n"
                )

            result_text = f"🔍 Результаты поиска в проекте '{project_name}':\n\n" + "\n".join(context_parts)

            return [TextContent(type="text", text=result_text)]

        except Exception as e:
            return [TextContent(type="text", text=f"❌ Ошибка при поиске: {str(e)}")]

    elif name == "list_rag_projects":
        try:
            collections = client.list_collections()
            if not collections:
                return [
                    TextContent(
                        type="text",
                        text=(
                            "📚 Проекты не найдены. Сначала запустите индексацию:\n"
                            "   cursor-rag index /path/to/project\n\n"
                            "Или с автоопределением имени:\n"
                            "   cursor-rag index ."
                        ),
                    )
                ]

            projects_info = []
            for col in collections:
                try:
                    count = col.count()
                    projects_info.append(f"  • {col.name} ({count} документов)")
                except Exception:
                    projects_info.append(f"  • {col.name}")

            result = (
                f"📚 Доступные проекты ({len(collections)}):\n"
                + "\n".join(projects_info)
                + "\n\n"
                + "💡 Используйте эти имена в search_codebase.\n"
                + "⚠️  ВАЖНО: Это имена коллекций (указанные при индексации), а НЕ имена папок!"
            )
            return [TextContent(type="text", text=result)]
        except Exception as e:
            return [TextContent(type="text", text=f"❌ Ошибка при получении списка проектов: {str(e)}")]

    else:
        return [TextContent(type="text", text=f"❌ Неизвестный инструмент: {name}")]


async def main():
    """Запуск MCP сервера"""
    try:
        async with stdio_server() as (read_stream, write_stream):
            await app.run(
                read_stream,
                write_stream,
                app.create_initialization_options(),
            )
    except KeyboardInterrupt:
        print("\n👋 Сервер остановлен", file=sys.stderr)
    except Exception as e:
        print(f"\n❌ Ошибка сервера: {e}", file=sys.stderr)
        raise


def run_server():
    """Entry point для CLI"""
    import asyncio

    print("🚀 MCP Cursor RAG Server запущен", file=sys.stderr)
    print(f"📂 БД: {get_db_path()}", file=sys.stderr)
    print("📍 Подключите в Cursor: Settings -> Features -> MCP Servers", file=sys.stderr)

    try:
        asyncio.run(main())
    finally:
        if _chroma_client:
            print("🔒 Закрытие соединения с БД...", file=sys.stderr)


if __name__ == "__main__":
    run_server()
