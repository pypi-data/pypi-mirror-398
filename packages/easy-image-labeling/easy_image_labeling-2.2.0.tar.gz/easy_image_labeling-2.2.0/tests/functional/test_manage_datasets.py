def test_create_new_dataset(client, tmp_path, create_tmp_dataset):
    """
    GIVEN an app instance
    WHEN dataset is uploaded in /config/upload_dataset
    THEN check if the uploaded images are accessible from the classfication endpoint.
    """

    create_tmp_dataset()

    data = {"files": [], "dataset_name": "temp_dataset"}

    # Open each file and add it as a tuple: (filename, file object)
    for file in (tmp_path / "temp_dataset").glob("*"):
        with open(file, "rb") as f:
            data["files"].append((file.absolute(), file.name))

    # Add 2 labels inside the session object
    label_names = dict()
    for i in (1, 2):
        label_names[f"label_{i}"] = f"test_label_{i}"
    with client.session_transaction() as session:
        session["label_names"] = label_names

    # Add new temporary dataset
    response = client.post(
        "/config/upload_folder", data=data, content_type="multipart/form-data"
    )
    assert response.status_code == 302 # Redirection to index page is expected

    # Check if every of the 20 different images are available via the
    requests = [f"classify/temp_dataset/{i}" for i in range(1, 21)]
    responses = map(client.get, requests)
    assert all(map(lambda r: r.status_code == 200, responses))
