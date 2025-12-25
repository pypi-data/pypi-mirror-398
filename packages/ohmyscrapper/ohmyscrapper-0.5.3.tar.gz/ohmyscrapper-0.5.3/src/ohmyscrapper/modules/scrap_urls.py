import ohmyscrapper.models.urls_manager as urls_manager
import ohmyscrapper.modules.sniff_url as sniff_url
import ohmyscrapper.modules.load_txt as load_txt
import ohmyscrapper.modules.classify_urls as classify_urls

import time
import random


def process_linkedin_redirect(url_report, url, verbose=False):
    if verbose:
        print("linkedin_redirect")

    if url_report["total-a-links"] < 5:
        if "first-a-link" in url_report.keys():
            url_destiny = url_report["first-a-link"]
        else:
            urls_manager.set_url_error(url=url["url"], value="error: no first-a-link")
            if verbose:
                print("no url for:", url["url"])
            return
    else:
        if "og:url" in url_report.keys():
            url_destiny = url_report["og:url"]
        else:
            urls_manager.set_url_error(url=url["url"], value="error: no og:url")
            if verbose:
                print("no url for:", url["url"])
            return
    if verbose:
        print(url["url"], ">>", url_destiny)
    urls_manager.add_url(url=url_destiny)
    urls_manager.set_url_destiny(url=url["url"], destiny=url_destiny)


def process_linkedin_feed(url_report, url, verbose=False):
    if verbose:
        print("linkedin_feed")

    if "og:url" in url_report.keys():
        url_destiny = url_report["og:url"]
    else:
        urls_manager.set_url_error(url=url["url"], value="error: no og:url")
        if verbose:
            print("no url for:", url["url"])
        return

    if verbose:
        print(url["url"], ">>", url_destiny)
    urls_manager.add_url(url=url_destiny)
    urls_manager.set_url_destiny(url=url["url"], destiny=url_destiny)


def process_linkedin_job(url_report, url, verbose=False):
    if verbose:
        print("linkedin_job")
    changed = False
    if "h1" in url_report.keys():
        if verbose:
            print(url["url"], ": ", url_report["h1"])
        urls_manager.set_url_h1(url=url["url"], value=url_report["h1"])
        changed = True
    elif "og:title" in url_report.keys():
        if verbose:
            print(url["url"], ": ", url_report["og:title"])
        urls_manager.set_url_h1(url=url["url"], value=url_report["og:title"])
        changed = True

    if "description" in url_report.keys():
        urls_manager.set_url_description(
            url=url["url"], value=url_report["description"]
        )
        changed = True
    elif "og:description" in url_report.keys():
        urls_manager.set_url_description(
            url=url["url"], value=url_report["og:description"]
        )
        changed = True
    if not changed:
        urls_manager.set_url_error(url=url["url"], value="error: no h1 or description")


def process_linkedin_post(url_report, url, verbose=False):
    if verbose:
        print("linkedin_post or generic")
        print(url["url"])
    changed = False
    if "h1" in url_report.keys():
        if verbose:
            print(url["url"], ": ", url_report["h1"])
        urls_manager.set_url_h1(url=url["url"], value=url_report["h1"])
        changed = True
    elif "og:title" in url_report.keys():
        urls_manager.set_url_h1(url=url["url"], value=url_report["og:title"])
        changed = True
    description = None
    if "description" in url_report.keys():
        description = url_report["description"]
        changed = True
    elif "og:description" in url_report.keys():
        description = url_report["og:description"]
        changed = True

    if description is not None:
        urls_manager.set_url_description(url=url["url"], value=description)
        description_links = load_txt.put_urls_from_string(
            text_to_process=description, parent_url=url["url"]
        )
        urls_manager.set_url_description_links(url=url["url"], value=description_links)

    if not changed:
        urls_manager.set_url_error(url=url["url"], value="error: no h1 or description")


def scrap_url(url, verbose=False):
    # TODO: Need to change this

    if url["url_type"] is None:
        if verbose:
            print("\n\ngeneric:", url["url"])
        url["url_type"] = "generic"
    else:
        if verbose:
            print("\n\n", url["url_type"] + ":", url["url"])
    try:
        url_report = sniff_url.get_tags(url=url["url"])
    except Exception as e:
        urls_manager.set_url_error(url=url["url"], value="error")
        urls_manager.touch_url(url=url["url"])
        if verbose:
            print("\n\n!!! ERROR FOR:", url["url"])
            print(
                "\n\n!!! you can check the URL using the command sniff-url",
                url["url"],
                "\n\n",
            )
        return

    if url["url_type"] == "linkedin_redirect":
        process_linkedin_redirect(url_report=url_report, url=url, verbose=verbose)

    if url["url_type"] == "linkedin_feed":
        process_linkedin_feed(url_report=url_report, url=url, verbose=verbose)

    if url["url_type"] == "linkedin_job":
        process_linkedin_job(url_report=url_report, url=url, verbose=verbose)

    if url["url_type"] == "linkedin_post" or url["url_type"] == "generic":
        process_linkedin_post(url_report=url_report, url=url, verbose=verbose)

    urls_manager.set_url_json(url=url["url"], value=url_report["json"])
    urls_manager.touch_url(url=url["url"])


def isNaN(num):
    return num != num


def scrap_urls(
    recursive=False,
    ignore_valid_prefix=False,
    randomize=False,
    only_parents=True,
    verbose=False,
    n_urls=0,
):
    limit = 10
    classify_urls.classify_urls()
    urls = urls_manager.get_untouched_urls(
        ignore_valid_prefix=ignore_valid_prefix,
        randomize=randomize,
        only_parents=only_parents,
        limit=limit,
    )
    if len(urls) == 0:
        print("📭 no urls to scrap")
        if n_urls > 0:
            print(f"-- 🗃️ {n_urls} scraped urls in total...")
            print("scrapping is over...")
        return
    for index, url in urls.iterrows():
        wait = random.randint(1, 3)
        print(
            "🐶 Scrapper is sleeping for", wait, "seconds before scraping next url..."
        )
        time.sleep(wait)

        print("🐕 Scrapper is sniffing the url...")
        scrap_url(url=url, verbose=verbose)

    n_urls = n_urls + len(urls)
    print(f"-- 🗃️ {n_urls} scraped urls...")
    classify_urls.classify_urls()
    if recursive:
        wait = random.randint(5, 10)
        print(
            f"🐶 Scrapper is sleeping for {wait} seconds before next round of {limit} urls"
        )
        time.sleep(wait)
        scrap_urls(
            recursive=recursive,
            ignore_valid_prefix=ignore_valid_prefix,
            randomize=randomize,
            only_parents=only_parents,
            verbose=verbose,
            n_urls=n_urls,
        )
    else:
        print("scrapping is over...")
