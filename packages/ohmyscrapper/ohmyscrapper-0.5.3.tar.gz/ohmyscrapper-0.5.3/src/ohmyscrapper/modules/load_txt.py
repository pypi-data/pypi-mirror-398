import os
from urlextract import URLExtract
import ohmyscrapper.models.urls_manager as urls_manager


def _increment_file_name(text_file_content, file_name):
    print(f"reading and loading file `{file_name}`... ")
    with open(file_name, "r") as f:
        return text_file_content + f.read()


def load_txt(file_name="input", verbose=False):
    if not os.path.exists("db"):
        os.mkdir("db")

    if not os.path.exists("input"):
        os.mkdir("input")

    urls_manager.seeds()

    text_file_content = ""
    if file_name is not None and not os.path.isdir(file_name):
        print(f"📖 reading file `{file_name}`... ")
        if not os.path.exists(file_name):
            if file_name.startswith("https://") or file_name.startswith("http://"):
                text_file_content = " " + file_name + " "
            else:
                print(f"\n file `{file_name}` not found.")
                return
        else:
            text_file_content = _increment_file_name(
                text_file_content=text_file_content, file_name=file_name
            )
    else:
        print("📂 reading /input directory... ")
        if file_name is None:
            dir_files = "input"
        else:
            dir_files = file_name
        text_files = os.listdir(dir_files)
        for file in text_files:
            if not file.endswith(".txt"):
                text_files.remove(file)
        if len(text_files) == 0:
            print("No text files found in /input directory!")
            return
        elif len(text_files) == 1:
            print(f"📖 reading file `{dir_files}/{text_files[0]}`... ")
            text_file_content = _increment_file_name(
                text_file_content=text_file_content,
                file_name=dir_files + "/" + text_files[0],
            )
        else:
            print("\nChoose a text file. Use `*` for process all and `q` to quit:")
            for index, file in enumerate(text_files):
                print(f"[{index}]:", dir_files + "/" + file)

            # TODO: there is a better way for sure!
            text_file_option = -1
            while text_file_option < 0 or text_file_option >= len(text_files):
                text_file_option = input("Enter the file number: ")
                if text_file_option == "*":
                    for file in text_files:
                        text_file_content = _increment_file_name(
                            text_file_content=text_file_content,
                            file_name=dir_files + "/" + file,
                        )
                        text_file_option = 0
                elif text_file_option == "q":
                    return
                elif text_file_option.isdigit():
                    text_file_option = int(text_file_option)
                    if text_file_option >= 0 and text_file_option < len(text_files):
                        text_file_content = _increment_file_name(
                            text_file_content=text_file_content,
                            file_name=dir_files
                            + "/"
                            + text_files[int(text_file_option)],
                        )

    print("🔎 looking for urls...")
    urls_found = put_urls_from_string(
        text_to_process=text_file_content, verbose=verbose
    )

    print("--------------------")
    print("files processed")
    print(f"📦 {urls_found} urls were extracted and packed into the database")


def put_urls_from_string(text_to_process, parent_url=None, verbose=False):
    if isinstance(text_to_process, str):
        extractor = URLExtract()
        for url in extractor.find_urls(text_to_process):
            urls_manager.add_url(url=url, parent_url=parent_url)
            if verbose:
                print(url, "added")

        return len(extractor.find_urls(text_to_process))
    else:
        return 0
