from lark import Lark, Transformer

__version__ = "1.0.0"
__author__ = "vancura"

grammar = """
	pair: string value
	value: string | dictionary
	dictionary: "{" (pair)* "}"
	string: ESCAPED_STRING

	%import common.ESCAPED_STRING
	%import common.CPP_COMMENT
	%import common.WS
	%ignore CPP_COMMENT
	%ignore WS
"""

parser = Lark(grammar, start="pair")

class TreeTransformer(Transformer):
	def pair(self, items):
		key, value = items
		return key, value

	def value(self, items):
		return items[0]

	def dictionary(self, items):
		return dict(items)

	def string(self, items):
		return items[0].strip('"')

transformer = TreeTransformer()

def _parse(s):
	"""
	@type fun(s: str) -> dict
	"""
	return dict([transformer.transform( parser.parse(s) )])

def _dict_to_vdf_string(d, s):
	"""
	@type fun(d: dict, s: str) -> str
	"""
	for k, v in d.items():
		s += '"' + k + '"'
		
		if isinstance(v, dict):
			s += " "
			s += "{ "
			s = _dict_to_vdf_string(v, s)
			s += "} "
		else:
			s += f' "{str(v)}" '
	
	return s

def _dict_to_vdf_string_pretty(d, s, depth):
	"""
	@type fun(d: dict, s: str, depth: int) -> str
	"""
	for k, v in d.items():
		s += "\t" * depth + '"' + k + '"'
		
		if isinstance(v, dict):
			s += "\n"
			s += "\t" * depth + "{\n"
			s = _dict_to_vdf_string_pretty(v, s, depth + 1)
			s += "\t" * depth + "}\n"
		else:
			s += f' "{str(v)}"\n'
	
	return s

def loads(s):
	"""
	@type fun(s: str) -> dict
	"""
	return _parse(s)

def load(f):
	"""
	@type fun(f: TextIO) -> dict
	"""
	return _parse(f.read())

def dumps(d, pretty=True):
	"""
	@type fun(d: dict, pretty: bool) -> str
	"""
	return _dict_to_vdf_string_pretty(d, "", 0) if pretty else _dict_to_vdf_string(d, "")

def dump(d, f, pretty=True):
	"""
	@type fun(d: dict, f: TextIO, pretty: bool)
	"""
	f.write(dumps(d, pretty))
