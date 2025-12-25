import json
import os
import typing

import requests

from .. import config
from ..internal.state import get_state
from ..platform.runtime import Runtime


class InstanceOffchainViewsMetadata:
    def __init__(self, content):
        self.content = content


def create_metadata_source(source_code_uri: str) -> typing.Dict[str, str]:
    """Create the source value to be inserted in the metadata.

    Args:
        source_code_uri (str): The URI of the source code in the format `'ipfs://<hash>'`.
            For example, `'ipfs://QmaV5gQ6p9ND9pjc1BPD3dc8oyi8CWEDdueSmkmasiaWGA'`
            Note: While the standard may support `'https://<address>'`, this function is tailored for IPFS URIs.
            Can be obtained with `sp.pin_on_ipfs(c1.get_source())`.

    Returns:
        dict: A dictionary containing:
            - "tools": A list with a single string denoting the SmartPy version.
            - "location": The provided source code URI.
    """
    if not isinstance(source_code_uri, str):
        raise ValueError(
            f"sp.create_metadata_source must be applied to constant strings and got ({source_code_uri})"
        )
    # Check the format of source_code_uri
    if not source_code_uri.startswith("ipfs://"):
        raise ValueError(
            "source_code_uri must be in the format 'ipfs://<hash>'. For example, 'ipfs://QmaV5gQ6p9ND9pjc1BPD3dc8oyi8CWEDdueSmkmasiaWGA'. Note: 'https://<address>' may be valid per standard, but this function expects IPFS URIs."
        )
    return {
        "tools": [f"SmartPy-{config.version}"],
        "location": source_code_uri,
    }


def create_errors(error_map):
    return [
        {"error": {"int": f"{value}"}, "expansion": {"string": key}}
        for (key, value) in error_map.items()
    ]


def create_tzip16_metadata(
    name: typing.Optional[str] = None,
    description: typing.Optional[str] = None,
    version: typing.Optional[str] = None,
    license_name: typing.Optional[str] = None,
    license_details: typing.Optional[str] = None,
    interfaces: typing.List[str] = None,
    authors: typing.List[str] = None,
    homepage: typing.Optional[str] = None,
    source_uri: typing.Optional[str] = None,
    offchain_views: typing.Optional[InstanceOffchainViewsMetadata] = None,
    error_map: typing.Optional[typing.Dict[str, str]] = None,
):
    """Return a TZIP-016 compliant metadata dictionary.

    Args:
        name: The name of the contract
            Should identify its purpose.
        description: A proper natural language description of the contract.
        version: The version of the contract.
            The version together with the name should be unique in the chain.
            For example: `"1.0.0"`.
        license_name:
            De facto license name when possible.
            See Debian [guidelines](https://www.debian.org/doc/packaging-manuals/copyright-format/1.0/#license-short-name)
        license_details:
            Optional license details
        interfaces: A list of the TZIP interfaces supported by the contract.
            TZIP-016 is added to this list.
            For example: `["TZIP-016"]`.
        authors: A list of the authors of the contract.
            For example: `["SmartPy <https://smartpy.io/>"]`.
        homepage: The homepage is for human-consumption.
            It may be the location of the source of the contract, how to submit issue tickets, or just a more elaborate description.
        source_uri: The URI of the source code in the format `'ipfs://<hash>'`.
            For example, 'ipfs://QmaV5gQ6p9ND9pjc1BPD3dc8oyi8CWEDdueSmkmasiaWGA'
        offchain_views: The offchain views as returned by `c.get_offchain_views()`.
        error_map: A dictionary mapping error codes to error messages.

    Returns:
        dict: A TZIP-016 compliant metadata dictionary.
    """

    # Validate inputs
    def validate_string(v, param_name):
        if v is not None and not isinstance(v, str):
            raise ValueError(f"'{param_name}' must be a string but got ({v})")

    def validate_list_of_strings(v, param_name):
        if v and (not isinstance(v, list) or not all(isinstance(i, str) for i in v)):
            raise ValueError(f"'{param_name}' must be a list of strings.")

    def validate_offchain_views(v):
        if v and not isinstance(v, InstanceOffchainViewsMetadata):
            raise ValueError(f"offchain_views must be `c.get_offchain_views()`")

    if interfaces is None:
        interfaces = []
    if authors is None:
        authors = []

    validate_string(name, "name")
    validate_string(description, "description")
    validate_string(version, "version")
    validate_string(license_name, "license_name")
    validate_string(license_details, "license_details")
    validate_list_of_strings(interfaces, "interfaces")
    validate_list_of_strings(authors, "authors")
    validate_string(homepage, "homepage")
    validate_string(source_uri, "source_uri")
    validate_offchain_views(offchain_views)

    # Construct the metadata dictionary
    metadata = {}
    if name:
        metadata["name"] = name
    if description:
        metadata["description"] = description
    if version:
        metadata["version"] = version
    if license_name:
        license_dict = {"name": license_name}
        if license_details:
            license_dict["details"] = license_details
        metadata["license"] = license_dict
    if "TZIP-016" not in interfaces:
        interfaces.append("TZIP-016")
    metadata["interfaces"] = interfaces
    if authors:
        metadata["authors"] = authors
    if homepage:
        metadata["homepage"] = homepage
    if source_uri:
        metadata["source"] = create_metadata_source(source_uri)
    if offchain_views:
        metadata["views"] = offchain_views.content
    if error_map:
        metadata["errors"] = create_errors(error_map)
    return metadata


class _Response:
    """Mimics the response object returned by requests when in browser mode."""

    def __init__(self, status_code, text):
        self.status_code = status_code
        self.text = text
        self.content = text.encode("utf-8")
        self.ok = self.status_code >= 200 and self.status_code < 300

    def json(self):
        try:
            return json.loads(self.text)
        except Exception as e:
            raise ValueError("Failed to decode JSON") from e

    def raise_for_status(self):
        if not self.ok:
            raise Exception(f"HTTP error {self.status_code}: {self.text}")


def _request_post(url, payload, headers):
    """Handles POST requests in native Python or browser runtime."""
    if (
        get_state().runtime == Runtime.IDE
        or get_state().runtime == Runtime.JUPYTER_LITE
    ):
        import js

        xhr = js.XMLHttpRequest.new()
        xhr.open("POST", url, False)  # False makes the request synchronous
        for key, value in headers.items():
            xhr.setRequestHeader(key, value)
        xhr.send(json.dumps(payload))
        return _Response(xhr.status, xhr.responseText)
    else:
        response = requests.post(url, json=payload, headers=headers)
        return _Response(response.status_code, response.text)


def _request_get(url):
    """Handles GET requests in native Python or browser runtime."""
    if (
        get_state().runtime == Runtime.IDE
        or get_state().runtime == Runtime.JUPYTER_LITE
    ):
        import js

        xhr = js.XMLHttpRequest.new()
        xhr.open("GET", url, False)  # False makes the request synchronous
        xhr.send()
        return _Response(xhr.status, xhr.responseText)
    else:
        response = requests.get(url)
        return _Response(response.status_code, response.text)


def pin_on_ipfs(
    data: typing.Dict[str, typing.Any],
    api_key: typing.Optional[str] = None,
    secret_key: typing.Optional[str] = None,
    name: typing.Optional[str] = None,
):
    """Encode a dict to JSON and pin it to IPFS through Pinata.

    Args:
        data: The metadata to pin.
            For example, the data returned by `sp.create_tzip16_metadata(...)` or by `contract.get_source()`.
        api_key: The API key for the Pinata account.
        secret_key: The secret key for the Pinata account.
        name: An optional name for the metadata file.


    Returns:
        str: The IPFS uri of the pinned metadata in the form `ipfs://<hash>`.
    """
    if api_key is None:
        api_key = str(os.environ.get("PINATA_KEY"))
    if secret_key is None:
        secret_key = str(os.environ.get("PINATA_SECRET"))
    url = "https://api.pinata.cloud/pinning/pinJSONToIPFS"
    headers = {
        "pinata_api_key": api_key,
        "pinata_secret_api_key": secret_key,
        "Content-Type": "application/json",
    }
    payload = {"pinataContent": data}
    if name is not None:
        payload["pinataMetadata"] = {"name": name}
    response = _request_post(url=url, payload=payload, headers=headers)
    if not response.ok:
        try:
            error_message = response.json().get("error", response.text)
        except ValueError:
            error_message = response.text
        raise Exception(f"Error from Pinata API: {error_message}")
    return f"ipfs://{response.json()['IpfsHash']}"


def get_metadata_uri(contract_address: str, network="mainnet") -> str:
    """Get the uri given in the metadata bigmap of the contract.

    Args:
        contract_address (str): The Tezos address of the contract.
            For example: `"KT1EQLe6AbouoX9RhFYHKeYQUAGAdGyFJXoi"`
        network (str, optional): The Tezos network.
            For example: "mainnet" (default) or "ghostnet"

    Returns:
        str: The metadata URI, usually in the format `ipfs://<hash>`.
    """
    base_url = f"https://api.{network}.tzkt.io/v1/"
    try:
        # Get the big map
        url = f"{base_url}bigmaps/?contract={contract_address}&path=metadata"
        response = _request_get(url)
        response.raise_for_status()  # Raise an exception for HTTP errors
        big_maps = response.json()
        if len(big_maps) == 0:
            raise Exception("Not metadata bigmap found.")
        big_map = big_maps[0]
        # Get the big map value
        url = f"{base_url}bigmaps/{big_map['ptr']}/keys/{''}"
        response = _request_get(url)
        response.raise_for_status()  # Raise an exception for HTTP errors
        values = response.json()
        if len(big_maps) == 0:
            raise Exception("The metadata bigmap doesn't contain the empty key.")
        value = values[0]["value"]
        value = bytes.fromhex(value).decode("utf-8")
        if not (value.startswith("ipfs://") or value.startswith("https://")):
            raise ValueError(
                f"Unexpected metadata format: {value}. Expected format: ipfs://<hash> or https://<hash>"
            )
        return value
    except requests.exceptions.RequestException as e:
        raise Exception(f"Error: {e}")


def get_ipfs_data(uri: str, ipfs_gateway_url="https://ipfs.io/ipfs/"):
    """Fetches and returns the content of a file from IPFS using the provided URI.

    Args:
        uri (str): The IPFS URI in the format `ipfs://<CID>`.
        ipfs_gateway_url (str, optional): The IPFS gateway URL to use for fetching the content.
            Defaults to the public IPFS gateway "https://ipfs.io/ipfs/".

    Returns:
        str: The content of the file from IPFS.
    """
    if not uri.startswith("ipfs://"):
        raise ValueError("The provided URI is not a valid IPFS URI.")

    # Ensure the gateway URL has a trailing slash
    if not ipfs_gateway_url.endswith("/"):
        ipfs_gateway_url += "/"

    cid = uri.replace("ipfs://", "")
    file_url = ipfs_gateway_url + cid
    try:
        response = _request_get(file_url)
        response.raise_for_status()
        return response.content.decode("utf-8")
    except requests.exceptions.RequestException as e:
        raise Exception(f"Error downloading the file from IPFS: {e}")


def get_metadata(contract_address: str, network="mainnet"):
    """Fetches and returns the metadata dictionary for a given contract address and network.

    Args:
        contract_address (str): The Tezos address of the contract.
            For example: `"KT1EQLe6AbouoX9RhFYHKeYQUAGAdGyFJXoi"`
        network (str, optional): The Tezos network.
            For example: "mainnet" (default) or "ghostnet"

    Returns:
        dict: The metadata dictionary.
    """
    return json.loads(get_ipfs_data(get_metadata_uri(contract_address, network)))


def get_metadata_code(metadata: typing.Dict[str, typing.Any]):
    """Fetches and returns the code metadata for a contract's metadata.

    Args:
        metadata (dict): The metadata dictionary, expected to have a "source" key with a nested "location" key.

    Returns:
        dict: The code metadata.
    """
    if not metadata.get("source") or not metadata["source"].get("location"):
        raise Exception(
            "The metadata doesn't contain the expected 'source' and 'location' structure."
        )
    code_metadata_uri = metadata["source"]["location"]
    return json.loads(get_ipfs_data(code_metadata_uri))


def get_michelson_code(contract_address: str, network="mainnet"):
    """Fetches and returns the Michelson code of a contract from a Tezos node.

    Args:
        contract_address (str): The Tezos address of the contract.
            For example: `"KT1EQLe6AbouoX9RhFYHKeYQUAGAdGyFJXoi"`
        network (str, optional): The Tezos network.
            For example: "mainnet" (default) or "ghostnet"

    Returns:
        dict: The Michelson code of the contract.
    """
    base_url = f"https://api.{network}.tzkt.io/v1/"
    try:
        url = f"{base_url}contracts/{contract_address}/code?format=0"
        response = _request_get(url)
        response.raise_for_status()  # Raise an exception for HTTP errors
        code = response.json()
        return code
    except requests.exceptions.RequestException as e:
        raise Exception(
            f"Error fetching Michelson code for contract {contract_address} on {network}: {e}"
        )
    except json.JSONDecodeError:
        raise Exception("The fetched Michelson code is not valid JSON.")


def check_sp_version(metadata: typing.Dict[str, typing.Any]):
    """Checks that current SmartPy version is compatible with the metadata."""
    if "source" not in metadata or "tools" not in metadata["source"]:
        raise Exception("metadata doesn't contain `source.tools`.")
    tools = metadata["source"]["tools"]
    sp_tools = [t for t in tools if t.startswith("SmartPy")]
    if len(sp_tools) == 0:
        raise Exception("Cannot test: SmartPy version not found in source.tools")
    if len(sp_tools) > 1:
        raise Exception("Incorrect metadata: Multiple SmartPy version found.")
    running = f"SmartPy-{config.version}"
    expected = sp_tools[0]
    if expected != running:
        raise Exception(f"Cannot test: Please use {expected} and not {running}.")


def normalize_micheline(micheline):
    storage = [p for p in micheline if p["prim"] == "storage"]
    code = [p for p in micheline if p["prim"] == "code"]
    parameter = [p for p in micheline if p["prim"] == "parameter"]
    views = [p for p in micheline if p["prim"] == "views"]
    return storage + code + parameter + views


def are_equivalent_micheline(m1, m2, path=[]):
    if isinstance(m1, dict) and isinstance(m2, dict):
        if set(m1.keys()) != set(m2.keys()):
            return (False, path)
        for k in m1:
            are_equal, diff_path = are_equivalent_micheline(m1[k], m2[k], path + [k])
            if not are_equal:
                return (False, diff_path)
        return (True, None)
    elif isinstance(m1, list) and isinstance(m2, list):
        if len(m1) != len(m2):
            return (False, path)
        for idx, (e1, e2) in enumerate(zip(m1, m2)):
            are_equal, diff_path = are_equivalent_micheline(e1, e2, path + [idx])
            if not are_equal:
                return (False, diff_path)
        return (True, None)
    else:
        return (m1 == m2, None if m1 == m2 else path)


def print_diff_path(diff_path):
    return "".join([f"[{p}]" if isinstance(p, int) else f"['{p}']" for p in diff_path])


class CodeMismatchException(Exception):
    def __init__(self, generated_michelson, diff_details):
        self.generated_michelson = generated_michelson
        self.diff_details = diff_details
        super().__init__("Generated michelson does not match onchain michelson")
