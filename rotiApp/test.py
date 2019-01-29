import asyncio
import types
import serial

ser = serial.Serial("COM8", 115200)
loop = asyncio.get_event_loop()

async def read_serial():
    return ser.readline()


async def hello():
    while True:
        await asyncio.sleep(0.1)
        print("hi")


async def wrapper():
    while True:
        data = await read_serial()
        print(data)


# task = asyncio.ensure_future(coroutine)
tasks = [asyncio.ensure_future(hello()), asyncio.ensure_future(wrapper())]
loop.run_until_complete(asyncio.wait(tasks))
loop.close()



