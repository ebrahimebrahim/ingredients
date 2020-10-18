import os,sys

INGREDIENTS_DIR = "ingredient_data"


# Read all the ingredients into a list of dicts
ingredient_dicts = []
for filename in os.listdir(INGREDIENTS_DIR):
  path = os.path.join(INGREDIENTS_DIR, filename)
  if not os.path.isfile(path): continue
  f = open(path)
  ingredient_dict = {"filepath":path}
  for line in f:
    line = line.strip() # remove whitespace
    line = line.split('#')[0] # remove comments
    if not line: continue # skip blanks
    try:
      k,v = line.split(':')
    except:
      raise Exception("Unable to parse the following line in {}:\n\t{}".format(path,line))
    k=k.strip()
    v=v.strip()
    ingredient_dict[k]=v
  ingredient_dicts.append(ingredient_dict)
  f.close()


# These attributes, along with filepath, are treated specially to help with parsing
required_attributes = ["name", "abstract", "inherit"]
for ing in ingredient_dicts:
  for a in required_attributes:
    if a not in ing:
      raise Exception("Ingredient in {} is missing the required attribute '{}'".format(ing['filepath'],a))

# Further validation and warnings
for ing in ingredient_dicts:
  if ing["abstract"] not in ["True", "False"]:
    raise Exception("Ingredient in {} has invalid value for attribute 'abstract'".format(ing['filepath']))
  if ing["name"] != os.path.basename(ing['filepath']):
    print("Warning: Ingredient in {} has name '{}' that does not match the filename. Was this intentional?".format(ing['filepath'],ing['name']), file=sys.stderr)


# Dict for to lookup ingredients by ingredient name
ingredient_dicts_byname = {}
for ing in ingredient_dicts:
  ingredient_dicts_byname[ing["name"]] = ing


# Gather all attributes, besides the ones needed for parsing, to help warn about missing attributes later
# This is also the collection of attributes that can be inherited
# A good way to think of it is that these are the non "header" attributes
attributes = set()
for ing in ingredient_dicts:
  attributes.update(ing.keys())
attributes.difference_update(["filepath"]+required_attributes)


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


def parse_inherit_list(s):
  """ Given a string s of the "inherit" value, parse it into a list of names and return the list
      If s is '' or 'None' then we return empty list (I sure hope we never make an abstact ingredient called 'None', lol)
  """
  if s.strip() in ['','None']:
    return []
  return [name.strip() for name in s.split(',')]


ingredients = []  # List of Ingredient objects
for ing_dict in ingredient_dicts:
  if ing_dict["abstract"]=="True": continue # We don't make entries for abstract ingredients

  inherit_list = parse_inherit_list(ing_dict["inherit"])

  ing = Ingredient(ing_dict["name"],inherit_list) # Ingredient to be constructed and appended to ingredients list
  
  # Load in attributes from parents in order
  for name in inherit_list:
    if name not in ingredient_dicts_byname:
      raise Exception("Ingredient in {} inherits nonexistent ingredient named {}".format(ing_dict["filepath"],name))
    parent = ingredient_dicts_byname[name]
    for a in parent:
      if a in attributes:
        ing.__dict__[a]=parent[a]
  
  # Load in own attributes
  for a in ing_dict:
    if a in attributes:
      ing.__dict__[a]=ing_dict[a]

  # Warn about seemingly missing attributes
  for a in attributes:
    if a not in ing.__dict__:
      print("Warning: Attribute {} is never defined in the ingredient {}".format(a,ing.name),file=sys.stderr)

  ingredients.append(ing)



