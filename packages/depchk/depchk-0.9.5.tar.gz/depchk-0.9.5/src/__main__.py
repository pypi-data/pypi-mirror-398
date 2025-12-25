import asyncio
import sys

from src.analyzer import PythonDepchecker


async def main() -> None:
    depchecker = PythonDepchecker()
    await depchecker.run(sys.argv[1:])


def main_sync() -> None:
    asyncio.run(main())


if __name__ == "__main__":
    asyncio.run(main())
