from urllib.parse import parse_qs
import requests
import configparser
import logging
from pathlib import Path

auth_secrets_path = Path.home() / ".config/polyhattrick/auth"
auth_secrets_path.parent.mkdir(parents=True, exist_ok=True)

environments = {"local": "http://localhost:8000", "prod": "http://161.35.142.18"}


def host(env):
    return environments[env]


class PolyhattrickClient:
    def __init__(self, env):
        self.env = env

    def authenticate(self):
        headers = {
            "User-Agent": "polyhattrick_client/0.1",
        }

        response = requests.post(
            f"{host(self.env)}/login/authenticate", headers=headers
        )
        json = response.json()

        config = configparser.ConfigParser()
        config["auth"] = {
            "resource_owner_key": json["resource_owner_key"],
            "resource_owner_secret": json["resource_owner_secret"],
        }
        with auth_secrets_path.open("w") as configfile:
            config.write(configfile)

        return json["auth_url"]

    def exchange_tokens(self, pin):
        config = configparser.ConfigParser()
        config.read(auth_secrets_path)

        if "auth" not in config:
            logging.warning("Auth section not found in config")
            print(
                "Looks like you haven't initiated the authentication flow yet. Please run `TODO`"
            )

        headers = {
            "User-Agent": "polyhattrick_client/0.1",
            "Content-Type": "application/json",
        }

        data = {
            "verification_code": pin,
            "resource_owner_key": config["auth"]["resource_owner_key"],
            "resource_owner_secret": config["auth"]["resource_owner_secret"],
        }

        response = requests.post(
            f"{host(self.env)}/login/exchange_tokens", headers=headers, json=data
        ).json()
        config.set("auth", "secret", response["secret"])

        with auth_secrets_path.open("w") as configfile:
            config.write(configfile)

    def get_live_result(self):
        config = configparser.ConfigParser()
        config.read(auth_secrets_path)

        if "auth" not in config or "secret" not in config["auth"]:
            logging.warning("Auth secret not found.")
            print("Not authenticated. Please authenticate first, then try again.")
            return

        headers = {
            "Authorization": "Bearer " + config["auth"]["secret"],
            "User-Agent": "polyhattrick_client/0.1",
        }

        response = requests.get(f"{host(self.env)}/watch/live", headers=headers)

        return response.text
