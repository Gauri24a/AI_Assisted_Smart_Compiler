class Optimizer:
    def optimize(self, ir, strategies):
        for strategy in strategies:
            method = getattr(self, f"_{strategy}", None)
            if method:
                ir = method(ir)
        return ir

    def _constant_fold(self, ir):
        constants = {}
        result = []
        for instr in ir:
            if instr.op == "assign" and instr.a and instr.a[0] in "\"'0123456789":
                constants[instr.dest] = instr.a
            if instr.op == "binop" and instr.a in constants:
                instr.a = constants[instr.a]
            result.append(instr)
        return result

    def _dead_code(self, ir):
        used = set()
        for instr in ir:
            if instr.a: used.update(str(instr.a).split())
            if instr.b: used.update(str(instr.b).split())
        return [i for i in ir if i.op != "assign" or i.dest == "_" or i.dest in used]

    def _loop_unroll(self, ir):
        # mark loops for the assembly generator — no structural change here
        for instr in ir:
            if instr.op == "label":
                instr._unroll_hint = True
        return ir

    def _inline(self, ir):
        # mark small call sites — assembly generator uses this hint
        for instr in ir:
            if instr.op == "call":
                instr._inline_hint = True
        return ir
