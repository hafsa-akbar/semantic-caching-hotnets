## Semantic Caching for Web Affordability
This project explores the use of semantic caching to reduce data usage in web browsing by evaluating the replaceability potential of images in web articles.

#### Dataset
The `data/` folder contains the complete dataset of LLM-assigned similarity scores. Each category for each website is presented as a replaceability matrix, covering five randomly selected categories from the top 50 news and media websites (by Similarweb 2024 traffic share).

#### Project Structure
```
src
├── article scrapper
│   ├── scrapping.ipynb	~> Selenium Scraper for downloading images+metadata within articles
│   └── scripts	~> Contains a JS script needed for the scraper
├── dataset insights
│   └── dataset.ipynb ~> Contains properties of the dataset e.g, # of img comparisons, avg ing size etc.
├── description to output
│   ├── descriptions ~> Using LLaVA NeXT to generate detailed descriptions of images within the dataset
│   └── prompting ~> Using Llama 3.1 to label replaceability of img pairs (zero-shot + dynamic few shot prompting)
├── image to output
│   ├── prompt_eng.py ~> prompt eng for Claude 3.5 / GPT-4o / Gemini 1.5 Pro for lowest error
│   ├── prompts.py ~> base + metric-driven prompt templates
│   └── util.py ~> utility functions for prompt_eng.py
├── inter rater agreement
│   ├── Set 1 ~> similarity scores labelled by two raters across 3 websites
│   ├── Set 2 ~> similarity scores labelled by two other raters across 3 websites 
│   └── inter rater agreement.ipynb ~> calculating inter rater agreement using Krippendorff's alpha
├── page weights
│   ├── WebPageTest.ipynb ~> using WPT API to measure page weights of the articles in the dataset
│   └── wpt_data.csv ~> WPT page weight results
├── performance
│   └── eval.ipynb ~> contains all evaluations + graphs attached in the paper 
├── proof of concept ~> proof of concept architecture to model semantic caching
│   ├── client
│   ├── eval.ipynb ~> contains the results of browsing pattern simulations and their data savings
│   └── server
└── response variance ~> calculating response variation in LLM assigned labels
    ├── error_testing.py
    ├── eval.ipynb ~> pooled std. dev of model responses
    └── test_error ~> dataset on which each of the model was tested to calculate response variation
```
