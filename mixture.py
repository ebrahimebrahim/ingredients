import copy
from component import *


class Mixture:
  """ Wraps a list of components.
  The initializer can be
  - a string representation of a token, which is a '+' separated list of parenthesized
  (string-represented) components
  - a list of Components
  - another Mixture (in which case a copy is created)
  """
  def __init__(self,init=None):
    if init is None:
      self.components = []
    elif isinstance(init,str):
      self.components = [Component(c.strip('() ')) for c in init.split('+')]
    elif isinstance(init,list):
      self.components = init
    elif isinstance(init,Mixture):
      self.components = copy.deepcopy(init.components)
    else:
      raise Exception("Cannot initialize a Mixture with '{}', which is of type '{}'".format(init,type(init)))

  def __str__(self):
    return ' + '.join('(' + str(component) + ')' for component in self.components)

  def __eq__(self,other):
    return self.components==other.components



class MixtureRuleLHS:
  """ Wraps a list of ComponentRuleLHS
  """
  def __init__(self,init):
    self.components = [ComponentRuleLHS(c.strip('() ')) for c in init.split('+')]

  def __str__(self):
    return ' + '.join('(' + str(component) + ')' for component in self.components)

  def __eq__(self,other):
    return self.components==other.components



class ReductionRuleMixture:
  """ A ReductionRuleMixture represents a rule that combines "reactants" on the lhs and turns them into the "products" on the rhs.
      The lhs_str is a string representing a MixtureRuleLHS and the rhs_str is a string representing a Mixture.
      type_checker is a subclass of TypeChecker
  """
  def __init__(self,lhs_str,rhs_str, type_checker=TrivialTypeChecker()):
    self.lhs = MixtureRuleLHS(lhs_str)
    self.rhs = Mixture(rhs_str)
    self.type_checker = type_checker

  def __str__(self):
    return str(self.lhs) + " -> " + str(self.rhs)

  def match_lhs(self,mixture):
    """ Match the lhs pattern to the given Mixture.
        Return None or a pair as described in match_mixture_pattern
    """
    return match_mixture_pattern(self.lhs.components,mixture.components,self.type_checker)

  def apply(self,mixture,debug=False):
    """ Apply the reduction rule to the given Mixture
        Return the resulting Mixture
    """
    match_result = self.match_lhs(mixture)

    if match_result is None:
      return mixture # No match, mixture is already reduced wrt this rule

    match_dict, remaining_components = match_result
    out = Mixture([apply_substitution_to_component(c, match_dict,self.type_checker) for c in self.rhs.components] + remaining_components)

    if debug:
      print("\nRULE",self)
      print('\tTURN',mixture)
      print('\tINTO',out)

    return out

  def set_type_checker(self,type_checker):
    self.type_checker = type_checker


class ReductionRuleComponentAsMixture:
  'Just wraps a ReductionRuleComponent, but has an apply method operates on mixtures'
  def __init__(self, component_rule):
    self.component_rule = component_rule

  def apply(self,mixture,debug=False):
    return Mixture([self.component_rule.apply(c,debug) for c in mixture.components])

  def set_type_checker(self, type_checker):
    self.component_rule.type_checker = type_checker

  def __str__(self):
    return str(self.component_rule)


def match_mixture_pattern(pattern_components,components,type_checker,partial_match={}):
  """
  pattern_components is a list of ComponentRuleLHS, probably consisting of some variables
  components is a list of Components, probably consisnting of only constants
  type_checker is a TypeChecker
  partial_match helps with recursion, ignore for normal usage
  Returns None if there is no match. If there is a match then it returns a pair consisting of:
  (1) a dict mapping modifier and ingredient variables to the constants showing up in components
  (2) a list of components that were not involved in the match
  """
  if not pattern_components:
    return partial_match,components
  for pattern_component in pattern_components:
    for component in components:
      component_match = match_component_pattern(pattern_component,component,type_checker)
      if component_match is not None:
        if 'o_auto' in component_match:
          raise Exception("Encountered component with a missing 'o' variable in mixture pattern "+str(pattern_component))
        if all(k not in partial_match or component_match[k]==partial_match[k] for k in component_match):
          pattern_components_reduced = copy.deepcopy(pattern_components)
          pattern_components_reduced.remove(pattern_component)
          components_reduced = copy.deepcopy(components)
          components_reduced.remove(component)
          partial_match_extended = copy.deepcopy(partial_match)
          partial_match_extended.update(component_match)
          match = match_mixture_pattern(pattern_components_reduced,components_reduced,type_checker,partial_match = partial_match_extended)
          if match is not None:
            return match
  return None
