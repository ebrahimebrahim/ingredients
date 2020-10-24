class Tree:
  """Basic tree structure with labeled nodes.
  |token| is the label on a node"""
  def __init__(self,token):
    self.token = token
    self.children = [] # list of Tree
    self.parent = None # a Tree, if this isn't the root

  def add_child(self,child):
    child.parent = self
    self.children.append(child)

  def add_sibling(self,sibling):
    self.parent.add_child(sibling)

  def last_child(self):
    return self.children[-1]

  def last_sibling(self):
    return self.parent.children[-1]

  def is_only_child(self):
    return len(self.parent.children)==1

  def to_str(self,tabs=''):
    return (tabs+str(self.token)+('\n' if self.children else '')+'\n'.join([child.to_str(tabs+'\t') for child in self.children]))

  def __str__(self):
    return self.to_str()


def read_condition_string(condition_string):
  """Read the given string and parse into an abstract syntax tree.
  Return the parsed tree. Input is str and output is Tree.
  Input is of the following grammar:
    - no spaces anywhere
    - all strings without special characters in '|&!' are called primitives
    - primitives are valid expressions
    - parenthesizing a valid expression yields a valid expression
    - primitives and parenthesized valid expressions are called peups
    - preceding a peup by '!' yields a valid expression
    - preceding a peup by '!' yields a peup
    - A1&A2&...&An  is a valid expression if A1, ..., An are peups
    - A1|A2|...|An  is a valid expression if A1, ..., An are peups
  """
  root = Tree('.')
  root.add_child(Tree(''))
  head = root.last_child()
  for c in condition_string:
    #print(root,"\n---")
    if c in '&|':
      while head.parent.token=='!':
        head = head.parent
      if head.is_only_child():
        head.parent.token=c
      else:
        assert(head.parent.token==c)
      head.add_sibling(Tree(''))
      head=head.last_sibling()
    elif c == '!':
      assert(head.token=='')
      head.token=c
      head.add_child(Tree(''))
      head = head.last_child()
    elif c=='(':
      assert(head.token=='')
      head.token='.'
      head.add_child(Tree(''))
      head = head.last_child()
    elif c==')':
      while head.parent.token=='!':
        head = head.parent
      head = head.parent
    else:
      head.token += c
  return root


class Cst:
  """ Condition syntax tree class. See read_condition_string
  docstring for condition_string syntax.

  This class wraps a Tree which is a parsed abstract syntax tree.
  It provides methods for applying semantics.

  Raises exception on parse error.
  """
  def __init__(self,condition_string):
    self.condition_string = condition_string
    try:
      self.ast = read_condition_string(condition_string) # abstract syntax tree
    except:
      raise Exception("Unable to parse condition string: "+str(condition_string))

  def evaluate(self,truth_mapping,ast=None):
    """ |truth_mapping| is a dict from primitive symbols in the condition string
    to bool values. This will evaluate the condition string, treating the tokens
    &, |, and ! as the usual "and," "or," and "not"
    |ast| is used for recursion and should be ignored for normal usage.
    """
    if ast is None:
      ast = self.ast

    truth_vals_of_children = [self.evaluate(truth_mapping,c) for c in ast.children]

    if ast.token=='&':
      return all(truth_vals_of_children)
    if ast.token=='|':
      return any(truth_vals_of_children)
    if ast.token=='!':
      if not len(truth_vals_of_children)==1:
        raise Exception("Malformed conditional expression: "+self.condition_string)
      return not truth_vals_of_children[0]
    if ast.token=='.':
      if not len(truth_vals_of_children)==1:
        raise Exception("Malformed conditional expression: "+self.condition_string)
      return truth_vals_of_children[0]
    else:
      assert(len(truth_vals_of_children)==0)
      return truth_mapping[ast.token]

  def symbols(self,ast=None):
    """ Return a list of the primitive symbols in the condition string.
    |ast| is used for recursion and should be ignored for normal usage.
    """
    if ast is None:
      ast = self.ast
    symbols_of_children = sum([self.symbols(c) for c in ast.children],[])
    if ast.token not in ['&','|','!','.']:
      return [ast.token]+symbols_of_children
    else:
      return symbols_of_children


  def __eq__(self,other):
    return self.condition_string==other.condition_string
