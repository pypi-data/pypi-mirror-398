

def list_states(country: str, **kwargs):
    """
    lists all the states of the given country

    Args:
        country: name of the country

    Returns:
        List[str]: states of the given country
    """
    test_data = {
        "india": [
            "Andhra Pradesh",
            "Arunachal Pradesh",
            "Assam",
            "Bihar",
            "Chhattisgarh",
            "Goa",
            "Gujarat",
            "Haryana",
            "Himachal Pradesh",
            "Jharkhand",
            "Karnataka",
            "Kerala",
        ],
        "us": [
            "Texas",
            "California"
        ]
    }

    return test_data[country.lower()]