import pandas as pd
import numpy as np
import re
from gensim.models import Word2Vec
from tensorflow.keras.models import Sequential
from tensorflow.keras.layers import Dense
from tensorflow.keras.utils import to_categorical
import pickle

# -----------------------
# LOAD DATASET
# -----------------------

import pickle
import os

# -----------------------
# LOAD DATASET
# -----------------------

# Get the directory of the current script to locate the dataset
script_dir = os.path.dirname(os.path.abspath(__file__))
dataset_path = os.path.join(script_dir, "compiler_statement_dataset.csv")

df = pd.read_csv(dataset_path)

# -----------------------
# TOKENIZER
# -----------------------

def tokenize(statement):
    return re.findall(r'[A-Za-z_]+|\d+|[=+\-*/<>;(){}]', statement)

df["tokens"] = df["Statement"].apply(tokenize)

sentences = df["tokens"].tolist()

# -----------------------
# TRAIN WORD2VEC
# -----------------------

w2v_model = Word2Vec(
    sentences,
    vector_size=20,
    window=3,
    min_count=1,
    workers=1
)

w2v_model.save("word2vec.model")

# -----------------------
# STATEMENT → VECTOR
# -----------------------

def statement_vector(tokens):
    vectors = []
    for token in tokens:
        if token in w2v_model.wv:
            vectors.append(w2v_model.wv[token])
    if len(vectors) == 0:
        return np.zeros(w2v_model.vector_size)
    return np.mean(vectors, axis=0)

X = np.array([statement_vector(t) for t in sentences])
y = df["Class"].values

y = to_categorical(y)

# -----------------------
# BUILD NN MODEL
# -----------------------

model = Sequential([
    Dense(32, activation="relu", input_shape=(20,)),
    Dense(16, activation="relu"),
    Dense(4, activation="softmax")
])

model.compile(
    optimizer="adam",
    loss="categorical_crossentropy",
    metrics=["accuracy"]
)

# -----------------------
# TRAIN
# -----------------------

model.fit(X, y, epochs=150, batch_size=16)

# -----------------------
# SAVE MODEL
# -----------------------

model.save("statement_classifier.h5")

print("Model training complete.")