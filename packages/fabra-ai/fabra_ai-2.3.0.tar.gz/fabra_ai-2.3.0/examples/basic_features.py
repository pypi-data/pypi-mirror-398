from datetime import timedelta
from fabra.core import FeatureStore, entity, feature
from fabra.store import DuckDBOfflineStore, InMemoryOnlineStore

# Initialize the store
# For serving, we typically want a persistent offline store and a fast online store.
# Here we use defaults for simplicity.
store = FeatureStore(
    offline_store=DuckDBOfflineStore(), online_store=InMemoryOnlineStore()
)


@entity(store)
class User:
    user_id: str


@feature(entity=User, refresh=timedelta(minutes=5), materialize=True)
def user_click_count(user_id: str) -> int:
    """Calculates the total clicks for a user."""
    # Deterministic demo value (stable across requests).
    return abs(hash(user_id + "clicks")) % 101


@feature(entity=User)
def user_is_active(user_id: str) -> bool:
    """Determines if a user is currently active."""
    return hash(user_id) % 3 != 0  # ~66% active, deterministic


# Pre-seed data on module import so `fabra serve examples/basic_features.py`
# returns values immediately.
async def _seed_demo_data() -> None:
    await store.online_store.set_online_features(
        "User",
        "u1",
        {
            "user_click_count": user_click_count("u1"),
            "user_is_active": user_is_active("u1"),
        },
    )


def _run_seed() -> None:
    import asyncio

    try:
        loop = asyncio.get_running_loop()
        loop.create_task(_seed_demo_data())
    except RuntimeError:
        asyncio.run(_seed_demo_data())


_run_seed()

if __name__ == "__main__":
    import asyncio

    asyncio.run(_seed_demo_data())
