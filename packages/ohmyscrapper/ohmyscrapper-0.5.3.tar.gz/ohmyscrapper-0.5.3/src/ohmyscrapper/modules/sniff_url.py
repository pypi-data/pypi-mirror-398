import requests
from bs4 import BeautifulSoup
import json


def sniff_url(url="https://www.linkedin.com/in/cesardesouzacardoso/", silent=False):
    if not silent:
        print("checking url:", url)

    r = requests.get(url=url)
    soup = BeautifulSoup(r.text, "html.parser")

    metatags_to_search = [
        "description",
        "og:url",
        "og:title",
        "og:description",
        "og:type",
        "lnkd:url",
    ]

    text_tags_to_search = {
        "h1": "",
        "h2": "|",
    }

    final_report = {}
    final_report["scrapped-url"] = url
    final_report.update(
        _extract_meta_tags(
            soup=soup, silent=silent, metatags_to_search=metatags_to_search
        )
    )
    final_report.update(
        _extract_text_tags(
            soup=soup, silent=silent, text_tags_to_search=text_tags_to_search
        )
    )
    final_report["a_links"] = _extract_a_tags(soup=soup, silent=silent)
    final_report = _complementary_report(final_report, soup, silent).copy()
    final_report["json"] = json.dumps(final_report)

    return final_report


def _extract_a_tags(soup, silent):
    a_links = []
    if not silent:
        print("\n\n\n\n---- all <a> links ---")

    i = 0
    for a_tag in soup.find_all("a"):
        i = i + 1
        a_links.append({"text": a_tag.text, "href": a_tag.get("href")})
        if not silent:
            print("\n-- <a> link", i, "-- ")
            print("target:", a_tag.get("target"))
            print("text:", str(a_tag.text).strip())
            print("href:", a_tag.get("href"))
            print("-------------- ")
    return a_links


def _extract_meta_tags(soup, silent, metatags_to_search):
    valid_meta_tags = {}
    if not silent:
        print("\n\n\n\n---- all <meta> tags ---\n")
    i = 0
    for meta_tag in soup.find_all("meta"):
        if (
            meta_tag.get("name") in metatags_to_search
            or meta_tag.get("property") in metatags_to_search
        ):
            if meta_tag.get("name") is not None:
                valid_meta_tags[meta_tag.get("name")] = meta_tag.get("content")
            elif meta_tag.get("property") is not None:
                valid_meta_tags[meta_tag.get("property")] = meta_tag.get("content")
        i = i + 1
        if not silent:
            print("-- meta tag", i, "--")
            print("name:", meta_tag.get("name"))
            print("property:", meta_tag.get("property"))
            print("content:", meta_tag.get("content"))
            print("---------------- \n")
    return valid_meta_tags


def _extract_text_tags(soup, silent, text_tags_to_search):
    valid_text_tags = {}
    if not silent:
        print("\n\n\n\n---- all <text> tags ---\n")
    i = 0
    for text_tag, separator in text_tags_to_search.items():
        if len(soup.find_all(text_tag)) > 0:
            valid_text_tags[text_tag] = []
            for obj_tag in soup.find_all(text_tag):
                valid_text_tags[text_tag].append(obj_tag.text.strip())
            valid_text_tags[text_tag] = separator.join(valid_text_tags[text_tag])
        i = i + 1
        if not silent:
            print("-- text tag", i, "--")
            print("name:", text_tag)
            print("separator:", separator)
            print("texts:", valid_text_tags[text_tag])
            print("---------------- \n")
    return valid_text_tags


def _complementary_report(final_report, soup, silent):

    if len(final_report["a_links"]) > 0:
        final_report["first-a-link"] = final_report["a_links"][0]["href"]
        final_report["total-a-links"] = len(final_report["a_links"])
    else:
        final_report["first-a-link"] = ""
        final_report["total-a-links"] = 0

    if len(soup.find_all("meta")) > 0:
        final_report["total-meta-tags"] = len(soup.find_all("meta"))
    else:
        final_report["total-meta-tags"] = 0
    if not silent:
        print("\n\n\n----report---\n")
        for key in final_report:
            if key != "a_links":
                print("* ", key, ":", final_report[key])

    return final_report


def get_tags(url):
    return sniff_url(url=url, silent=True)
