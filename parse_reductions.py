import itertools

REDUCTIONS_FILENAME = "reductions"


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

def is_component_reduction_rule(line):
  return ("->" in line and "+" not in line) or "=" in line

def is_mixture_reduction_rule(line):
  return "->" in line and "+" in line

def parse_component_reduction_rule(line):
  """ Parse the string into a list of reduction rules and return the list """
  if "->" in line:
    return [parse_primitive_reduction_rule(line)]
  if "=" in line :
    if "+>" in line:
      return [parse_concise_reduction_rule(line)]
    if "+" in line and "+>" not in line:
      return parse_concise_symmetric_reduction_rule(line)
  raise Exception("Parse error: Could not determine the type of reduction rule used here:\n",line)

def parse_primitive_reduction_rule(line):
  """ Parse a primitive reduction rule and return the ReductionRuleComponent """
  lhs,rhs = [s.split() for s in line.split('->')]
  lhs = [t.strip() for t in lhs]
  rhs = [t.strip() for t in rhs]
  return ReductionRuleComponent(lhs,rhs)

def parse_concise_reduction_rule(line):
  """ Parse a reduction rule of the form that uses +> and return the ReductionRuleComponent """
  lhs,rhs = line.split('=')
  lhs_tokens = lhs.split('+>')
  lhs_tokens = [t.strip() for t in lhs_tokens]
  rhs = rhs.strip()
  return expand_concise_reduction_rule(lhs_tokens,rhs)

def expand_concise_reduction_rule(lhs_tokens,rhs):
  """ Return the ReductionRuleComponent obtained by interspersing the lhs_tokens with modifier variables
      and preserving those variables on the rhs.
      So for example if lhs_tokens = ["fried", "charred"] and rhs = "burnt" then we get the ReductionRuleComponent
      m1 fried m2 charred m3 i1 -> burnt m1 m2 m3 i1 
  """
  variable_numbers = [int(token[1:]) for token in lhs_tokens if token_type(token)=="modifier variable"]
  new_variable_start_index = 0 if not variable_numbers else max(variable_numbers)+1
  new_variables = ['m'+str(i) for i in range(new_variable_start_index, new_variable_start_index+len(lhs_tokens)+1 )]
  rule_lhs = [new_variables[0]]
  for i in range(len(lhs_tokens)):
    rule_lhs.append(lhs_tokens[i])
    rule_lhs.append(new_variables[i+1])
  rule_rhs = [rhs] + new_variables
  rule_lhs.append('i1')
  rule_rhs.append('i1')
  return ReductionRuleComponent(rule_lhs,rule_rhs)

def parse_concise_symmetric_reduction_rule(line):
  """ Parse a reduction rule of the form that uses + and return a LIST of ReductionRuleComponent's """
  lhs,rhs = line.split('=')
  lhs_tokens = lhs.split('+')
  lhs_tokens = [t.strip() for t in lhs_tokens]
  rhs = rhs.strip()
  return [expand_concise_reduction_rule(perm,rhs) for perm in set(itertools.permutations(lhs_tokens))]
  
def parse_mixture_reduction_rule(line):
  """ Parse the string into a ReductionRuleMixture and return it """
  lhs,rhs = line.split('->')
  lhs_components = [c.strip('() ').split() for c in lhs.split('+')]
  rhs_components = [c.strip('() ').split() for c in rhs.split('+')]
  return ReductionRuleMixture(lhs_components,rhs_components)
  


def main():
  reduction_rules_components = []
  reduction_rules_mixtures = []
  
  
  f = open(REDUCTIONS_FILENAME)
  for line in f:
    line = line.strip() # remove whitespace
    line = line.split('#')[0] # remove comments
    if not line: continue # skip blanks
    if is_component_reduction_rule(line):
      reduction_rules_components += parse_component_reduction_rule(line)
    elif is_mixture_reduction_rule(line):
      reduction_rules_mixtures.append(parse_mixture_reduction_rule(line))
  f.close()
  
  
  print("Component rules:")
  for r in reduction_rules_components:
    print(r)
  print("Mixture rules:")
  for r in reduction_rules_mixtures:
    print(r)



if __name__ == '__main__' :
  main()

