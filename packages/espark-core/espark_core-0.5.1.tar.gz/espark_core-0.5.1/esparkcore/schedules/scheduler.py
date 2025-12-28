from apscheduler.schedulers.asyncio import AsyncIOScheduler


async def start_scheduler():
    scheduler = AsyncIOScheduler()
    scheduler.start()

    return scheduler
