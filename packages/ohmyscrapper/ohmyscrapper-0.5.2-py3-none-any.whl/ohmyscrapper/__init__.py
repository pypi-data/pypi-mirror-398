import argparse

from ohmyscrapper.modules.classify_urls import classify_urls
from ohmyscrapper.modules.sniff_url import sniff_url
from ohmyscrapper.modules.load_txt import load_txt
from ohmyscrapper.modules.seed import seed, export_url_types_to_file
from ohmyscrapper.modules.scrap_urls import scrap_urls
from ohmyscrapper.modules.show import (
    show_url,
    show_urls,
    show_urls_valid_prefix,
    export_urls,
    export_report,
)
from ohmyscrapper.modules.untouch_all import untouch_all
from ohmyscrapper.modules.process_with_ai import process_with_ai, reprocess_ai_history
from ohmyscrapper.modules.merge_dbs import merge_dbs


def main():
    parser = argparse.ArgumentParser(prog="ohmyscrapper")
    parser.add_argument("--version", action="version", version="%(prog)s v0.5.2")

    subparsers = parser.add_subparsers(dest="command", help="Available commands")
    start_parser = subparsers.add_parser(
        "start",
        help="Make the entire process of 📦 loading, 🐶 scraping and 📜🖋️ exporting with the default configuration.",
    )

    start_parser.add_argument(
        "--ai",
        default=False,
        help="Make the entire process of loading, processing, reprocessing with AI and exporting with the default configuration.",
        action="store_true",
    )

    ai_process_parser = subparsers.add_parser("ai", help="Process with AI.")
    ai_process_parser.add_argument(
        "--history", default=False, help="Reprocess ai history", action="store_true"
    )

    seed_parser = subparsers.add_parser(
        "seed", help="Seed database with `url_types` to classify the `urls`."
    )
    seed_parser.add_argument(
        "--export",
        default=False,
        help="Add all `url_types` from the bank to the `/customize/url_types.yaml` file.",
        action="store_true",
    )
    untouch_parser = subparsers.add_parser(
        "untouch-all", help="Untouch all urls. That resets classification"
    )

    classify_urls_parser = subparsers.add_parser(
        "classify-urls", help="Classify loaded urls"
    )
    classify_urls_parser.add_argument(
        "--recursive", default=False, help="Run in recursive mode", action="store_true"
    )

    load_txt_parser = subparsers.add_parser("load", help="📦 Load txt file")
    load_txt_parser.add_argument(
        "-input", default=None, help="File/Folder path or url."
    )
    load_txt_parser.add_argument(
        "--verbose", default=False, help="Run in verbose mode", action="store_true"
    )

    scrap_urls_parser = subparsers.add_parser("scrap-urls", help="🐶 Scrap urls")
    scrap_urls_parser.add_argument(
        "--recursive", default=False, help="Run in recursive mode", action="store_true"
    )
    scrap_urls_parser.add_argument(
        "--ignore-type", default=False, help="Ignore urls types", action="store_true"
    )
    scrap_urls_parser.add_argument(
        "--randomize", default=False, help="Random order", action="store_true"
    )
    scrap_urls_parser.add_argument(
        "--only-parents", default=False, help="Only parents urls", action="store_true"
    )
    scrap_urls_parser.add_argument(
        "--verbose", default=False, help="Run in verbose mode", action="store_true"
    )

    sniff_url_parser = subparsers.add_parser("sniff-url", help="🐕 Sniff/Check url")
    sniff_url_parser.add_argument(
        "url", default="https://cesarcardoso.cc/", help="Url to sniff"
    )

    show_urls_parser = subparsers.add_parser("show", help="Show urls and prefixes")
    show_urls_parser.add_argument(
        "--prefixes", default=False, help="Show urls valid prefix", action="store_true"
    )
    show_urls_parser.add_argument("--limit", default=0, help="Limit of lines to show")
    show_urls_parser.add_argument("-url", default="", help="Url to show")

    export_parser = subparsers.add_parser("export", help="📊🖋️ Export urls to csv.")
    export_parser.add_argument("--limit", default=0, help="Limit of lines to export")
    export_parser.add_argument(
        "--file",
        default="output/urls.csv",
        help="File path. Default is output/urls.csv",
    )
    export_parser.add_argument(
        "--simplify",
        default=False,
        help="Ignore json and descriptions",
        action="store_true",
    )

    report_parser = subparsers.add_parser(
        "report", help="📜🖋️ Export urls report to csv."
    )
    merge_parser = subparsers.add_parser("merge_dbs", help="Merge databases.")

    args = parser.parse_args()

    if args.command == "classify-urls":
        classify_urls(args.recursive)
        return

    if args.command == "load":
        load_txt(file_name=args.input, verbose=args.verbose)
        return

    if args.command == "seed":
        if args.export:
            export_url_types_to_file()
        else:
            seed()
        return

    if args.command == "untouch-all":
        untouch_all()
        return

    if args.command == "sniff-url":
        sniff_url(args.url)
        return

    if args.command == "scrap-urls":
        scrap_urls(
            recursive=args.recursive,
            ignore_valid_prefix=args.ignore_type,
            randomize=args.randomize,
            only_parents=args.only_parents,
            verbose=args.verbose,
        )
        return

    if args.command == "show":
        if args.prefixes:
            show_urls_valid_prefix(int(args.limit))
            return
        if args.url != "":
            show_url(args.url)
            return
        show_urls(int(args.limit))
        return

    if args.command == "export":
        export_urls(limit=int(args.limit), csv_file=args.file, simplify=args.simplify)
        return

    if args.command == "process-with-ai":
        if args.history:
            reprocess_ai_history()
        else:
            process_with_ai()
        return

    if args.command == "report":
        export_report()
        return

    if args.command == "merge_dbs":
        merge_dbs()
        return

    if args.command == "start":
        load_txt()
        scrap_urls(
            recursive=True,
            ignore_valid_prefix=True,
            randomize=False,
            only_parents=False,
        )
        if args.ai:
            process_with_ai()
        export_urls()
        export_urls(csv_file="output/urls-simplified.csv", simplify=True)
        export_report()
        return


if __name__ == "__main__":
    main()
