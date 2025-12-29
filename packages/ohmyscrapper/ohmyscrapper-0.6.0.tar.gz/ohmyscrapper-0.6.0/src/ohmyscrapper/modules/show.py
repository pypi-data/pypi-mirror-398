import ohmyscrapper.models.urls_manager as urls_manager
from ohmyscrapper.core import config
import math
import os
from rich.console import Console
from rich.table import Table


def export_urls(limit=0, csv_file="output/urls.csv", simplify=False):
    output_folder = config.get_dir("output")

    df = urls_manager.get_urls(limit=limit)

    if simplify:
        df.drop(columns=["description", "json"], inplace=True)

    df.to_csv(csv_file, index=False)
    print("--------------------")
    print("📊🖋️ Urls exported to", csv_file)
    if "description" in df:
        try:
            df.replace(
                {
                    "description": {r"\n": " "},
                },
                regex=True,
                inplace=True,
            )
        except:
            pass
    df.to_html(csv_file + "-preview.html", index=False)
    print("📜🖋️ Urls preview exported to", csv_file + "-preview.html")
    print("--------------------")


def export_report(csv_file="output/report.csv"):
    output_folder = config.get_dir("output")
    df = urls_manager.get_urls_report()

    df.to_csv(csv_file, index=False)
    _clear_file(csv_file)
    print("--------------------")
    print("📊🖋️ Urls report exported to", csv_file)

    df.replace(
        {
            "description": {r"\n": " "},
        },
        regex=True,
        inplace=True,
    )
    df.to_html(csv_file + "-preview.html", index=False)
    _clear_file(csv_file + "-preview.html")

    print("📜🖋️ Urls report preview exported to", csv_file + "-preview.html")
    print("--------------------")


# TODO: Add transformation layer
def _clear_file(txt_tile):
    with open(txt_tile, "r") as f:
        content = f.read()
        content = content.replace(" -  -", " -")
        content = content.replace(" -<", "<")
        with open(txt_tile, "w") as f:
            f.write(content)


def show_urls(limit=0, jump_to_page=0):
    df = urls_manager.get_urls(limit=limit)
    df.drop(columns=["json", "description"], inplace=True)
    # df = df.head(n=20)

    # https://medium.com/@inzaniak/create-tables-in-your-terminal-with-python-6747d68d71a6

    total_items = len(df)
    items_per_page = 15
    n_pages = math.ceil(total_items / items_per_page)

    last_popped = 0
    for page in range(n_pages):

        df_page = df.head(n=items_per_page)
        df_t = df.T
        for i in range(items_per_page):
            if last_popped < total_items:
                df_t.pop(last_popped)
            last_popped += 1
        df = df_t.T
        if page < jump_to_page:
            continue
        show_table(df_page)

        print("Page", page + 1, "of", n_pages)
        user_input = input("Press enter to continue or type q to quit: ")
        if user_input == "q":
            break
        if user_input.isnumeric():
            jump_to_page = math.ceil(int(user_input))
            if jump_to_page > n_pages or jump_to_page < 1:
                print("This page does not exist")
                jump_to_page = 0
            else:
                jump_to_page = jump_to_page - 1
                if page < jump_to_page:
                    continue
                elif jump_to_page >= 0:
                    show_urls(limit=limit, jump_to_page=jump_to_page)
                    break

    return


# TODO: Change place
def show_table(df):
    columns = df.columns.tolist()
    df = df.to_dict(orient="records")
    table = Table(show_header=True, header_style="bold magenta")
    for column in columns:
        table.add_column(column)

    for row in df:
        table.add_row(*[str(value) for value in row.values()])
    console = Console()
    console.print(table)


def show_urls_valid_prefix(limit=0):
    print(urls_manager.get_urls_valid_prefix(limit=limit))
    return


def show_url(url):
    print(urls_manager.get_url_by_url(url=url).T)
    return
