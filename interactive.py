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
    self.marked_for_deletion = False

  def reduce(self):
    self.mixture = rs.reduce_mixture(self.mixture)

  def mix_in(self, other):
    self.in_container = self.in_container or other.in_container
    self.mixture.components += other.mixture.components
    self.reduce()

  def remove_component(self,component):
    self.mixture.components.remove(component)
    if not self.mixture.components:
      self.marked_for_deletion = True

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
        # condition on different actions like "gain_mod" and "yield", and transform component and mixture accordingly
        args = action.split()
        if not args or args[0]=='nothing':
          print("Nothing happens when you {} {}".format(attribute,ing_name))
        elif args[0]=='gain_mod':
          if len(args)!=2:
            print("Invalid arguments in action:",action)
          else:
            component.tokens.insert(0,args[1])
        elif args[0]=='delete':
          if len(args)!=1:
            print("Invalid arguments in action:",action)
          else:
            self.remove_component(component)
        elif args[0]=='yield':
          if len(args)<2:
            print("Invalid arguments in action:",action)
          else:
            new_component_tokens = [t if t!='SELF' else ing_name for t in args[1:]]
            new_ing_name = new_component_tokens[-1]
            if new_ing_name not in ingredients_byname:
              print("Warning: a yield action from {} has produced an ingredient {} that does not exist.\
                This is probaly bad.".format(ing_name,new_ing_name))
            self.mixture.components.append(Component(new_component_tokens))
        else:
          print("Didn't know what to do with this action: "+action)
    # reduce the mixture using reduction system made out of parsed reductions file
    self.reduce()

  def cook(self):
    # Note that cook is a "keyword" and should never show up as an attribute name
    # similarly for "filename". Probably should add warning in ingdt parser
    # Similarly "None" should not show up as a name of an ingdt
    # It should be noted somewhere that Fat and Water are special ingdt names for the purpose of cook action
    # They, or anything that inherits from them, will be treated specially for cook
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
  file = None

  def preloop(self):
    self.foods = []

  def do_chop(self, arg):
    'Chop the food of the indicated index in the list : chop 3'
    if not self.validate_foods_index(arg): return
    self.foods[int(arg)].apply_action_from_attribute('chop')

  def do_press(self, arg):
    'Press the food of the indicated index in the list : press 3'
    if not self.validate_foods_index(arg): return
    self.foods[int(arg)].apply_action_from_attribute('press')

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
    'Mix foods of the indicated indices in the list: mix 2 3 5'
    try:
      indices = list(set(int(index_str) for index_str in arg.split()))
      assert(len(indices)>1)
      for i in indices:
        assert(i>=0 and i<len(self.foods))
    except:
      print("Error: arguments should be at least two distinct valid indices of food items from the list.")
      return
    i = indices.pop(0)
    for j in indices:
      self.foods[i].mix_in(self.foods[j])
    self.foods = [self.foods[k] for k in range(len(self.foods)) if k not in indices]

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
      print("\t[No foods]")
    for i,food in enumerate(self.foods):
      print("\t{}: {}".format(i,str(food)))
    print()

  def postcmd(self,stop,line):
    if not stop:
      for food in self.foods:
        if food.marked_for_deletion:
          self.foods.remove(food)
      self.report_foods()
    return stop

  def complete_get(self, text, line, begidx, endidx):
    return [ing.name for ing in ingredients]


    # ----- record and playback ----- (Copied from the example in the docs)
  def do_record(self, arg):
    'Save future commands to filename:  record cake.recipe'
    self.file = open(arg, 'w')
  def do_playback(self, arg):
    'Playback commands from a file:  playback cake.recipe'
    self.close()
    with open(arg) as f:
      self.cmdqueue.extend(f.read().splitlines())
  def precmd(self, line):
    if self.file and 'playback' not in line:
      print(line, file=self.file)
    return line
  def close(self):
    if self.file:
      self.file.close()
      self.file = None



if __name__ == '__main__':
    IngredientsCmd().cmdloop()
