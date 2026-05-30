from pathlib import Path

from werkzeug.utils import secure_filename

from ..dao import RAW_DIR, CLEANED_DIR, MODELS_DIR, ensure_data_dirs
from ..dao.dataset_dao import DatasetDAO

ALLOWED_EXTENSIONS = {"csv", "xlsx"}


def _allowed_file(filename: str) -> bool:
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS


def save_dataset(file, dataset_type: str = "dataset") -> str:
    """Save an uploaded file to data/datasets/raw/, create DB record.

    Returns the sanitised filename.
    Raises ValueError for invalid files, FileExistsError for duplicates.
    """
    ensure_data_dirs()

    if not file or not file.filename:
        raise ValueError("未选择文件")

    filename = secure_filename(file.filename)
    if not filename or not _allowed_file(filename):
        raise ValueError(f"不支持的文件格式，仅允许: {', '.join(ALLOWED_EXTENSIONS)}")

    dao = DatasetDAO()
    if dao.filename_exists(filename):
        raise FileExistsError(f"文件 {filename} 已存在，请重命名后重新上传")

    ext = filename.rsplit(".", 1)[1].lower()
    file_path = RAW_DIR / filename
    file.save(str(file_path))

    dao.insert(
        filename=filename,
        metadata={
            "file_type": ext,
            "file_path": str(file_path.resolve()),
            "is_cleaned": False,
            "clean_type": None,
        },
    )
    return filename


def get_raw_path(filename: str) -> Path:
    return RAW_DIR / filename


def get_cleaned_path(filename: str) -> Path:
    return CLEANED_DIR / filename


def get_model_path(model_name: str) -> Path:
    return MODELS_DIR / model_name
