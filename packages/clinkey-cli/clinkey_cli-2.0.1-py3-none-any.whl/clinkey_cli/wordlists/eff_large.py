"""EFF Large Wordlist for diceware passphrase generation.

This wordlist contains 7,776 words optimized for memorability and
unambiguity. Each word can be selected with 5 dice rolls (6^5 = 7,776).

Source: Electronic Frontier Foundation
https://www.eff.org/deeplinks/2016/07/new-wordlists-random-passphrases
"""
import importlib.resources as resources
import json


wordlist_path = resources.files(__package__).joinpath("eff_large.json")
with wordlist_path.open("r", encoding="utf-8") as wordlist_file:
    EFF_LARGE_WORDLIST = json.load(wordlist_file)
