import random
import pandas as pd

# identifiers
VAR = ["x", "y", "count", "total", "sum", "index", "value", "i", "j"]

# operators
OPS = ["+", "-", "*", "/"]

# types
TYPES = ["int", "float", "double"]

# function names
FUNC = ["abs", "sqrt", "log"]

# ------------------------------
# TEMPLATES
# ------------------------------

assignment_templates = [
    "{v} = {n};",
    "{v} = {v} {op} {n};",
    "{v} = {v} {op} {v};",
    "{v} = {f}({v});"
]

declaration_templates = [
    "{t} {v};",
    "{t} {v} = {n};",
    "{t} {v} = {v} {op} {n};"
]

loop_templates = [
    "for(int {v}=0; {v}<{n}; {v}++) {{ }}",
    "for({v}=0; {v}<{n}; {v}++) {{ }}",
    "while({v} < {n}) {{ }}"
]

conditional_templates = [
    "if({v} > {n}) {{ }}",
    "if({v} == {v}) {{ }}",
    "if({v} < {n}) {{ }}"
]

# ------------------------------
# STATEMENT GENERATOR
# ------------------------------

def generate_statement(template):
    return template.format(
        v=random.choice(VAR),
        n=random.randint(0,100),
        op=random.choice(OPS),
        f=random.choice(FUNC),
        t=random.choice(TYPES)
    )

data = []

# assignment class = 0
for _ in range(300):
    stmt = generate_statement(random.choice(assignment_templates))
    data.append([stmt, 0])

# loop class = 1
for _ in range(300):
    stmt = generate_statement(random.choice(loop_templates))
    data.append([stmt, 1])

# conditional class = 2
for _ in range(300):
    stmt = generate_statement(random.choice(conditional_templates))
    data.append([stmt, 2])

# declaration class = 3
for _ in range(300):
    stmt = generate_statement(random.choice(declaration_templates))
    data.append([stmt, 3])

# ------------------------------
# DATAFRAME
# ------------------------------

df = pd.DataFrame(data, columns=["Statement", "Class"])

print(df.head())

df.to_csv("compiler_statement_dataset.csv", index=False)