from pydantic import BaseModel, Field


class SystemConfig(BaseModel):
    class Network(BaseModel):
        proxies: dict[str, str] = Field(
            default_factory=dict,
            description="Proxy configuration, e.g., {'http': 'http://...', 'https': 'https://...'}",
        )

    class Policy(BaseModel):
        # article_max_ageday: int = Field(
        #     180,
        #     description="Maximum allowed article age in days (older articles are ignored)",
        # )
        perf_merged_details: bool = Field(
            True,
            description="Whether to merge detailed items in performance reports",
        )

        class Attempt(BaseModel):
            getter_timeline: list[int] = Field(
                default_factory=lambda: [5, 10, 50],
                description="A warning is triggered after getter_instance.timeline fails several consecutive times",
            )

        attempt: Attempt = Attempt()

    network: Network = Network()
    policy: Policy = Policy()
