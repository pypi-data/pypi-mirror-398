from urllib.parse import quote


def construct_zillow_basic_property_url(property_address: str) -> str:
    """
    Constructs a Zillow property URL by encoding the address to be URL-safe.
    :param property_address: The address of the property, e.g., "123 Main St, Anytown, USA"
    :return: A URL string pointing to the Zillow listing
    """
    encoded_address = quote(property_address)
    return f'https://www.zillow.com/homes/{encoded_address}'
