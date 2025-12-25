import os
import urllib.parse
from typing import List

from .api_client import APIClientBase, InvalidInputException
from .keyring import KeyRing


class Authentication(APIClientBase):
    _API_KEYS_ENDPOINT = "/v1/apiKeys"

    def __init__(self, url_base=None, **kwargs):
        super().__init__(url_base or os.environ.get("AUTHORIZATION_SERVICE", ""), **kwargs)

    def on_login_response(self, response):
        if "jwt" in response:
            token = response["jwt"]
            parsed_base_url = urllib.parse.urlparse(self.url_base)
            keyring = KeyRing(parsed_base_url.netloc)
            keyring.set_token(token)
        return response

    def login(self, username: str, password: str):
        body = {"username": username, "password": password}
        return self.post_request("/login", body=body, on_response_callback=self.on_login_response)

    def get_public_key(self, username: str):
        return self.get_request("/public-key", query_args={"username": username})

    def add_authorized_key(self, username: str, public_key: str):
        return self.post_request(
            "/authorized-keys",
            query_args={"username": username},
            body={"public_key": public_key},
        )

    def remove_authorized_key(self, username: str, public_key: str):
        return self.delete_request(
            "/authorized-keys",
            query_args={"username": username, "public_key": public_key},
        )

    def get_ca_certificate(self):
        return self.get_request(relative_url="/ca")

    def get_certificates(self):
        return self.get_request(relative_url="/ca/certs")

    def get_certificate(self, name: str):
        return self.get_request(relative_url=f"/ca/certs/{name}")

    def get_certificate_authority_settings(self):
        return self.get_request(relative_url="/ca/settings")

    def update_certificate_authority_settings(self, enterprise_ca_hostname: str):
        body = {"enterpriseCaHostname": enterprise_ca_hostname}
        return self.put_request(relative_url="/ca/settings", body=body)

    def renew_certificate(
        self,
        name: str,
        common_name: str,
        dns_names: List[str] = None,
        duration: str = None,
        email_addresses: List[str] = None,
        ip_addresses: List[str] = None,
        renew_before: str = None,
        subject: str = None,
        uris: List[str] = None,
        subject_countries: str = None,
        subject_localities: str = None,
        subject_organizational_units: str = None,
        subject_organizations: str = None,
        subject_postal_codes: str = None,
        subject_provinces: str = None,
        subject_serial_number: str = None,
        subject_street_addresses: str = None,
        is_ca: bool = None,
        encode_usages_in_request: bool = None,
        private_key_algo: str = None,
        private_key_encoding: str = None,
        private_key_rotation_policy: str = None,
        private_key_size: int = None,
        literal_subject: str = None,
        usages: List[str] = None,
    ):
        def remove_none_and_empty(d):
            if isinstance(d, dict):
                return {
                    k: remove_none_and_empty(v)
                    for k, v in d.items()
                    if v is not None and not (isinstance(v, (dict, list)) and not v)
                }
            elif isinstance(d, list):
                return [
                    remove_none_and_empty(v) for v in d if v is not None and not (isinstance(v, (dict, list)) and not v)
                ]
            else:
                return d

        def clean_missing_values(d):
            return remove_none_and_empty(remove_none_and_empty(d))

        certificate_data = {
            "commonName": common_name,
            "dnsNames": dns_names,
            "duration": duration,
            "emailAddresses": email_addresses,
            "encodeUsagesInRequest": encode_usages_in_request,
            "ipAddresses": ip_addresses,
            "isCA": is_ca,
            "privateKey": {
                "algorithm": private_key_algo,
                "encoding": private_key_encoding,
                "rotationPolicy": private_key_rotation_policy,
                "size": private_key_size,
            },
            "renewBefore": renew_before,
            "literalSubject": literal_subject,
            "subject": {
                "countries": subject_countries,
                "localities": subject_localities,
                "organizationalUnits": subject_organizational_units,
                "organizations": subject_organizations,
                "postalCodes": subject_postal_codes,
                "provinces": subject_provinces,
                "serialNumber": subject_serial_number,
                "streetAddresses": subject_street_addresses,
            },
            "uris": uris,
            "usages": usages,
        }
        certificate_data = clean_missing_values(certificate_data)
        return self.post_request(relative_url=f"/ca/certs/{name}", body=certificate_data)

    def get_api_keys(self, type_: str = None):
        return self.get_request(self._API_KEYS_ENDPOINT, query_args={"type": type_})

    def get_api_key(self, id_: str):
        if not id_:
            raise InvalidInputException(f"Expected a valid api key id, received: `{id_}`")
        return self.get_request(f"{self._API_KEYS_ENDPOINT}/{id_}", id=id_)

    def delete_api_key(self, id_: str):
        if not id_:
            raise InvalidInputException(f"Expected a valid api key id, received: `{id_}`")
        return self.delete_request(f"{self._API_KEYS_ENDPOINT}/{id_}", id=id_)

    def create_api_key(
        self,
        name: str,
        owner: str,
        key_type: str = "custom",
        scopes: List[dict] = [],
        allowed_networks: List[str] = ["0.0.0.0/0"],
        validity: str = "365d",
    ):
        if not name:
            raise InvalidInputException(f"Expected a valid api key name, received: `{name}`")

        return self.post_request(
            self._API_KEYS_ENDPOINT,
            body={
                "type": key_type,
                "name": name,
                "owner": owner,
                "scopes": scopes,
                "allowedNetworks": allowed_networks,
                "validity": validity,
            },
        )

    def create_remote_node(self, id: str, host: str, api_key_id: str, api_key_token: str):
        return self.post_request(
            "/v1/remoteNodes", body={"id": id, "host": host, "apiKeyToken": api_key_token, "apiKeyId": api_key_id}
        )

    def delete_remote_node(self, id: str):
        return self.delete_request(f"/v1/remoteNodes/{id}")

    def get_remote_node(self, id: str):
        return self.get_request(f"/v1/remoteNodes/{id}")

    def get_remote_nodes(self):
        return self.get_request("/v1/remoteNodes")
