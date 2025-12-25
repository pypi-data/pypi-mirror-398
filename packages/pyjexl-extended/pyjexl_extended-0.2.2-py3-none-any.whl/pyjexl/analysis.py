class JEXLAnalyzer(object):
    def __init__(self, jexl_config):
        self.config = jexl_config

    def visit(self, expression):
        method = getattr(self, "visit_" + type(expression).__name__, self.generic_visit)
        return method(expression)

    def generic_visit(self, expression):
        raise NotImplementedError()


class ValidatingAnalyzer(JEXLAnalyzer):
    def visit_Transform(self, transform):
        if transform.name not in self.config.transforms:
            yield "The `{name}` transform is undefined.".format(name=transform.name)
        for t in self.generic_visit(transform):
            yield t

    def visit_Function(self, func):
        if func.name not in self.config.functions:
            yield "The `{name}` function is undefined.".format(name=func.name)
        for t in self.generic_visit(func):
            yield t

    def generic_visit(self, expression):
        for child in expression.children:
            assert child is not None
            for c in self.visit(child):
                yield c
