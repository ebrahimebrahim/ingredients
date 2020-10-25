import unittest
import parse_reductions
from util import Ingredient,ReductionSystem
from component import *
from mixture import *


class TestComponentRuleLHS(unittest.TestCase):

  def test_parsing(self):
    lhs_strings = [
      "Onion",
      "salty Onion",
      "& salty Onion",
      "&& salty Onion",
      "o1 && salty Onion",
      "o1 o2 o3 && salty Onion",
      "o1:a,b o2:a,b,c o3 o4:a & salty Onion"
      "o1 salty Onion",
      "o1 o2 o3 salty Onion",
      "o1:a,b o2:a,b,c o3 o4:a salty Onion"
    ]
    for lhs_string in lhs_strings:
      p = ComponentRuleLHS(lhs_string)
      self.assertEqual(lhs_string,str(p))


class TestTypeChecker(unittest.TestCase):

  def test_typeinfo(self):
    type_checker = TrivialTypeChecker()
    examples_not_last = {
      "i1" : ('uqvar','ingmod'),
      "i349" : ('uqvar','ingmod'),
      "i24:AnIngredient" : ('qvar','ingmod'),
      "m24:salty" : ('qvar','mod'),
      "m24" : ('uqvar','mod'),
      "AnIngredient" : ('const','ingmod'),
      "salty" : ('const','mod'),
    }
    for token in examples_not_last:
      self.assertEqual(examples_not_last[token] , type_checker.type_info(token))

    examples_last = {
      "i1" : ('uqvar','ing'),
      "i349" : ('uqvar','ing'),
      "i24:AnIngredient" : ('qvar','ing'),
      "AnIngredient" : ('const','ing'),
      "salty" : ('const','mod'),
    }
    for token in examples_last:
      self.assertEqual(examples_last[token] , type_checker.type_info(token,last=True))


class TestPatternMatch(unittest.TestCase):

  def test_match_component_pattern(self):
    type_checker = TrivialTypeChecker()

    # pattern, target, expected match
    examples = [
      ("m1 i1", "salty AnIngredient",
          {'m1': 'salty', 'i1': 'AnIngredient', 'o_auto': []} ),
      ("m1 i1:AnIngredient_tag", "salty AnIngredient",
          {'m1': 'salty', 'i1': 'AnIngredient', 'o_auto': []} ),
      ("m1:salty_tag i1", "soggy salty crappy AnIngredient",
          {'m1': 'salty', 'i1': 'AnIngredient', 'o_auto': ['soggy','crappy']} ),
      ("o3 m1:salty_tag i1", "soggy salty crappy AnIngredient",
          {'m1': 'salty', 'i1': 'AnIngredient', 'o3': ['soggy','crappy']} ),
      ("& m1:salty_tag i1", "soggy salty crappy AnIngredient",
          {'m1': 'salty', 'i1': 'AnIngredient', 'o_auto': ['soggy','crappy']} ),
      ("&& m1:salty_tag i1", "soggy salty crappy AnIngredient",
          None ),
      ("&& m1 i1", "soggy salty crappy AnIngredient",
          {'m1':'crappy' , 'i1': 'AnIngredient', 'o_auto': ['soggy','salty']} ),
      ("o5:salty_tag && m1 i1", "soggy salty crappy AnIngredient",
          {'m1':'crappy' , 'i1': 'AnIngredient', 'o5': ['salty']} ),
      ("o5:salty_tag && m1 m1 i1", "soggy salty crappy AnIngredient",
          None ),
      ("o5 && m1 m1 i1", "soggy salty salty AnIngredient",
          {'m1':'salty' , 'i1': 'AnIngredient', 'o5': ['soggy']} ),
      ("o5 && m1 m2 m1 i1", "soggy salty salty AnIngredient",
          None ),
      ("o5 m1 m2 m1 i1", "soggy salty salty AnIngredient",
          {'m1':'salty' , 'm2':'soggy', 'i1': 'AnIngredient', 'o5': []} ),
      ("o5 & soggy salty i1", "soggy salty salty AnIngredient",
          {'i1': 'AnIngredient', 'o5': ['salty']} ),
      ("o5 & salty soggy i1", "soggy salty salty AnIngredient",
          None ),
      ("o5 & salty soggy i1 !! neupy", "salty soggy peupy AnIngredient",
          {'i1':'AnIngredient', 'o5':['peupy']} ),
      ("o5 & salty soggy i1 !! peupy", "salty soggy peupy AnIngredient",
          None ),
    ]
    for pattern, target, expected in examples:
      match = match_component_pattern(
        ComponentRuleLHS(pattern),
        Component(target),
        type_checker
      )
      self.assertEqual(expected,match)




class TestReductionRuleComponent(unittest.TestCase):

  def setUp(self):
    self.rrc = ReductionRuleComponent('o1 & fried chopped AnIngredient','o1 Fries')
    self.component = Component("dirty zesty fried salty chopped AnIngredient")
    self.reduced_component = Component("dirty zesty salty Fries")

  def test_string_conversion(self):
    self.assertEqual(str(self.rrc), 'o1 & fried chopped AnIngredient -> o1 Fries')

  def test_apply(self):
    self.assertEqual(str(self.reduced_component), str(self.rrc.apply(self.component)))



class TestReductionRuleMixture(unittest.TestCase):

  def setUp(self):
    self.rrm = ReductionRuleMixture("(o1 AnIngredient) + (o2 powdered i7:AnotherIngredient_tag)","o1 o2 i7 Dough")

  def test_string_conversion(self):
    self.assertEqual("(o1 AnIngredient) + (o2 powdered i7:AnotherIngredient_tag) -> (o1 o2 i7 Dough)",str(self.rrm))

  def test_apply(self):
    self.assertEqual(
      "(Apple AnotherIngredient Dough)",
      str(self.rrm.apply(Mixture("(powdered AnotherIngredient) + (Apple AnIngredient)")))
    )
    self.assertEqual(
      "(Apple AnotherIngredient Dough)",
      str(self.rrm.apply(Mixture("(Apple AnIngredient) + (powdered AnotherIngredient)")))
    )

  def test_apply2(self):
    self.assertEqual(
      "(Apple AnotherIngredient Dough) + (fried Potato)",
      str(self.rrm.apply(Mixture("(powdered AnotherIngredient) + (Apple AnIngredient) + (fried Potato)")))
    )


class TestTypeChecker(TypeChecker):
  def __init__(self):
    pass

  def tags_of_const(self, const_token):
    if const_token.name=='Oat': return ['Grain']
    else: return []

  def is_ingredient(self,name):
    return name in ["Oat", "Water", "Oil", "Dough"]

class TestReductionSystem(unittest.TestCase):

  def test_component_reduction(self):
    crules = [parse_reductions.parse_component_reduction_rule("happy sad i1 -> neutral i1")]
    crules.append( parse_reductions.parse_component_reduction_rule("neutral neutral i1 -> neutral i1") )
    crules.append( parse_reductions.parse_component_reduction_rule("happy mad i1 -> manic i1") )
    rs = ReductionSystem([ReductionRuleComponentAsMixture(c) for c in crules])
    reduced = rs.reduce_component(Component("happy happy happy sad sad mad AnIngredient"))
    self.assertEqual("neutral manic AnIngredient",str(reduced))

  def test_mixture_reduction(self):
    mrules = [parse_reductions.parse_mixture_reduction_rule("(o1 powdered i1:Grain) + (o2 Water) -> (o1 o2 i1 Dough)")]
    mrules.append(parse_reductions.parse_mixture_reduction_rule("(o1 Oil) + (o2 i1)-> (o1 o2 oily i1)"))
    crules = [parse_reductions.parse_component_reduction_rule("& crushed dried i1 -> powdered i1")]
    rs = ReductionSystem(mrules+[ReductionRuleComponentAsMixture(c) for c in crules])
    rs.set_type_checker(TestTypeChecker())
    reduced = rs.reduce_mixture(Mixture("(crushed dried Oat) + (Apple Water) + Oil"))
    self.assertEqual("(oily Apple Oat Dough)",str(reduced))




if __name__ == '__main__':
    unittest.main()
