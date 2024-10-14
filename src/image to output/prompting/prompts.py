base_prompt = """
You are tasked with evaluating the replaceability of two images from different articles within the same category of a news website. 
Consider how well the two images align with each other in terms of their content and context. 

Use the following rating scale:

0: Not replaceable
1: Somewhat replaceable
2: Moderately replaceable
3: Very replaceable
4: Completely replaceable

Images and Associated Context:
<image_a>
    {{ image_a }}
</image_a>
<image_a_context>
    {{ image_a_context }}
</image_a_context>

<image_b>
    {{ image_b }}
</image_b>
<image_b_context>
    {{ image_b_context }}
</image_b_context>
"""

prompt1 = """You are tasked with evaluating the semantic replaceability of two images (Image A and Image B) from different articles within the same category of a news website. 
Your goal is to determine how interchangeable these images are based on their contexts and semantic similarity of the images, which include the article headings and alt text (where available).

Use the following rating scale for replaceability:
0: Not replaceable
1: Somewhat replaceable
2: Moderately replaceable
3: Very replaceable
4: Completely replaceable

Here are the contexts for the two images:

<image_a>
    {{ image_a }}
</image_a>
<image_a_context>
    {{ image_a_context }}
</image_a_context>

<image_b>
    {{ image_b }}
</image_b>
<image_b_context>
    {{ image_b_context }}
</image_b_context>

Consider the following factors when evaluating their semantic replaceability:
1. Similarity of topics
2. Specificity of information conveyed (e.g, specific people, places etc)
3. Emotional tone or impact
4. Potential for misinterpretation if swapped
"""

#########################################################################################

cot = """
Using chain of thought prompting, analyze these two images and rate their replaceability. 
Break down your thought process step by step. 
Write your answer in the following format:

<rating>
[Your rating (0-4)]
</rating>
<justification>
Explanation: [Brief explanation for your rating, synthesizing your analysis of all factors]
</justification>
"""

format = """
Write your answer in the following format:

<rating>
[Your rating (0-4)]
</rating>
"""