import copy

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
    return ' '.join(apply_substitution_to_component(self.rhs,match))


def apply_substitution_to_component(component, subst_dict):
  """ Given a component as a list of tokens, and given a subst_dict mapping variables
  in that component to constants, return a version of component with all the substitutions
  have been carried out. """
  result = []
  for token in component:
    if token_type(token) in ["modifier variable","basic ingredient variable"]:
      if not subst_dict[token]: # If it's an empty list
        continue
      result += subst_dict[token]
    elif token_type(token)=="qualified ingredient variable":
      ivar = token.split(':')[0]
      result += subst_dict[ivar]
    elif token_type(token)=="constant":
      result.append(token)
  return result



def match_pattern(pattern,component,inheritance_check):
  """ Match the pattern to the component, and return the match dict.
  component is a list of tokens, which are strings
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


class Mixture:
  """ Wraps a list of components.
      A component is a list of tokens, the same tokens described in ReductionRuleComponent
  """
  def __init__(self,string=None):
    if string is None:
      self.components = []
    else:
      self.components = [c.strip('() ').split() for c in string.split('+')]


  def __str__(self):
    return ' + '.join('(' + ' '.join(component) + ')' for component in self.components)


class ReductionRuleMixture:
  """ A ReductionRuleMixture represents a rule that combines "reactants" on the lhs and turns them into the "products" on the rhs.
      The lhs and rhs are both Mixtures.
      inheritance_check is the function that will be used to match qualified ingredient variables,
        see ReductionRuleComponent for more on that
  """
  def __init__(self,lhs,rhs, inheritance_check = lambda child,parent : True):
    self.lhs = lhs
    self.rhs = rhs
    self.inheritance_check = inheritance_check

  def __str__(self):
    return str(self.lhs) + " -> " + str(self.rhs)

  def match_lhs(self,mixture):
    """ Match the lhs pattern to the given Mixture.
        Return a dict representing the match; the dict maps
        modifier and ingredient variables in the lhs to lists of
        modifiers and ingredient elements selected from the given Mixture
    """
    return match_mixture_pattern(self.lhs.components,mixture.components,self.inheritance_check)


  def apply(self,mixture):
    """ Apply the reduction rule to the given Mixture
        Return the resulting Mixture
    """
    match = self.match_lhs(mixture)
    if match is None:
      return mixture # No match, mixture is already reduced wrt this rule
    result = Mixture()
    result.components = [apply_substitution_to_component(c, match) for c in self.rhs.components]
    return result



def match_mixture_pattern(pattern_components,components,inheritance_check,partial_match={}):
  """
  pattern_components is a list of components, each of which is a list of tokens probably
  consisting of modifier and ingredient variables
  components is a list of components, each of which is a list of tokens that are probably all constants
  inheritance_check is the same parameter showing up in match_pattern
  partial_match helps with recursion, ignore for normal usage
  Returns a dict mapping modifier and ingredient variables to the constants showing up in components
  This CAN handle repeated variables, but not if they are repeated within the same component
  (Because match_pattern cannot handle repeated variables within a component)
  """
  if not pattern_components:
    return partial_match
  for pattern_component in pattern_components:
    for component in components:
      component_match = match_pattern(pattern_component,component,inheritance_check)
      if component_match is not None:
        if all(k not in partial_match or component_match[k]==partial_match[k] for k in component_match):
          pattern_components_reduced = copy.deepcopy(pattern_components)
          pattern_components_reduced.remove(pattern_component)
          components_reduced = copy.deepcopy(components)
          components_reduced.remove(component)
          partial_match_extended = copy.deepcopy(partial_match)
          partial_match_extended.update(component_match)
          match = match_mixture_pattern(pattern_components_reduced,components_reduced,inheritance_check,partial_match = partial_match_extended)
          if match is not None:
            return match
  return None



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


class ReductionSystem:
  """Initialize with a list of ReductionRuleComponent and a list of ReductionRuleMixture
  """
  def __init__(self, component_rules, mixture_rules):
    self.component_rules = component_rules
    self.mixture_rules = mixture_rules
    self.max_iterations = 1000

  def reduce_component(self, component):
    """ Repeatedly apply the component rules until component is fully reduced
        Return reduced form.
        Here component is assumed to be a string of space separated tokens
    """
    result = component
    for i in range(self.max_iterations):
      old_result = result
      for rule in self.component_rules:
        result = rule.apply(result)
      if old_result == result:
        return result
    raise Exception("Timed out while reducing the component '{}'. Was stuck at '{}'.\n\
      \t Is there a cycle in your reduction system?".format(component,result))

  def reduce_mixture(self, mixture):
    """ First reduce all components of the mixture.
        Then repeatedly apply the mixture rules until mixture is fully reduced
        Return reduced form.
        Here component is assumed to be a Mixture.
    """
    result = [self.reduce_component(' '.join(c)).split() for c in mixture.components]

    for i in range(self.max_iterations):
      old_result = copy.deepcopy(result)
      for rule in self.mixture_rules:
        m = Mixture()
        m.components = result
        result = rule.apply(m).components
      if old_result == result:
        m = Mixture()
        m.components = result
        return m
    raise Exception("Timed out while reducing the mixture '{}'. Was stuck at '{}'.\n\
      \t Is there a cycle in your reduction system?".format(mixture,result))
