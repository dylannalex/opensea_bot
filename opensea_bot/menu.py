from os import system
from opensea_bot.bot import OpenSeaBot


def _get_expected_input(msg: str, excepted_inputs: list[str]):
    input_ = ""
    while input_ not in excepted_inputs:
        system("cls")
        input_ = input(msg).strip().lower()
    return input_


def _get_secret_phrase() -> str:
    VALID_LENGTHS = (12, 15, 18, 21, 24)

    while True:
        secret_phrase = (
            input("Enter secret phrase with spaces between words: ").strip().lower()
        )
        if len(secret_phrase.split(" ")) in VALID_LENGTHS:
            return secret_phrase


def _get_menu_options() -> str:
    OPTIONS = ["Find account NFTs", "Transfer NFTs found"]
    msg = ""
    for i, option in enumerate(OPTIONS):
        msg += f"[{i + 1}] {option}\n"

    msg += "\nEnter option: "
    return msg


def menu(bot: OpenSeaBot):
    metamask_extension_path_added = _get_expected_input(
        "Is Metamask extension path added? (y/n): ", ("y", "n")
    )
    if metamask_extension_path_added == "y":
        secret_phrase = _get_secret_phrase()
        bot.connect_to_metamask(secret_phrase)

    else:
        bot.driver.get(
            r"https://chrome.google.com/webstore/detail/metamask/nkbihfbeogaeaoehlefnkodbefgpgknn"
        )

    system("cls")
    input("Press Enter after connecting your wallet to OpenSea....")

    nfts = []
    while True:
        option = int(_get_expected_input(_get_menu_options(), ("1", "2")))
        system("cls")

        if option == 1:
            type = _get_expected_input(
                "Enter where to find NFTs (all/collected/hidden): ",
                ("all", "collected", "hidden"),
            )
            nfts = bot.get_nfts(type)
        if option == 2:
            if not nfts:
                print("No NFTs to transfer. Please find NFTs before sending them.")
                input("Press Enter to continue...")
                continue
            wallet = input("Enter wallet to transfer NFTs: ")
            confirm = _get_expected_input(
                f"Are you sure you want to transfer the selected NFTs to {wallet}? (y/n): ",
                ("y", "n"),
            )
            if confirm == "y":
                bot.transfer_nfts(wallet, nfts)
