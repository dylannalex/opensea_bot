from opensea_bot import bot
from opensea_bot import menu


def main():
    opensea_bot = bot.OpenSeaBot()
    menu.menu(opensea_bot)


if __name__ == "__main__":
    main()
