

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
      inheritance_check is the function that will be used to match qualified ingredient variables
      when applying the reduction rule to components.
      So for example the pattern i1:Vegetable will match the component Onion only if
      inheritance_check(Onion,Vegetable) is True
  """
  def __init__(self, lhs, rhs, inheritance_check = lambda child,parent : True):
    self.lhs = lhs
    self.rhs = rhs
    self.inheritance_check = inheritance_check

  def __str__(self):
    return ' '.join(self.lhs) + " -> " + ' '.join(self.rhs)

  def match_lhs(self,component):
    """ Match the pattern of the lhs to the given component, and return
    a dict representing the match. Return None if there is no match.
    The given component is assumed to be a list of strings that are
    "constant" tokens. (Remember, a component is an ingredient with a bunch of modifiers in front)
    Returns the match, which is a dict whose keys are the variables in the lhs of this recursion,
    and whose values are lists of elements of component.
    """
    return match_pattern(self.lhs,component,self.inheritance_check)

  def apply(self,component):
    """ Apply the reduction rule to the given component
        component is a string (a bunch of modifiers and then an ingredient, separated by spaces)
        Returns the result of applying the rule to component
    """
    match = self.match_lhs(component.split())
    if match is None:
      return component # No match, component is already reduced wrt this rule
    result = []
    for token in self.rhs:
      if token_type(token) in ["modifier variable","basic ingredient variable"]:
        if not match[token]: # If it's an empty list
          continue
        result.append(' '.join(match[token]))
      elif token_type(token)=="qualified ingredient variable":
        ivar = token.split(':')[0]
        result.append(' '.join(match[ivar]))
      elif token_type(token)=="constant":
        result.append(token)
    return ' '.join(result)



def match_pattern(pattern,component,inheritance_check):
  """ Match the pattern to the component, and return the match dict.
  Returns None if there is no match.
  See the docstring on ReductionRuleComponent.match_lhs
  """
  if not pattern:
    return None if component else {}
  fst = pattern[0]
  if token_type(fst)=="modifier variable":
    for i in range(len(component)+1): # For each initial segment component[:i]
      result = match_pattern(pattern[1:],component[i:],inheritance_check)
      if result is not None:
        result[fst] = component[:i]
        return result
    return None
  if token_type(fst)=="constant":
    if not component:
      return None
    if fst == component[0]:
      return match_pattern(pattern[1:],component[1:],inheritance_check)
    return None
  if token_type(fst)=="basic ingredient variable":
    if len(pattern)!=1:
      raise Exception("Encountered a pattern with an ingredient variable in the middle of it")
    if len(component)!=1:
      return None
    return {fst:[component[0]]}
  if token_type(fst)=="qualified ingredient variable":
    if len(pattern)!=1:
      raise Exception("match_pattern: Encountered a pattern with an ingredient variable in the middle of it")
    if len(component)!=1:
      return None
    ivar,parent = fst.split(":")
    if inheritance_check(component[0],parent):
      return {ivar:[component[0]]}
    return None
  raise Exception("match_pattern: Encountered an invalid pattern:",pattern)



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
