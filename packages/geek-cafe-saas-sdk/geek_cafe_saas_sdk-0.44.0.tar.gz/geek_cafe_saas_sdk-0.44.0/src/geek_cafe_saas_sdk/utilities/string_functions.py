import hashlib
import secrets
import string
import uuid
import time
from geek_cafe_saas_sdk.utilities.logging_utility import LoggingUtility
from geek_cafe_saas_sdk.utilities.datetime_utility import DatetimeUtility

logger = LoggingUtility(__name__).logger


class StringFunctions:
    SPECIAL_CHARACTERS = "!\\#$%&()*+,-.:;<=>?@[]^_{|}~"

    @staticmethod
    def generate_random_string(length=12, digits=True, letters=True, special=False):
        characters = ""
        if letters:
            characters += string.ascii_letters
        if digits:
            characters += string.digits
        if special:
            characters += StringFunctions.SPECIAL_CHARACTERS

        random_string = "".join(secrets.choice(characters) for _ in range(length))
        return random_string

    @staticmethod
    def generate_random_password(length=15, digits=True, letters=True, special=True):
        characters = ""
        # we have a min lenght requirement of 8
        if length < 8:
            length = 8

        if letters:
            characters += string.ascii_letters
        if digits:
            characters += string.digits
        if special:
            characters += StringFunctions.SPECIAL_CHARACTERS

        if len(characters) == 0:
            raise RuntimeError(
                "You must choose at least one of the options: digits, letters, special"
            )

        # Ensure at least two characters from each selected set are included
        password = []
        if letters:
            # lower
            password.append(secrets.choice(string.ascii_lowercase))
            password.append(secrets.choice(string.ascii_lowercase))
            # upper
            password.append(secrets.choice(string.ascii_uppercase))
            password.append(secrets.choice(string.ascii_uppercase))
        if digits:
            password.append(secrets.choice(string.digits))
            password.append(secrets.choice(string.digits))
        if special:
            password.append(secrets.choice(StringFunctions.SPECIAL_CHARACTERS))
            password.append(secrets.choice(StringFunctions.SPECIAL_CHARACTERS))

        # Fill the remaining length with random characters from the selected sets
        remaining_length = length - len(password)
        password.extend(secrets.choice(characters) for _ in range(remaining_length))

        # Shuffle the password to randomize the order of characters
        secrets.SystemRandom().shuffle(password)

        return "".join(password)

    @staticmethod
    def wrap_text(text: str, max_width: int):
        """Wrap text at a specified width."""
        wrapped_text = ""
        if not text:
            return text

        while len(text) > max_width:
            # Find the maximum width position, breaking at max_width
            # If there are no spaces to break on, break at max_width directly
            break_point = (
                text.rfind(" ", 0, max_width) if " " in text[0:max_width] else max_width
            )
            if break_point == -1:  # no spaces found, hard break
                break_point = max_width
            wrapped_text += text[:break_point] + "\n"
            text = text[break_point:].lstrip()  # remove any leading space
        wrapped_text += text
        return wrapped_text

    @staticmethod
    def generate_uuid():
        return str(uuid.uuid4())

    @staticmethod
    def generate_hash(input_string: str) -> str:
        """
        Generates a SHA-256 hash for the given input string.

        Args:
        input_string (str): The string to hash.

        Returns:
        str: The resulting hash value as a hexadecimal string.
        """
        # Encode the input string to bytes
        encoded_string = input_string.encode()

        # Create a SHA-256 hash object
        hash_object = hashlib.sha256()

        # Update the hash object with the encoded string
        hash_object.update(encoded_string)

        # Get the hexadecimal representation of the hash
        hash_hex = hash_object.hexdigest()

        return hash_hex

    @staticmethod
    def generate_sortable_uuid():
        """
        Generates a unique id for the execution event
        """
        epoch_time = time.time()
        sortable_uuid: uuid.UUID = DatetimeUtility.uuid1_utc(timestamp=epoch_time)

        time_stamp = str(epoch_time).replace(".", "-")
        sortable_id = f"{time_stamp}:{str(sortable_uuid)}"
        return sortable_id

    @staticmethod
    def to_bool(value: str | bool | int | None) -> bool:
        """
        Converts a string or boolean value to a boolean.

        Args:
            value (str | bool | int | None): The value to convert.

        Returns:
            bool: The converted boolean value.

        Raises:
            ValueError: If the input value is not a valid boolean or string representation.
        """
        return StringFunctions.to_boolean(value)

    @staticmethod
    def to_boolean(value: str | bool | int | None) -> bool:
        """
        Converts a string or boolean value to a boolean.

        Args:
            value (str | bool | int | None): The value to convert.

        Returns:
            bool: The converted boolean value.

        Raises:
            ValueError: If the input value is not a valid boolean or string representation.
        """
        if isinstance(value, bool):
            return value
        if isinstance(value, str):
            value = str(value).lower().strip()
            if value in ("true", "1", "t", "y", "yes"):
                return True
            if value in ("false", "0", "f", "n", "no"):
                return False
            else:
                logger.warning(f"Invalid boolean value: {value}; returning False.")
                return False

        elif isinstance(value, int):
            return bool(value)
        elif value is None:
            return False
        else:
            raise ValueError(f"Invalid boolean value: {value}")
