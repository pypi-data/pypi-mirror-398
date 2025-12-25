import ohmyscrapper.models.urls_manager as urls_manager
from bs4 import BeautifulSoup
from google import genai
from dotenv import load_dotenv
import random
import time
import os
import yaml
import json

# TODO: !!! REFACTOR !!!
load_dotenv()


def reprocess_ai_history():
    df = urls_manager.get_ai_log().to_dict(orient="records")
    for row in df:
        process_ai_response(row["response"])


def process_ai_response(response):
    job_positions = xml2dict(response)

    for index, xml_item_children in job_positions.items():
        for url_child_xml in xml_item_children:

            url_parent = urls_manager.get_url_by_id(url_child_xml["id"])
            if len(url_parent) > 0:
                url_parent = url_parent.iloc[0]
            h1 = url_child_xml.copy()
            del h1["id"]
            del h1["url"]
            h1 = " - ".join(h1.values())
            if url_parent["description_links"] > 1 and url_child_xml["id"] != "":
                print("-- child updated -- \n", url_child_xml["url"], ":", h1)
                urls_manager.set_url_h1(url_child_xml["url"], h1)
                urls_manager.set_url_ai_processed_by_url(
                    url_child_xml["url"], str(json.dumps(url_child_xml))
                )
                if url_parent["url"] != url_child_xml["url"]:
                    urls_manager.set_url_ai_processed_by_url(
                        url_parent["url"], "children-update"
                    )
            else:
                print("-- parent updated -- \n", url_parent["url"], ":", h1)
                urls_manager.set_url_h1(url_parent["url"], h1)
                urls_manager.set_url_ai_processed_by_url(
                    url_parent["url"], str(json.dumps(url_child_xml))
                )


def xml2dict(xml_string):
    soup = BeautifulSoup(xml_string, "html.parser")

    children_items_dict = {}
    for item in soup.find_all():
        if item.parent.name == "[document]":
            children_items_dict[item.name] = []
        elif item.parent.name in children_items_dict:
            children_items_dict[item.parent.name].append(_xml_children_to_dict(item))

    return children_items_dict


def _xml_children_to_dict(xml):
    item_dict = {}
    for item in xml.find_all():
        item_dict[item.name] = item.text
    return item_dict


def process_with_ai(recursive=True, triggered_times=0):
    triggered_times = triggered_times + 1

    prompt = _get_prompt()
    if not prompt:
        return

    url_type = "linkedin_post"
    df = urls_manager.get_urls_by_url_type_for_ai_process(url_type)
    if len(df) == 0:
        print("no urls to process with ai anymore")
        return

    texts = ""
    for index, row in df.iterrows():
        texts = (
            texts
            + f"""
        <text>
        <id>{str(row['id'])}</id>
        {row['description']}
        </text>
        """
        )
    if texts == "":
        print("no urls to process")
        return

    print("starting...")
    print("prompt:", prompt["name"])
    print("model:", prompt["model"])
    print("description:", prompt["description"])
    prompt["instructions"] = prompt["instructions"].replace(
        "{ohmyscrapper_texts}", texts
    )

    # The client gets the API key from the environment variable `GEMINI_API_KEY`.
    client = genai.Client()
    response = client.models.generate_content(
        model=prompt["model"], contents=prompt["instructions"]
    )
    response = str(response.text)
    urls_manager.add_ai_log(
        instructions=prompt["instructions"],
        response=response,
        model=prompt["model"],
        prompt_name=prompt["name"],
        prompt_file=prompt["prompt_file"],
    )
    print(response)
    print("^^^^^^")
    process_ai_response(response=response)
    print("ending...")

    for index, row in df.iterrows():
        urls_manager.set_url_empty_ai_processed_by_id(row["id"])

    if recursive:
        wait = random.randint(1, 3)
        print("sleeping for", wait, "seconds before next round")
        time.sleep(wait)

        if triggered_times > 5:
            print("!!! This is a break to prevent budget accident$.")
            print("You triggered", triggered_times, "times the AI processing function.")
            print(
                "If you are sure this is correct, you can re-call this function again."
            )
            print("Please, check it.")
            return

        process_with_ai(recursive=recursive, triggered_times=triggered_times)

    return


def _get_prompt():
    prompts_path = "prompts"
    default_prompt = """---
model: "gemini-2.5-flash"
name: "default-prompt"
description: "Put here your prompt description."
---
Process with AI this prompt: {ohmyscrapper_texts}
"""
    if not os.path.exists(prompts_path):
        os.mkdir(prompts_path)

        open(f"{prompts_path}/prompt.md", "w").write(default_prompt)
        print(
            f"You didn't have a prompt file. One was created in the /{prompts_path} folder. You can change it there."
        )
        return False

    prompt_files = os.listdir(prompts_path)
    if len(prompt_files) == 0:
        open(f"{prompts_path}/prompt.md", "w").write(default_prompt)
        print(
            f"You didn't have a prompt file. One was created in the /{prompts_path} folder. You can change it there."
        )
        return False
    prompt = {}
    if len(prompt_files) == 1:
        prompt = _parse_prompt(prompts_path=prompts_path, prompt_file=prompt_files[0])
    else:
        print("Choose a prompt:")
        prompts = {}
        for index, file in enumerate(prompt_files):
            prompts[index] = _parse_prompt(prompts_path=prompts_path, prompt_file=file)
            print(index, ":", prompts[index]["name"])
        input_prompt = input(
            "Type the number of the prompt you want to use or 'q' to quit: "
        )
        if input_prompt == "q":
            return False
        try:
            prompt = prompts[int(input_prompt)]
        except:
            print("! Invalid prompt\n")
            prompt = _get_prompt()
    return prompt


def _parse_prompt(prompts_path, prompt_file):
    prompt = {}
    raw_prompt = open(f"{prompts_path}/{prompt_file}", "r").read().split("---")
    prompt = yaml.safe_load(raw_prompt[1])
    prompt["instructions"] = raw_prompt[2].strip()
    prompt["prompt_file"] = prompt_file

    return prompt


# TODO: Separate gemini from basic function
def _process_with_gemini(model, instructions):
    response = """"""
    return response


def _process_with_openai(model, instructions):
    # import os
    # from openai import OpenAI

    # client = OpenAI(
    #    # This is the default and can be omitted
    #    api_key=os.environ.get("OPENAI_API_KEY"),
    # )

    # response = client.responses.create(
    #    model="gpt-4o",
    #    instructions="You are a coding assistant that talks like a pirate.",
    #    input="How do I check if a Python object is an instance of a class?",
    # )

    # print(response.output_text)

    response = """"""
    return response
