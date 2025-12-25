import ohmyscrapper.models.urls_manager as urls_manager
import pandas as pd
import time


def classify_urls(recursive=False):
    urls_manager.seeds()
    df = urls_manager.get_urls_valid_prefix()

    keep_alive = True
    while keep_alive:
        print("#️⃣  URL Classifier woke up to classify urls!")
        for index, row_prefix in df.iterrows():
            df_urls = urls_manager.get_url_like_unclassified(
                like_condition=row_prefix["url_prefix"]
            )
            for index, row_urls in df_urls.iterrows():
                urls_manager.set_url_type_by_id(
                    url_id=row_urls["id"], url_type=row_prefix["url_type"]
                )

        if not recursive:
            print("#️⃣  URL Classifier said: I'm done! See you soon...")
            keep_alive = False
        else:
            print("#️⃣  URL Classifier is taking a nap...")
            time.sleep(10)
