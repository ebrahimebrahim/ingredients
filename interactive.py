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
    self.food = Food(Mixture("Onion"))
    self.report_food()

  def do_chop(self, arg):
    'Chop the food : chop'
    self.food.apply_action_from_attribute('chop')
    self.report_food()
  def do_cook(self, arg):
    'Cook the food : cook'
    self.food.cook()
    self.report_food()
  def do_quit(self, arg):
    'Quit:  quit'
    print('peupe.')
    return True
  def do_EOF(self, arg):
    'Quit (press ctrl+D)'
    print('peup.')
    return True

  def report_food(self):
    print()
    print('\t'+str(self.food))
    print()



if __name__ == '__main__':
    IngredientsCmd().cmdloop()
