import re
from decimal import Decimal, InvalidOperation
from typing import List

from colorfulPyPrint.py_color import print_error, print_exception, print_magenta, print_info
from datetimeops.datetime_utils import validate_date, hhmmss_check
from string_list import list_from_string, string_from_list, str_enumerate


def is_valid_custom(user_input: str, expected_inputs: list) -> str:
    if user_input in expected_inputs:
        return user_input
    else:
        print_error(f"Error: expected {expected_inputs}")
        raise ValueError(f"{user_input} is not in {expected_inputs}")


def is_not_in(user_input: str, not_in: list) -> str:
    not_in = [n.lower() for n in not_in]
    if user_input.lower() not in not_in:
        return user_input
    else:
        print_error(f"Error: Value already exists in {not_in}")
        raise ValueError(f"{user_input} can not be in {not_in}")


def is_yes_no(user_input: str) -> str:
    user_input = user_input.strip().lower()
    return is_valid_custom(user_input, ['y', 'n'])


def none_if_blank(user_input: str):
    return None if len(user_input) == 0 else user_input


def is_not_blank(user_input: str, expected_inputs: List[str] = None) -> str:
    if len(user_input) == 0:
        print_error("Error: Can not be blank.")
        raise ValueError(f"Can not be blank")
    if expected_inputs is not None:
        if str(user_input) not in expected_inputs:
            print_error(f"Error: expected {expected_inputs}")
            raise ValueError(f"{user_input} is not in {expected_inputs}")
    try:
        return str(user_input)
    except Exception:
        print_error("Error: String values only.")
        raise ValueError(f"{user_input} is not valid string")


def is_valid_int(user_input: str, expected_inputs: List[int] = None,
                 maximum: int = None, minimum: int = None) -> int:
    if expected_inputs is not None:
        if int(user_input) not in expected_inputs:
            print_error(f"Error: expected {expected_inputs}")
            raise ValueError(f"{user_input} is not in {expected_inputs}")
    if maximum is not None and int(user_input) > maximum:
        print_error(f"Error: {user_input} is greater than {maximum}")
        raise ValueError(f"{user_input} has to be less than {maximum}")
    if minimum is not None and int(user_input) < minimum:
        print_error(f"Error: {user_input} is less than {minimum}")
        raise ValueError(f"{user_input} has to be more than {minimum}")
    try:
        return int(user_input)
    except Exception:
        print_error("Error: Integer values only.")
        raise ValueError(f"{user_input} is not valid integer")


def is_valid_float(user_input: str, expected_inputs: List[float] = None,
                   maximum: float = None, minimum: float = None) -> float:
    if expected_inputs is not None:
        if float(user_input) not in expected_inputs:
            print_error(f"Error: expected {expected_inputs}")
            raise ValueError(f"{user_input} is not in {expected_inputs}")
    if maximum is not None and float(user_input) > maximum:
        print_error(f"Error: {user_input} is greater than {maximum}")
        raise ValueError(f"{user_input} has to be less than {maximum}")
    if minimum is not None and float(user_input) < minimum:
        print_error(f"Error: {user_input} is less than {minimum}")
        raise ValueError(f"{user_input} has to be more than {minimum}")
    try:
        return float(user_input)
    except Exception:
        print_error("Error: Float values only.")
        raise ValueError(f"{user_input} is not valid float")


def is_valid_decimal(
    user_input: str,
    expected_inputs: List[Decimal] = None,
    maximum: Decimal = None,
    minimum: Decimal = None,
) -> Decimal:
    try:
        value = Decimal(user_input)
    except (InvalidOperation, ValueError):
        print_error("Error: Decimal values only.")
        raise ValueError(f"{user_input} is not valid decimal")

    if expected_inputs is not None:
        if value not in expected_inputs:
            print_error(f"Error: expected {expected_inputs}")
            raise ValueError(f"{user_input} is not in {expected_inputs}")

    if maximum is not None and value > maximum:
        print_error(f"Error: {user_input} is greater than {maximum}")
        raise ValueError(f"{user_input} has to be less than {maximum}")

    if minimum is not None and value < minimum:
        print_error(f"Error: {user_input} is less than {minimum}")
        raise ValueError(f"{user_input} has to be more than {minimum}")

    return value


def is_valid_alpha(user_input: str) -> str:
    if user_input.isalpha():
        return user_input
    else:
        print_error("Error: Alphabets only [A-Z]")
        raise ValueError(f"{user_input} is not valid alpha value")


def is_valid_alphanum(user_input: str) -> str:
    if user_input.isalnum():
        return user_input
    else:
        print_error("Error: Alphanumeric values only [A-Z0-9]")
        raise ValueError(f"{user_input} is not valid alphanumeric value")


def is_valid_regex(user_input: str, allowed_regex: str) -> str:
    if re.match(rf'{allowed_regex}', user_input):
        return user_input
    else:
        print_error(f"Error: Allowed regex: {allowed_regex}")
        raise ValueError(f"{user_input} has invalid format (allowed regex: {allowed_regex})")


def is_valid_char(user_input: str, allowed_char_regex: str) -> str:
    allowed_char_regex = f'[{allowed_char_regex}]'.replace('[[', '[').replace(']]', ']')
    if re.match(rf'^{allowed_char_regex}+$', user_input):
        return user_input
    else:
        print_error(f"Error: Allowed chars: {allowed_char_regex}")
        raise ValueError(f"{user_input} has invalid characters (allowed chars: {allowed_char_regex})")


# noinspection PyPep8Naming
def get_language_ISO_639_1(language):
    import pycountry
    if len(language) == 2:
        k = pycountry.languages.get(alpha_2=language)
    else:
        k = pycountry.languages.get(name=language)
    if k is None:
        raise ValueError(f"Incorrect Language '{language}' - see https://en.wikipedia.org/wiki/List_of_ISO_639-1_codes")
    else:
        print_magenta(f'{k.alpha_2}: {k.name}')
        return k.alpha_2


def is_valid_language(user_input: str) -> str:
    res = []
    try:
        for lang in list_from_string(user_input):
            if get_language_ISO_639_1(lang):
                res.append(lang)
        return string_from_list(res)
    except ValueError as e:
        print_exception(e)
        raise e


def is_valid_date(user_input: str) -> str:
    if validate_date(user_input) is False and validate_date(user_input, fmt="%Y-%m-%d") is False:
        print_error("Invalid date: (formats allowed: yyyy-mm-dd or yyyy-mm-dd hh:mm:ss)")
        raise ValueError(f"Invalid date: {user_input}")
    else:
        return user_input


def is_valid_date_future(user_input: str) -> str:
    if validate_date(user_input, chk_future_date=True) is False and \
            validate_date(user_input, fmt="%Y-%m-%d", chk_future_date=True) is False:
        print_error("Invalid Future Date: Date must be today or in the future. "
                    "(formats allowed: yyyy-mm-dd or yyyy-mm-dd hh:mm:ss)")
        raise ValueError(f"Invalid future date: {user_input}")
    else:
        return user_input


def is_valid_time(user_input: str) -> str:
    try:
        return hhmmss_check(user_input)
    except Exception as e:
        print_error(f"Invalid time: {user_input} (format allowed: hh:mm:ss)")
        raise e


def is_url(user_input: str, ignore_subdomain_check=True, http_protocol_required=False) -> str:
    """
        Validates and processes a given URL string. It optionally checks if the URL belongs to a specific domain list.

    Args:
        user_input (str): The URL to validate and normalize.
        ignore_subdomain_check (bool, optional): If True, allows URLs without a subdomain. Defaults to True.
        http_protocol_required (bool, optional): If True, return with a http:// or https:// protocol. Defaults to False.

    Returns:
        str: The normalized URL.

    Examples:
        >> is_url('www.example.com')
        'www.example.com'

        >> is_url('https://www.example.com')
        'https://www.example.com'

        >> is_url('subdomain.example.com')
        'subdomain.example.com'

        >> is_url('example.com', ignore_subdomain_check=True)
        'example.com'
        
        >> is_url('subdomain.example.com/path?query=1')
        'subdomain.example.com/path?query=1'

        >> is_valid_ms_domain('subdomain.watchmyfilm.com')
        raises ValueError if the domain is not in the allowed list.

        >>> is_url('example.com', http_protocol_required=True)
        Please specify the protocol ('http://' or 'https://'): https://
        'https://example.com'
    """

    # Check and remove the protocol (http:// or https://) if it exists
    protocols = ('https://', 'http://')
    protocol = ''

    # Check and remove the protocol if it exists
    for proto in protocols:
        if user_input.startswith(proto):
            user_input = user_input[len(proto):]
            protocol = proto
            break

    try:
        # Splitting user_input into subdomain, domain and TLD
        try:
            subdomain, domain, tld = user_input.split('.')
        except ValueError as e:
            if ignore_subdomain_check:
                subdomain = ''
                domain, tld = user_input.split('.')
            else:
                raise e

        # Further splitting TLD into path and query parameters
        if '/' in tld:
            tld, path = tld.split('/', 1)
            path = '/' + path
        else:
            path = ''

        if '?' in path:
            path, queries = path.split('?', 1)
            queries = '?' + queries
        else:
            queries = ''
    except Exception as e:
        print_error(f"Incorrect URL format: {user_input}. "
                    f"Expected format like: 'www.watchmyfilm.com' / 'yiff.festivalsaints.com' / etc.")
        raise e

    # If no protocol was found and protocol_required is True, prompt user for a protocol
    if http_protocol_required and not protocol:
        enum_protocols = str_enumerate(list(protocols))
        while (pr := input("URL requires a protocol. Choose (0: https / 1: http) ")) not in enum_protocols.keys():
            print_error(f"Expected {list(enum_protocols.keys())}")
        protocol = enum_protocols[pr]

    # Return the formatted URL with the chosen or existing protocol
    return f"{protocol}{subdomain.lower()}.{domain.lower()}.{tld.lower()}{path}{queries}"


def is_valid_email(user_input: str, clean_up_email=False) -> str:
    from email_validator import validate_email, EmailNotValidError, EmailUndeliverableError
    common_tlds = ['com', 'org', 'net', 'edu', 'de', 'fr']

    def clean_domain(email: str) -> str:
        email_part, domain_name = email.split('@')
        clean_domain_name = re.match(r'^[^A-Z]*', domain_name).group(0)
        tld_match = next((tld for tld in common_tlds if re.search(rf'\.{tld}', clean_domain_name)), None)
        if tld_match:
            clean_domain_name = re.sub(rf'\.{tld_match}.*', f'.{tld_match}', clean_domain_name)
        return f"{email_part}@{clean_domain_name}"

    try:
        return validate_email(user_input)['email']
    except EmailUndeliverableError as e:
        if clean_up_email and 'The domain name' in e.args[0]:
            cleaned_email = clean_domain(user_input)
            print_info(f"Trying with cleaned domain: {cleaned_email}")
            try:
                return validate_email(cleaned_email)['email']
            except EmailUndeliverableError as e:
                print_error(f"EmailUndeliverableError: {cleaned_email}. {str(e)}")
                raise EmailUndeliverableError(f"EmailUndeliverableError: {user_input}. {str(e)}")
        else:
            print_error(f"EmailUndeliverableError: {user_input}. {str(e)}")
            raise EmailUndeliverableError(f"EmailUndeliverableError: {user_input}. {str(e)}")
    except EmailNotValidError as e:
        print_error(f"EmailNotValidError: {user_input}. {str(e)}")
        raise EmailNotValidError(f"EmailNotValidError: {user_input}. {str(e)}")


def is_valid_phone(user_input: str) -> str:
    user_input = re.sub(r'[ \-.()]', '', user_input)
    if re.match(r'^\+?\d+$', user_input):
        return user_input
    else:
        print_error(f"Invalid Phone: Should be in the format +91 0123456789")
        raise ValueError(f"Invalid Phone {user_input}: Should be in the format +910123456789)")


def is_valid_slug(user_input: str, delimiter='-') -> str:
    """
        Validates and sanitizes a slug by ensuring it contains only alphanumeric values and lowercase
        with a single delimiter. Removes leading/trailing delimiters and deduplicates them.

        Args:
            user_input (str): The slug to validate and sanitize.
            delimiter (str): The delimiter used in the slug (default is '-').

        Returns:
            str: A sanitized slug with only alphanumeric values and single delimiters.
        """
    # Remove leading/trailing delimiters
    slug = user_input.strip(delimiter)

    # Replace repeated delimiters with a single delimiter
    slug = re.sub(rf'{delimiter}+', delimiter, slug)

    # Ensure only alphanumeric characters and the delimiter remain
    slug = re.sub(rf'[^{delimiter}a-zA-Z0-9]', '', slug).lower()

    print_magenta(f"Slug: {slug}")
    return slug


__all__ = [
    "is_valid_custom",
    "is_not_in",
    "is_yes_no",
    "none_if_blank",
    "is_not_blank",
    "is_valid_int",
    "is_valid_float",
    "is_valid_decimal",
    "is_valid_alpha",
    "is_valid_alphanum",
    "is_valid_regex",
    "is_valid_char",
    "get_language_ISO_639_1",
    "is_valid_language",
    "is_valid_date",
    "is_valid_date_future",
    "is_valid_time",
    "is_url",
    "is_valid_email",
    "is_valid_phone",
    "is_valid_slug",
]
