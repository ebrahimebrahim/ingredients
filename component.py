import copy
import condition_syntax_tree


class Component:
  """ Wraps a list of token strings.
      The initializer can be
      - a string representation of a token, which is space separated
      - a list of tokens
      - another Component (in which case a copy is created)
  """
  def __init__(self,init=None):
    if init is None:
      self.tokens = []
    elif isinstance(init,str):
      self.tokens = [t.strip() for t in init.split()]
    elif isinstance(init,list):
      self.tokens = init
    elif isinstance(init,Component):
      self.tokens = copy.deepcopy(init.tokens)
    else:
      raise Exception("Cannot initialize a Component with '{}', which is of type '{}'".format(init,type(init)))

  def __str__(self):
    return ' '.join(self.tokens)

  def __eq__(self,other):
    return self.tokens==other.tokens


class Token:
  'Represents a token. See TypeChecker.type_info for description of type_info tuple.'
  def __init__(self, token_str, type_info):
    self.str = token_str
    self.varness, self.category = type_info
    token_str_colon_split = token_str.split(':')
    self.name = token_str_colon_split[0]
    if self.varness == "qvar":
      self.qualifier = condition_syntax_tree.Cst(token_str_colon_split[1])

  def matches(self,const_token,type_checker):
    'Return whether this token pattern matches the |const_token|, which is a Token'
    assert(const_token.varness=='const')
    if self.category != const_token.category: return False
    if self.varness == 'uqvar' : return True
    if self.varness == 'const' : return self.name==const_token.name
    if self.varness == 'qvar' : return type_checker.const_satisfies_qualifier(const_token,self.qualifier)
    raise ValueError

  def __eq__(self,other):
    self.str==other.str


class TypeChecker:
  def __init__(self):
    raise NotImplementedError

  def type_info(self, token_str, last=False):
    """ Return a tuple describing the type of |token_str|.
    Set |last| to True if this token is the last of its Component.
    The tuple has 2 components:
    - varness, which is "const" or "uqvar" or "qvar"
      (constant, unqualified variable, or qualified variable)
    - category, which is "mod", "ingmod", "ing", or "o"
      (modifier that isn't an ingedient, ingredient being used as a modifier, ingredient as the base,
      or a variable standing for a selection from the list of tokens not involved in a match)
    """
    if not token_str:
      raise Exception("Token type checker has been given an empty or null token.")
    if token_str[0] == 'm':
      if token_str[1:].isnumeric():
        if last : raise Exception("Missing ingredient base at end of pattern")
        return "uqvar", "mod"
      elif ':' in token_str:
        try:
          a,_=token_str.split(':')
          assert(a[1:].isnumeric())
          assert(not last)
        except:
          raise Exception("Invalid token '{}'".format(token_str))
        return "qvar", "mod"
    if token_str[0] == 'i':
      if token_str[1:].isnumeric():
        return "uqvar", ("ing" if last else "ingmod")
      elif ':' in token_str:
        try:
          a,_=token_str.split(':')
          assert(a[1:].isnumeric())
        except:
          raise Exception("Invalid token '{}'".format(token_str))
        return "qvar", ("ing" if last else "ingmod")
    if token_str[0] == 'o':
      if token_str[1:].isnumeric():
        return "uqvar",'o'
      elif ':' in token_str:
        try:
          a,_=token_str.split(':')
          assert(a[1:].isnumeric())
        except:
          raise Exception("Invalid token '{}'".format(token_str))
        return "qvar", 'o'
    if self.is_ingredient(token_str):
      return "const", ("ing" if last else "ingmod")
    return "const", "mod"


  def tags_of_const(self, const_token):
    """ Given a const Token, return the list of tags that apply to it.
    If the const token is a modifier,
      then this could be the list of tags that are somehow attached to that modifier.
    If the const token is an ingredient (used as a modifier or not),
      then this could be the list of all its ancestor ingredients
    """
    raise NotImplementedError

  def const_has_tag(self, const_token, tag):
    'Return whether the token has the tag'
    return tag in self.tags_of_const(const_token)

  def parse_token(self, token_str):
    'Convert the given token string into a Token'
    return Token(token_str, self.type_info(token_str))

  def const_satisfies_qualifier(self,const_token,cst):
    'Return whether the tags that const_token has make it qualify for the condition_syntax_tree.Cst |cst|'
    tags_in_qualifier_condition = cst.symbols()
    tags_of_const_token = self.tags_of_const(const_token)
    truth_mapping = {tag:(tag in tags_of_const_token)  for tag in tags_in_qualifier_condition}
    return cst.evaluate(truth_mapping)

  def is_ingredient(self,name):
    'Return whether |name| is the name of an ingredient'
    raise NotImplementedError


# Useful for testing
class TrivialTypeChecker(TypeChecker):
  def __init__(self):
    pass

  def tags_of_const(self, const_token):
    return [const_token.name, const_token.name+"_tag"]

  def is_ingredient(self,name):
    return name in ["AnIngredient", "AnotherIngredient"]


class ComponentRuleLHS:
  """ Represents the pattern on the LHS of a component reduction rule.
  Internal structure:
  - component: a Component
  - strictness: a strictness setting for pattern matching
  - o_dict: a dict mapping qualified 'o' variables to their qualifier condition_syntax_tree.Cst
  and unqualified 'o' variables to None
  - dont_match: possibly another ComponentRuleLHS representing a pattern to *not* match in order for this ComponentRuleLHS to match
  """
  def __init__(self, lhs_string):
    split = lhs_string.split()

    self.dont_match = None
    if "!!" in split:
      sep_idx = split.index("!!")
      self.dont_match = ComponentRuleLHS(' '.join(split[(sep_idx+1):]))
      split = split[:sep_idx]

    self.o_dict = {}
    while split:
      t = split.pop(0)
      if t[0] == 'o':
        if t[1:].isnumeric():
          self.o_dict[t]=None
        elif ':' in t:
          try:
            a,b = t.split(':')
            assert(a[1:].isnumeric())
            self.o_dict[a] = condition_syntax_tree.Cst(b)
          except:
            raise Exception("Invalid token in '{}'".format(lhs_string))
        else: break
      else: break

    if t in ['&', '&&']:
      self.strictness = t
    else:
      self.strictness = ''
      split.insert(0,t)

    if not split:
      raise Exception("Invalid pattern '{}'".format(lhs_string))

    self.component = Component(split)

  def __str__(self):
    o_header = ' '.join(ovar+('' if self.o_dict[ovar] is None else ':'+self.o_dict[ovar].condition_string) for ovar in self.o_dict)
    out_parts = []
    if o_header!='': out_parts.append(o_header)
    if self.strictness!='': out_parts.append(self.strictness)
    out_parts.append(str(self.component))
    if self.dont_match:
      out_parts.append('!!')
      out_parts += self.dont_match.__str__().split()
    return ' '.join(out_parts)

  def __eq__(self,other):
    return self.component==other.component and self.strictness==other.strictness and self.o_dict==other.o_dict and self.dont_match==other.dont_match





def match_component_pattern(pattern, target, type_checker):
  """Given a ComponentRuleLHS |pattern| and given a Component |target|,
  return a match dictionary mapping the m and i variables in |pattern|
  to various constants in |target|, and mapping the o variables in |pattern|
  to lists of constants from |target|. Return None if no match.
  """

  if pattern.dont_match is not None:
    if match_component_pattern(pattern.dont_match, target, type_checker) is not None:
      return None

  parsed_pattern_tokens = []
  for i,token_str in enumerate(pattern.component.tokens):
    parsed_pattern_tokens.append(
      Token(token_str, type_checker.type_info(token_str, last=(i==len(pattern.component.tokens)-1) ) )
    )

  parsed_target_tokens = []
  for i,token_str in enumerate(target.tokens):
    parsed_target_tokens.append(
      Token(token_str, type_checker.type_info(token_str, last=(i==len(target.tokens)-1) ) )
    )

  return match_component_pattern_recurse(
    parsed_pattern_tokens,
    parsed_target_tokens,
    type_checker,
    pattern,
    True,
    {}
  )


def match_component_pattern_recurse(pattern_tokens,target_tokens,type_checker,original_lhs,search_beyond_head,partial_match):
  """
  pattern_tokens: list of Token
  target_tokens: list of Token
  type_checker: TypeChecker
  original_lhs: ComponentRuleLHS
  search_beyond_head: bool
  partial_match: dict
  """

  if len(pattern_tokens)==0:
    final_match = copy.deepcopy(partial_match)
    add_to_o_assignment(final_match, target_tokens, original_lhs.o_dict, type_checker)
    return final_match

  tp = pattern_tokens[0]
  for tti,tt in enumerate(target_tokens):
    if tp.matches(tt,type_checker):
      if tp.name not in partial_match or partial_match[tp.name]==tt.name:
        new_partial_match = partial_match
        if tp.varness != 'const':
          new_partial_match = copy.deepcopy(partial_match)
          new_partial_match.update({tp.name : tt.name})
        if original_lhs.strictness in ['&', '&&']:
          new_target_tokens = target_tokens[tti+1:]
          add_to_o_assignment(new_partial_match, target_tokens[:tti], original_lhs.o_dict, type_checker)
        else:
          new_target_tokens = copy.deepcopy(target_tokens)
          new_target_tokens.pop(tti)
        match = match_component_pattern_recurse(
          pattern_tokens[1:],
          new_target_tokens,
          type_checker,
          original_lhs,
          original_lhs.strictness!='&&',
          new_partial_match
        )
        if match is not None: return match
    if not search_beyond_head: break
  return None

def add_to_o_assignment(match_dict, const_tokens, o_dict, type_checker):
  if not o_dict:
    match_dict['o_auto'] = match_dict.get('o_auto',[]) + [tt.name for tt in const_tokens]
  else:
    for ovar,ovar_qualifier in o_dict.items():
      match_dict[ovar] = match_dict.get(ovar,[]) +\
        [tt.name for tt in const_tokens if ovar_qualifier is None or type_checker.const_satisfies_qualifier(tt,ovar_qualifier)]


class ReductionRuleComponent:
  """ A ReductionRuleComponent represents a rule that converts things matching the lhs pattern to the form described by the rhs
      The rhs_str is a string representing a Component and the lhs_str is a string representing a ComponentRuleLHS.
      type_checker is a pattern_match.TypeChecker subclass
  """
  def __init__(self, lhs_str, rhs_str, type_checker=TrivialTypeChecker()):
    self.lhs = ComponentRuleLHS(lhs_str)
    self.rhs = Component(rhs_str)
    self.type_checker = type_checker

  def __str__(self):
    return str(self.lhs) + " -> " + str(self.rhs)

  def match_lhs(self,component):
    """ Match the pattern of the lhs to the given Component, and return
    a dict representing the match. Return None if there is no match.
    It makes sense for the tokens of Component to all be constant type.
    Returns the match, which is a dict whose keys are the variables in the lhs,
    and whose values are tokens or lists of tokens selected from component.
    """
    return match_component_pattern(self.lhs,component,self.type_checker)

  def apply(self,component,debug=False):
    """ Apply the reduction rule to the given Component
        Returns a Component, the result of applying the rule to component
    """
    match = self.match_lhs(component)
    if match is None:
      return component # No match, component is already reduced wrt this rule

    out = apply_substitution_to_component(self.rhs, match, self.type_checker)

    if debug:
      print("\nRULE",self)
      print('\tTURN',component)
      print('\tINTO',out)
      print()

    return out


def apply_substitution_to_component(component, subst_dict, type_checker):
  """ Given a Component and given a subst_dict mapping variables
  in |tokens| to constants, return the component that results from carrying
  out all the substitutions. If subst_dict has an 'o_auto' then put that in no matter what."""

  parsed_tokens = []
  for i,token_str in enumerate(component.tokens):
    parsed_tokens.append(
      Token(token_str, type_checker.type_info(token_str, last=(i==len(component.tokens)-1) ) )
    )

  result_tokens = []
  if 'o_auto' in subst_dict:
    result_tokens += subst_dict['o_auto']
  for token in parsed_tokens:
    if token.category=='o':
      result_tokens += subst_dict[token.name]
    elif token.varness in ['uqvar','qvar']:
      result_tokens.append(subst_dict[token.name])
    elif token.varness=="const":
      result_tokens.append(token.name)
  return Component(result_tokens)
