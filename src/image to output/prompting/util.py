import os
import re
import csv
import PIL
import base64
import prompts
import vertexai
import numpy as np
import pandas as pd
from jinja2 import Template
from openai import OpenAI
from dotenv import load_dotenv
from anthropic import AnthropicVertex
from google.oauth2.service_account import Credentials
from vertexai.preview.generative_models import GenerativeModel, Image


def get_dirs(base_dir):
    return [d for d in os.listdir(base_dir) if os.path.isdir(os.path.join(base_dir, d))]


def get_rating(response):
    return int(re.search(r'<rating>.*?\b(\d)\b.*?<\/rating>', response, re.DOTALL).group(1))


def parse_image_name(filename):
    image_name = os.path.splitext(filename)[0]
    return tuple(map(int, image_name.split('_')[1:]))


def create_key(img_a, img_b):
    return f'{img_a[0]}_{img_a[1]}-{img_b[0]}_{img_b[1]}'


def make_similarity_dict(image_names):
    sorted_imgs = sorted(image_names, key=parse_image_name)
    result = {}

    for i in range(len(sorted_imgs)):
        for j in range(i, len(sorted_imgs)):
            img_a = parse_image_name(sorted_imgs[i])
            img_b = parse_image_name(sorted_imgs[j])
            result[create_key(img_a, img_b)] = 4 if img_a == img_b else 0

    return result


def write_similarity_matrix(similarity_dict, output_path):
    def f(img_str):
        return img_str.split("_", 1)[1]

    image_nums = sorted(
        set(key.split('-')[0] for key in similarity_dict.keys()), 
        key=lambda x: tuple(map(int, x.split('_')))
    )

    images = [f'image_{num}' for num in image_nums]

    matrix = []
    for img_a in images:
        row = [img_a]  
        for img_b in images:
            key_upper = f'{f(img_a)}-{f(img_b)}'
            key_lower = f'{f(img_b)}-{f(img_a)}'
            
            value = similarity_dict.get(key_upper, similarity_dict.get(key_lower, 0))
            row.append(value)
        matrix.append(row)

    with open(output_path, mode='w', newline='') as file:
        writer = csv.writer(file)
        writer.writerow([''] + images)  
        writer.writerows(matrix)


def convert_image_to_jpg(image_path):
    img = PIL.Image.open(image_path)
    if img.mode in ('RGBA', 'P'):
        img = img.convert('RGB')
    new_path = os.path.splitext(image_path)[0] + '.jpg'
    img.save(new_path, 'JPEG')
    return new_path


def load_jpg_as_base64(image_path):
    image_path_jpg = convert_image_to_jpg(image_path)
    with open(image_path_jpg, 'rb') as img_file:
        return base64.b64encode(img_file.read()).decode('utf-8')


def auth(model, c_region='us-east5', g_region='us-central1'): 
    """Add the following to an env in this dir:
    - openAI_key
    - c_projectID #project id for claude sonnet (vertex api)
    - g_projectID #project id for gemini 1.5 (vertex api)
    """
    
    load_dotenv()

    creds = Credentials.from_service_account_file(
        'claude_SA.json',
        scopes=['https://www.googleapis.com/auth/cloud-platform']
    )

    switcher = {
        'gpt': lambda: OpenAI(api_key=os.getenv('openAI_key')),
        'claude': lambda: AnthropicVertex(project_id=os.getenv('c_projectID'), region=c_region, credentials=creds),
        'gemini': lambda: (vertexai.init(project=os.getenv('g_projectID'), location=g_region), 
            GenerativeModel("gemini-1.5-pro-002"))[1],
    }

    return switcher.get(model, lambda: None)()


def extract_context(img_str, metadata_df):
        try:
            art_num, img_num = map(int, img_str.split('_'))
            filter = metadata_df.query('`image number` == @img_num and `article_number` == @art_num')
            alt_text = filter['alt'].iloc[0]
            heading = filter['article_heading'].iloc[0]
            return alt_text, heading
        except:
            print(img_str)
            return None, None


def create_img_struct(model, img_path):
    img_base64 = load_jpg_as_base64(img_path)
    img_struct = {}

    if model == 'gpt':
        img_struct = {
            "type": "image_url", 
            "image_url": {"url": f"data:image/jpeg;base64,{img_base64}"}
        }
    elif model == 'claude':
        img_struct = {
            "type": "image",
            "source": {
                "type": "base64",
                "media_type": "image/jpeg",
                "data": img_base64  
            }
        }
    elif model == 'gemini':
        img_struct = Image.load_from_file(img_path)

    return img_struct


def create_message(model, prompt_template, img_a_data, img_b_data, with_cot = True):
    img_a_struct, img_a_alt, img_a_heading = img_a_data
    img_b_struct, img_b_alt, img_b_heading = img_b_data

    data = {
        "image_a_context": f"Alt Text: {img_a_alt}, Heading: {img_a_heading}",
        "image_b_context": f"Alt Text: {img_b_alt}, Heading: {img_b_heading}"
    }

    if model == 'gemini':
        data["image_a"] = img_a_struct
        data["image_b"] = img_b_struct

    template = Template(prompt_template)
    rendered_text = template.render(data)

    if model == 'gemini':
        rendered_text += f"\n\n{prompts.cot}" if with_cot else f"\n\n{prompts.format}"
        return rendered_text
    
    parts = rendered_text.split("<image_a>")
    part1 = parts[0] 
    
    parts = parts[1].split("<image_b>")
    part2, part3 = parts[0], parts[1]

    if model == 'gemini':
        message = []

    message = {
        "role": "user",
        "content": [
            {"type": "text", "text": part1.strip()},  
            img_a_struct,  
            {"type": "text", "text": part2.strip()},  
            img_b_struct,  
            {"type": "text", "text": part3.strip()},
        ]
    }

    if with_cot:
        message["content"].append({"type": "text", "text": prompts.cot})
    else:
        message["content"].append({"type": "text", "text": prompts.format})

    return message


def calculate_rmse(similarity_dict, category_dir):
    try:
        true_labels_path = os.path.join(category_dir, 'true_labels.csv')
        true_labels_df = pd.read_csv(true_labels_path, index_col=0)

        predicted_values = []
        true_values = []
        wrong_labels = {}

        for pair, pred in similarity_dict.items():
            art_num_a, art_num_b = [part.split('_')[0] for part in pair.split('-')]

            if art_num_a == art_num_b:
                continue

            predicted_values.append(pred)

            img_a, img_b = [f'image_{num}' for num in pair.split('-')]
            true_value = true_labels_df.at[img_a, img_b]

            true_values.append(true_value)
            if true_value != pred:
                wrong_labels[pair] = pred, true_value

        squared_errors = [(int(true) - int(pred)) ** 2 for true, pred in zip(true_values, predicted_values)]
        mse = np.mean(squared_errors)
        rmse = np.sqrt(mse)

        return rmse/4.0, wrong_labels
    
    except Exception as e:
        print(e)
        return None, {}


def write_results(prompt, model, category, with_cot, rmse, wrong_labels, out_path='results.csv'):
    with open(out_path, mode='a', newline='') as file:
        writer = csv.writer(file)
        wrong_labels_str = ', '.join([f'{key}: {val}' for key, val in wrong_labels.items()])
        writer.writerow([prompt, model, category, with_cot, rmse, wrong_labels_str])
