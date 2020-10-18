import os

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

required_attributes = ["name", "abstract", "inherit"]
for ing in ingredient_dicts:
  for a in required_attributes:
    if a not in ing:
      raise Exception("Ingredient in {} is missing the required attribute '{}'".format(ing['filepath'],a))
