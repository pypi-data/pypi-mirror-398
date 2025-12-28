import argparse
from binascii import a2b_hex, b2a_hex
from typing import List, cast

from Crypto.Cipher import AES  # type: ignore
from twine import repository, settings  # type: ignore
from twine.commands.upload import upload  # type: ignore


class SettingsWrap(settings.Settings):
    def create_repository(self) -> repository.Repository:
        """Create a new repository for uploading."""
        username = decode_aes(self.username).strip()
        password = decode_aes(self.password).strip()
        repo = repository.Repository(
            cast(str, self.repository_config["repository"]),
            username,
            password,
            self.disable_progress_bar,
        )
        repo.set_certificate_authority(self.cacert)
        repo.set_client_certificate(self.client_cert)
        return repo


def bytes16_converter(data):
    """convert data len to 16^n"""
    while len(data) % 16 != 0:
        data += " "
    return data


def encode_aes(data, secret_key="Dean"):
    aes = AES.new(bytes16_converter(secret_key).encode(), AES.MODE_ECB)
    encrypted_text = aes.encrypt(bytes16_converter(data).encode())
    return b2a_hex(encrypted_text)


def decode_aes(data, secret_key="Dean"):
    aes = AES.new(bytes16_converter(secret_key).encode(), AES.MODE_ECB)
    return str(aes.decrypt(a2b_hex(data)), encoding="utf-8", errors="ignore")


def main(args: List[str]) -> None:
    """Execute the ``secureupload`` command.

    :param args:
        The command-line arguments.
    """
    parser = argparse.ArgumentParser(prog="twine upload")
    SettingsWrap.register_argparse_arguments(parser)
    parser.add_argument(
        "dists",
        nargs="+",
        metavar="dist",
        help="The distribution files to upload to the repository "
        "(package index). Usually dist/* . May additionally contain "
        "a .asc file to include an existing signature with the "
        "file upload.",
    )

    parsed_args = parser.parse_args(args)
    upload_settings = SettingsWrap.from_argparse(parsed_args)

    # Call the secureupload function with the arguments from the command line
    return upload(upload_settings, parsed_args.dists)
