import asyncio
import datetime
import json

from pyasic import get_miner, settings


def print_inheritance(cls, indent=0):
    """Рекурсивно печатает дерево наследования"""
    print('  ' * indent + cls.__name__)
    for base in cls.__bases__:
        print_inheritance(base, indent + 1)


async def main():
    ip = "10.76.107.252"
    try:

        miner = await get_miner(ip=ip)

        print(f"Miner: {miner}")

        miningMode = await miner.is_mining()
        sleepMode = await miner.is_sleep()
        errors = await miner.get_errors()
        minerData = await miner.get_data()

        print(f"Is mining: {miningMode}")
        print(f"Sleep mode: {sleepMode}")
        print(f"Errors: {errors}")
        print(f"MinerData: {minerData}")

        ### STOP

        # stop = await miner.stop_mining()
        # print(f"Stop mining: {stop}")

        ### RESUME

        # resume = await miner.resume_mining()
        # print(f"Resume mining: {resume}")

        ### REBOOT

        # reboot = await miner.reboot()
        # print(f"Reboot mining: {reboot}")

        ### LED ON
        # fault_light_on = await miner.fault_light_on()
        # print(f"Fault light on: {fault_light_on}")

    except Exception as e:
        print(f"Error:: {e}")


if __name__ == "__main__":
    asyncio.run(main())
