

class Ingredient:
  """ Represents a NON_ABSTRACT ingredient. Any "ingredient inheritance" should be already resolved.
      Still, it remembers the names of the ingredients in originally inherited from.
      Example:
        If ingredient file Onion inherts from file Vegetable,
        then there will be an Ingredient object named "Onion" after parsing is done.
        Whatever attributes Vegetable file had that Onion file does not override will end up in the Ingredient named "Onion"
        If Vegetable file is abstract, then there is will be no Ingredient named "Vegetable"
        But the Ingredient named "Onion" will still remember that it inherited from something called "Vegetable"
  """
  def __init__(self, name, inherited_from=[]):
    self.name=name
    self.inherited_from = inherited_from


class ReductionRuleComponent:
  """ A ReductionRuleComponent represents a rule that converts things matching the lhs pattern to the form described by the rhs
      The lhs and rhs are both lists of tokens. A token is one of the following strings:
      - "m1", "m2", etc. : These are modifier variables
      - "i1", "i2", etc. : These are ingredient variables
      - "i1:Vegetable", "i2:Water", etc. : These are ingredient variables which only match ingredients that derive from a specified base ingredient
      - a constant: The name of an ingredient variable
  """
  def __init__(self,lhs,rhs):
    self.lhs = lhs
    self.rhs = rhs

  def __str__(self):
    return ' '.join(self.lhs) + " -> " + ' '.join(self.rhs)


class ReductionRuleMixture:
  """ A ReductionRuleMixture represents a rule that combines "reactants" on the lhs and turns them into the "products" on the rhs.
      The lhs and rhs are both lists of *components*.
      A component is a list of tokens, the same tokens described in ReductionRuleComponent
  """
  def __init__(self,lhs,rhs):
    self.lhs = lhs
    self.rhs = rhs

  def __str__(self):
    lhs_str = ' + '.join('(' + ' '.join(component) + ')' for component in self.lhs)
    rhs_str = ' + '.join('(' + ' '.join(component) + ')' for component in self.rhs)
    return lhs_str + " -> " + rhs_str


def token_type(token):
  """ Return a string describing the type of the token. The types are:
      - modifier variable
      - basic ingredient variable
      - qualified ingredient variable
      - constant
  """
  if not token:
    raise Exception("token_type has been given an empty or null token")
  if token[0] == 'm' and token[1:].isnumeric():
    return "modifier variable"
  if token[0] == 'i':
    if token[1:].isnumeric():
      return "basic ingredient variable"
    if ':' in token and token_type(token.split(':')[0])=="basic ingredient variable":
      return "qualified ingredient variable"
  return "constant"
