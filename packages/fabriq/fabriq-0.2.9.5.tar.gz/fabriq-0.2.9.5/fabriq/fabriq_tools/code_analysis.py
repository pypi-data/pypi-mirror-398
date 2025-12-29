import ast
import subprocess
import re

class CodeAnalysisTool:
    def __init__(self):
        self.description = "A tool for analyzing Python code files. It provides information about functions, classes, docstring styles, line counts, syntax validity, and Pylint scores."
        
    def analyze_code(self, file_path: str) -> dict:
        with open(file_path, "r") as file:
            code = file.read()
        result = {
            "functions": [],
            "classes": [],
            "docstring_style": [],
            "docstring_style_counts": {},
            "lines": len(code.splitlines()),
            "syntax_valid": True,
            "pylint_score": None,
            "pylint_messages": []
        }
        try:
            tree = ast.parse(code)
            result["functions"] = [node.name for node in ast.walk(tree) if isinstance(node, ast.FunctionDef)]
            result["classes"] = [node.name for node in ast.walk(tree) if isinstance(node, ast.ClassDef)]
        except SyntaxError as e:
            result["syntax_valid"] = False
            result["error"] = str(e)
            return result

        docstring_list = [ast.get_docstring(node) for node in ast.walk(tree) if isinstance(node, (ast.FunctionDef, ast.ClassDef)) and ast.get_docstring(node)]
        docstring_info = self.infer_docstring_style(docstring_list)
        result.update(docstring_info)

        try:
            pylint_output = subprocess.run(
                ["pylint", file_path, "--score", "y", "--output-format", "json2"],
                capture_output=True,
                text=True
            )
            import json
            messages = json.loads(pylint_output.stdout)
            result["pylint_messages"] = messages
            result["pylint_score"] = messages.get("statistics").get("score")
        except Exception as e:
            result["pylint_error"] = str(e)
        
        return result
    
    def infer_docstring_style(self, docstrings: list) -> dict:
        styles = {"google": 0, "numpy": 0, "rst": 0, "unknown": 0}
        try:
            for doc in docstrings:
                # Google style: Args:, Returns:, Raises:
                if re.search(r"Args:|Returns:|Raises:", doc):
                    styles["google"] += 1
                # NumPy style: Parameters, Returns, Examples
                elif re.search(r"Parameters\n[-]+|Returns\n[-]+|Examples\n[-]+", doc):
                    styles["numpy"] += 1
                # reStructuredText: :param, :return, :raises
                elif re.search(r":param|:return:|:raises:", doc):
                    styles["reStructuredText"] += 1
                else: styles["unknown"] += 1
        except Exception:
            pass
        # Find the most common style
        main_style = max(styles, key=styles.get)
        return {"docstring_style": main_style, "docstring_style_counts": styles}