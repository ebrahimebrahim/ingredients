from interactive import *
import random

icmd = IngredientsCmd()
icmd.preloop()

print("Gathering some ingredients...")

ingdts_to_use = random.sample(gettable_ingredients,int(random.normalvariate(3,1)+1))
for ing_name in ingdts_to_use:
  icmd.do_get(ing_name)
icmd.report_foods()

print("Chopping and mushing...")

for i in range(len(icmd.foods)):
  rand = random.random()
  if rand < 0.2 :
    icmd.do_chop(str(i))
  elif rand < 0.3 :
    icmd.do_chop(str(i))
    icmd.do_chop(str(i))
  elif rand < 0.6:
    icmd.do_mush(str(i))

icmd.report_foods()


print("Preparing for cooking...")

fats = [i for i in ingredients_byname if 'Fat' in ingredients_byname[i].inherited_from]
def mix(list_of_indices):
  if len(list_of_indices)==1:
    return
  icmd.do_mix(' '.join(list(map(str,list_of_indices))))
def get_and_mix_in(ing_name, index_to_mix_into):
  icmd.do_get(ing_name)
  mix([index_to_mix_into,len(icmd.foods)-1])

for i in range(len(icmd.foods)):
  rand = random.random()
  if rand < 0.3 :
    fat = random.choice(fats)
    get_and_mix_in(fat, i)
  elif rand < 0.6:
    get_and_mix_in('Water', i)
  elif rand < 0.9:
    pass # just keep it in baking mode
  else:
    icmd.do_pot(str(i))

icmd.report_foods()


print("Mixing some things...")

num_to_mix = len(icmd.foods)//2 + 1
ones_to_mix = random.sample(range(len(icmd.foods)),num_to_mix)
mix(ones_to_mix)

icmd.report_foods()

print("Cooking...")

for i in range(len(icmd.foods)):
  if random.random()<0.8:
    icmd.do_cook(str(i))

icmd.report_foods()

print("Final mix...")

mix(range(len(icmd.foods)))

icmd.report_foods()
