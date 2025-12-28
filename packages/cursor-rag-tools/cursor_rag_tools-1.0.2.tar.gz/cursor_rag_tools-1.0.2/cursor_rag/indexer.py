"""
Универсальный индексатор проектов для cursor-rag-tools.
Объединяет функциональность индексации и автоопределения имени проекта.
"""

import os
import re
import sys
import time
import warnings
from pathlib import Path
from typing import Any, Optional

import chromadb
from sentence_transformers import SentenceTransformer

from .chunking import Chunk, chunk_file, text_chunks
from .config import (
    MAX_RETRIES,
    RETRY_DELAY,
    ensure_db_path,
    get_allowed_ext,
    get_chunk_overlap,
    get_chunk_size,
    get_db_path,
    get_enable_semantic_chunking,
    get_ignore_dirs,
    get_ignore_ext,
    get_max_chunks_per_file,
    get_max_file_bytes,
    get_min_chunk_size,
    get_model,
    get_slow_file_seconds,
)

# Подавляем предупреждения от библиотек
warnings.filterwarnings("ignore")


def transliterate_cyrillic(text: str) -> str:
    """
    Транслитерирует кириллицу в латиницу для совместимости с ChromaDB.

    Args:
        text: Текст с возможными кириллическими символами

    Returns:
        str: Транслитерированный текст
    """
    cyrillic_to_latin = {
        "а": "a",
        "б": "b",
        "в": "v",
        "г": "g",
        "д": "d",
        "е": "e",
        "ё": "yo",
        "ж": "zh",
        "з": "z",
        "и": "i",
        "й": "y",
        "к": "k",
        "л": "l",
        "м": "m",
        "н": "n",
        "о": "o",
        "п": "p",
        "р": "r",
        "с": "s",
        "т": "t",
        "у": "u",
        "ф": "f",
        "х": "h",
        "ц": "ts",
        "ч": "ch",
        "ш": "sh",
        "щ": "sch",
        "ъ": "",
        "ы": "y",
        "ь": "",
        "э": "e",
        "ю": "yu",
        "я": "ya",
        "А": "A",
        "Б": "B",
        "В": "V",
        "Г": "G",
        "Д": "D",
        "Е": "E",
        "Ё": "Yo",
        "Ж": "Zh",
        "З": "Z",
        "И": "I",
        "Й": "Y",
        "К": "K",
        "Л": "L",
        "М": "M",
        "Н": "N",
        "О": "O",
        "П": "P",
        "Р": "R",
        "С": "S",
        "Т": "T",
        "У": "U",
        "Ф": "F",
        "Х": "H",
        "Ц": "Ts",
        "Ч": "Ch",
        "Ш": "Sh",
        "Щ": "Sch",
        "Ъ": "",
        "Ы": "Y",
        "Ь": "",
        "Э": "E",
        "Ю": "Yu",
        "Я": "Ya",
    }

    result = []
    for char in text:
        result.append(cyrillic_to_latin.get(char, char))
    return "".join(result)


def auto_detect_project_name(project_path: Path) -> str:
    """
    Автоматически определяет имя проекта из пути.
    Транслитерирует кириллицу, убирает спецсимволы и делает имя читаемым.

    Args:
        project_path: Путь к проекту

    Returns:
        str: Очищенное имя проекта в нижнем регистре
    """
    name = project_path.name

    # Транслитерируем кириллицу
    name = transliterate_cyrillic(name)

    # Убираем спецсимволы, оставляем только латинские буквы, цифры и подчеркивания
    name = re.sub(r"[^a-zA-Z0-9\s_-]", "", name)
    # Заменяем пробелы и дефисы на подчеркивания
    name = re.sub(r"[\s-]+", "_", name)
    # Убираем множественные подчеркивания
    name = re.sub(r"_+", "_", name)
    # Убираем подчеркивания в начале и конце
    name = name.strip("_")

    # Если имя пустое или слишком короткое, используем дефолтное
    if not name or len(name) < 2:
        name = "project"

    return name.lower()


class Indexer:
    """
    Универсальный индексатор проектов с поддержкой ChromaDB.
    """

    def __init__(
        self,
        db_path: Optional[Path] = None,
        model_name: Optional[str] = None,
    ):
        """
        Инициализация индексатора.

        Args:
            db_path: Путь к базе данных (если None, используется из конфига)
            model_name: Название модели (если None, используется из конфига)
        """
        self.db_path = db_path if db_path else get_db_path()
        self.model_name = model_name if model_name else get_model()
        self.client: Any | None = None
        self.model: Optional[SentenceTransformer] = None

        # Создаем директорию БД если не существует
        ensure_db_path(self.db_path)

    def _get_client(self) -> Any:
        """
        Получить или создать ChromaDB клиента с retry логикой.

        Returns:
            chromadb.PersistentClient: Инициализированный клиент

        Raises:
            RuntimeError: Если не удалось подключиться после всех попыток
        """
        if self.client is not None:
            return self.client

        for attempt in range(MAX_RETRIES):
            try:
                self.client = chromadb.PersistentClient(path=str(self.db_path))
                return self.client
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
                        raise RuntimeError(
                            f"❌ Не удалось подключиться к ChromaDB после {MAX_RETRIES} попыток.\n"
                            f"Возможно, другой процесс использует БД: {self.db_path}\n"
                            f"Попробуйте остановить все процессы или удалить БД."
                        ) from e
                else:
                    raise RuntimeError(f"❌ Ошибка инициализации ChromaDB: {e}") from e

        raise RuntimeError("❌ Не удалось инициализировать ChromaDB клиент")

    def _get_model(self) -> SentenceTransformer:
        """
        Получить или загрузить модель для эмбеддингов.

        Returns:
            SentenceTransformer: Загруженная модель
        """
        if self.model is None:
            print("🔄 Загрузка модели нейросети...")
            self.model = SentenceTransformer(self.model_name)
            print("✅ Модель загружена")
        return self.model

    def get_files(self, root_dir: Path) -> list[Path]:
        """
        Сканирует директорию и возвращает список файлов для индексации.

        Args:
            root_dir: Корневая директория для сканирования

        Returns:
            list[Path]: Список путей к файлам
        """
        ignore_dirs = get_ignore_dirs()
        ignore_ext = get_ignore_ext()
        allowed_ext = get_allowed_ext()

        files_to_process = []
        print(f"🔍 Сканирование файлов в: {root_dir}")

        for root, dirs, files in os.walk(root_dir):
            # Фильтрация папок in-place
            dirs[:] = [d for d in dirs if d not in ignore_dirs and not d.startswith(".")]

            for file in files:
                file_path = Path(root) / file

                # Пропускаем игнорируемые расширения
                if file_path.suffix in ignore_ext:
                    continue

                # Если заданы разрешенные расширения, проверяем их
                if allowed_ext and file_path.suffix not in allowed_ext:
                    continue

                files_to_process.append(file_path)

        return files_to_process

    def chunk_text(self, text: str, chunk_size: Optional[int] = None, overlap: Optional[int] = None) -> list[str]:
        """
        Разбивает текст на чанки с перекрытием.

        Args:
            text: Исходный текст
            chunk_size: Размер чанка (если None, из конфига)
            overlap: Размер перекрытия (если None, из конфига)

        Returns:
            list[str]: Список чанков
        """
        if not text:
            return []

        chunk_size = chunk_size if chunk_size else get_chunk_size()
        overlap = overlap if overlap else get_chunk_overlap()

        chunks = []
        for i in range(0, len(text), chunk_size - overlap):
            chunks.append(text[i : i + chunk_size])

        return chunks

    def chunk_document(
        self,
        *,
        content: str,
        file_path: Path,
        chunk_size: Optional[int] = None,
        overlap: Optional[int] = None,
    ) -> list[Chunk]:
        """
        Chunk a file content. Prefers semantic chunking for code files when enabled.
        """
        chunk_size = chunk_size if chunk_size else get_chunk_size()
        overlap = overlap if overlap else get_chunk_overlap()
        min_chunk_size = get_min_chunk_size()
        enable_semantic = get_enable_semantic_chunking()

        try:
            return chunk_file(
                content=content,
                file_path=file_path,
                max_chars=chunk_size,
                overlap=overlap,
                min_chars=min_chunk_size,
                enable_semantic=enable_semantic,
            )
        except Exception:
            # Safety net: never fail indexing because of chunking.
            return text_chunks(content, max_chars=chunk_size, overlap=overlap)

    def index_project(
        self,
        project_path: str | Path,
        project_name: Optional[str] = None,
        force: bool = False,
    ) -> tuple[int, int]:
        """
        Индексирует проект в ChromaDB.

        Args:
            project_path: Путь к проекту
            project_name: Имя проекта (если None, определяется автоматически)
            force: Перезаписать существующий индекс

        Returns:
            tuple[int, int]: (количество файлов, количество чанков)

        Raises:
            ValueError: Если путь не существует
            RuntimeError: Если проект уже существует и force=False
        """
        path = Path(project_path).resolve()
        if not path.exists():
            raise ValueError(f"❌ Путь не найден: {path}")

        # Автоопределение имени проекта
        if project_name is None:
            project_name = auto_detect_project_name(path)

        project_name = project_name.lower()

        print(f"🔍 Имя проекта: '{project_name}'")
        print(f"📁 Путь к проекту: {path}")
        print(f"📦 База данных: {self.db_path}")

        # Получаем клиента
        client = self._get_client()

        # Проверяем существующие коллекции
        existing_collections = [c.name for c in client.list_collections()]
        if project_name in existing_collections:
            if force:
                print(f"🗑️  Удаление старого индекса '{project_name}'...")
                client.delete_collection(project_name)
            else:
                raise RuntimeError(
                    f"⚠️  Проект '{project_name}' уже есть в индексе.\n"
                    f"   Используйте --force для перезаписи или выберите другое имя."
                )

        # Создаем коллекцию
        collection = client.get_or_create_collection(name=project_name)

        # Сканируем файлы
        files = self.get_files(path)
        print(f"📄 Найдено файлов: {len(files)}")

        if not files:
            print("⚠️  Файлы для индексации не найдены")
            return 0, 0

        # Получаем модель
        model = self._get_model()

        count = 0
        total_chunks = 0

        print("🚀 Начало индексации...")
        try:
            max_file_bytes = get_max_file_bytes()
            max_chunks_per_file = get_max_chunks_per_file()
            slow_file_seconds = get_slow_file_seconds()

            skipped_by_size = 0
            skipped_by_chunks = 0
            errored_files = 0

            # Keep a small leaderboard of slow files to help diagnose "hangs".
            slow_files: list[tuple[float, str, dict[str, float], int, int]] = []

            for idx, file_path in enumerate(files, start=1):
                try:
                    # Print "in progress" to avoid perceived hangs on heavy files.
                    print(f"\r⏳ Обработка: {idx}/{len(files)} ({file_path.name})", end="")

                    # Quick size check before reading the file into memory.
                    try:
                        file_size = file_path.stat().st_size
                    except Exception:
                        file_size = 0
                    if max_file_bytes is not None and file_size > max_file_bytes:
                        skipped_by_size += 1
                        print(
                            f"\n⚠️  Пропуск (слишком большой файл): {file_path} "
                            f"({file_size} bytes > {max_file_bytes} bytes)"
                        )
                        continue

                    t0 = time.perf_counter()
                    with open(file_path, encoding="utf-8", errors="ignore") as f:
                        content = f.read()
                    t_read = time.perf_counter()

                    if not content.strip():
                        continue

                    t1 = time.perf_counter()
                    chunks = self.chunk_document(content=content, file_path=file_path)
                    t_chunk = time.perf_counter()
                    if not chunks:
                        continue

                    if max_chunks_per_file is not None and len(chunks) > max_chunks_per_file:
                        skipped_by_chunks += 1
                        print(
                            f"\n⚠️  Пропуск (слишком много чанков): {file_path} ({len(chunks)} > {max_chunks_per_file})"
                        )
                        continue

                    # Генерация эмбеддингов батчем для файла
                    documents = [c.text for c in chunks]
                    t2 = time.perf_counter()
                    embeddings = model.encode(documents)
                    t_encode = time.perf_counter()

                    source_str = str(file_path)
                    ids = []
                    metadatas = []
                    for i, c in enumerate(chunks):
                        start_line = c.start_line if c.start_line is not None else 0
                        end_line = c.end_line if c.end_line is not None else 0
                        ids.append(f"{source_str}::{start_line}-{end_line}::{i}")
                        raw_meta = {
                            "source": source_str,
                            "chunk": i,
                            "start_line": c.start_line,
                            "end_line": c.end_line,
                            "symbol_type": c.symbol_type,
                            "symbol_name": c.symbol_name,
                            "language": c.language,
                        }
                        # Chroma metadata values must be non-null primitives.
                        metadatas.append({k: v for k, v in raw_meta.items() if v is not None})

                    collection.add(
                        ids=ids,
                        documents=documents,
                        embeddings=embeddings.tolist(),
                        metadatas=metadatas,
                    )
                    t_add = time.perf_counter()

                    total_chunks += len(chunks)
                    count += 1
                    print(f"\r✅ Обработано: {count}/{len(files)} ({file_path.name})", end="")

                    total_s = t_add - t0
                    if slow_file_seconds > 0 and total_s >= slow_file_seconds:
                        timings = {
                            "read_s": t_read - t0,
                            "chunk_s": t_chunk - t1,
                            "encode_s": t_encode - t2,
                            "add_s": t_add - t_encode,
                            "total_s": total_s,
                        }
                        slow_files.append((total_s, str(file_path), timings, file_size, len(chunks)))
                        # Keep only top 10 slowest
                        slow_files.sort(key=lambda x: x[0], reverse=True)
                        slow_files = slow_files[:10]

                except Exception as e:
                    errored_files += 1
                    print(f"\n❌ Ошибка с файлом {file_path.name}: {e}")

            print(f"\n\n✨ Готово! Индексировано файлов: {count}, всего чанков: {total_chunks}")
            if skipped_by_size or skipped_by_chunks or errored_files:
                print(
                    "📌 Сводка пропусков/ошибок:\n"
                    f"  - Пропущено по размеру: {skipped_by_size}\n"
                    f"  - Пропущено по чанкам: {skipped_by_chunks}\n"
                    f"  - Ошибок при обработке: {errored_files}"
                )
            if slow_files:
                print("\n🐢 Самые медленные файлы (top 10):")
                for total_s, path_str, timings, size_b, n_chunks in slow_files:
                    print(
                        f"  - {total_s:.2f}s | chunks={n_chunks} | size={size_b}B | {path_str}\n"
                        f"    read={timings['read_s']:.2f}s, chunk={timings['chunk_s']:.2f}s, "
                        f"encode={timings['encode_s']:.2f}s, add={timings['add_s']:.2f}s"
                    )
            print(f"💡 Теперь можно использовать MCP с именем проекта: '{project_name}'")

            return count, total_chunks

        except KeyboardInterrupt:
            print("\n⛔ Индексация прервана пользователем")
            return count, total_chunks

    def list_projects(self) -> list[tuple[str, int]]:
        """
        Получить список всех проиндексированных проектов.

        Returns:
            list[tuple[str, int]]: Список (имя проекта, количество документов)
        """
        client = self._get_client()
        collections = client.list_collections()

        result = []
        for col in collections:
            try:
                count = col.count()
                result.append((col.name, count))
            except Exception:
                result.append((col.name, 0))

        return result

    def delete_project(self, project_name: str) -> bool:
        """
        Удалить проект из индекса.

        Args:
            project_name: Имя проекта для удаления

        Returns:
            bool: True если удален успешно, False если проект не найден
        """
        client = self._get_client()
        existing = [c.name for c in client.list_collections()]

        if project_name not in existing:
            return False

        client.delete_collection(project_name)
        return True
