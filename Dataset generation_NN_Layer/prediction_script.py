import json
import numpy as np
import re
from gensim.models import Word2Vec
from tensorflow.keras.models import load_model

# -----------------------
# LOAD MODELS
# -----------------------

w2v_model = Word2Vec.load("D:\AI_Assisted_Smart_Compiler\Dataset generation_NN_Layer\word2vec.model")
model = load_model("D:\AI_Assisted_Smart_Compiler\Dataset generation_NN_Layer\statement_classifier.h5")

# -----------------------
# TOKENIZER
# -----------------------

def tokenize(statement):
    return re.findall(r'[A-Za-z_]+|\d+|[=+\-*/<>;(){}]', statement)


# -----------------------
# VECTORIZE STATEMENT
# -----------------------

def statement_vector(tokens):
    vectors = []

    for token in tokens:
        if token in w2v_model.wv:
            vectors.append(w2v_model.wv[token])

    if len(vectors) == 0:
        return np.zeros(w2v_model.vector_size)

    return np.mean(vectors, axis=0)


# -----------------------
# CLASS LABELS
# -----------------------

labels = {
    0: "assignment",
    1: "loop",
    2: "conditional",
    3: "declaration"
}


# -----------------------
# CONVERT AST NODE → TEXT
# -----------------------

def node_to_statement(node):

    node_type = node["type"]

    if node_type == "AssignmentNode":
        target = node["target"]["name"]
        value = node["value"]["value"]
        return f"{target} = {value};"

    if node_type == "IfNode":
        op = node["condition"]["operator"]
        left = node["condition"]["left"]["name"]
        right = node["condition"]["right"]["value"]
        return f"if({left} {op} {right})"

    if node_type == "PrintNode":
        value = node["expression"]["value"]
        return f'print("{value}")'

    return ""


# -----------------------
# LOAD JSON AST
# -----------------------

with open("D:\AI_Assisted_Smart_Compiler\Dataset generation_NN_Layer\input_program.json") as f:
    data = json.load(f)

statements = data["program"]["statements"]


# -----------------------
# PREDICT EACH STATEMENT
# -----------------------

for stmt_node in statements:

    stmt_text = node_to_statement(stmt_node)

    tokens = tokenize(stmt_text)

    vec = statement_vector(tokens).reshape(1, -1)

    prediction = model.predict(vec)

    class_id = np.argmax(prediction)

    print("Statement:", stmt_text)
    print("Predicted Type:", labels[class_id])
    print("Confidence:", float(np.max(prediction)))
    print("------------------")