import sqlite3
from datetime import datetime
from dataclasses import dataclass
from contextlib import contextmanager


LabeledImage = tuple[int, str, str]
LabeledImageColumns = ["DatasetID", "ImageName", "LabelName"]


@contextmanager
def sqlite_connection(db_path):
    """Context manager for SQLite database connection."""
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    try:
        yield cursor
        conn.commit()
    except Exception as e:
        conn.rollback()
        raise e
    finally:
        conn.close()


def insert_labels(cur: sqlite3.Cursor, dataset: str, labels: list[str]) -> None:
    """
    Insert labels into database.
    """
    dataset_ids = list(range(1, len(labels) + 1))
    dataset_name_list = [dataset] * len(labels)
    data = list(zip(dataset_name_list, labels, dataset_ids))
    cur.executemany(
        "INSERT INTO Label (Dataset, LabelName, DatasetID) VALUES (?, ?, ?)",
        data,
    )


def bulk_insert_images(
    cur: sqlite3.Cursor,
    dataset: str,
    image_names: list[str],
    chunk_size: int,
    start_dataset_index: int = 1,
) -> None:
    """
    Insert entire dataset of images into Image table in a chunked-wise
    fashion.
    """

    def chunk_data(data):
        for i in range(0, len(data), chunk_size):
            yield data[i : i + chunk_size]

    dataset_ids = list(
        range(start_dataset_index, start_dataset_index + len(image_names))
    )
    dataset_name_list = [dataset] * len(image_names)
    data = list(zip(dataset_name_list, image_names, dataset_ids))
    for chunked_data in chunk_data(data):
        cur.executemany(
            "INSERT INTO Image (Dataset, ImageName, DatasetID) VALUES (?, ?, ?)",
            chunked_data,
        )


def remove_dataset_from_db(cur: sqlite3.Cursor, dataset: str) -> None:
    """
    Remove all images and labels that belong to the given dataset.
    """
    cur.execute("DELETE FROM Image WHERE Dataset = ?", (dataset,))
    cur.execute("DELETE FROM Label WHERE Dataset = ?", (dataset,))


def get_lowest_dataset_id(
    cur: sqlite3.Cursor, dataset: str, only_skipped: bool = False
) -> int:
    """
    Retrieve lowest DatasetId of row in Image table, that contains
    unlabelled image. If `only_skipped` is True, retrieve the lowest
    DatasetId of all skipped images in the dataset.
    """
    if only_skipped:
        return cur.execute(
            "SELECT MIN(DatasetID) FROM Image WHERE Dataset = ? AND LabelName = ?",
            (dataset, "Unknown"),
        ).fetchone()[0]

    return cur.execute(
        "SELECT MIN(DatasetID) FROM Image WHERE Dataset = ? AND LabelName IS NULL",
        (dataset,),
    ).fetchone()[0]


def get_next_dataset_id(
    cur: sqlite3.Cursor, dataset: str, dataset_id: int, only_skipped: bool = False
) -> int | None:
    """
    The parameters `dataset` and `dataset_id` uniquely identify an image
    in the Image table. If only skipped is False, return the lowest
    larger DatasetID in the same dataset, i.e. DatasetID + 1 if that
    entry exists or None if it does not exist. Else, return the lowest
    larger DatasetID of a skipped image in the dataset. If no skipped
    image exists, return None.
    """
    if only_skipped:
        return cur.execute(
            "SELECT MIN(DatasetID) FROM Image WHERE Dataset = ? AND LabelName = ? AND DatasetID > ?",
            (dataset, "Unknown", dataset_id),
        ).fetchone()[0]

    max_size = get_size_of_dataset(cur, dataset)
    if dataset_id + 1 > max_size:
        return None
    else:
        return dataset_id + 1


def get_previous_dataset_id(
    cur: sqlite3.Cursor, dataset: str, dataset_id: int, only_skipped: bool = False
) -> int | None:
    """
    The parameters `dataset` and `dataset_id` uniquely identify an image
    in the Images table. If only skipped is False, return the highest
    lower DatasetID in the same dataset, i.e. DatasetID - 1 if that
    entry exists or None if it does not exist. Else, return the highest
    lower DatasetID of a skipped image in the dataset. If no skipped
    image exists, return None.
    """
    if only_skipped:
        return cur.execute(
            "SELECT MAX(DatasetID) FROM Image WHERE Dataset = ? AND LabelName = ? AND DatasetID < ?",
            (dataset, "Unknown", dataset_id),
        ).fetchone()[0]

    if dataset_id <= 1:
        return None
    else:
        return dataset_id - 1


def get_image_name(cur: sqlite3.Cursor, dataset: str, dataset_id: int) -> int:
    """
    Retrieve image name for given Dataset and DatasetId.
    """
    image_name = cur.execute(
        "SELECT ImageName FROM Image WHERE Dataset = ? AND DatasetID = ?",
        (dataset, dataset_id),
    ).fetchone()[0]
    return image_name


def get_size_of_dataset(cur: sqlite3.Cursor, dataset: str) -> int:
    """
    Retrieve the totatl number of images in the specified dataset.
    """
    return cur.execute(
        "SELECT MAX(DatasetID) FROM Image WHERE Dataset = ?",
        (dataset,),
    ).fetchone()[0]


def get_skipped_image_ids(cur: sqlite3.Cursor, dataset: str) -> list[str]:
    """
    Retrieve the DatasetIDs of skipped images in the specified dataset.
    """
    return cur.execute(
        "SELECT DatasetID FROM Image WHERE Dataset = ? AND LabelName = ?",
        (dataset, "Unknown"),
    ).fetchall()


def get_num_of_labelled_images(cur: sqlite3.Cursor, dataset: str) -> int:
    """
    Retrieve the number of labelled images (skipped images included) in
    the specified dataset.
    """
    return cur.execute(
        "SELECT COUNT(*) FROM Image WHERE Dataset = ? AND LabelName IS NOT NULL",
        (dataset,),
    ).fetchone()[0]


def get_labels(cur: sqlite3.Cursor, dataset: str) -> list[str]:
    """
    Retrieve all labels belonging to a dataset.
    """
    labels = cur.execute(
        "SELECT LabelName FROM Label WHERE Dataset = ?",
        (dataset,),
    ).fetchall()
    return list(map(lambda _tuple: _tuple[0], labels))


def get_results_by_dataset(cur: sqlite3.Cursor, dataset: str) -> list[LabeledImage]:
    """
    Retrieve DatasetID, ImageName and LabelName columns of all images
    belonging to the specified dataset ordered by the DatasetID column.
    """
    results = cur.execute(
        "SELECT DatasetID, ImageName, LabelName FROM Image WHERE Dataset = ? ORDER BY DatasetID",
        (dataset,),
    ).fetchall()
    return results


def set_image_label(
    cur: sqlite3.Cursor, dataset: str, dataset_id: int, label: str | None
) -> None:
    """
    Set label column of image inside dataset with given dataset id to
    specified value. If no label is specified, set label to 'Unknown'.
    """
    label_date = datetime.now()
    if label is None:
        label = "Unknown"  # Skipped images appear with label "Unknown" in database
    cur.execute(
        "UPDATE IMAGE SET (LabelName, LastLabelDate) = (?, ?) WHERE Dataset = ? AND DatasetID = ?",
        (label, label_date, dataset, dataset_id),
    )


def reset_dataset_labels(cur: sqlite3.Cursor, dataset: str) -> None:
    cur.execute(
        "UPDATE IMAGE SET (LabelName, LastLabelDate) = (NULL, NULL) WHERE Dataset = ?",
        (dataset,),
    )
