class Instr:
    def __init__(self, op, dest=None, a=None, b=None):
        self.op   = op
        self.dest = dest
        self.a    = a
        self.b    = b

    def __repr__(self):
        parts = [self.op]
        if self.dest: parts.append(self.dest)
        if self.a is not None: parts.append(str(self.a))
        if self.b is not None: parts.append(str(self.b))
        return "  " + "  ".join(parts)