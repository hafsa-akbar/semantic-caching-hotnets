import os
import util
import prompts
import time
import pandas as pd
from tqdm import tqdm

def gpt_predictions(gpt_client, msg, retries=3, delay=5):
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


def claude_predictions(claude_client, msg, retries=3, delay=5):
    for _ in range(retries):
        try:
            response = claude_client.messages.create(
                model="claude-3-5-sonnet@20240620",
                messages=[msg],
                max_tokens=1024,
                stream=False
            )
            time.sleep(15) # rate limit
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
                    "max_output_tokens": 8192,
                    "temperature": 1,
                    "top_p": 0.95
                },
                stream=False
            )
            time.sleep(11)
            return util.get_rating(response.text)
        except Exception as e:
            print(e)
            time.sleep(delay)
    return 0


def get_predictions(category_dir, model, prompt, with_cot=True):
    image_names = [f for f in os.listdir(category_dir) if f.endswith('.jpg')]
    similarity_dict = util.make_similarity_dict(image_names)
    metadata_df = pd.read_csv(os.path.join(category_dir, 'image_data.csv'))

    def get_img_data(img_str):
        path = os.path.join(category_dir, f'image_{img_str}.jpg')
        img_struct = util.create_img_struct(model, path)
        context_tuple = util.extract_context(img_str, metadata_df)
        return (img_struct, *context_tuple) 

    client = util.auth(model)

    prediction_func = globals()[f'{model}_predictions']

    for test_pair in tqdm(similarity_dict):
        img_strs = test_pair.split('-')
        art_num1, art_num2 = map(lambda x: int(x.split('_')[0]), img_strs)
        img_a_data, img_b_data = map(get_img_data, img_strs)

        if art_num1 == art_num2:
            continue

        msg = util.create_message(model, prompt, img_a_data, img_b_data, with_cot)
        similarity_dict[test_pair] = prediction_func(client, msg)
    
    return similarity_dict


def process_websites(base_dir, model, prompt, with_cot=True, websites=[]):
    if not websites:
        websites = util.get_dirs(base_dir)

    for website in websites:
        categories = util.get_dirs(os.path.join(base_dir, website))

        for category in categories:
            pred_file = f'{model}_pred_labels.csv'
            if os.path.exists(os.path.join(base_dir, website, category, pred_file)):
                continue

            print(f'Testing {website} - {category}\n')
            category_dir = os.path.join(base_dir, website, category)
            similarity_dict = get_predictions(category_dir, model, prompt, with_cot)

            output_path = os.path.join(category_dir, pred_file)
            util.write_similarity_matrix(similarity_dict, output_path)

            # for testing out additional prompts, put prompt string in prompt.py
            # and uncomment the following

            #rmse, wrong_labels = util.calculate_rmse(similarity_dict, category_dir)
            #
            #util.write_results(
            #    prompt= prompt,
            #    model= model,
            #    category= f'{website} - {category}',
            #    with_cot= with_cot,
            #    rmse= rmse,
            #    wrong_labels= wrong_labels,
            #)

if __name__ == '__main__':
    model, prompt = 'gpt', prompts.prompt2
    process_websites('../../data', model, prompt, with_cot=True)