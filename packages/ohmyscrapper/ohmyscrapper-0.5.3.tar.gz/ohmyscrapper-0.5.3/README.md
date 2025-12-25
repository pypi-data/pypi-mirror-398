# 🐶 OhMyScrapper - v0.5.3

OhMyScrapper scrapes texts and urls looking for links and jobs-data to create a
final report with general information about job positions.

## Scope

- Read texts;
- Extract and load urls;
- Scrapes the urls looking for og:tags and titles;
- Export a list of links with relevant information;

## Installation

You can install directly in your `pip`:
```shell
pip install ohmyscrapper
```

I recomend to use the [uv](https://docs.astral.sh/uv/getting-started/installation/#standalone-installer), so you can just use the command bellow and everything is installed:
```shell
uv add ohmyscrapper
uv run ohmyscrapper --version
```

But you can use everything as a tool, for example:
```shell
uvx ohmyscrapper --version
```


## How to use and test (development only)

OhMyScrapper works in 3 stages:

1. It collects and loads urls from a text in a database;
2. It scraps/access the collected urls and read what is relevant. If it finds new urls, they are collected as well;
3. Export a list of urls in CSV files;

You can do 3 stages with the command:
```shell
ohmyscrapper start
```
> Remember to add your text file in the folder `/input` with the name that finishes with `.txt`!

You will find the exported files in the folder `/output` like this:
- `/output/report.csv`
- `/output/report.csv-preview.html`
- `/output/urls-simplified.csv`
- `/output/urls-simplified.csv-preview.html`
- `/output/urls.csv`
- `/output/urls.csv-preview.html`

### BUT: if you want to do step by step, here it is:

First we load a text file you would like to look for urls. It it works with any txt file.

The default folder is `/input`. Put one or more text (finished with `.txt`) files
in this folder and use the command `load`:
```shell
ohmyscrapper load
```
or, if you have another file in a different folder, just use the argument `-input` like this:
```shell
ohmyscrapper load -input=my-text-file.txt
```
In this case, you can add an url directly to the database, like this:
```shell
ohmyscrapper load -input=https://cesarcardoso.cc/
```
That will append the last url in the database to be scraped.

That will create a database if it doesn't exist and store every url the oh-my-scrapper
find. After that, let's scrap the urls with the command `scrap-urls`:

```shell
ohmyscrapper scrap-urls --recursive --ignore-type
```

That will scrap only the linkedin urls we are interested in. For now they are:
- linkedin_post: https://%.linkedin.com/posts/%
- linkedin_redirect: https://lnkd.in/%
- linkedin_job: https://%.linkedin.com/jobs/view/%
- linkedin_feed" https://%.linkedin.com/feed/%
- linkedin_company: https://%.linkedin.com/company/%

But we can use every other one generically using the argument `--ignore-type`:
```shell
ohmyscrapper scrap-urls --ignore-type
```

And we can ask to make it recursively adding the argument `--recursive`:
```shell
ohmyscrapper scrap-urls --recursive
```
> !!! important: we are not sure about blocks we can have for excess of requests

And we can finally export with the command:
```shell
ohmyscrapper export
ohmyscrapper export --file=output/urls-simplified.csv --simplify
ohmyscrapper report
```


That's the basic usage!
But you can understand more using the help:
```shell
ohmyscrapper --help
```

## See Also

- Github: https://github.com/bouli/ohmyscrapper
- PyPI: https://pypi.org/project/ohmyscrapper/

## License
This package is distributed under the [MIT license](https://opensource.org/license/MIT).
