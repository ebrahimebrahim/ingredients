import copy
from component import *
from mixture import *

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
  def __init__(self, name):
    self.name=name
    self.inherited_from = []





def apply_till_no_change(f,x,max_iterations):
  """Apply f repeatedly to x and return the result if it converges. Raise Exception otherwise."""
  old_x=copy.deepcopy(x)
  for _ in range(max_iterations):
    new_x = f(old_x)
    if new_x == old_x:
      return new_x
    old_x = new_x
  raise Exception("Timed out while reducing '{}'. Was stuck at '{}'.\n\
    \t Is there a cycle in your reduction system?".format(x,new_x))


def apply_each_rule_till_no_change(rules, x, max_iterations):
  """For each rule in rules, apply it to x until convergence.
     Here a rule just has to have an apply method,
     so it could be a component rule (in which case x must be a Component)
     or a mixture rule (in which case x must be a Mixture)"""
  y = copy.deepcopy(x)
  for rule in rules:
    y = apply_till_no_change(rule.apply,y,max_iterations)
  return y



class ReductionSystem:
  """Initialize with a list of ReductionRuleComponent and a list of ReductionRuleMixture
  """
  def __init__(self, rules):
    self.rules = rules
    self.max_iterations = 500


  def reduce_component(self, component):
    """ Repeatedly apply the component rules until component is fully reduced
        Return reduced form.
        component is a Component
    """
    component_rules_as_mixture = filter(lambda r : isinstance(r,ReductionRuleComponentAsMixture), self.rules)
    component_rules = map(lambda r : r.component_rule, component_rules_as_mixture)
    return apply_till_no_change(
      lambda c : apply_each_rule_till_no_change(component_rules,c,self.max_iterations),
      component,
      self.max_iterations
    )

  def reduce_mixture(self, mixture):
    """ First reduce all components of the mixture.
        Then repeatedly apply the mixture rules until mixture is fully reduced
        Return reduced form.
        Here component is assumed to be a Mixture.
    """
    return apply_till_no_change(
      lambda m : apply_each_rule_till_no_change(self.rules,m,self.max_iterations),
      mixture,
      self.max_iterations
    )

  def set_type_checker(self,type_checker):
    'Set the type checker for all reduction rules'
    for rule in self.rules:
      rule.set_type_checker(type_checker)
