from tortoise import Tortoise, run_async

from protocols.cleaning import cleaning_proto
from protocols.cleaning.models import Availability, Provider, Service, ServiceType

from nexus import Agent, EventType
from nexus.setup import fund_agent_if_low


cleaner = Agent(
    name="cleaner",
    port=8001,
    seed="cleaner secret seed phrase",
    endpoint="http://127.0.0.1:8001/submit",
)

fund_agent_if_low(cleaner.wallet.address())

print("Agent address:", cleaner.address)

# build the cleaning service agent from the cleaning protocol
cleaner.include(cleaning_proto)

@cleaner.on_event(EventType.STARTUP)
async def startup():
    await Tortoise.init(db_url="sqlite://db.sqlite3", modules={"models": ["__main__"]})
    await Tortoise.generate_schemas()

    provider = await Provider.create(name=cleaner.name, address=12)

    floor = await Service.create(type=ServiceType.FLOOR)
    window = await Service.create(type=ServiceType.WINDOW)
    laundry = await Service.create(type=ServiceType.LAUNDRY)

    await provider.services.add(floor)
    await provider.services.add(window)
    await provider.services.add(laundry)

    await Availability.create(
        provider=provider,
        time_start=10,
        time_end=22,
        max_distance=10,
        min_hourly_price=5,
    )

@cleaner.on_event(EventType.SHUTDOWN)
async def shutdown():
    await Tortoise.close_connections()

if __name__ == "__main__":
    run_async(init_db())
    cleaner.run()
