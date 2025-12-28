import os
from pathlib import Path

import requests
import yaml
from fastapi import Depends

module_dir = Path(__file__).resolve().parent.parent


class ClashConfig:
    def __init__(self, rule_base_url: str, my_rule_base_url: str, request_proxy: str):
        self.rule_base_url = rule_base_url.rstrip("/")
        self.my_rule_base_url = my_rule_base_url.rstrip("/")
        self.request_proxy = request_proxy


class ClashYamlGenerator:
    def __init__(self, config: ClashConfig):
        self.rule_base_url = config.rule_base_url
        self.my_rule_base_url = config.my_rule_base_url
        self.request_proxy = config.request_proxy

    def gen(self, sub_list: list[dict]):
        proxies = None
        if self.request_proxy:
            proxies = {
                "http": self.request_proxy,
                "https": self.request_proxy,
            }

        with open(str(module_dir / "data/template.yaml"), "r", encoding="utf-8") as f:
            template = yaml.safe_load(f)

        template["proxy-groups"].extend(
            [
                {
                    "name": "全局选择",
                    "type": "select",
                    "proxies": ["自动选择", "手动选择", "轮询"]
                    + [item["name"] for item in sub_list],
                },
                {
                    "name": "自动选择",
                    "type": "url-test",
                    "url": "https://www.gstatic.com/generate_204",
                    "interval": 300,
                    "tolerance": 11,
                    "lazy": True,
                    "use": [f"provider.{item['name']}" for item in sub_list],
                },
                {
                    "name": "手动选择",
                    "type": "select",
                    "use": [f"provider.{item['name']}" for item in sub_list],
                },
                {
                    "name": "轮询",
                    "type": "load-balance",
                    "url": "https://www.gstatic.com/generate_204",
                    "interval": 300,
                    "lazy": True,
                    "strategy": "round-robin",
                    "use": [f"provider.{item['name']}" for item in sub_list],
                },
            ]
        )
        userinfo = ""
        for item in sub_list:
            headers = {"User-Agent": item["user_agent"]} if item["user_agent"] else {}

            if not item["url"]:
                raise ValueError("Invalid subscription URL.")
            response = requests.get(item["url"], headers=headers, proxies=proxies)
            response.raise_for_status()
            if not userinfo:
                userinfo = response.headers["Subscription-Userinfo"]
            remote_config = yaml.safe_load(response.text)

            ps = remote_config.get("proxies", [])
            if not ps:
                raise ValueError("No proxies found in subscription.")

            template["proxy-providers"][f"provider.{item['name']}"] = {
                "type": "inline",
                "payload": ps,
            }

            template["proxy-groups"].append(
                {
                    "name": item["name"],
                    "type": "url-test",
                    "url": "https://www.gstatic.com/generate_204",
                    "interval": 300,
                    "tolerance": 11,
                    "lazy": True,
                    "use": [f"provider.{item['name']}"],
                },
            )

        # 获取rules
        rule_list = [
            [f"{self.my_rule_base_url}/direct.yaml", "DIRECT"],
            [f"{self.my_rule_base_url}/proxy.yaml", "全局选择"],
            [
                f"{self.my_rule_base_url}/round.yaml",
                "轮询",
            ],
        ]

        for item in rule_list:
            response = requests.get(item[0], proxies=proxies)
            response.raise_for_status()
            remote = yaml.safe_load(response.text)
            template["rule-providers"][os.path.basename(item[0])] = {
                "type": "inline",
                "behavior": "classical",
                "payload": remote["payload"],
            }

            template["rules"].append(f"RULE-SET,{os.path.basename(item[0])},{item[1]}")

        template["rule-providers"].update(
            {
                "applications": {
                    "type": "http",
                    "behavior": "classical",
                    "url": f"{self.rule_base_url}/applications.txt",
                    "path": "./ruleset/applications.yaml",
                    "interval": 86400,
                },
                "private": {
                    "type": "http",
                    "behavior": "domain",
                    "url": f"{self.rule_base_url}/private.txt",
                    "path": "./ruleset/private.yaml",
                    "interval": 86400,
                },
                "icloud": {
                    "type": "http",
                    "behavior": "domain",
                    "url": f"{self.rule_base_url}/icloud.txt",
                    "path": "./ruleset/icloud.yaml",
                    "interval": 86400,
                },
                "apple": {
                    "type": "http",
                    "behavior": "domain",
                    "url": f"{self.rule_base_url}/apple.txt",
                    "path": "./ruleset/apple.yaml",
                    "interval": 86400,
                },
                "google": {
                    "type": "http",
                    "behavior": "domain",
                    "url": f"{self.rule_base_url}/google.txt",
                    "path": "./ruleset/google.yaml",
                    "interval": 86400,
                },
                "proxy": {
                    "type": "http",
                    "behavior": "domain",
                    "url": f"{self.rule_base_url}/proxy.txt",
                    "path": "./ruleset/proxy.yaml",
                    "interval": 86400,
                },
                "direct": {
                    "type": "http",
                    "behavior": "domain",
                    "url": f"{self.rule_base_url}/direct.txt",
                    "path": "./ruleset/direct.yaml",
                    "interval": 86400,
                },
                "lancidr": {
                    "type": "http",
                    "behavior": "ipcidr",
                    "url": f"{self.rule_base_url}/lancidr.txt",
                    "path": "./ruleset/lancidr.yaml",
                    "interval": 86400,
                },
                "cncidr": {
                    "type": "http",
                    "behavior": "ipcidr",
                    "url": f"{self.rule_base_url}/cncidr.txt",
                    "path": "./ruleset/cncidr.yaml",
                    "interval": 86400,
                },
                "telegramcidr": {
                    "type": "http",
                    "behavior": "ipcidr",
                    "url": f"{self.rule_base_url}/telegramcidr.txt",
                    "path": "./ruleset/telegramcidr.yaml",
                    "interval": 86400,
                },
            },
        )

        template["rules"].extend(
            [
                "RULE-SET,applications,DIRECT",
                "DOMAIN,clash.razord.top,DIRECT",
                "DOMAIN,yacd.haishan.me,DIRECT",
                "RULE-SET,private,DIRECT",
                "RULE-SET,icloud,DIRECT",
                "RULE-SET,apple,DIRECT",
                "RULE-SET,google,全局选择",
                "RULE-SET,proxy,全局选择",
                "RULE-SET,direct,DIRECT",
                "RULE-SET,lancidr,DIRECT",
                "RULE-SET,cncidr,DIRECT",
                "RULE-SET,telegramcidr,全局选择",
                "GEOIP,LAN,DIRECT,no-resolve",
                "GEOIP,CN,DIRECT,no-resolve",
                "MATCH,全局选择",
            ]
        )

        return template, userinfo

    def query2sub(self, urls: str, agents: str, names: str):
        url_list = urls.split(",") if urls else []
        agents_list = agents.split(",") if agents else []
        name_list = names.split(",") if names else []

        max_length = max(len(url_list), len(agents_list), len(name_list))

        while len(url_list) < max_length:
            url_list.append("")
        while len(agents_list) < max_length:
            agents_list.append("")
        while len(name_list) < max_length:
            name_list.append("")

        sub_list = []

        for i in range(max_length):
            if not url_list[i]:
                raise ValueError(f"Invalid subscription URL. #{i + 1}")

            sub_list.append(
                {
                    "url": url_list[i],
                    "user_agent": agents_list[i] if agents_list[i] else "",
                    "name": name_list[i] if name_list[i] else f"订阅{i}",
                }
            )

        return sub_list


generator_instance = None


def init_generator(config: ClashConfig):
    global generator_instance
    generator_instance = ClashYamlGenerator(config)


def get_generator():
    global generator_instance
    if generator_instance is None:
        raise RuntimeError("ClashYamlGenerator not initialized")
    return generator_instance


def get_generator_dependency():
    return Depends(get_generator)
