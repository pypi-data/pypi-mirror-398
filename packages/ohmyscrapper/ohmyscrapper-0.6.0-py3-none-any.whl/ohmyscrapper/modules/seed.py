import ohmyscrapper.models.urls_manager as urls_manager
from ohmyscrapper.core import config
import os
import yaml


def seed():
    seeds = get_url_types_from_file()
    if len(seeds) == 0:
        url_types = urls_manager.get_urls_valid_prefix()
        if len(url_types) == 0:
            _push_seed_sample_data()
            seeds = get_url_types_from_file()

    if len(seeds) > 0:
        urls_manager.seeds(seeds=seeds)
        print("🫒 db seeded")
    return

# TODO: Make it yaml.safe_dump
def _push_seed_sample_data():
    sample_data = """
linkedin_post: https://%.linkedin.com/posts/%
linkedin_redirect: https://lnkd.in/%
linkedin_job: https://%.linkedin.com/jobs/view/%
linkedin_feed: https://%.linkedin.com/feed/%
linkedin_company: https://%.linkedin.com/company/%
    """.strip()

    with open(_get_url_types_file_path(), "+w") as f:
        f.write(sample_data)


def get_url_types_from_file():
    if os.path.exists(_get_url_types_file_path()):
        with open(_get_url_types_file_path(), "r") as f:
            url_types = yaml.safe_load(f.read())
            if url_types is None:
                url_types = {}
            return url_types
    else:
        export_url_types_to_file()
        return get_url_types_from_file()


def export_url_types_to_file():
    url_types = urls_manager.get_urls_valid_prefix()
    yaml_url_types = {}
    for index, url_type in url_types.iterrows():
        yaml_url_types[url_type["url_type"]] = url_type["url_prefix"]

    # append
    with open(_get_url_types_file_path(), "+a") as f:
        yaml.dump(yaml_url_types, f, allow_unicode=True)
    # read
    with open(_get_url_types_file_path(), "r") as f:
        yaml_url_types = yaml.safe_load(f.read())
    # overwrite preventing repetition
    with open(_get_url_types_file_path(), "w") as f:
        yaml.dump(yaml_url_types, f, allow_unicode=True)


def _get_url_types_file_path():
    customize_folder = config.get_dir()
    url_types_file = config.get_files("url_types")

    url_types_file = os.path.join(customize_folder,url_types_file)
    return url_types_file
