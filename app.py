from flask import Flask, render_template
from flask import url_for, redirect, request, make_response, jsonify, send_from_directory

import pandas as pd

import transformers
from ferret.explainers.shap import SHAPExplainer
from ferret.explainers.gradient import IntegratedGradientExplainer
from ferret.explainers.lime import LIMEExplainer
import spacy
import os
import inseq
from inseq.data.aggregator import SubwordAggregator


# ------------------ Prepare models and variables ------------------

try:
    nlp = spacy.load("it_core_news_sm")
except:
    os.system("python -m spacy download it_core_news_sm")
    nlp = spacy.load("it_core_news_sm")

clf_model_name = "E-MIMIC/inclusively-classification"
s2s_model_name = "E-MIMIC/inclusively-reformulation-it5"

clf_pipeline = transformers.pipeline("text-classification", model=clf_model_name, tokenizer=clf_model_name, device=0)
s2s_pipeline = transformers.pipeline("text2text-generation", model=s2s_model_name, tokenizer=s2s_model_name, device=0)

clf_model = transformers.AutoModelForSequenceClassification.from_pretrained(clf_model_name).to("cuda")
clf_tokenizer = transformers.AutoTokenizer.from_pretrained(clf_model_name)
s2s_explainability_techniques = [
    "saliency",
    "integrated_gradients",
    "deeplift",
    "gradient_shap",
    "lime",
    "input_x_gradient",
]
s2s_explainers = {}
for technique in s2s_explainability_techniques:
    s2s_explainers[technique] = inseq.load_model(s2s_model_name, technique, device="cpu")

explainers = {
    "shap": SHAPExplainer(clf_model, clf_tokenizer),
    "gradient": IntegratedGradientExplainer(clf_model, clf_tokenizer),
    "lime": LIMEExplainer(clf_model, clf_tokenizer)
}

clf_mapping = {
    "LABEL_0" : "inclusive",
    "LABEL_1" : "not_inclusive",
    "LABEL_2" : "not_pertinent",
}

FEEDBACKS_FOLDER = "feedbacks/"

# ------------------ Define functions ------------------
def _classify(text):
    return clf_mapping[clf_pipeline(text)[0]["label"]]

def _classify_and_get_class_id(text):
    cls = clf_pipeline(text)[0]["label"]
    return cls, int(cls.split("_")[1])

def _reformulate(text):
    return s2s_pipeline(text, max_length=128)[0]["generated_text"]

def _sentence_splitting(text):
    doc = nlp(text)
    return [sent.text for sent in doc.sents]

# ------------------ Define routes ------------------
app = Flask(__name__)


@app.route('/')
def index():
    title = 'Inclusively'
    return render_template('index.html', title=title)

@app.route('/testing')
def testing():
    title = 'Testing'
    return render_template('testing.html', title=title)

@app.route("/submit_testing", methods=["GET", "POST"])
def submit_testing():
    '''
    This function receive the input text as a POST request and return the output text HTML formatted.
    It processes the text with both classification and rewriting models (if needed).
    '''
    title = 'Testing'

    input_text = request.form.get("input_text")
    success = False

    # check if the input text is not empty
    if input_text.strip() != "":

        # sentences splitting
        sentences = _sentence_splitting(input_text)
        output_HTML = "<p>"
        for s in sentences:
            # classification
            sentence_class = _classify(s)
            if sentence_class not in ["inclusive", "not_pertinent"]:
                # rewrite
                sentence_rewritten = _reformulate(s)
                # add original sentence in red and crossed out
                output_HTML += f"<span style='color:red; text-decoration: line-through;'>{s}</span> "
                # add reformulated sentence in green
                output_HTML += f"<span style='color:green;'>{sentence_rewritten}</span> "
            else:
                # add original sentence in black
                output_HTML += f"<span style='color:black;'>{s}</span> "

        output_HTML += "</p>"
        success = True
    else:
        # output_HTML contains a red underlined text, "No text provided"
        output_HTML = "<p><span style='color:red; text-decoration: underline;'>No text provided</span></p>"
        success = False

    # this function is called by AJAX, so it returns a JSON object
    return jsonify(
        {
            "output_HTML": output_HTML,
            "success": success
        }
    )

@app.route('/evaluation')
def evaluation():
    '''
    This function is called when the user clicks on the evaluation page.
    '''
    title = 'Evaluation'
    return render_template('evaluation.html', title=title)

@app.route('/submit_evaluation', methods=["GET", "POST"])
def submit_evaluation():
    '''
    This function is called when the user submit a text on the evaluation page.
    It should run the classification and rewriting models (if needed) and return the output.
    The output is a JSON object containing, for each sentence, the original sentence, the classification and the rewriting.
    '''
    title = 'Evaluation'

    input_text = request.form.get("input_text")
    success = False

    # check if the input text is not empty
    if input_text.strip() != "":

        sentences = _sentence_splitting(input_text)
        output = {
            "original_sentences": [],
            "classification": [],
            "rewriting": []
        }
        for s in sentences:
            # classification
            sentence_class = _classify(s)
            output["original_sentences"].append(s)
            output["classification"].append(sentence_class)
            if sentence_class not in ["inclusive", "not_pertinent"]:
                # rewrite
                sentence_rewritten = _reformulate(s)
                output["rewriting"].append(sentence_rewritten)
            else:
                output["rewriting"].append("")
        success = True
    else:
        output = {
            "original_sentences": [],
            "classification": [],
            "rewriting": []
        }
        success = False

    # this function is called by AJAX, so it returns a JSON object
    return jsonify(
        {
            "output": output,
            "success": success
        }
    )
# ------------------ Feedback ------------------
@app.route('/submit_feedback_evaluation', methods=["GET", "POST"])
def submit_feedback_evaluation():
    '''
    This function is called when the user submit the feedback form on the evaluation page.
    '''

    success = True
    try:
        # get the feedback
        feedback = request.json
        original_sentences = feedback["original_sentences"]
        rewriting = feedback["rewriting"]
        classification = feedback["classification"]
        classification_feedback = feedback["classification_feedback"]
        rewriting_feedback = feedback["rewriting_feedback"]
        return_message = "Thank you for your feedback!"

        # create a dataframe with the feedback
        df = pd.DataFrame({
            "original_sentence": original_sentences,
            "model_classification": classification,
            "classification_feedback": classification_feedback,
            "model_rewriting": rewriting,
            "rewriting_feedback": rewriting_feedback
        })

        # save the dataframe as a tsv file
        # find a unique filename in the feedbacks folder
        i = 0
        while os.path.exists(FEEDBACKS_FOLDER + f"feedback_{i}.tsv"):
            i += 1
        df.to_csv(FEEDBACKS_FOLDER + f"feedback_{i}.tsv", sep="\t", index=False)

    except Exception as e:
        print(e)
        success = False

    return jsonify(
        {
            "success": success,
            "message": return_message
        }
    )

@app.route('/explanation')
def explanation():
    title = 'explanation'
    return render_template('explanation.html', title=title)

@app.route('/submit_for_explanation', methods=["GET", "POST"])
def run_explainability_models():
    '''
    This function is called when the user submit a text on the explanation page.
    It should run the classification and rewriting models (if needed) and return the output.
    The output is a JSON object containing, for each sentence, the original sentence, the classification and the rewriting.
    '''
    title = 'Explanation'

    input_text = request.form.get("input_text")
    explainability_technique = request.form.get("explainability_technique")
    s2s_explainability_technique = request.form.get("s2s_explainability_technique")

    if explainability_technique not in explainers.keys():
        return jsonify(
            {
                "success": False,
                "message": "Explainability technique not supported"
            }
        )
    
    cls_output, class_int = _classify_and_get_class_id(input_text)
    explainer = explainers[explainability_technique]
    output_explanation = explainer(input_text, target=class_int)
    # output_explanation contains .text, .tokens, .scores
    tokens = output_explanation.tokens
    scores = list(output_explanation.scores)

    # s2s explanation
    s2s_explainer = s2s_explainers[s2s_explainability_technique]
    out = s2s_explainer.attribute(input_text, n_steps=100)
    header_html = """<br/><b>0th instance:</b><br/>\n<html>\n"""
    s2s_html_explanation = out.aggregate().show(display=False, return_html=True, aggregator=SubwordAggregator).replace(header_html, "")

    return jsonify(
        {
            "success": True,
            "tokens": tokens,
            "scores": scores,
            "explainability_technique": explainability_technique,
            "classification_output": clf_mapping[cls_output],
            "s2s_html_explanation": s2s_html_explanation
        }
    )

    


if __name__ == '__main__':
    app.run(debug=True, port=9999)