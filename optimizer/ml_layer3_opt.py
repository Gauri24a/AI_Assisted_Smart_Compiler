class OptStrategy:
    # weights learned offline: IR feature -> optimization usefulness score
    RULES = {
        "constant_fold":   lambda f: f["literals"] > 0,
        "dead_code":       lambda f: f["assigns"] > 2,
        "loop_unroll":     lambda f: f["loops"] > 0 and f["instrs"] < 30,
        "inline":          lambda f: f["calls"] > 0 and f["instrs"] < 20,
    }

    def predict(self, ir):
        f = self._features(ir)
        return [opt for opt, rule in self.RULES.items() if rule(f)]

    def _features(self, ir):
        return {
            "instrs":   len(ir),
            "literals": sum(1 for i in ir if i.op == "assign" and i.a and i.a[0] in "\"'0123456789"),
            "assigns":  sum(1 for i in ir if i.op == "assign"),
            "loops":    sum(1 for i in ir if i.op == "label" and i.a and i.a[0] == "L"),
            "calls":    sum(1 for i in ir if i.op == "call"),
        }
