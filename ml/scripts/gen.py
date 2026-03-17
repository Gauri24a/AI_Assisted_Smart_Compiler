"""
generate_dataset.py  v2
========================
STRICT TEMPLATE SEPARATION — every class has syntactically unique templates.

Key rules applied:
  - Pointer Operation : MUST contain at least one of  * & ->
  - Increment/Decrement: ONLY ++ / -- / <<= / >>=  (no +=/-= which bleed into Assignment)
  - Assignment        : plain  =  or  op=  (NO pointer symbols, NO ++ / --)
  - Bitwise           : MUST contain & | ^ ~ << >>  (not += forms)
  - Cast              : MUST contain ( type )  or  _cast<
  - Memory Allocation : MUST contain malloc/calloc/realloc/new/free/delete
  - Exception         : MUST contain throw/try/catch/assert
"""

import random
import pandas as pd

# ── Vocabulary ───────────────────────────────────────────────
VARS   = ["x","y","z","count","total","sum","index","value",
          "i","j","k","n","result","flag","len","size","offset","temp","ret","err","code"]
TYPES  = ["int","float","double","char","long","size_t","uint8_t","uint32_t","int64_t","bool"]
FUNCS  = ["abs","sqrt","log","exp","strlen","printf","scanf","memcpy","memset",
          "fopen","fclose","rand","atoi"]
STRUCTS= ["node","list","tree","obj","ctx","cfg","header","packet","point"]
FIELDS = ["data","next","prev","size","len","head","tail","val","key","left","right","flags"]
ARRAYS = ["arr","data","buf","list","table","matrix","nums","vals","stack","queue"]
EXCEPTS= ["std::runtime_error","std::invalid_argument","std::out_of_range","std::bad_alloc"]
NUMS   = list(range(1, 128))

def v():  return random.choice(VARS)
def t():  return random.choice(TYPES)
def n():  return random.choice(NUMS)
def f():  return random.choice(FUNCS)
def s():  return random.choice(STRUCTS)
def fd(): return random.choice(FIELDS)
def a():  return random.choice(ARRAYS)
def cop():return random.choice([">","<",">=","<=","==","!="])
def lop():return random.choice(["&&","||"])
def exc():return random.choice(EXCEPTS)
def aop():return random.choice(["+","-","*","/","%"])

# ── CLASS 0 : Assignment ─────────────────────────────────────
# Rule: plain = or compound-assign, NO pointer symbols, NO ++/--
def make_assignment():
    return random.choice([
        lambda: f"{v()} = {n()};",
        lambda: f"{v()} = {v()};",
        lambda: f"{v()} = {v()} + {n()};",
        lambda: f"{v()} = {v()} - {n()};",
        lambda: f"{v()} = {v()} * {n()};",
        lambda: f"{v()} = {v()} / {n()};",
        lambda: f"{v()} = {v()} % {n()};",
        lambda: f"{v()} = {v()} + {v()};",
        lambda: f"{v()} = {v()} - {v()};",
        lambda: f"{v()} = {v()} * {v()};",
        lambda: f"{v()} = {f()}({v()});",
        lambda: f"{v()} = {f()}({v()}, {n()});",
        lambda: f"{v()} = {v()} ? {n()} : {n()};",
        lambda: f"{v()} = {v()} ? {v()} : {v()};",
        lambda: f"{v()} = sizeof({t()});",
        lambda: f"{v()} = sizeof({v()});",
        lambda: f"{v()} = NULL;",
        lambda: f"{v()} = 0;",
        lambda: f"{v()} = {v()} + {v()} + {n()};",
        lambda: f"{v()} = {v()} * {v()} - {n()};",
        lambda: f"{v()} = {n()} + {n()};",
        lambda: f"{v()} = {n()} * {n()};",
        lambda: f"{v()} = {f()}({v()}) + {n()};",
        lambda: f"{v()} = {f()}({v()}) - {v()};",
        lambda: f"{v()} = {v()} / {v()};",
    ])()

# ── CLASS 1 : Loop ───────────────────────────────────────────
def make_loop():
    return random.choice([
        lambda: f"for (int {v()} = 0; {v()} < {n()}; {v()}++) {{ }}",
        lambda: f"for (int {v()} = 0; {v()} <= {n()}; {v()}++) {{ }}",
        lambda: f"for (int {v()} = {n()}; {v()} > 0; {v()}--) {{ }}",
        lambda: f"for ({v()} = 0; {v()} < {n()}; {v()}++) {{ }}",
        lambda: f"for ({v()} = 0; {v()} < {v()}; {v()}++) {{ }}",
        lambda: f"for ({v()} = 0; {v()} < {v()}; {v()} += {n()}) {{ }}",
        lambda: f"while ({v()} < {n()}) {{ }}",
        lambda: f"while ({v()} != {n()}) {{ }}",
        lambda: f"while ({v()} > 0) {{ }}",
        lambda: f"while ({v()} {cop()} {v()}) {{ }}",
        lambda: f"while (!{v()}) {{ }}",
        lambda: f"while ({v()}) {{ }}",
        lambda: f"do {{ }} while ({v()} < {n()});",
        lambda: f"do {{ }} while ({v()} {cop()} {n()});",
        lambda: f"do {{ }} while ({v()});",
        lambda: f"for (int {v()} = 0; {v()} < {v()}; ++{v()}) {{ }}",
        lambda: f"for (; {v()} < {n()};) {{ }}",
        lambda: f"for ({t()} {v()} = 0; {v()} < {n()}; {v()}++) {{ }}",
        lambda: f"for (int {v()} = {n()} - 1; {v()} >= 0; {v()}--) {{ }}",
        lambda: f"while ({v()} != NULL) {{ }}",
        lambda: f"while ({v()} {cop()} {n()} && {v()} > 0) {{ }}",
        lambda: f"for (int {v()} = 0; {v()} < {n()}; {v()} += 2) {{ }}",
        lambda: f"for (int {v()} = 1; {v()} < {n()}; {v()} *= 2) {{ }}",
        lambda: f"while (({v()} = {f()}({v()})) > 0) {{ }}",
        lambda: f"do {{ }} while (--{v()} > 0);",
    ])()

# ── CLASS 2 : Conditional ────────────────────────────────────
def make_conditional():
    return random.choice([
        lambda: f"if ({v()} > {n()}) {{ }}",
        lambda: f"if ({v()} < {n()}) {{ }}",
        lambda: f"if ({v()} == {n()}) {{ }}",
        lambda: f"if ({v()} != {n()}) {{ }}",
        lambda: f"if ({v()} >= {n()}) {{ }}",
        lambda: f"if ({v()} <= {n()}) {{ }}",
        lambda: f"if ({v()} == {v()}) {{ }}",
        lambda: f"if ({v()} {cop()} {v()}) {{ }}",
        lambda: f"if ({v()} > {n()} && {v()} < {n()}) {{ }}",
        lambda: f"if ({v()} == {n()} || {v()} == {n()}) {{ }}",
        lambda: f"if (!{v()}) {{ }}",
        lambda: f"if ({v()}) {{ }}",
        lambda: f"if ({v()} == NULL) {{ }}",
        lambda: f"if ({v()} != NULL) {{ }}",
        lambda: f"if ({f()}({v()}) {cop()} {n()}) {{ }}",
        lambda: f"if ({f()}({v()}) > 0) {{ }}",
        lambda: f"switch ({v()}) {{ }}",
        lambda: f"if ({v()} {lop()} {v()}) {{ }}",
        lambda: f"if (({v()} {cop()} {n()}) {lop()} ({v()} {cop()} {n()})) {{ }}",
        lambda: f"if ({v()} == 0) {{ }}",
        lambda: f"if ({v()} != 0) {{ }}",
        lambda: f"if ({v()} > 0 && {v()} < {n()}) {{ }}",
        lambda: f"if ({v()} == {v()} && {v()} != {n()}) {{ }}",
        lambda: f"if (!{v()} || {v()} > {n()}) {{ }}",
        lambda: f"if ({f()}({v()}) == 0) {{ }}",
    ])()

# ── CLASS 3 : Declaration ────────────────────────────────────
def make_declaration():
    return random.choice([
        lambda: f"{t()} {v()};",
        lambda: f"{t()} {v()} = {n()};",
        lambda: f"{t()} {v()} = {v()};",
        lambda: f"{t()} {v()} = {v()} + {n()};",
        lambda: f"{t()} {v()} = {f()}({v()});",
        lambda: f"{t()} {v()} = {f()}({v()}, {n()});",
        lambda: f"{t()} {v()}, {v()};",
        lambda: f"{t()} {v()} = 0, {v()} = {n()};",
        lambda: f"const {t()} {v()} = {n()};",
        lambda: f"static {t()} {v()} = {n()};",
        lambda: f"extern {t()} {v()};",
        lambda: f"volatile {t()} {v()};",
        lambda: f"{t()} {v()}[{n()}];",
        lambda: f"{t()} {v()}[{n()}] = {{0}};",
        lambda: f"struct {s()} {v()};",
        lambda: f"auto {v()} = {n()};",
        lambda: f"auto {v()} = {f()}({v()});",
        lambda: f"{t()} {v()} = {n()} + {n()};",
        lambda: f"{t()} {v()} = {v()} * {n()};",
        lambda: f"const {t()} {v()} = {v()} + {n()};",
        lambda: f"static {t()} {v()};",
        lambda: f"{t()} {v()} = {v()} - {n()};",
        lambda: f"{t()} {v()}[{n()}][{n()}];",
        lambda: f"const {t()} {v()} = {f()}({v()});",
        lambda: f"{t()} {v()} = ({t()}) {n()};",
    ])()

# ── CLASS 4 : Function Call ──────────────────────────────────
def make_function_call():
    return random.choice([
        lambda: f"{f()}({v()});",
        lambda: f"{f()}({v()}, {n()});",
        lambda: f"{f()}({v()}, {v()});",
        lambda: f"{f()}({n()});",
        lambda: f"{f()}({v()}, {v()}, {n()});",
        lambda: f"{f()}(&{v()}, {n()});",
        lambda: f"{f()}({v()}, &{v()});",
        lambda: f"{f()}({v()}, NULL);",
        lambda: f"{f()}(NULL);",
        lambda: f'printf("%d\\n", {v()});',
        lambda: f'printf("%s\\n", {v()});',
        lambda: f'printf("%d %d\\n", {v()}, {v()});',
        lambda: f'scanf("%d", &{v()});',
        lambda: f"memset({v()}, 0, sizeof({v()}));",
        lambda: f"memcpy({v()}, {v()}, {n()});",
        lambda: f"fclose({v()});",
        lambda: f"free({v()});",
        lambda: f"assert({v()} {cop()} {n()});",
        lambda: f"{f()}({f()}({v()}));",
        lambda: f"{f()}({v()}, {f()}({v()}));",
        lambda: f"{s()}_init(&{v()});",
        lambda: f"{s()}_destroy({v()});",
        lambda: f'{f()}({v()}, {v()}, {v()});',
        lambda: f"{f()}();",
        lambda: f'{f()}("{v()}", {n()});',
    ])()

# ── CLASS 5 : Return ─────────────────────────────────────────
def make_return():
    return random.choice([
        lambda: f"return {v()};",
        lambda: f"return {n()};",
        lambda: f"return 0;",
        lambda: f"return -1;",
        lambda: f"return NULL;",
        lambda: f"return {v()} + {n()};",
        lambda: f"return {v()} - {n()};",
        lambda: f"return {v()} * {n()};",
        lambda: f"return {v()} + {v()};",
        lambda: f"return {f()}({v()});",
        lambda: f"return {f()}({v()}, {n()});",
        lambda: f"return {v()} > {n()};",
        lambda: f"return {v()} == {n()};",
        lambda: f"return !{v()};",
        lambda: f"return ({v()} > {n()}) ? {v()} : {n()};",
        lambda: f"return sizeof({t()});",
        lambda: f"return {v()} > 0 && {v()} < {n()};",
        lambda: f"return {v()} != NULL;",
        lambda: f"return {v()} == NULL;",
        lambda: f"return {v()} % {n()} == 0;",
        lambda: f"return {v()} / {n()};",
        lambda: f"return {v()} > {v()};",
        lambda: f"return {v()} >= 0;",
        lambda: f"return {n()};",
        lambda: f"return ({v()} == {v()}) ? 1 : 0;",
    ])()

# ── CLASS 6 : Array Access ───────────────────────────────────
def make_array_access():
    return random.choice([
        lambda: f"{v()} = {a()}[{n()}];",
        lambda: f"{v()} = {a()}[{v()}];",
        lambda: f"{a()}[{n()}] = {v()};",
        lambda: f"{a()}[{v()}] = {n()};",
        lambda: f"{a()}[{v()}] = {v()};",
        lambda: f"{a()}[{v()}] += {n()};",
        lambda: f"{a()}[{v()}] -= {n()};",
        lambda: f"{a()}[{v()}]++;",
        lambda: f"{a()}[{v()}]--;",
        lambda: f"{v()} = {a()}[{v()}] + {n()};",
        lambda: f"{v()} = {a()}[{v()}] + {a()}[{v()}];",
        lambda: f"{t()} {v()} = {a()}[{v()}];",
        lambda: f"{a()}[{n()}] = {f()}({v()});",
        lambda: f"{a()}[{v()} + {n()}] = {v()};",
        lambda: f"{a()}[{v()} - 1] = {n()};",
        lambda: f"{v()} = {a()}[0];",
        lambda: f"{v()} = {a()}[{v()} - 1];",
        lambda: f"{a()}[{v()}][{v()}] = {n()};",
        lambda: f"{v()} = {a()}[{v()}][{v()}];",
        lambda: f"{a()}[{v()} % {n()}] = {v()};",
        lambda: f"if ({a()}[{v()}] > {n()}) {{ }}",
        lambda: f"if ({a()}[{v()}] == {n()}) {{ }}",
        lambda: f"{a()}[{v()}] = {a()}[{v()} - 1];",
        lambda: f"for (int {v()} = 0; {v()} < {n()}; {v()}++) {a()}[{v()}] = 0;",
        lambda: f"{v()} = {a()}[{n()} - 1];",
    ])()

# ── CLASS 7 : Pointer Operation ──────────────────────────────
# Rule: EVERY template MUST contain * or & or ->
def make_pointer_op():
    return random.choice([
        lambda: f"{v()} = *{v()};",
        lambda: f"*{v()} = {n()};",
        lambda: f"*{v()} = {v()};",
        lambda: f"{t()} *{v()} = &{v()};",
        lambda: f"{v()} = &{v()};",
        lambda: f"*{v()} += {n()};",
        lambda: f"*{v()} -= {n()};",
        lambda: f"(*{v()})++;",
        lambda: f"(*{v()})--;",
        lambda: f"{v()} = *(({t()} *) {v()});",
        lambda: f"*{v()} = *{v()};",
        lambda: f"*({v()} + {n()}) = {v()};",
        lambda: f"{v()} = *({v()} + {n()});",
        lambda: f"void *{v()} = (void *) {v()};",
        lambda: f"{t()} *{v()} = ({t()} *) {v()};",
        lambda: f"{t()} **{v()} = &{v()};",
        lambda: f"*{v()} = {f()}({v()});",
        lambda: f"{v()} = &{a()}[{v()}];",
        lambda: f"if (*{v()} == {n()}) {{ }}",
        lambda: f"if (*{v()} != NULL) {{ }}",
        lambda: f"*{v()} = *{v()} + {n()};",
        lambda: f"{t()} *{v()} = NULL;",
        lambda: f"*{v()} = 0;",
        lambda: f"{v()} = *{v()} + *{v()};",
        lambda: f"if ({v()} == &{v()}) {{ }}",
    ])()

# ── CLASS 8 : Struct Access ──────────────────────────────────
# Rule: EVERY template MUST contain . or ->
def make_struct_access():
    return random.choice([
        lambda: f"{v()}.{fd()} = {n()};",
        lambda: f"{v()}.{fd()} = {v()};",
        lambda: f"{v()} = {v()}.{fd()};",
        lambda: f"{v()}.{fd()} += {n()};",
        lambda: f"{v()}.{fd()}++;",
        lambda: f"{v()}.{fd()}--;",
        lambda: f"{v()}->{fd()} = {n()};",
        lambda: f"{v()}->{fd()} = {v()};",
        lambda: f"{v()} = {v()}->{fd()};",
        lambda: f"{v()}->{fd()} += {n()};",
        lambda: f"{v()}->{fd()}++;",
        lambda: f"{v()}->{fd()}--;",
        lambda: f"{v()}.{fd()} = {v()}.{fd()};",
        lambda: f"{v()}->{fd()} = {v()}->{fd()};",
        lambda: f"{v()} = {v()}->{fd()} + {n()};",
        lambda: f"{v()}.{fd()} = {f()}({v()});",
        lambda: f"{v()}->{fd()} = {f()}({v()});",
        lambda: f"if ({v()}->{fd()} {cop()} {n()}) {{ }}",
        lambda: f"if ({v()}.{fd()} {cop()} {n()}) {{ }}",
        lambda: f"{t()} {v()} = {v()}.{fd()};",
        lambda: f"if ({v()}->{fd()} == NULL) {{ }}",
        lambda: f"if ({v()}.{fd()} == 0) {{ }}",
        lambda: f"{v()}->{fd()} = {v()}->{fd()} + {n()};",
        lambda: f"{v()}.{fd()} = {v()}.{fd()} + {n()};",
        lambda: f"return {v()}->{fd()};",
    ])()

# ── CLASS 9 : Increment / Decrement ─────────────────────────
# Rule: ONLY ++ / -- / <<= / >>= — no +=/-= (those bleed into Assignment)
def make_inc_dec():
    return random.choice([
        lambda: f"{v()}++;",
        lambda: f"{v()}--;",
        lambda: f"++{v()};",
        lambda: f"--{v()};",
        lambda: f"{a()}[{v()}]++;",
        lambda: f"{a()}[{v()}]--;",
        lambda: f"(*{v()})++;",
        lambda: f"(*{v()})--;",
        lambda: f"{v()}->{fd()}++;",
        lambda: f"{v()}->{fd()}--;",
        lambda: f"{v()}.{fd()}++;",
        lambda: f"{v()}.{fd()}--;",
        lambda: f"++{a()}[{v()}];",
        lambda: f"--{a()}[{v()}];",
        lambda: f"for (int {v()} = 0; {v()} < {n()}; {v()}++) {v()}++;",
        lambda: f"{v()} <<= 1;",
        lambda: f"{v()} >>= 1;",
        lambda: f"{v()} <<= {n()};",
        lambda: f"{v()} >>= {n()};",
        lambda: f"++(*{v()});",
        lambda: f"--(*{v()});",
        lambda: f"({v()}++);",
        lambda: f"({v()}--);",
        lambda: f"(++{v()});",
        lambda: f"(--{v()});",
    ])()

# ── CLASS 10 : Bitwise Operation ─────────────────────────────
# Rule: MUST contain &, |, ^, ~, <<, >> (but NOT as pointer/address-of)
def make_bitwise():
    return random.choice([
        lambda: f"{v()} = {v()} & {n()};",
        lambda: f"{v()} = {v()} | {n()};",
        lambda: f"{v()} = {v()} ^ {n()};",
        lambda: f"{v()} = {v()} << {n()};",
        lambda: f"{v()} = {v()} >> {n()};",
        lambda: f"{v()} = ~{v()};",
        lambda: f"{v()} &= {n()};",
        lambda: f"{v()} |= {n()};",
        lambda: f"{v()} ^= {n()};",
        lambda: f"{v()} &= {v()};",
        lambda: f"{v()} |= {v()};",
        lambda: f"{v()} ^= {v()};",
        lambda: f"{v()} = {v()} & {v()};",
        lambda: f"{v()} = {v()} | {v()};",
        lambda: f"{v()} = {v()} ^ {v()};",
        lambda: f"{v()} = ({v()} & {n()}) >> {n()};",
        lambda: f"{v()} = ({v()} | {n()}) << {n()};",
        lambda: f"if ({v()} & {n()}) {{ }}",
        lambda: f"if ({v()} & {v()}) {{ }}",
        lambda: f"{v()} = {v()} & ~{n()};",
        lambda: f"{v()} = ({v()} >> {n()}) & {n()};",
        lambda: f"{v()} = {v()} | (1 << {n()});",
        lambda: f"{v()} = {v()} & ~(1 << {n()});",
        lambda: f"if (({v()} & {n()}) == 0) {{ }}",
        lambda: f"if (({v()} & {n()}) != 0) {{ }}",
    ])()

# ── CLASS 11 : Logical Expression ───────────────────────────
def make_logical_expr():
    return random.choice([
        lambda: f"{v()} = {v()} && {v()};",
        lambda: f"{v()} = {v()} || {v()};",
        lambda: f"{v()} = !{v()};",
        lambda: f"{v()} = ({v()} {cop()} {n()}) && ({v()} {cop()} {n()});",
        lambda: f"{v()} = ({v()} {cop()} {n()}) || ({v()} {cop()} {n()});",
        lambda: f"if ({v()} && {v()}) {{ }}",
        lambda: f"if ({v()} || {v()}) {{ }}",
        lambda: f"if (!{v()} && {v()}) {{ }}",
        lambda: f"if ({v()} && !{v()}) {{ }}",
        lambda: f"if (!{v()} || !{v()}) {{ }}",
        lambda: f"{t()} {v()} = ({v()} && {v()});",
        lambda: f"{t()} {v()} = ({v()} || {v()});",
        lambda: f"{t()} {v()} = !{v()};",
        lambda: f"if (({v()} {cop()} {n()}) && ({v()} {cop()} {n()}) && {v()}) {{ }}",
        lambda: f"if (({v()} {cop()} {n()}) || ({v()} {cop()} {n()}) || {v()}) {{ }}",
        lambda: f"{v()} = ({v()} {cop()} {v()}) ? 1 : 0;",
        lambda: f"if ({f()}({v()}) && {v()} {cop()} {n()}) {{ }}",
        lambda: f"if ({f()}({v()}) || {v()} {cop()} {n()}) {{ }}",
        lambda: f"{v()} = {v()} {cop()} {n()} && {v()} {cop()} {n()};",
        lambda: f"bool {v()} = ({v()} && {v()});",
        lambda: f"bool {v()} = !{v()} && !{v()};",
        lambda: f"bool {v()} = {v()} || !{v()};",
        lambda: f"if (!({v()} && {v()})) {{ }}",
        lambda: f"if (!({v()} || {v()})) {{ }}",
        lambda: f"{v()} = !({v()} {cop()} {n()});",
    ])()

# ── CLASS 12 : Cast Expression ───────────────────────────────
# Rule: MUST contain ( type ) or _cast<
def make_cast():
    return random.choice([
        lambda: f"{v()} = ({t()}) {v()};",
        lambda: f"{t()} {v()} = ({t()}) {v()};",
        lambda: f"{v()} = ({t()}) {n()};",
        lambda: f"{v()} = ({t()}) {f()}({v()});",
        lambda: f"{t()} {v()} = ({t()}) {f()}({v()});",
        lambda: f"{v()} = ({t()} *) {v()};",
        lambda: f"{t()} *{v()} = ({t()} *) {v()};",
        lambda: f"{v()} = (void *) {v()};",
        lambda: f"{v()} = ({t()}) {v()} + {n()};",
        lambda: f"return ({t()}) {v()};",
        lambda: f"return ({t()} *) {v()};",
        lambda: f"if (({t()}) {v()} {cop()} {n()}) {{ }}",
        lambda: f"{v()} = ({t()}) ({v()} + {v()});",
        lambda: f"{t()} {v()} = ({t()}) {v()} / {n()};",
        lambda: f"{v()} = (unsigned int) {v()};",
        lambda: f"const {t()} {v()} = ({t()}) {v()};",
        lambda: f"{v()} = static_cast<{t()}>({v()});",
        lambda: f"{v()} = reinterpret_cast<{t()} *>({v()});",
        lambda: f"{v()} = dynamic_cast<{t()} *>({v()});",
        lambda: f"{v()} = const_cast<{t()} *>({v()});",
        lambda: f"{t()} {v()} = static_cast<{t()}>({v()});",
        lambda: f"{t()} *{v()} = reinterpret_cast<{t()} *>({v()});",
        lambda: f"if (static_cast<{t()}>({v()}) {cop()} {n()}) {{ }}",
        lambda: f"{v()} = ({t()}) {v()} * {n()};",
        lambda: f"{v()} = ({t()}) ({v()} - {n()});",
    ])()

# ── CLASS 13 : Memory Allocation ────────────────────────────
# Rule: MUST contain malloc/calloc/realloc/new/free/delete/memset
def make_memory_alloc():
    return random.choice([
        lambda: f"{v()} = malloc({n()});",
        lambda: f"{v()} = malloc(sizeof({t()}));",
        lambda: f"{v()} = malloc(sizeof({t()}) * {n()});",
        lambda: f"{v()} = calloc({n()}, sizeof({t()}));",
        lambda: f"{v()} = realloc({v()}, {n()});",
        lambda: f"{v()} = realloc({v()}, sizeof({t()}) * {n()});",
        lambda: f"free({v()});",
        lambda: f"{t()} *{v()} = malloc(sizeof({t()}));",
        lambda: f"{t()} *{v()} = malloc(sizeof({t()}) * {n()});",
        lambda: f"{t()} *{v()} = calloc({n()}, sizeof({t()}));",
        lambda: f"{v()} = new {t()}();",
        lambda: f"{v()} = new {t()}[{n()}];",
        lambda: f"{t()} *{v()} = new {t()}();",
        lambda: f"{t()} *{v()} = new {t()}[{n()}];",
        lambda: f"delete {v()};",
        lambda: f"delete[] {v()};",
        lambda: f"{t()} *{v()} = ({t()} *) malloc(sizeof({t()}) * {n()});",
        lambda: f"memset({v()}, 0, sizeof({t()}) * {n()});",
        lambda: f"memset({v()}, 0, {n()});",
        lambda: f"if (({v()} = malloc(sizeof({t()}))) == NULL) {{ }}",
        lambda: f"if (({v()} = calloc({n()}, sizeof({t()}))) == NULL) {{ }}",
        lambda: f"{v()} = ({t()} *) calloc({n()}, sizeof({t()}));",
        lambda: f"free({v()}); {v()} = NULL;",
        lambda: f"{t()} *{v()} = ({t()} *) realloc({v()}, {n()});",
        lambda: f"std::unique_ptr<{t()}> {v()} = std::make_unique<{t()}>();",
    ])()

# ── CLASS 14 : Exception Handling ───────────────────────────
# Rule: MUST contain throw/try/catch/assert/static_assert
def make_exception():
    return random.choice([
        lambda: f'throw {exc()}("{v()}");',
        lambda: f"throw {exc()}();",
        lambda: f"throw;",
        lambda: f"catch ({exc()} &{v()}) {{ }}",
        lambda: f"catch (...) {{ }}",
        lambda: f"catch (const {exc()} &{v()}) {{ }}",
        lambda: f"try {{ }} catch ({exc()} &{v()}) {{ }}",
        lambda: f"try {{ }} catch (...) {{ }}",
        lambda: f'if ({v()} < 0) throw {exc()}("{v()}");',
        lambda: f"if ({v()} == NULL) throw {exc()}();",
        lambda: f'if ({v()} {cop()} {n()}) throw {exc()}("{v()}");',
        lambda: f"assert({v()} != NULL);",
        lambda: f"assert({v()} {cop()} {n()});",
        lambda: f"assert({v()} >= 0);",
        lambda: f"if (!{v()}) throw {exc()}();",
        lambda: f'static_assert(sizeof({t()}) == {n()}, "size mismatch");',
        lambda: f"try {{ }} catch (const {exc()} &{v()}) {{ }} catch (...) {{ }}",
        lambda: f"throw {exc()}(std::to_string({v()}));",
        lambda: f"assert({v()} > 0);",
        lambda: f"assert({v()} == {v()});",
        lambda: f'if ({v()} > {n()}) throw {exc()}("overflow");',
        lambda: f"assert({v()} != {v()});",
        lambda: f"assert({v()} < {n()});",
        lambda: f'throw {exc()}("invalid " + std::to_string({v()}));',
        lambda: f"if ({v()} != 0) throw {exc()}();",
    ])()

# ── Class registry ────────────────────────────────────────────

CLASS_MAP = {
    0:  ("Assignment",          make_assignment),
    1:  ("Loop",                make_loop),
    2:  ("Conditional",         make_conditional),
    3:  ("Declaration",         make_declaration),
    4:  ("Function Call",       make_function_call),
    5:  ("Return",              make_return),
    6:  ("Array Access",        make_array_access),
    7:  ("Pointer Operation",   make_pointer_op),
    8:  ("Struct Access",       make_struct_access),
    9:  ("Increment/Decrement", make_inc_dec),
    10: ("Bitwise Operation",   make_bitwise),
    11: ("Logical Expression",  make_logical_expr),
    12: ("Cast Expression",     make_cast),
    13: ("Memory Allocation",   make_memory_alloc),
    14: ("Exception Handling",  make_exception),
}

SAMPLES_PER_CLASS = 1000

# ── Generate ──────────────────────────────────────────────────

random.seed(42)
rows = []

for class_id, (class_name, generator) in CLASS_MAP.items():
    for _ in range(SAMPLES_PER_CLASS):
        rows.append({
            "statement":  generator(),
            "class_id":   class_id,
            "class_name": class_name,
        })

df = pd.DataFrame(rows)
df = df.sample(frac=1, random_state=42).reset_index(drop=True)
df.to_csv("dataset.csv", index=False)

print(f"Dataset saved  →  dataset.csv")
print(f"Total samples  :  {len(df)}")
print(f"\nClass distribution:")
print(df.groupby(["class_id","class_name"]).size().rename("count").to_string())

# ── Overlap audit ─────────────────────────────────────────────
print("\n── Overlap audit (x op= N patterns) ──")
for cls in df["class_name"].unique():
    sub   = df[df["class_name"] == cls]
    bleed = sub[sub["statement"].str.match(r'^[a-z_]+ [+\-]?= \d+;$')]
    if len(bleed) > 0:
        print(f"  {cls}: {len(bleed)} rows  ← check these")