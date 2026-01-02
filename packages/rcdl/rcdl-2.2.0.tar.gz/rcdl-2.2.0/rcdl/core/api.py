# core/api.py

from .models import Creator


class URL:
    DOMAINS_BASE_URL = {
        "coomer": "https://coomer.st/api/v1/",
        "kemono": "https://kemono.cr/api/v1/",
    }

    @staticmethod
    def get_base_url(domain: str) -> str:
        if domain not in URL.DOMAINS_BASE_URL:
            raise KeyError(f"{domain} not in known domains urls")
        return URL.DOMAINS_BASE_URL[domain]

    @staticmethod
    def get_post_revision(creator: Creator, post_id) -> str:
        return f"{URL.get_base_url(creator.domain)}{creator.service}/user/{creator.creator_id}/post/{post_id}/revisions"

    @staticmethod
    def get_headers() -> dict:
        return {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/117.0 Safari/537.36",
            "Accept": "text/css",
        }

    @staticmethod
    def get_url_from_file(domain: str, path_url: str):
        if domain == "coomer":
            return f"https://coomer.st{path_url}"
        elif domain == "kemono":
            return f"https://kemono.cr{path_url}"
        else:
            raise ValueError(
                f"Domain {domain} is not an accepted value/does not exist. Please check your creators.json file"
            )

    @staticmethod
    def add_params(url: str, params: dict):
        url += "?"
        for key in params:
            url += f"{key}={params[key]}&"
        return url[:-1]

    @staticmethod
    def get_creator_post_wo_param(creator: Creator) -> str:
        return f"{URL.get_base_url(creator.domain)}{creator.service}/user/{creator.creator_id}/posts"

    @staticmethod
    def get_posts_page_url_wo_param():
        domain = URL.DOMAINS_BASE_URL["coomer"]
        return f"{domain}posts"
