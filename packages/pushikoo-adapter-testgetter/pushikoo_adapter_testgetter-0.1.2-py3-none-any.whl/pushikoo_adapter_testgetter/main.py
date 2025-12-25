import time

from loguru import logger
from pushikoo_interface import Detail, Getter, GetterConfig, GetterInstanceConfig  # noqa: F401

from pushikoo_adapter_testgetter.api import MockAPIClient
from pushikoo_adapter_testgetter.config import AdapterConfig, InstanceConfig


class TestGetter(
    Getter[
        AdapterConfig,  # If you don't have any configuration, you can just use GetterConfig
        InstanceConfig,  # If you don't have any configuration, you can just use GetterInstanceConfig
    ]
):
    # This is your Adapter main implementation.
    # If a fatal error occurs (cannot be recovered properly), do not capture it.
    # Exceptions should be raised directly, with the framework responsible for final error handling and logging.

    def __init__(self) -> None:
        logger.debug(
            f"{self.adapter_name}.{self.identifier} initialized"
        )  # We recommend to use loguru for logging

    def _create_api(self) -> MockAPIClient:
        """Create API client instance with current config (supports hot-reload)."""
        return MockAPIClient(
            token=self.instance_config.token,
            userid=self.instance_config.userid,
            delay=self.config.mockapi_delay,
            # You can use self.ctx to access to framework context.
            # Framework provides proxies via ctx
            proxies=self.ctx.get_proxies(),  # {"http": "http://127.0.0.1:7890", "https": "http://127.0.0.1:7890"}
        )

    def timeline(self) -> list[str]:
        # Return list of message identifiers.
        api = self._create_api()
        return api.get_list(self.config.get_list_option.count)

    def detail(self, identifier: str) -> Detail:
        # Return detail of message.
        api = self._create_api()
        post = api.get_post(identifier)

        return Detail(
            ts=post["timestamp"],
            content=post["content"],
            title=post.get("title"),
            author_id=post.get("userid"),
            author_name=post.get("username"),
            url=post.get("url", []),
            image=post.get("picture", []),
            extra_detail=[post["ip_location"], post["author_statement"]],
        )

    def details(self, identifiers: list[str]) -> Detail:
        """Get detail of specific identifiers as a single Detail.

        Different types of messages have different semantic aggregation granularity
        - Some messages (such as long-content game posts) can only be processed separately;
        - Some messages, such as short, frequent posts, can be combined into a single logical message.
        Therefore, adapter developers can implement this method,
        if framework option "getter_instance.prefer_details" is True, this method will be called preferentially.
        This method is not enforced, and if it is not implemented, it will fallback to `detail`.
        """

        api = self._create_api()
        posts = [api.get_post(i) for i in identifiers]

        content = "\n".join(p["content"] for p in posts)
        ts = int(time.time())
        title = "Aggregated Messages"
        author_id = ", ".join(p.get("userid", "") for p in posts if p.get("userid"))
        author_name = ", ".join(
            p.get("username", "") for p in posts if p.get("username")
        )
        url = [p.get("url") for p in posts if p.get("url")]
        image = [img for p in posts for img in p.get("picture", [])]

        return Detail(
            ts=ts,
            content=content,
            title=title,
            author_id=author_id,
            author_name=author_name,
            url=url,
            image=image,
            extra_detail=[],
        )
