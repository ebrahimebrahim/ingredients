

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
      - modifier variable (for example m1, m2, ...)
      - basic ingredient variable (for example i1, i2, ...)
      - qualified ingredient variable (for example i1:Grain, i2:Vegetable, etc.)
      - constant (for example Onion, Brocolli, etc.)
      Does not sanity-check constants.
      Things that aren't among the first three are constants.
  """
  if not token:
    raise Exception("token_type has been given an empty or null token")
  if token[0] == 'm' and token[1:].isnumeric():
    return "modifier variable"
  if token[0] == 'i':
    if token[1:].isnumeric():
      return "basic ingredient variable"
  token_colon_split = token.split(':')
  if len(token_colon_split)==2:
    l,r = token_colon_split
    if token_type(l)!="basic ingredient variable":
        raise Exception("Invalid token '{}', misplaced colon.".format(token))
    if token_type(r)!="constant":
        raise Exception("Invalid token '{}', a constant must come after the colon".format(token))
    return "qualified ingredient variable"
  return "constant"
