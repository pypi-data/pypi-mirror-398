import sys
from google_play_scraper import search


def main():
    args = sys.argv[1:]
    result = search(" ".join(args))
    for i in result:
        print("-" * 40)
        print("Name     :", i.get("title"))
        print("Package  :", i.get("appId"))
        print("Dev      :", i.get("developer"))
        print("Installs :", i.get("installs"))

