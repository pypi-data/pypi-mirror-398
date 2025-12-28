def test_index_page_loads(app, client):
    """
    GIVEN a flask app client object
    WHEN a get request to the index page is made
    THEN check the response is valid and contains the expected string
    in the its data.
    """

    response = client.get("/index")
    assert response.data == client.get("/").data
    assert response.status_code == 200

    required_substrings = [
        b"Welcome to Easy Image Labeling",
        b"How to Use",
        b"Classify Dataset",
    ]
    for required_substring in required_substrings:
        assert required_substring in response.data
