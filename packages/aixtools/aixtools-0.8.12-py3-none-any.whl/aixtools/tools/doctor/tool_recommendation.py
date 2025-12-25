from pydantic import BaseModel

"""
These are classes that represent recommendations for improving tools.
They are ued by ToolDoctor
"""


class ArgumentRecommendation(BaseModel):
    """A recommendation for an argument"""

    arg_name: str
    arg_type: str
    arg_description_improvement: str

    def __str__(self):
        return f"{self.arg_name} ({self.arg_type}): {self.arg_description_improvement}"


class ToolRecommendation(BaseModel):
    """A recomendation for a tool"""

    name: str
    needs_improvement: bool
    description_improvement: str
    arguments: list[ArgumentRecommendation]
    return_description_improvement: str

    def signature(self):
        """Generate the function signature for the tool"""
        signature = f"def {self.name}("
        if self.arguments:
            signature += ", ".join([f"{arg.arg_name}: {arg.arg_type}" for arg in self.arguments])
        signature += ")"
        return signature

    def __str__(self):
        out = f"Tool name: '{self.name}'\n"
        out += f"  - Signature: {self.signature()}\n"
        out += f"  - Needs improvement: {self.needs_improvement}\n"
        if self.description_improvement:
            out += f"  - Description improvement: {self.description_improvement}\n"
        if self.return_description_improvement:
            out += f"  - Return description improvement: {self.return_description_improvement}\n"
        if self.arguments:
            out += "  - Arguments:\n"
            for arg in self.arguments:
                out += f"    - {arg}\n"
        return out
