from deepparse.parser import AddressParser
from deepparse.parser.formatted_parsed_address import FormattedParsedAddress

from inoopa_utils.custom_types.exceptions import AddressParserError
from inoopa_utils.custom_types.companies import ParsedAddress, Address

# Make it a global variable to avoid loading the model each time the function is called
PARSER = AddressParser(model_type="bpemb")


def parse_address(address: Address) -> Address:
    """Parse an Address object, update it with the parsed info and return the updated Address."""
    if address.string_address is None:
        return address
    parsed_address = parse_string_address(address.string_address)

    address.street = parsed_address.street
    address.number = parsed_address.number
    address.city = parsed_address.city
    address.postal_code = parsed_address.postal_code

    return address


def parse_string_address(address: str) -> ParsedAddress:
    """
    Parse a string address and return a ParsedAddress object.

    :param address: The address to parse in string format.
    :return: A ParsedAddress object.

    :raises AddressParserError: If the address parser fails to parse the address.
    """
    parsed_address = PARSER(address)
    if not isinstance(parsed_address, FormattedParsedAddress):
        raise AddressParserError(f"The address parser failed to parse the address: {address}")
    # Store the parsed address in a dataclass because the default parsed address type is not well structured
    parsed_address = ParsedAddress(
        street=parsed_address.StreetName,
        number=parsed_address.StreetNumber,
        city=parsed_address.Municipality,
        postal_code=parsed_address.PostalCode,
    )
    return parsed_address


if __name__ == "__main__":
    address = parse_string_address("1 rue de la paix 75001 Paris")
    print(address)
