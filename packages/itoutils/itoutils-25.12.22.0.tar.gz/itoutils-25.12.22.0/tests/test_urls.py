from itoutils.urls import add_url_params


def test_add_url_params():
    base_url = "http://localhost/test?next=/path%3Fparam1%3D100%26param2%3Dabc"

    url_test = add_url_params(base_url, {"test": "value"})
    assert url_test == "http://localhost/test?next=%2Fpath%3Fparam1%3D100%26param2%3Dabc&test=value"

    url_test = add_url_params(base_url, {"mypath": "%2Fvalue%2Fpath"})

    assert url_test == ("http://localhost/test?next=%2Fpath%3Fparam1%3D100%26param2%3Dabc&mypath=%252Fvalue%252Fpath")

    url_test = add_url_params(base_url, {"mypath": None})

    assert url_test == "http://localhost/test?next=%2Fpath%3Fparam1%3D100%26param2%3Dabc"

    url_test = add_url_params(base_url, {"mypath": ""})

    assert url_test == "http://localhost/test?next=%2Fpath%3Fparam1%3D100%26param2%3Dabc&mypath="
