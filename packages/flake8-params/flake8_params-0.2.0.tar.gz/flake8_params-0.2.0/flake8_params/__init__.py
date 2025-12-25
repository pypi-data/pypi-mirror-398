#!/usr/bin/env python3
#
#  __init__.py
"""
A flake8 plugin which checks for mismatches between function signatures and docstring params.
"""
#
#  Copyright (c) 2025 Dominic Davis-Foster <dominic@davis-foster.co.uk>
#
#  Permission is hereby granted, free of charge, to any person obtaining a copy
#  of this software and associated documentation files (the "Software"), to deal
#  in the Software without restriction, including without limitation the rights
#  to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
#  copies of the Software, and to permit persons to whom the Software is
#  furnished to do so, subject to the following conditions:
#
#  The above copyright notice and this permission notice shall be included in
#  all copies or substantial portions of the Software.
#
#  THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
#  IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
#  FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
#  AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
#  LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
#  OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
#  THE SOFTWARE.
#

# stdlib
import ast
from typing import Iterator, List, Optional, Union

# 3rd party
import flake8_helper

__all__ = ("Plugin", "Visitor", "get_decorator_names", "check_params", "get_docstring_args", "get_signature_args")

__author__ = "Dominic Davis-Foster"
__copyright__ = "2025 Dominic Davis-Foster"
__license__ = "MIT"
__version__ = "0.0.0"
__email__ = "dominic@davis-foster.co.uk"

PRM001 = "PRM001 Docstring parameters in wrong order."
PRM002 = "PRM002 Missing parameters in docstring"
PRM003 = "PRM003 Extra parameters in docstring"
# TODO: class-specific codes?

deco_allowed_attr_names = {
		".setter",  # Property setter
		".command",  # Probably a click command
		".group",  # Probably a click group
		}


def _get_deco_name_parts(node: ast.expr) -> Iterator[str]:
	if isinstance(node, ast.Name):
		yield node.id
	elif isinstance(node, ast.Attribute):
		yield from _get_deco_name_parts(node.value)
		yield node.attr
	else:
		raise NotImplementedError(node)


def _get_deco_name(decorator: ast.expr) -> Iterator[str]:
	if isinstance(decorator, (ast.Name, ast.Attribute)):
		yield '.'.join(_get_deco_name_parts(decorator))
	elif isinstance(decorator, ast.Call):
		yield from _get_deco_name(decorator.func)
	else:
		raise NotImplementedError(decorator)


def get_decorator_names(function: Union[ast.AsyncFunctionDef, ast.FunctionDef, ast.ClassDef]) -> Iterator[str]:
	"""
	Returns an iterator of the dotted names of decorators for the given function.

	:param function:
	"""

	for decorator in function.decorator_list:
		yield from _get_deco_name(decorator)


def check_params(
		signature_args: List[str],
		docstring_args: List[str],
		decorators: List[str],
		) -> Optional[str]:
	"""
	Check if signature and docstring parameters match, and return the flake8 error code if not.

	:param signature_args:
	:param docstring_args:
	:param decorators: List of dotted names (e.g. ``foo.bar``, for ``@foo.bar()``) of decorators for the function or class.

	:returns: Either a flake8 error code and description, or :py:obj:`None` if no errors were detected.
	"""

	if "self" in signature_args:
		signature_args.remove("self")

	if "classmethod" in decorators and signature_args:
		signature_args.pop(0)
	for deco in decorators:
		if any(deco.endswith(name) for name in deco_allowed_attr_names):
			signature_args = []
			break

	if not signature_args and not docstring_args:
		# No args either way
		return None

	if signature_args == docstring_args:
		# All match
		return None

	# Either wrong order, extra in signature, extra in doc
	signature_set = set(signature_args)
	docstring_set = set(docstring_args)
	if signature_set == docstring_set:
		# Wrong order
		return PRM001
	elif signature_set - docstring_set:
		# Extras in signature
		return PRM002 + ": " + ' '.join(sorted(signature_set - docstring_set))
	elif docstring_set - signature_set:
		# Extras in docstrings
		return PRM003 + ": " + ' '.join(sorted(docstring_set - signature_set))

	return None  # pragma: no cover


def get_signature_args(function: Union[ast.FunctionDef, ast.AsyncFunctionDef]) -> Iterator[str]:
	"""
	Extract arguments from the function signature.

	:param function:

	:rtype:

	..versionadded:: 0.2.0
	"""

	for arg in function.args.posonlyargs:
		yield arg.arg

	for arg in function.args.args:
		yield arg.arg

	if function.args.vararg:
		yield '*' + function.args.vararg.arg

	for arg in function.args.kwonlyargs:
		yield arg.arg

	if function.args.kwarg:
		yield "**" + function.args.kwarg.arg


def get_docstring_args(docstring: str) -> Iterator[str]:
	"""
	Extract arguments from the docstring.

	:param docstring:

	:rtype:

	..versionadded:: 0.2.0
	"""

	for line in docstring.split('\n'):
		line = line.strip()
		if line.startswith(":param"):
			yield line[6:].split(':', 1)[0].strip().replace(r"\*", '*')


class Visitor(flake8_helper.Visitor):
	"""
	AST node visitor for identifying mismatches between function signatures and docstring params.
	"""

	def visit_FunctionDef(self, node: ast.FunctionDef) -> None:  # noqa: D102
		self._visit_function(node)

	def visit_AsyncFunctionDef(self, node: ast.AsyncFunctionDef) -> None:  # noqa: D102
		self._visit_function(node)

	def _visit_function(self, node: Union[ast.FunctionDef, ast.AsyncFunctionDef]) -> None:
		if node.name == "__init__":
			self.generic_visit(node)
			return

		docstring = ast.get_docstring(node, clean=False)

		if not docstring:
			self.generic_visit(node)
			return

		docstring_args = list(get_docstring_args(docstring))
		signature_args = list(get_signature_args(node))
		decorators = list(get_decorator_names(node))

		error = check_params(signature_args, docstring_args, decorators)
		if not error:
			self.generic_visit(node)
			return

		self.errors.append((
				node.lineno,
				node.col_offset,
				error,
				))

		self.generic_visit(node)

	def visit_ClassDef(self, node: ast.ClassDef) -> None:  # noqa: D102
		docstring = ast.get_docstring(node, clean=False)

		if not docstring:
			self.generic_visit(node)
			return

		docstring_args = list(get_docstring_args(docstring))
		decorators = list(get_decorator_names(node))

		signature_args = []
		functions_in_body: List[ast.FunctionDef] = [n for n in node.body if isinstance(n, ast.FunctionDef)]

		for function in functions_in_body:
			if function.name == "__init__":
				signature_args = list(get_signature_args(function))
				break
		else:
			# No __init__; maybe it comes from a base class.
			# TODO: check for base classes and still error if non exist
			self.generic_visit(node)
			return

		error = check_params(signature_args, docstring_args, decorators)
		if not error:
			self.generic_visit(node)
			return

		self.errors.append((
				node.lineno,
				node.col_offset,
				error,
				))

		self.generic_visit(node)


class Plugin(flake8_helper.Plugin[Visitor]):
	"""
	A Flake8 plugin which checks for mismatches between function signatures and docstring params.

	:param tree: The abstract syntax tree (AST) to check.
	"""

	name: str = __name__

	#: The plugin version
	version: str = __version__

	visitor_class = Visitor
