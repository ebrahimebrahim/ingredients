import itertools
from component import ReductionRuleComponent
from mixture import ReductionRuleMixture

REDUCTIONS_FILENAME = "reductions"



def is_component_reduction_rule(line):
  return "->" in line and "+" not in line

def is_mixture_reduction_rule(line):
  return "->" in line and "+" in line

def is_modifier_tag_definition(line):
  return ':' in line and '->' not in line

def parse_component_reduction_rule(line):
  """ Parse the string into a component reduction rule and return it """
  lhs,rhs = line.split('->')
  return ReductionRuleComponent(lhs, rhs)

def parse_mixture_reduction_rule(line):
  """ Parse the string into a ReductionRuleMixture and return it """
  lhs,rhs = line.split('->')
  return ReductionRuleMixture(lhs,rhs)

def update_modifier_tags(modifier_tags,line):
  'Parse modifier tags definition in |line| and update modifier_tags dict'
  try:
    tag_name,modifiers = line.split(':')
  except:
    raise Exception("Unable to parse modifier tage definition:",line)
  modifiers_list = [m.strip() for m in modifiers.split(',')]
  for modifier in modifiers_list:
    if modifier in modifier_tags:
      modifier_tags[modifier].append(tag_name)
    else:
      modifier_tags[modifier] = [tag_name]




def parse(filepath):
  """ Parse the reduction rules in filepath and return a three things:
      the list of ReductionRuleComponent,
      the list of ReductionRuleMixture,
      and the dict of modifier tags
  """
  reduction_rules_components = []
  reduction_rules_mixtures = []
  modifier_tags = {}


  f = open(REDUCTIONS_FILENAME)
  for line in f:
    line = line.strip() # remove whitespace
    line = line.split('#')[0] # remove comments
    if not line: continue # skip blanks
    if is_component_reduction_rule(line):
      reduction_rules_components.append(parse_component_reduction_rule(line))
    elif is_mixture_reduction_rule(line):
      reduction_rules_mixtures.append(parse_mixture_reduction_rule(line))
    elif is_modifier_tag_definition(line):
      update_modifier_tags(modifier_tags,line)
    else:
      raise Exception("Unable to parse line:",line)
  f.close()

  return reduction_rules_components, reduction_rules_mixtures,modifier_tags


def main():
  reduction_rules_components, reduction_rules_mixtures, modifier_tags = parse(REDUCTIONS_FILENAME)

  print("\nComponent rules:")
  for r in reduction_rules_components:
    print(r)

  print("\nMixture rules:")
  for r in reduction_rules_mixtures:
    print(r)

  print("\nModifier tags:")
  for mod,tags in modifier_tags.items():
    print(mod,':',tags)




if __name__ == '__main__' :
  main()
