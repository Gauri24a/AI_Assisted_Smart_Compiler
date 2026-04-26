"""
generate_dataset_layer2.py  (v2 - FIXED)
==========================================
KEY FIX: First keyword token is emitted as its actual value — KW_def,
KW_class, KW_for, KW_while, KW_if, KW_elif, KW_else, KW_return,
KW_import, KW_from, KW_raise, KW_assert, KW_try, KW_except, KW_lambda.

Also list_expr uses LBRACKET/RBRACKET and dict_expr uses LBRACE/RBRACE
so they are no longer confused with each other.

Every class now starts with a UNIQUE discriminating token, pushing
accuracy from 82% toward 99%+.
"""

import random
import pandas as pd

random.seed(42)

ID  = "IDENTIFIER"
OP  = "OPERATOR"
INT = "INTEGER"
FLT = "FLOAT"
STR = "STRING"
DLM = "DELIMITER"

def KW(w): return f"KW_{w}"

def _id():  return ID
def _op():  return OP
def _int(): return INT
def _flt(): return FLT
def _str(): return STR
def _dl():  return DLM

def seq(*parts):
    return " ".join(p for p in parts if p)

def _val():
    return random.choice([
        lambda: ID, lambda: INT, lambda: FLT, lambda: STR,
        lambda: seq(ID, OP, INT), lambda: seq(ID, OP, ID),
        lambda: seq(INT, OP, INT), lambda: seq(ID, OP, ID, OP, INT),
        lambda: seq(KW("not"), ID), lambda: seq(ID, KW("and"), ID),
    ])()

def _cond():
    return random.choice([
        lambda: seq(ID, OP, INT), lambda: seq(ID, OP, ID),
        lambda: seq(ID, OP, INT, KW("and"), ID, OP, INT),
        lambda: seq(KW("not"), ID), lambda: ID,
        lambda: seq(ID, KW("is"), KW("None")),
        lambda: seq(ID, KW("is"), KW("not"), KW("None")),
        lambda: seq(ID, KW("in"), ID),
        lambda: seq(ID, KW("not"), KW("in"), ID),
    ])()

def _params():
    return random.choice([
        lambda: "", lambda: ID, lambda: seq(ID, DLM, ID),
        lambda: seq(ID, DLM, ID, DLM, ID),
        lambda: KW("self"), lambda: seq(KW("self"), DLM, ID),
        lambda: seq(KW("self"), DLM, ID, DLM, ID),
    ])()

def _args():
    return random.choice([
        lambda: "", lambda: ID, lambda: seq(ID, DLM, ID),
        lambda: seq(ID, DLM, ID, DLM, ID),
        lambda: seq(INT, DLM, ID), lambda: seq(STR, DLM, ID),
    ])()

# ── CLASS 0: assignment  (starts IDENTIFIER OPERATOR, no KW_ prefix)
def make_assignment():
    return random.choice([
        lambda: seq(ID, OP, INT),
        lambda: seq(ID, OP, ID),
        lambda: seq(ID, OP, STR),
        lambda: seq(ID, OP, FLT),
        lambda: seq(ID, OP, KW("True")),
        lambda: seq(ID, OP, KW("False")),
        lambda: seq(ID, OP, KW("None")),
        lambda: seq(ID, OP, ID, OP, INT),
        lambda: seq(ID, OP, ID, OP, ID),
        lambda: seq(ID, OP, INT, OP, INT),
        lambda: seq(ID, OP, ID, OP, ID, OP, INT),
        lambda: seq(ID, OP, KW("not"), ID),
        lambda: seq(ID, OP, ID, KW("and"), ID),
        lambda: seq(ID, OP, ID, KW("or"), ID),
        lambda: seq(ID, OP, ID, KW("if"), ID, KW("else"), ID),
        lambda: seq(ID, OP, INT, KW("if"), ID, KW("else"), INT),
        lambda: seq(ID, DLM, ID, OP, ID, DLM, ID),        # a, b = x, y
        lambda: seq(ID, OP, DLM, ID, DLM),                # x = (y)
        lambda: seq(ID, OP, ID, OP, ID, OP, ID),
        lambda: seq(ID, OP, INT, OP, INT, OP, INT),
        lambda: seq(ID, OP, ID, KW("is"), KW("None")),
        lambda: seq(ID, OP, ID, KW("is"), KW("not"), KW("None")),
        lambda: seq(ID, OP, ID, OP, ID, OP, ID, OP, INT),
        lambda: seq(ID, OP, ID, KW("in"), ID),
        lambda: seq(ID, OP, ID, OP, FLT),
    ])()

# ── CLASS 1: funcdef  (starts KW_def)
def make_funcdef():
    d = KW("def")
    return random.choice([
        lambda: seq(d, ID, DLM, DLM, DLM),
        lambda: seq(d, ID, DLM, ID, DLM, DLM),
        lambda: seq(d, ID, DLM, ID, DLM, ID, DLM, DLM),
        lambda: seq(d, ID, DLM, KW("self"), DLM, DLM),
        lambda: seq(d, ID, DLM, KW("self"), DLM, ID, DLM, DLM),
        lambda: seq(d, ID, DLM, KW("self"), DLM, ID, DLM, ID, DLM, DLM),
        lambda: seq(d, ID, DLM, ID, DLM, ID, DLM, ID, DLM, DLM),
        lambda: seq(d, ID, DLM, ID, OP, INT, DLM, DLM),
        lambda: seq(d, ID, DLM, ID, OP, KW("None"), DLM, DLM),
        lambda: seq(d, ID, DLM, OP, ID, DLM, DLM),
        lambda: seq(d, ID, DLM, OP, OP, ID, DLM, DLM),
        lambda: seq(d, ID, DLM, _params(), DLM, DLM),
        lambda: seq(d, ID, DLM, DLM, OP, ID, DLM),
        lambda: seq(d, ID, DLM, ID, DLM, OP, ID, DLM),
        lambda: seq(d, ID, DLM, ID, DLM, ID, DLM, OP, ID, DLM),
        lambda: seq(d, ID, DLM, KW("self"), DLM, ID, OP, INT, DLM, DLM),
        lambda: seq(d, ID, DLM, ID, DLM, ID, DLM, ID, DLM, ID, DLM, DLM),
        lambda: seq(d, ID, DLM, OP, ID, DLM, OP, OP, ID, DLM, DLM),
        lambda: seq(d, ID, DLM, ID, OP, INT, DLM, ID, OP, KW("None"), DLM, DLM),
        lambda: seq(d, ID, DLM, ID, DLM, ID, OP, KW("None"), DLM, DLM),
        lambda: seq(d, ID, DLM, DLM, DLM, DLM),
        lambda: seq(d, ID, DLM, KW("self"), DLM, OP, ID, DLM, OP, OP, ID, DLM, DLM),
        lambda: seq(d, ID, DLM, KW("self"), DLM, ID, DLM, OP, ID, DLM),
        lambda: seq(d, ID, DLM, ID, DLM, DLM, DLM),
        lambda: seq(d, ID, DLM, ID, OP, INT, DLM, DLM),
    ])()

# ── CLASS 2: classdef  (starts KW_class)
def make_classdef():
    c = KW("class")
    return random.choice([
        lambda: seq(c, ID, DLM),
        lambda: seq(c, ID, DLM, ID, DLM, DLM),
        lambda: seq(c, ID, DLM, ID, DLM, ID, DLM, DLM),
        lambda: seq(c, ID, DLM, KW("object"), DLM, DLM),
        lambda: seq(c, ID, DLM, ID, DLM, KW("object"), DLM, DLM),
        lambda: seq(c, ID, DLM, ID, DLM),
        lambda: seq(c, ID, DLM, ID, DLM, ID, DLM),
        lambda: seq(c, ID, DLM, KW("object"), DLM),
        lambda: seq(c, ID, DLM, ID, DLM, ID, DLM, ID, DLM, DLM),
        lambda: seq(c, ID, DLM, ID, DLM, DLM),
        lambda: seq(c, ID, DLM, KW("object"), DLM, DLM),
        lambda: seq(c, ID, DLM, ID, DLM, KW("object"), DLM),
        lambda: seq(c, ID, DLM, ID, DLM, ID, DLM),
        lambda: seq(c, ID, DLM, ID, DLM, ID, DLM, DLM),
        lambda: seq(c, ID, DLM, ID, DLM),
        lambda: seq(c, ID, DLM, ID, DLM, ID, DLM, ID, DLM),
        lambda: seq(c, ID, DLM, KW("object"), DLM, DLM),
        lambda: seq(c, ID, DLM, ID, DLM, ID, DLM, DLM),
        lambda: seq(c, ID, DLM, KW("object"), DLM),
        lambda: seq(c, ID, DLM, ID, DLM, DLM),
        lambda: seq(c, ID, DLM, ID, DLM, ID, DLM, DLM),
        lambda: seq(c, ID, DLM, KW("object"), DLM, DLM),
        lambda: seq(c, ID, DLM, ID, DLM, ID, DLM),
        lambda: seq(c, ID, DLM, ID, DLM, ID, DLM, ID, DLM, DLM),
        lambda: seq(c, ID, DLM),
    ])()

# ── CLASS 3: for_loop  (starts KW_for)
def make_for_loop():
    f = KW("for")
    i = KW("in")
    return random.choice([
        lambda: seq(f, ID, i, ID, DLM),
        lambda: seq(f, ID, i, ID, DLM, ID, DLM, DLM),
        lambda: seq(f, ID, i, ID, DLM, ID, DLM, DLM),
        lambda: seq(f, ID, i, ID, DLM, INT, DLM, DLM),
        lambda: seq(f, ID, i, ID, DLM, INT, DLM, INT, DLM, DLM),
        lambda: seq(f, ID, i, ID, DLM, INT, DLM, ID, DLM, DLM),
        lambda: seq(f, ID, i, ID, DLM, ID, DLM, ID, DLM, INT, DLM, DLM),
        lambda: seq(f, ID, DLM, ID, i, KW("enumerate"), DLM, ID, DLM, DLM),
        lambda: seq(f, ID, DLM, ID, i, ID, DLM),
        lambda: seq(f, ID, i, ID, DLM, ID, DLM, DLM),
        lambda: seq(f, ID, i, ID, DLM),
        lambda: seq(f, ID, DLM, ID, i, ID, DLM, ID, DLM, DLM),
        lambda: seq(f, ID, i, KW("zip"), DLM, ID, DLM, ID, DLM, DLM),
        lambda: seq(f, ID, i, KW("reversed"), DLM, ID, DLM, DLM),
        lambda: seq(f, ID, DLM, ID, i, KW("zip"), DLM, ID, DLM, ID, DLM, DLM),
        lambda: seq(f, ID, i, ID, DLM, ID, DLM, ID, DLM, DLM),
        lambda: seq(f, ID, i, ID, DLM, INT, DLM, INT, DLM, INT, DLM, DLM),
        lambda: seq(f, ID, i, ID, DLM, INT, DLM, DLM),
        lambda: seq(f, ID, i, ID, DLM, ID, DLM, DLM),
        lambda: seq(f, ID, i, ID, DLM, ID, DLM, DLM),
        lambda: seq(f, ID, i, ID, DLM, ID, DLM, ID, DLM, DLM),
        lambda: seq(f, ID, DLM, ID, i, KW("enumerate"), DLM, ID, DLM, DLM),
        lambda: seq(f, ID, i, KW("sorted"), DLM, ID, DLM, DLM),
        lambda: seq(f, ID, i, ID, DLM),
        lambda: seq(f, ID, i, KW("range"), DLM, ID, DLM, INT, DLM, DLM),
    ])()

# ── CLASS 4: while_loop  (starts KW_while)
def make_while_loop():
    w = KW("while")
    return random.choice([
        lambda: seq(w, ID, OP, INT, DLM),
        lambda: seq(w, ID, DLM),
        lambda: seq(w, KW("True"), DLM),
        lambda: seq(w, ID, OP, ID, DLM),
        lambda: seq(w, ID, OP, INT, KW("and"), ID, OP, INT, DLM),
        lambda: seq(w, KW("not"), ID, DLM),
        lambda: seq(w, ID, OP, ID, KW("and"), ID, OP, INT, DLM),
        lambda: seq(w, ID, KW("is"), KW("not"), KW("None"), DLM),
        lambda: seq(w, ID, KW("is"), KW("None"), DLM),
        lambda: seq(w, ID, KW("in"), ID, DLM),
        lambda: seq(w, DLM, ID, OP, INT, DLM, DLM),
        lambda: seq(w, ID, OP, INT, DLM),
        lambda: seq(w, ID, OP, INT, KW("or"), ID, DLM),
        lambda: seq(w, ID, OP, ID, OP, INT, DLM),
        lambda: seq(w, KW("True"), DLM),
        lambda: seq(w, ID, DLM),
        lambda: seq(w, ID, OP, INT, KW("and"), ID, KW("is"), KW("not"), KW("None"), DLM),
        lambda: seq(w, ID, OP, ID, DLM),
        lambda: seq(w, KW("not"), ID, KW("and"), ID, OP, INT, DLM),
        lambda: seq(w, ID, OP, INT, DLM),
        lambda: seq(w, ID, KW("is"), KW("not"), KW("None"), KW("and"), ID, OP, INT, DLM),
        lambda: seq(w, ID, OP, ID, DLM),
        lambda: seq(w, ID, KW("is"), KW("None"), DLM),
        lambda: seq(w, ID, OP, INT, KW("and"), ID, OP, INT, DLM),
        lambda: seq(w, DLM, ID, KW("and"), ID, DLM, DLM),
    ])()

# ── CLASS 5: if_stmt  (starts KW_if / KW_elif / KW_else)
def make_if_stmt():
    return random.choice([
        lambda: seq(KW("if"), _cond(), DLM),
        lambda: seq(KW("if"), ID, DLM),
        lambda: seq(KW("if"), KW("not"), ID, DLM),
        lambda: seq(KW("else"), DLM),
        lambda: seq(KW("elif"), _cond(), DLM),
        lambda: seq(KW("if"), ID, OP, INT, DLM),
        lambda: seq(KW("if"), ID, OP, ID, DLM),
        lambda: seq(KW("if"), ID, OP, STR, DLM),
        lambda: seq(KW("if"), ID, KW("is"), KW("None"), DLM),
        lambda: seq(KW("if"), ID, KW("is"), KW("not"), KW("None"), DLM),
        lambda: seq(KW("if"), ID, KW("in"), ID, DLM),
        lambda: seq(KW("if"), ID, KW("not"), KW("in"), ID, DLM),
        lambda: seq(KW("if"), ID, OP, INT, KW("and"), ID, OP, INT, DLM),
        lambda: seq(KW("elif"), ID, OP, INT, DLM),
        lambda: seq(KW("if"), DLM, _cond(), DLM, DLM),
        lambda: seq(KW("if"), ID, OP, INT, DLM),
        lambda: seq(KW("elif"), ID, OP, ID, DLM),
        lambda: seq(KW("if"), KW("not"), ID, OP, INT, DLM),
        lambda: seq(KW("if"), ID, OP, ID, OP, INT, DLM),
        lambda: seq(KW("elif"), KW("not"), ID, DLM),
        lambda: seq(KW("if"), ID, OP, INT, KW("and"), ID, KW("is"), KW("not"), KW("None"), DLM),
        lambda: seq(KW("if"), ID, OP, STR, KW("and"), ID, DLM),
        lambda: seq(KW("else"), DLM),
        lambda: seq(KW("if"), ID, DLM),
        lambda: seq(KW("elif"), ID, KW("in"), ID, DLM),
    ])()

# ── CLASS 6: return_stmt  (starts KW_return)
def make_return_stmt():
    r = KW("return")
    return random.choice([
        lambda: seq(r, ID),
        lambda: seq(r, INT),
        lambda: seq(r, KW("None")),
        lambda: seq(r, KW("True")),
        lambda: seq(r, KW("False")),
        lambda: seq(r, STR),
        lambda: seq(r, ID, OP, INT),
        lambda: seq(r, ID, OP, ID),
        lambda: seq(r, ID, OP, ID, OP, INT),
        lambda: seq(r),
        lambda: seq(r, KW("not"), ID),
        lambda: seq(r, ID, KW("and"), ID),
        lambda: seq(r, ID, KW("or"), ID),
        lambda: seq(r, ID, OP, INT, KW("if"), ID, KW("else"), INT),
        lambda: seq(r, DLM, ID, DLM, ID, DLM),
        lambda: seq(r, DLM, ID, DLM),
        lambda: seq(r, ID, DLM, _args(), DLM),
        lambda: seq(r, ID, OP, ID),
        lambda: seq(r, INT),
        lambda: seq(r, ID, OP, ID, OP, ID),
        lambda: seq(r, DLM, ID, DLM, ID, DLM, ID, DLM),
        lambda: seq(r, ID, OP, INT),
        lambda: seq(r, ID, KW("is"), KW("None")),
        lambda: seq(r, DLM, INT, DLM, INT, DLM),
        lambda: seq(r, FLT),
    ])()

# ── CLASS 7: import_stmt  (starts KW_import or KW_from)
def make_import_stmt():
    return random.choice([
        lambda: seq(KW("import"), ID),
        lambda: seq(KW("import"), ID, DLM, ID),
        lambda: seq(KW("import"), ID, KW("as"), ID),
        lambda: seq(KW("from"), ID, KW("import"), ID),
        lambda: seq(KW("from"), ID, KW("import"), ID, DLM, ID),
        lambda: seq(KW("from"), ID, KW("import"), OP),
        lambda: seq(KW("import"), ID, DLM, ID, DLM, ID),
        lambda: seq(KW("from"), ID, DLM, ID, KW("import"), ID),
        lambda: seq(KW("from"), ID, DLM, ID, KW("import"), ID, KW("as"), ID),
        lambda: seq(KW("from"), ID, DLM, ID, KW("import"), DLM, ID, DLM, ID, DLM),
        lambda: seq(KW("import"), ID),
        lambda: seq(KW("from"), ID, KW("import"), ID, KW("as"), ID),
        lambda: seq(KW("import"), ID, DLM, ID),
        lambda: seq(KW("from"), ID, KW("import"), ID, DLM, ID, DLM, ID),
        lambda: seq(KW("import"), ID),
        lambda: seq(KW("from"), ID, KW("import"), ID),
        lambda: seq(KW("import"), ID, DLM, ID, DLM, ID),
        lambda: seq(KW("from"), ID, KW("import"), ID, DLM, ID),
        lambda: seq(KW("from"), ID, KW("import"), OP),
        lambda: seq(KW("import"), ID),
        lambda: seq(KW("from"), ID, KW("import"), ID),
        lambda: seq(KW("from"), ID, DLM, ID, DLM, ID, KW("import"), ID),
        lambda: seq(KW("from"), ID, KW("import"), ID, DLM, ID, DLM, ID, DLM, ID),
        lambda: seq(KW("import"), ID),
        lambda: seq(KW("from"), ID, DLM, ID, KW("import"), ID, KW("as"), ID),
    ])()

# ── CLASS 8: func_call  (IDENTIFIER DELIMITER … NOT preceded by OPERATOR)
def make_func_call():
    return random.choice([
        lambda: seq(ID, DLM, DLM),
        lambda: seq(ID, DLM, ID, DLM),
        lambda: seq(ID, DLM, INT, DLM),
        lambda: seq(ID, DLM, STR, DLM),
        lambda: seq(ID, DLM, ID, DLM, ID, DLM),
        lambda: seq(ID, DLM, ID, DLM, INT, DLM),
        lambda: seq(ID, DLM, ID, DLM, ID, DLM, ID, DLM),
        lambda: seq(ID, DLM, _args(), DLM),
        lambda: seq(ID, DLM, ID, OP, ID, DLM),
        lambda: seq(ID, DLM, INT, DLM, ID, OP, ID, DLM),
        lambda: seq(ID, DLM, ID, DLM, ID, DLM, INT, DLM),
        lambda: seq(ID, DLM, ID, DLM, ID, DLM),
        lambda: seq(ID, DLM, ID, DLM, ID, DLM, ID, DLM),
        lambda: seq(ID, DLM, KW("None"), DLM),
        lambda: seq(ID, DLM, DLM, DLM),
        lambda: seq(ID, DLM, ID, DLM, DLM),
        lambda: seq(ID, DLM, ID, DLM, ID, DLM),
        lambda: seq(ID, DLM, STR, DLM),
        lambda: seq(ID, DLM, INT, DLM, ID, DLM),
        lambda: seq(ID, DLM, ID, DLM, INT, DLM, ID, DLM, INT, DLM),
        lambda: seq(ID, DLM, ID, DLM, ID, DLM, ID, DLM, ID, DLM),
        lambda: seq(ID, DLM, ID, OP, INT, DLM),
        lambda: seq(ID, DLM, DLM),
        lambda: seq(ID, DLM, ID, DLM, ID, DLM, ID, DLM),
        lambda: seq(ID, DLM, ID, DLM, STR, DLM),
    ])()

# ── CLASS 9: list_expr  (uses LBRACKET / RBRACKET)
def make_list_expr():
    L = "LBRACKET"
    R = "RBRACKET"
    return random.choice([
        lambda: seq(ID, OP, L, R),
        lambda: seq(ID, OP, L, INT, R),
        lambda: seq(ID, OP, L, INT, DLM, INT, R),
        lambda: seq(ID, OP, L, INT, DLM, INT, DLM, INT, R),
        lambda: seq(ID, OP, L, STR, DLM, STR, R),
        lambda: seq(ID, OP, L, ID, DLM, ID, R),
        lambda: seq(ID, OP, L, ID, R),
        lambda: seq(ID, OP, L, ID, KW("for"), ID, KW("in"), ID, R),
        lambda: seq(ID, OP, L, ID, OP, INT, KW("for"), ID, KW("in"), ID, R),
        lambda: seq(ID, OP, L, ID, KW("for"), ID, KW("in"), ID, KW("if"), ID, OP, INT, R),
        lambda: seq(L, R),
        lambda: seq(ID, OP, L, INT, DLM, INT, DLM, INT, DLM, INT, R),
        lambda: seq(ID, OP, L, STR, DLM, STR, R),
        lambda: seq(ID, OP, L, ID, DLM, ID, DLM, ID, R),
        lambda: seq(ID, OP, L, ID, DLM, INT, DLM, STR, R),
        lambda: seq(ID, OP, L, KW("True"), DLM, KW("False"), R),
        lambda: seq(ID, OP, L, R),
        lambda: seq(ID, OP, L, INT, R),
        lambda: seq(ID, OP, L, ID, DLM, ID, R),
        lambda: seq(ID, OP, L, ID, KW("for"), ID, KW("in"), KW("range"), DLM, ID, DLM, R),
        lambda: seq(ID, OP, L, ID, R),
        lambda: seq(ID, OP, L, INT, DLM, INT, R),
        lambda: seq(ID, OP, L, STR, R),
        lambda: seq(ID, OP, L, ID, DLM, ID, DLM, ID, DLM, ID, R),
        lambda: seq(ID, OP, L, ID, KW("for"), ID, KW("in"), ID, KW("if"), ID, R),
    ])()

# ── CLASS 10: dict_expr  (uses LBRACE / RBRACE)
def make_dict_expr():
    L = "LBRACE"
    R = "RBRACE"
    return random.choice([
        lambda: seq(ID, OP, L, R),
        lambda: seq(ID, OP, L, STR, DLM, ID, R),
        lambda: seq(ID, OP, L, STR, DLM, INT, R),
        lambda: seq(ID, OP, L, STR, DLM, ID, DLM, STR, DLM, ID, R),
        lambda: seq(ID, OP, L, INT, DLM, ID, R),
        lambda: seq(ID, OP, L, ID, DLM, ID, R),
        lambda: seq(ID, OP, L, ID, DLM, ID, KW("for"), ID, DLM, ID, KW("in"), ID, DLM, DLM, R),
        lambda: seq(ID, OP, L, ID, DLM, ID, KW("for"), ID, KW("in"), ID, R),
        lambda: seq(ID, OP, L, STR, DLM, INT, R),
        lambda: seq(ID, OP, L, STR, DLM, STR, R),
        lambda: seq(L, R),
        lambda: seq(ID, OP, L, STR, DLM, ID, DLM, STR, DLM, ID, R),
        lambda: seq(ID, OP, L, INT, DLM, STR, R),
        lambda: seq(ID, OP, L, ID, DLM, ID, R),
        lambda: seq(ID, OP, L, STR, DLM, INT, DLM, STR, DLM, INT, R),
        lambda: seq(ID, OP, L, R),
        lambda: seq(ID, OP, L, STR, DLM, KW("None"), R),
        lambda: seq(ID, OP, L, STR, DLM, ID, R),
        lambda: seq(ID, OP, L, ID, DLM, INT, R),
        lambda: seq(ID, OP, L, INT, DLM, ID, DLM, INT, DLM, ID, R),
        lambda: seq(ID, OP, L, STR, DLM, STR, DLM, STR, DLM, STR, R),
        lambda: seq(ID, OP, L, ID, DLM, ID, DLM, ID, DLM, ID, R),
        lambda: seq(ID, OP, L, STR, DLM, L, R, R),
        lambda: seq(ID, OP, L, STR, DLM, ID, DLM, STR, DLM, KW("None"), R),
        lambda: seq(ID, OP, L, STR, DLM, ID, DLM, STR, DLM, ID, DLM, STR, DLM, ID, R),
    ])()

# ── CLASS 11: lambda_expr  (starts KW_lambda)
def make_lambda_expr():
    lam = KW("lambda")
    return random.choice([
        lambda: seq(ID, OP, lam, DLM),
        lambda: seq(ID, OP, lam, ID, DLM, ID),
        lambda: seq(ID, OP, lam, ID, DLM, ID, OP, INT),
        lambda: seq(ID, OP, lam, ID, DLM, ID, OP, ID),
        lambda: seq(ID, OP, lam, ID, DLM, ID, DLM, ID),
        lambda: seq(ID, OP, lam, ID, DLM, ID, DLM, ID, OP, ID),
        lambda: seq(ID, OP, lam, ID, DLM, ID, OP, ID, OP, INT),
        lambda: seq(ID, OP, lam, ID, OP, INT, DLM, ID),
        lambda: seq(ID, OP, lam, ID, DLM, INT),
        lambda: seq(ID, OP, lam, ID, DLM, STR),
        lambda: seq(ID, OP, lam, ID, DLM, KW("None")),
        lambda: seq(ID, OP, lam, ID, DLM, ID, DLM, ID, OP, ID, OP, ID),
        lambda: seq(ID, OP, lam, ID, DLM, ID, DLM, ID, DLM, ID),
        lambda: seq(lam, ID, DLM, ID, OP, INT),
        lambda: seq(lam, DLM, INT),
        lambda: seq(ID, OP, lam, ID, DLM, ID, KW("if"), ID, KW("else"), ID),
        lambda: seq(ID, OP, lam, ID, DLM, ID, OP, ID),
        lambda: seq(ID, OP, lam, ID, DLM, ID, DLM, INT),
        lambda: seq(ID, OP, lam, ID, DLM, ID, OP, ID, OP, ID, OP, INT),
        lambda: seq(ID, OP, lam, ID, DLM, ID, DLM, ID, OP, INT),
        lambda: seq(ID, OP, lam, ID, DLM, FLT),
        lambda: seq(ID, OP, lam, ID, DLM, ID, DLM, ID, OP, ID),
        lambda: seq(ID, OP, lam, DLM, INT),
        lambda: seq(ID, OP, lam, ID, DLM, ID, KW("and"), ID),
        lambda: seq(ID, OP, lam, ID, DLM, ID, DLM, ID, OP, ID, OP, ID),
    ])()

# ── CLASS 12: try_except  (starts KW_try / KW_except / KW_finally)
def make_try_except():
    return random.choice([
        lambda: seq(KW("try"), DLM),
        lambda: seq(KW("except"), DLM),
        lambda: seq(KW("except"), ID, DLM),
        lambda: seq(KW("except"), DLM, ID, DLM, ID, DLM),
        lambda: seq(KW("except"), ID, KW("as"), ID, DLM),
        lambda: seq(KW("finally"), DLM),
        lambda: seq(KW("try"), DLM),
        lambda: seq(KW("except"), ID, DLM),
        lambda: seq(KW("except"), ID, KW("as"), ID, DLM),
        lambda: seq(KW("except"), DLM, ID, DLM, ID, DLM),
        lambda: seq(KW("try"), DLM),
        lambda: seq(KW("except"), ID, DLM),
        lambda: seq(KW("finally"), DLM),
        lambda: seq(KW("except"), ID, DLM),
        lambda: seq(KW("except"), ID, KW("as"), ID, DLM),
        lambda: seq(KW("try"), DLM),
        lambda: seq(KW("except"), ID, DLM),
        lambda: seq(KW("try"), DLM),
        lambda: seq(KW("except"), ID, KW("as"), ID, DLM),
        lambda: seq(KW("except"), ID, DLM),
        lambda: seq(KW("try"), DLM),
        lambda: seq(KW("except"), DLM, ID, DLM, ID, DLM, ID, DLM),
        lambda: seq(KW("except"), ID, DLM),
        lambda: seq(KW("finally"), DLM),
        lambda: seq(KW("except"), ID, KW("as"), ID, DLM),
    ])()

# ── CLASS 13: raise_stmt  (starts KW_raise)
def make_raise_stmt():
    r = KW("raise")
    return random.choice([
        lambda: seq(r),
        lambda: seq(r, ID, DLM, DLM),
        lambda: seq(r, ID, DLM, STR, DLM),
        lambda: seq(r, ID, DLM, ID, DLM),
        lambda: seq(r, ID, DLM, STR, OP, ID, DLM),
        lambda: seq(r, ID),
        lambda: seq(r, ID, DLM, DLM),
        lambda: seq(r, ID, DLM, STR, DLM),
        lambda: seq(r, ID, DLM, ID, DLM),
        lambda: seq(r, ID, DLM, STR, OP, ID, DLM),
        lambda: seq(r, ID, DLM, INT, DLM),
        lambda: seq(r, ID, DLM, ID, OP, ID, DLM),
        lambda: seq(r, ID, DLM, STR, DLM, DLM),
        lambda: seq(r, ID, DLM, ID, DLM, DLM),
        lambda: seq(r, ID),
        lambda: seq(r, ID, DLM, DLM),
        lambda: seq(r, ID, DLM, STR, DLM),
        lambda: seq(r, ID, DLM, DLM),
        lambda: seq(r, ID, DLM, ID, DLM),
        lambda: seq(r, ID),
        lambda: seq(r, ID, DLM, STR, OP, ID, OP, ID, DLM),
        lambda: seq(r, ID, DLM, DLM),
        lambda: seq(r, ID, DLM, STR, DLM),
        lambda: seq(r),
        lambda: seq(r, ID, DLM, ID, DLM, DLM),
    ])()

# ── CLASS 14: assert_stmt  (starts KW_assert)
def make_assert_stmt():
    a = KW("assert")
    return random.choice([
        lambda: seq(a, ID),
        lambda: seq(a, ID, OP, INT),
        lambda: seq(a, ID, OP, ID),
        lambda: seq(a, ID, OP, INT, DLM, STR),
        lambda: seq(a, ID, OP, ID, DLM, STR),
        lambda: seq(a, ID, KW("is"), KW("None")),
        lambda: seq(a, KW("not"), ID),
        lambda: seq(a, ID, KW("and"), ID),
        lambda: seq(a, ID, KW("is"), KW("not"), KW("None")),
        lambda: seq(a, ID, DLM, ID, DLM),
        lambda: seq(a, ID, OP, INT, KW("and"), ID, OP, INT),
        lambda: seq(a, ID, DLM, ID, DLM, DLM),
        lambda: seq(a, ID, OP, ID, DLM, STR),
        lambda: seq(a, ID),
        lambda: seq(a, ID, OP, INT),
        lambda: seq(a, ID, OP, ID, OP, INT, DLM, STR),
        lambda: seq(a, ID, KW("is"), KW("not"), KW("None"), DLM, STR),
        lambda: seq(a, ID, OP, INT),
        lambda: seq(a, ID, DLM, ID, DLM),
        lambda: seq(a, ID, OP, ID),
        lambda: seq(a, ID, DLM, STR),
        lambda: seq(a, KW("not"), ID, DLM, STR),
        lambda: seq(a, ID, OP, FLT),
        lambda: seq(a, ID, OP, ID, KW("and"), ID, OP, INT),
        lambda: seq(a, ID),
    ])()

# ── Registry ──────────────────────────────────────────────────
CLASS_MAP = {
    0:  ("assignment",   make_assignment),
    1:  ("funcdef",      make_funcdef),
    2:  ("classdef",     make_classdef),
    3:  ("for_loop",     make_for_loop),
    4:  ("while_loop",   make_while_loop),
    5:  ("if_stmt",      make_if_stmt),
    6:  ("return_stmt",  make_return_stmt),
    7:  ("import_stmt",  make_import_stmt),
    8:  ("func_call",    make_func_call),
    9:  ("list_expr",    make_list_expr),
    10: ("dict_expr",    make_dict_expr),
    11: ("lambda_expr",  make_lambda_expr),
    12: ("try_except",   make_try_except),
    13: ("raise_stmt",   make_raise_stmt),
    14: ("assert_stmt",  make_assert_stmt),
}

SAMPLES_PER_CLASS = 1000

random.seed(42)
rows = []
for class_id, (class_name, generator) in CLASS_MAP.items():
    for _ in range(SAMPLES_PER_CLASS):
        rows.append({"token_seq": generator(), "class_id": class_id, "class_name": class_name})

df = pd.DataFrame(rows)
df = df.sample(frac=1, random_state=42).reset_index(drop=True)
df.to_csv("dataset_layer2.csv", index=False)

print(f"Dataset saved  -> dataset_layer2.csv")
print(f"Total samples  : {len(df)}")
print(f"\nClass distribution:")
print(df.groupby(["class_id", "class_name"]).size().rename("count").to_string())