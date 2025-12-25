from urllib.parse import parse_qsl, urlencode, urlsplit


def add_url_params(url: str, params: dict[str, str]) -> str:
    """Add GET params to provided URL being aware of existing.

    :param url: string of target URL
    :param params: dict containing requested params to be added
    :return: string with updated URL

    >> url = 'http://localhost:8000/login/activate_employer_account?next_url=%2Finvitations
    >> new_params = {'test': 'value' }
    >> add_url_params(url, new_params)
    'http://localhost:8000/login/activate_employer_account?next_url=%2Finvitations&test=value
    """

    # Remove params with None values
    params = {key: value for key, value in params.items() if value is not None}

    url_parts = urlsplit(url)
    query = dict(parse_qsl(url_parts.query))
    query.update(params)

    new_url = url_parts._replace(query=urlencode(query)).geturl()

    return new_url
