import cmd, parse_reductions, parse_ingredients
from util import *


# Load ingredients
ingredients = parse_ingredients.parse(parse_ingredients.INGREDIENTS_DIR)
ingredients_byname = {}
for ing in ingredients:
  ingredients_byname[ing.name] = ing



# Load reduction rules
reduction_rules_component,reduction_rules_mixture = parse_reductions.parse(parse_reductions.REDUCTIONS_FILENAME)

def inheritance_check(child, parent):
  if child not in ingredients_byname:
    raise Exception("Encountered an ingredient that doesn't exist: "+child)
  return parent==child or parent in ingredients_byname[child].inherited_from

for rule in reduction_rules_component:
  rule.inheritance_check = inheritance_check
for rule in reduction_rules_mixture:
  rule.inheritance_check = inheritance_check

rs = ReductionSystem(reduction_rules_component,reduction_rules_mixture)



class Food:
  def __init__(self,mixture=Mixture(),in_container=False):
    self.mixture = mixture
    self.in_container = in_container

  def mix_in(self, other):
    self.in_container = self.in_container or other.in_container
    self.mixture.components += other.mixture.components

  def apply_action_from_attribute(self,attribute):
    for component in self.mixture.components:
      # extract base ingredient from component, asserting that it's a const
      ing_name = component.tokens[-1]
      if token_type(ing_name) != 'constant':
        raise Exception("It does not make sense to apply actions component expressions with variables: "+str(component))
      # lookup in parsed ingredients and find that ingredient's "attribute" attribute (e.g. "chop")
      if ing_name not in ingredients_byname:
        raise Exception("Ingredient does not exist: "+ing_name)
      ing = ingredients_byname[ing_name]
      if attribute not in ing.__dict__:
        raise Exception("Ingredient {} is missing attribute {}.".format(ing_name,attribute))
      actions_string = ing.__dict__[attribute]
      # split that attribute value on ';' to get a list "actions"
      actions = [a.strip() for a in actions_string.split(';')]
      for action in actions:
        print("Didn't know what to do with this action: "+action)
        # if branch on different actions like "gain_mod" and "yield", and transform component and mixture accordingly
    # reduce the mixture using reduction system made out of parsed reductions file
    self.mixture = rs.reduce_mixture(self.mixture)

  def cook(self):
    # Note that cook is a "keyword" and should never show up as an attribute name
    # similarly for "filename". Probably should add warning in ingdt parser
    # Similarly "None" should not show up as a name of an ingdt
    # It should be noted somewhere that Fat and Water are special ingdt names for the purpose of cook action
    # They, or anything that inherits from them, will be treated specially for cook
    for component in self.mixture.components:
      if not self.in_container:
        self.apply_action_from_attribute("cook_flame")
      elif any(inheritance_check(component.tokens[-1],"Water") for component in self.mixture.components):
        self.apply_action_from_attribute("cook_boil")
      elif any(inheritance_check(component.tokens[-1],"Fat") for component in self.mixture.components):
        self.apply_action_from_attribute("cook_fry")
      else:
        self.apply_action_from_attribute("cook_bake")

  def __str__(self):
    pot_str = "Pot containing " if self.in_container else ""
    return pot_str+str(self.mixture)



class IngredientsCmd(cmd.Cmd):
  intro = 'Type ? to list commands.\n'
  prompt = 'ingdts> '

  def preloop(self):
    self.foods = []

  def do_chop(self, arg):
    'Chop the food of the indicated index in the list : chop 3'
    if not self.validate_foods_index(arg): return
    self.foods[int(arg)].apply_action_from_attribute('chop')

  def do_cook(self, arg):
    'Cook the food of the indicated index in the list : cook 2'
    if not self.validate_foods_index(arg): return
    self.foods[int(arg)].cook()

  def do_get(self, arg):
    'Grab an ingredient : get Onion'
    if arg not in ingredients_byname:
      print("Not an ingredient. Possible ingredients: "+', '.join(ing.name for ing in ingredients))
      return
    self.foods.append(Food(Mixture(arg)))

  def help_get(self):
    print('Grab an ingredient : get Onion\nPossible ingredients: '+', '.join(ing.name for ing in ingredients))

  def do_mix(self,arg):
    'Mix two foods of the indicated indices in the list: mix 2 3'
    try:
      i_str,j_str=arg.split()
      i,j = int(i_str), int(j_str)
      assert(i>=0 and j>=0 and i<len(self.foods) and j<len(self.foods) and i!=j)
    except:
      print("Error: arguments should be two distinct valid indices of food items from the list.")
      return
    self.foods[i].mix_in(self.foods[j])
    self.foods.pop(j)

  def do_pot(self, arg):
    'Put the indicated food into a pot or remove it if it is already: pot 2'
    if not self.validate_foods_index(arg): return
    self.foods[int(arg)].in_container = not self.foods[int(arg)].in_container

  def do_quit(self, arg):
    'Quit:  quit'
    print('peupe.')
    return True

  def do_EOF(self, arg):
    'Quit (press ctrl+D)'
    print('peup.')
    return True

  def validate_foods_index(self,i_str):
    'Should be True iff self.foods[int(arg)] wont blow up'
    out = i_str.isnumeric() and int(i_str) >= 0 and int(i_str) < len(self.foods)
    if not out:
      print("Error: argument should be the number of a food item from the displayed list of foods.")
    return out

  def report_foods(self):
    print()
    if not self.foods:
      print("[No foods]")
    for i,food in enumerate(self.foods):
      print("\t{}: {}".format(i,str(food)))
    print()

  def postcmd(self,stop,line):
    if not stop:
      self.report_foods()
    return stop



if __name__ == '__main__':
    IngredientsCmd().cmdloop()
