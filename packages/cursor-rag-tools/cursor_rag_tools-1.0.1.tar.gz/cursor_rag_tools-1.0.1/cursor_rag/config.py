"""
Центральная конфигурация для cursor-rag-tools.
Использует дефолтные значения с возможностью переопределения через переменные окружения.
"""

import json
import os
from pathlib import Path

# ==================== DEFAULTS ====================

# Путь к базе данных по умолчанию (в home directory пользователя)
DEFAULT_DB_PATH = Path.home() / ".cursor_rag"

# Путь к глобальному конфигу (не зависит от CURSOR_RAG_DB_PATH)
DEFAULT_CONFIG_PATH = DEFAULT_DB_PATH / "config.json"

# Модель для генерации эмбеддингов
DEFAULT_MODEL = "all-MiniLM-L6-v2"

# Игнорируемые директории при индексации
IGNORE_DIRS = {
    "node_modules",
    "venv",
    ".venv",
    "env",
    ".git",
    ".idea",
    ".vscode",
    "__pycache__",
    "dist",
    "build",
    "coverage",
    ".next",
    ".nuxt",
    "target",
    ".pytest_cache",
    ".mypy_cache",
    ".ruff_cache",
    ".tox",
    "htmlcov",
}

# Игнорируемые расширения файлов
IGNORE_EXT = {
    ".pyc",
    ".pyo",
    ".pyd",
    ".so",
    ".dll",
    ".dylib",
    ".class",
    ".exe",
    ".jpg",
    ".jpeg",
    ".png",
    ".gif",
    ".ico",
    ".svg",
    ".bmp",
    ".webp",
    ".zip",
    ".tar",
    ".gz",
    ".bz2",
    ".7z",
    ".rar",
    ".lock",
    ".woff",
    ".woff2",
    ".ttf",
    ".eot",
    ".pdf",
}

# Разрешенные расширения (текстовые файлы с кодом и документацией)
ALLOWED_EXT = {
    # Programming languages
    ".py",
    ".js",
    ".jsx",
    ".ts",
    ".tsx",
    ".go",
    ".rs",
    ".java",
    ".cpp",
    ".c",
    ".h",
    ".hpp",
    ".cs",
    ".rb",
    ".php",
    ".swift",
    ".kt",
    ".scala",
    ".r",
    ".m",
    ".sh",
    ".bash",
    ".zsh",
    ".fish",
    # Markup and data
    ".md",
    ".markdown",
    ".rst",
    ".txt",
    ".json",
    ".yaml",
    ".yml",
    ".toml",
    ".xml",
    ".html",
    ".htm",
    ".css",
    ".scss",
    ".sass",
    ".less",
    ".sql",
    ".graphql",
    ".proto",
    # Config files
    ".ini",
    ".cfg",
    ".conf",
    ".env",
    ".gitignore",
    ".dockerignore",
}

# Параметры чанкинга
DEFAULT_CHUNK_SIZE = 500
DEFAULT_CHUNK_OVERLAP = 50
DEFAULT_MIN_CHUNK_SIZE = 200

# Включить semantic chunking для кода (tree-sitter/AST) по умолчанию
DEFAULT_ENABLE_SEMANTIC_CHUNKING = True

# Параметры retry для ChromaDB
MAX_RETRIES = 3
RETRY_DELAY = 1  # seconds


# ==================== ENV VARS OVERRIDE ====================


def _read_global_config() -> dict[str, object]:
    """
    Read global config from ~/.cursor_rag/config.json.

    Returns:
        dict[str, Any]: Parsed config; empty dict on missing/invalid file.
    """
    try:
        if not DEFAULT_CONFIG_PATH.exists():
            return {}
        with open(DEFAULT_CONFIG_PATH, encoding="utf-8") as f:
            data = json.load(f)
        if not isinstance(data, dict):
            return {}
        return {str(k): v for k, v in data.items()}
    except Exception:
        return {}


def _write_global_config(data: dict[str, object]) -> None:
    """
    Write global config to ~/.cursor_rag/config.json.
    """
    DEFAULT_DB_PATH.mkdir(parents=True, exist_ok=True)
    tmp = DEFAULT_CONFIG_PATH.with_suffix(".json.tmp")
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
    _ = tmp.replace(DEFAULT_CONFIG_PATH)


def set_saved_model(model_name: str) -> None:
    """
    Persist default embedding model in the global config.
    """
    data = _read_global_config()
    data["model"] = model_name
    _write_global_config(data)


def get_saved_model() -> str | None:
    """
    Read saved model from the global config.
    """
    model = _read_global_config().get("model")
    return model if isinstance(model, str) and model.strip() else None


def get_model_info() -> tuple[str, str]:
    """
    Get effective embedding model and its source.

    Priority:
    1) CURSOR_RAG_MODEL env var
    2) ~/.cursor_rag/config.json ("model")
    3) DEFAULT_MODEL
    """
    env_model = os.getenv("CURSOR_RAG_MODEL")
    if env_model:
        return env_model, "env"

    saved = get_saved_model()
    if saved:
        return saved, "config"

    return DEFAULT_MODEL, "default"


def get_db_path(project_name: str | None = None) -> Path:
    """
    Получить путь к базе данных.

    Порядок приоритета:
    1. Переменная окружения CURSOR_RAG_DB_PATH
    2. Дефолтный путь ~/.cursor_rag

    Args:
        project_name: Имя проекта (будет добавлено как подпапка, если указано)

    Returns:
        Path: Полный путь к директории базы данных
    """
    env_path = os.getenv("CURSOR_RAG_DB_PATH")

    if env_path:
        base_path = Path(env_path).expanduser().resolve()
    else:
        base_path = DEFAULT_DB_PATH

    if project_name:
        return base_path / project_name

    return base_path


def get_model() -> str:
    """
    Получить название модели для эмбеддингов.

    Returns:
        str: Название модели
    """
    return get_model_info()[0]


def get_chunk_size() -> int:
    """
    Получить размер чанка для индексации.

    Returns:
        int: Размер чанка в символах
    """
    try:
        return int(os.getenv("CURSOR_RAG_CHUNK_SIZE", str(DEFAULT_CHUNK_SIZE)))
    except ValueError:
        return DEFAULT_CHUNK_SIZE


def get_chunk_overlap() -> int:
    """
    Получить размер перекрытия между чанками.

    Returns:
        int: Размер перекрытия в символах
    """
    try:
        return int(os.getenv("CURSOR_RAG_CHUNK_OVERLAP", str(DEFAULT_CHUNK_OVERLAP)))
    except ValueError:
        return DEFAULT_CHUNK_OVERLAP


def get_min_chunk_size() -> int:
    """
    Получить минимальный размер чанка. Маленькие чанки будут объединяться с соседними, если возможно.

    Returns:
        int: Минимальный размер чанка в символах
    """
    try:
        return int(os.getenv("CURSOR_RAG_MIN_CHUNK_SIZE", str(DEFAULT_MIN_CHUNK_SIZE)))
    except ValueError:
        return DEFAULT_MIN_CHUNK_SIZE


def get_enable_semantic_chunking() -> bool:
    """
    Включить/выключить семантический чанкинг кода.

    Returns:
        bool: True если включено
    """
    val = os.getenv("CURSOR_RAG_SEMANTIC_CHUNKING")
    if val is None:
        return DEFAULT_ENABLE_SEMANTIC_CHUNKING
    return val.strip().lower() in {"1", "true", "yes", "on"}


def get_ignore_dirs() -> set[str]:
    """
    Получить набор игнорируемых директорий.

    Можно добавить дополнительные через CURSOR_RAG_IGNORE_DIRS (через запятую).

    Returns:
        set[str]: Множество имен директорий для игнорирования
    """
    extra_dirs = os.getenv("CURSOR_RAG_IGNORE_DIRS", "")
    if extra_dirs:
        extra_set = {d.strip() for d in extra_dirs.split(",") if d.strip()}
        return IGNORE_DIRS | extra_set
    return IGNORE_DIRS.copy()


def get_ignore_ext() -> set[str]:
    """
    Получить набор игнорируемых расширений файлов.

    Можно добавить дополнительные через CURSOR_RAG_IGNORE_EXT (через запятую).

    Returns:
        set[str]: Множество расширений для игнорирования
    """
    extra_ext = os.getenv("CURSOR_RAG_IGNORE_EXT", "")
    if extra_ext:
        extra_set = {
            ext.strip() if ext.startswith(".") else f".{ext.strip()}" for ext in extra_ext.split(",") if ext.strip()
        }
        return IGNORE_EXT | extra_set
    return IGNORE_EXT.copy()


def get_allowed_ext() -> set[str]:
    """
    Получить набор разрешенных расширений файлов.

    Можно переопределить через CURSOR_RAG_ALLOWED_EXT (через запятую).

    Returns:
        set[str]: Множество разрешенных расширений
    """
    custom_ext = os.getenv("CURSOR_RAG_ALLOWED_EXT", "")
    if custom_ext:
        return {
            ext.strip() if ext.startswith(".") else f".{ext.strip()}" for ext in custom_ext.split(",") if ext.strip()
        }
    return ALLOWED_EXT.copy()


# ==================== UTILITIES ====================


def ensure_db_path(db_path: Path) -> Path:
    """
    Убедиться, что путь к БД существует, создать если нужно.

    Args:
        db_path: Путь к директории базы данных

    Returns:
        Path: Проверенный и созданный путь
    """
    db_path.mkdir(parents=True, exist_ok=True)
    return db_path


def print_config_info():
    """
    Вывести информацию о текущей конфигурации (для отладки).
    """
    print("📋 Текущая конфигурация:")
    print(f"  DB Path: {get_db_path()}")
    model, source = get_model_info()
    print(f"  Model: {model} (source: {source})")
    print(f"  Chunk Size: {get_chunk_size()}")
    print(f"  Chunk Overlap: {get_chunk_overlap()}")
    print(f"  Min Chunk Size: {get_min_chunk_size()}")
    print(f"  Semantic Chunking: {get_enable_semantic_chunking()}")
    print(f"  Ignore Dirs: {len(get_ignore_dirs())} директорий")
    print(f"  Ignore Ext: {len(get_ignore_ext())} расширений")
    print(f"  Allowed Ext: {len(get_allowed_ext())} расширений")
