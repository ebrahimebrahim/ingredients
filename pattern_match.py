from util import Component
import copy

class Token:
  'Represents a token. See TypeChecker.type_info for description of type_info tuple.'
  def __init__(self, token_str, type_info):
    self.str = token_str
    self.varness, self.category = type_info
    token_str_colon_split = token_str.split(':')
    self.name = token_str_colon_split[0]
    if self.varness == "qvar":
      self.qualifiers = token_str_colon_split[1].split(',')

  def matches(self,const_token,type_checker):
    'Return whether this token pattern matches the |const_token|, which is a Token'
    assert(const_token.varness=='const')
    if self.category != const_token.category: return False
    if self.varness == 'uqvar' : return True
    if self.varness == 'const' : return self.name==const_token.name
    if self.varness == 'qvar' : return type_checker.const_satisfies_qualifiers(const_token,self.qualifiers)
    raise ValueError


class TypeChecker:
  def __init__(self):
    raise NotImplementedError

  def type_info(self, token_str, last=False):
    """ Return a tuple describing the type of |token_str|.
    Set |last| to True if this token is the last of its Component.
    The tuple has 2 components:
    - varness, which is "const" or "uqvar" or "qvar"
      (constant, unqualified variable, or qualified variable)
    - category, which is "mod", "ingmod", or "ing"
      (modifier that isn't an ingedient, ingredient being used as a modifier, or ingredient as the base)
    """
    if not token_str:
      raise Exception("Token type checker has been given an empty or null token.")
    elif token_str[0] == 'm':
      if token_str[1:].isnumeric():
        if last : raise Exception("Missing ingredient base at end of pattern")
        return "uqvar", "mod"
      elif ':' in token_str:
        try:
          a,b=token_str.split(':')
          assert(a[1:].isnumeric())
          assert(not last)
        except:
          raise Exception("Invalid token '{}'".format(token_str))
        return "qvar", "mod"
    elif token_str[0] == 'i':
      if token_str[1:].isnumeric():
        return "uqvar", ("ing" if last else "ingmod")
      elif ':' in token_str:
        try:
          a,b=token_str.split(':')
          assert(a[1:].isnumeric())
        except:
          raise Exception("Invalid token '{}'".format(token_str))
        return "qvar", ("ing" if last else "ingmod")
    elif self.is_ingredient(token_str):
      return "const", ("ing" if last else "ingmod")
    else:
      return "const", "mod"


  def tags_of_const(self, const_token):
    """ Given a const Token, return the list of tags that apply to it.
    If the const token is a modifier,
      then this could be the list of tags that are somehow attached to that modifier.
    If the const token is an ingredient (used as a modifier or not),
      then this could be the list of all its ancestor ingredients
    """
    raise NotImplementedError

  def const_satisfies_qualifiers(self,const_token,qualifiers_list):
    'Return whether any of the tags that const_token has are in qualifiers_list'
    return any(tag in qualifiers_list for tag in self.tags_of_const(const_token))

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
    return name=="AnIngredient"


class ComponentRuleLHS:
  """ Represents the pattern on the LHS of a component reduction rule.
  Internal structure:
  - component: a Component
  - strictness: a strictness setting for pattern matching
  - o_dict: a dict mapping qualified 'o' variables to their list of associated tags
  and unqualified 'o' variables to None
  """
  def __init__(self, lhs_string):
    self.o_dict = {}
    split = lhs_string.split()
    while split:
      t = split.pop(0)
      if t[0] == 'o':
        if t[1:].isnumeric():
          self.o_dict[t]=None
        elif ':' in t:
          try:
            a,b = t.split(':')
            assert(a[1:].isnumeric())
            self.o_dict[a] = b.split(',')
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
    o_header = ' '.join(ovar+('' if self.o_dict[ovar] is None else ':'+','.join(self.o_dict[ovar])) for ovar in self.o_dict)
    out_parts = []
    if o_header!='': out_parts.append(o_header)
    if self.strictness!='': out_parts.append(self.strictness)
    out_parts.append(str(self.component))
    return ' '.join(out_parts)





def match_component_pattern(pattern, target, type_checker):
  """Given a ComponentRuleLHS |pattern| and given a Component |target|,
  return a match dictionary mapping the m and i variables in |pattern|
  to various constants in |target|, and mapping the o variables in |pattern|
  to lists of constants from |target|.
  """
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
    match_dict['o0'] = match_dict.get('o0',[]) + [tt.name for tt in const_tokens]
  else:
    for ovar,ovar_qualifiers in o_dict.items():
      match_dict[ovar] = match_dict.get(ovar,[]) +\
        [tt.name for tt in const_tokens if ovar_qualifiers is None or type_checker.const_satisfies_qualifiers(tt,ovar_qualifiers)]
