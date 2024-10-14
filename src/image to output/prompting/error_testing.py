import os
import util
import prompts
import time
import pandas as pd
import json
from tqdm import tqdm

def gpt_predictions(gpt_client, msg, retries=3, delay=25):
    for _ in range(retries):
        try:
            response = gpt_client.chat.completions.create(
                model="gpt-4o", 
                max_tokens=400,
                messages=[msg]
            )
            return util.get_rating(response.choices[0].message.content.strip())
        except Exception as e:
            print(e)
            time.sleep(delay)
    return 0


def claude_predictions(claude_client, msg, retries=3, delay=25):
    for _ in range(retries):
        try:
            response = claude_client.messages.create(
                model="claude-3-5-sonnet@20240620",
                messages=[msg],
                max_tokens=400,
                stream=False
            )
            time.sleep(8) # rate limit
            return util.get_rating(response.content[0].text)
        except Exception as e:
            print(e)
            time.sleep(delay)
    return 0


def gemini_predictions(gemini_client, msg, retries=3, delay=25):
    for _ in range(retries):
        try:
            response = gemini_client.generate_content(
                [msg],
                generation_config = {
                    "max_output_tokens": 400,
                    "temperature": 1,
                    "top_p": 0.95
                },
                stream=False
            )
            time.sleep(8)
            return util.get_rating(response.text)
        except Exception as e:
            print(e)
            time.sleep(delay)
    return 0


def get_predictions(category_dir, model, prompt, with_cot=True):
    image_names = [f for f in os.listdir(category_dir) if f.endswith('.jpg')]
    img_a, img_b = map(util.parse_image_name, image_names)
    test_pair = util.create_key(img_a, img_b)

    metadata_df = pd.read_csv(os.path.join(category_dir, 'image_data.csv'))

    def get_img_data(img_str):
        path = os.path.join(category_dir, f'image_{img_str}.jpg')
        img_struct = util.create_img_struct(model, path)
        context_tuple = util.extract_context(img_str, metadata_df)
        return (img_struct, *context_tuple) 

    client = util.auth(model)

    prediction_func = globals()[f'{model}_predictions']

    img_strs = test_pair.split('-')
    img_a_data, img_b_data = map(get_img_data, img_strs)

    msg = util.create_message(model, prompt, img_a_data, img_b_data, with_cot)
    pred_score = prediction_func(client, msg)

    return metadata_df.iloc[0]['score'], pred_score


def process_websites(base_dir, model, prompt, with_cot=True, websites=[], runs=20):
    if not websites:
        websites = util.get_dirs(base_dir)
    
    output_path = os.path.join(base_dir, 'output.json')
    score_dict = {}
    
    for website in tqdm(websites):
        for run in range(runs):  
            
            categories = util.get_dirs(os.path.join(base_dir, website))
            
            for category in categories:
                pred_file = f'{model}_pred_labels.csv'
                if os.path.exists(os.path.join(base_dir, website, category, pred_file)):
                    continue
                
                print(f'Testing {website} - Run {run}')
                category_dir = os.path.join(base_dir, website, category)
                
                true, pred = map(int, get_predictions(category_dir, model, prompt, with_cot))
                
                if true not in score_dict:
                    score_dict[true] = []
                
                score_dict[true].append(pred)
            print(score_dict)
    
    with open(output_path, 'w') as f:
        json.dump(score_dict, f, indent=4)

    print(f"Predictions written to {output_path}")

if __name__ == '__main__':
    model, prompt = 'gpt', prompts.prompt2
    process_websites(f'test_error/{model}', model, prompt, with_cot=True)
