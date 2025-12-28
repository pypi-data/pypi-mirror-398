from easy_image_labeling.db.db import (
    insert_labels,
    bulk_insert_images,
    remove_dataset_from_db,
    get_lowest_dataset_id,
    get_next_dataset_id,
    get_previous_dataset_id,
)

import pytest
import random


def test_insert_labels(get_test_db):
    """
    GIVEN an empty database
    WHEN labels are added to  two datasets
    THEN check Dataset, LabelName, DatasetID fields from the Label
    table are defined correctly.
    """

    dataset_name1 = "Dataset1"
    dataset_name2 = "Dataset2"

    # Create new labels
    labels1 = ["MyLabel1", "MyLabel2", "MyLabel3"]
    labels2 = ["MyOtherLabel1", "MyOtherLabel2"]

    # Insert into database
    insert_labels(get_test_db, dataset_name1, labels1)
    insert_labels(get_test_db, dataset_name2, labels2)

    # Check labels
    data = get_test_db.execute("SELECT * FROM Label").fetchall()
    total_ids, datasets, label_names, dataset_ids = tuple(zip(*data))
    assert total_ids == tuple(range(1, len(labels1) + len(labels2) + 1))
    assert datasets == tuple(
        [dataset_name1] * len(labels1) + [dataset_name2] * len(labels2)
    )
    assert label_names == tuple(labels1 + labels2)
    assert dataset_ids == tuple(
        list(range(1, len(labels1) + 1)) + list(range(1, len(labels2) + 1))
    )


def test_bulk_insert_images(get_test_db):
    """
    GIVEN an empty database
    WHEN 2 new datasets are added with 10 images each
    THEN check the Dataset, ImageName, DatasetID fields are defined
    correctly.
    """

    # Create 2 datasets
    dataset_name1 = "MyDataset"
    dataset_name2 = "MyOtherDataset"
    image_names1 = [f"MyImage{i}" for i in range(1, 11)]
    image_names2 = image_names1.copy()
    random.shuffle(image_names2)

    # Insert into database
    bulk_insert_images(get_test_db, dataset_name1, image_names1, chunk_size=10)
    bulk_insert_images(get_test_db, dataset_name2, image_names2, chunk_size=10)

    # Check results
    data = get_test_db.execute("SELECT * FROM Image").fetchall()
    total_ids, datasets, image_names, dataset_ids, labels, label_dates = tuple(zip(*data))
    assert total_ids == tuple(range(1, 21))
    assert datasets == tuple([dataset_name1] * 10 + [dataset_name2] * 10)
    assert image_names[: len(image_names1)] == tuple(image_names1)
    assert image_names[len(image_names1) :] == tuple(image_names2)
    assert dataset_ids == tuple(
        list(range(1, len(image_names1) + 1)) + list(range(1, len(image_names2) + 1))
    )
    assert all(label == None for label in labels)
    assert all(label_date == None for label_date in label_dates)


def test_remove_dataset_from_db(get_test_db, add_dataset, add_labels):
    """
    GIVEN a database with 2 datasets and corresponding labels
    WHEN 1 dataset is removed from the database
    THEN check if the correct database and labels were removed.
    """

    # Add datasets and labels to empty database (this is part of setup)
    dataset_name1 = "Dataset1"
    dataset_name2 = "Dataset2"
    labels1 = ["MyLabel1", "MyLabel2"]
    labels2 = ["MyLabel1", "MyLabel2", "MyLabel3"]
    add_dataset(dataset_name1, 10)
    add_dataset(dataset_name2, 10)
    add_labels(labels1, dataset_name1)
    add_labels(labels2, dataset_name2)
    image_data_before_test = get_test_db.execute("SELECT * FROM Image").fetchall()
    label_data_before_test = get_test_db.execute("SELECT * FROM Label").fetchall()
    assert len(image_data_before_test) == 20
    assert image_data_before_test[0][1] == dataset_name1
    assert image_data_before_test[-1][1] == dataset_name2
    assert len(label_data_before_test) == 5
    assert label_data_before_test[0][2] == labels1[0]
    assert label_data_before_test[-1][2] == labels2[-1]

    # Remove labels for dataset 2
    remove_dataset_from_db(get_test_db, dataset_name2)

    # Check if all entries belonging to dataset 2 were removed and
    # entries belonging to dataset 1 still exist
    image_data_after_test = get_test_db.execute("SELECT * FROM Image").fetchall()
    label_data_after_test = get_test_db.execute("SELECT * FROM Label").fetchall()
    assert image_data_after_test == list(
        filter(lambda entry: dataset_name1 in entry, image_data_before_test)
    )
    assert label_data_after_test == list(
        filter(lambda entry: dataset_name1 in entry, label_data_before_test)
    )


def test_get_lowest_dataset_id(get_test_db, fill_db):
    """
    GIVEN a database with 2 datasets and corresponding labels
    WHEN the lowest unlabeled dataset id for a datast is retrieved
    THEN check if the returned image id is the expected one.
    """

    # Create database with 2 datasets and 3 label categories. Assign
    # labels such that first unlabeled entry in first dataset has
    # DatasetID=4.
    fill_db([[1, 2, 3, 10, 11, 15], [4, 6, 8, 13], [16, 17, 18]])
    lowest_image_id = get_lowest_dataset_id(get_test_db, "Dataset1")
    assert lowest_image_id == 4


def test_get_lowest_skipped_image_id(get_test_db, fill_db):
    """
    GIVEN a database with 2 datasets and corresponding labels
    WHEN the lowest unlabeled dataset id for a datast is retrieved
    THEN check if the returned image id is the expected one.
    """

    # Create database with 2 datasets. Assign labels such that first
    # skipped entry in second dataset has DatasetID=4.
    fill_db(None, [15, 17, 19])
    lowest_image_id = get_lowest_dataset_id(get_test_db, "Dataset2", only_skipped=True)
    assert lowest_image_id == 4


@pytest.mark.parametrize(
    "start_dataset_id, expected_next_id", [(0, 1), (5, 6), (11, None), (9, None)]
)
def test_get_next_dataset_id(
    get_test_db, add_dataset, start_dataset_id, expected_next_id
):
    """
    GIVEN a database with 2 datasets
    WHEN the next dataset id starting from a random dataset id in dataset 1
    THEN check if the returned image id is the expected one.
    """

    # Create database with 2 datasets.
    dataset_name1 = "Dataset1"
    dataset_name2 = "Dataset2"
    add_dataset(dataset_name1, 10)
    add_dataset(dataset_name2, 10)
    next_lowest_image_id = get_next_dataset_id(
        get_test_db, dataset_name1, start_dataset_id
    )
    assert next_lowest_image_id == expected_next_id


@pytest.mark.parametrize(
    "dataset, start_dataset_id, expected_next_id",
    [
        ("Dataset1", -1, 0),
        ("Dataset1", 0, 1),
        ("Dataset1", 1, 2),
        ("Dataset1", 2, 8),
        ("Dataset1", 9, None),
        ("Dataset2", 0, 1),
        ("Dataset2", 2, 4),
        ("Dataset2", 8, None),
    ],
)
def test_get_next_skipped_dataset_id(
    get_test_db, fill_db, dataset, start_dataset_id, expected_next_id
):
    """
    GIVEN a database with 2 datasets and some labeled images
    WHEN the next skipped dataset id starting from a random dataset id in dataset 1
    THEN check if the returned image id is the expected one.
    """

    # Create database with 2 datasets.
    fill_db(None, [1, 2, 3, 9, 10, 11, 12, 15, 19])
    next_lowest_image_id = get_next_dataset_id(
        get_test_db, dataset, start_dataset_id, only_skipped=True
    )
    assert next_lowest_image_id == expected_next_id


@pytest.mark.parametrize(
    "start_dataset_id, expected_previous_id", [(9, 8), (6, 5), (-1, None), (0, None)]
)
def test_previous_dataset_id(
    get_test_db, add_dataset, start_dataset_id, expected_previous_id
):
    """
    GIVEN a database with 2 datasets
    WHEN the previous dataset id starting from a random dataset id in dataset 1
    THEN check if the returned image id is the expected one.
    """

    # Create database with 2 datasets.
    dataset_name1 = "Dataset1"
    dataset_name2 = "Dataset2"
    add_dataset(dataset_name1, 10)
    add_dataset(dataset_name2, 10)
    previous_dataset_id = get_previous_dataset_id(
        get_test_db, dataset_name2, start_dataset_id
    )
    assert previous_dataset_id == expected_previous_id


@pytest.mark.parametrize(
    "dataset, start_dataset_id, expected_next_id",
    [
        ("Dataset1", 0, None),
        ("Dataset1", 1, 0),
        ("Dataset1", 2, 1),
        ("Dataset1", 8, 2),
        ("Dataset1", 9, 8),
        ("Dataset2", 1, 0),
        ("Dataset2", 4, 1),
        ("Dataset2", 8, 4),
    ],
)
def test_get_previous_skipped_dataset_id(
    get_test_db, fill_db, dataset, start_dataset_id, expected_next_id
):
    """
    GIVEN a database with 2 datasets and some labeled images
    WHEN the next skipped dataset id starting from a random dataset id in dataset 1
    THEN check if the returned image id is the expected one.
    """

    # Create database with 2 datasets.
    fill_db(None, [1, 2, 3, 9, 10, 11, 12, 15, 19])
    next_lowest_image_id = get_previous_dataset_id(
        get_test_db, dataset, start_dataset_id, only_skipped=True
    )
    assert next_lowest_image_id == expected_next_id
