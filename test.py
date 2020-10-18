import unittest
import parse_reductions
from util import Ingredient,ReductionRuleMixture,ReductionRuleComponent,token_type,match_pattern


class TestMatchPattern(unittest.TestCase):

  def setUp(self):
    self.trivial_check = lambda child,parent : True

  def test_pattern(self):
    pattern = ['m1']
    self.assertEqual(
      {"m1":['Peup']},
      match_pattern(pattern,['Peup'],self.trivial_check)
    )

  def test_pattern2(self):
    pattern = ['m1', 'Onion']
    self.assertEqual(
      {"m1":['Peup']},
      match_pattern(pattern,['Peup','Onion'],self.trivial_check)
    )
    self.assertEqual(
      None,
      match_pattern(pattern,['Peup'],self.trivial_check)
    )
    self.assertEqual(
      None,
      match_pattern(pattern,['Onion','Peup'],self.trivial_check)
    )

  def test_pattern3(self):
    pattern = "m1 salty m2 pickled m3 Cucumber".split()
    self.assertEqual(
      {
        "m1" : "aaa".split(),
        "m2" : "bbb ccc".split(),
        "m3" : "ddd eee fff".split()
      },
      match_pattern(pattern,"aaa salty bbb ccc pickled ddd eee fff Cucumber".split(),self.trivial_check)
    )
    self.assertEqual(
      {
        "m1" : "aaa".split(),
        "m2" : [],
        "m3" : []
      },
      match_pattern(pattern,"aaa salty pickled Cucumber".split(),self.trivial_check)
    )
    self.assertEqual(
      None,
      match_pattern(pattern,"aaa salty bbb ccc pickled ddd eee fff Burger".split(),self.trivial_check)
    )


  def test_pattern4(self):
    pattern = "m1 salty m2 pickled m3 i1".split()
    self.assertEqual(
      {
        "m1" : "aaa".split(),
        "m2" : "bbb ccc".split(),
        "m3" : "ddd eee fff".split(),
        "i1" : "Cucumber".split()
      },
      match_pattern(pattern,"aaa salty bbb ccc pickled ddd eee fff Cucumber".split(),self.trivial_check)
    )

  @unittest.skip("pattern match does not support repeated variables")
  def test_pattern5(self):
    pattern = "m1 salty m1 pickled m3 Cucumber".split()
    self.assertEqual(
      {
        "m1" : "aaa".split(),
        "m3" : "bbb ccc".split(),
      },
      match_pattern(pattern,"aaa salty aaa pickled bbb ccc Cucumber".split(),self.trivial_check)
    )
    self.assertEqual(
      None,
      match_pattern(pattern,"aaa salty ddd pickled bbb ccc Cucumber".split(),self.trivial_check)
    )




class TestReductionRuleComponent(unittest.TestCase):

  def setUp(self):
    self.rrc = ReductionRuleComponent(['m1', 'fried', 'm2', 'chopped', 'm3', 'Potato'], ['m1', 'm2', 'm3', 'FrenchFries'])
    self.component_str = "dirty zesty fried chopped salty Potato"
    self.reduced_str = "dirty zesty salty FrenchFries"
    self.component_list = self.component_str.split()
    self.match_lhs_result = {
      "m1" : ['dirty','zesty'],
      "m2" : [],
      "m3" : ['salty']
    }

  def test_string_conversion(self):
    self.assertEqual(str(self.rrc), 'm1 fried m2 chopped m3 Potato -> m1 m2 m3 FrenchFries')

  def test_match_lhs(self):
    self.assertEqual(self.match_lhs_result, self.rrc.match_lhs(self.component_list))

  def test_apply(self):
    self.assertEqual(self.reduced_str, self.rrc.apply(self.component_str))



class TestReductionRuleMixture(unittest.TestCase):

  def setUp(self):
    self.rrm = ReductionRuleMixture([["m1","Water"],["m4","i7:Grain"]],[["m4", "m1", "i7", "Dough"]])

  def test_string_conversion(self):
    self.assertEqual("(m1 Water) + (m4 i7:Grain) -> (m4 m1 i7 Dough)",str(self.rrm))



class TestRuleParsers(unittest.TestCase):

  def setUp(self):
    self.component_rules = [
      "fried + burnt = extremely_burnt", # symmetric_concise_component_rule ; Note that this one get parsed into multiple primitive rules
      "baked + baked = burnt", # already_symmetric_symmetric_concise_component_rule
      "fried +> boiled = fried", # concise_component_rule
      "m1 Oil m2 Water -> m1 m2 oily Water", # primitive_component_rule
    ]
    self.mixture_rules = [
      "(m1 i1:Water) + (m2 i2:Oil) -> (m1 m2 oily i1)" # mixture_rule
    ]

  def test_token_type(self):
    self.assertEqual(token_type("m843"),"modifier variable")
    self.assertEqual(token_type("i42"),"basic ingredient variable")
    self.assertEqual(token_type("i93:Onion"),"qualified ingredient variable")
    self.assertEqual(token_type("Onion"),"constant")
    with self.assertRaises(Exception):
      token_type("i1:i2")
    with self.assertRaises(Exception):
      token_type("Onion:Vegetable")


  def test_component_vs_mixture_rule_identification(self):
    for r in self.component_rules:
      self.assertTrue(parse_reductions.is_component_reduction_rule(r))
      self.assertFalse(parse_reductions.is_mixture_reduction_rule(r))
    for r in self.mixture_rules:
      self.assertFalse(parse_reductions.is_component_reduction_rule(r))
      self.assertTrue(parse_reductions.is_mixture_reduction_rule(r))

  def test_parse_component_reduction_rule(self):
    parsed = [parse_reductions.parse_component_reduction_rule(r) for r in self.component_rules]  # a list of lists of ReductionRuleComponent

    # Check first concise component rule, the one that get parsed into multiple primitive rules:
    self.assertEqual(len(parsed[0]),2)
    self.assertIn("m0 fried m1 burnt m2 i1 -> extremely_burnt m0 m1 m2 i1",list(map(str,parsed[0])))
    self.assertIn("m0 burnt m1 fried m2 i1 -> extremely_burnt m0 m1 m2 i1",list(map(str,parsed[0])))

    # Check the others
    for p in parsed[1:]:
      self.assertEqual(len(p),1)
    strs = [str(p[0]) for p in parsed] # Convert first rule in each list to a string
    self.assertEqual(strs[1],"m0 baked m1 baked m2 i1 -> burnt m0 m1 m2 i1")
    self.assertEqual(strs[2],"m0 fried m1 boiled m2 i1 -> fried m0 m1 m2 i1")
    self.assertEqual(strs[3],"m1 Oil m2 Water -> m1 m2 oily Water")

    # Verify correct token count
    r = parsed[3][0]
    self.assertEqual(len(r.lhs),4)
    self.assertEqual(len(r.rhs),4)

    # Check that it duplicate variable names:
    p = parse_reductions.parse_component_reduction_rule("baked +> m3 = baked")
    self.assertEqual(len(p),1)
    self.assertEqual(str(p[0]),"m4 baked m5 m3 m6 i1 -> baked m4 m5 m6 i1")

    # Check three "summands", nonsymmetric
    p = parse_reductions.parse_component_reduction_rule("fried +> baked +> boiled = soggy")
    self.assertEqual(len(p),1)
    self.assertEqual(str(p[0]),"m0 fried m1 baked m2 boiled m3 i1 -> soggy m0 m1 m2 m3 i1")

    # Check three "summands", symmetric
    p = parse_reductions.parse_component_reduction_rule("fried + baked + boiled = soggy")
    self.assertEqual(len(p),6)



  def test_parse_mixture_reduction_rule(self):
    parsed = [parse_reductions.parse_mixture_reduction_rule(r) for r in self.mixture_rules]  # a list of ReductionRuleComponent
    for i in range(len(parsed)):
      self.assertEqual(str(parsed[i]),self.mixture_rules[i]) # parsing and converting back to string should make no change

    r = parsed[0]

    # Verify correct component count
    self.assertEqual(len(r.lhs),2)
    self.assertEqual(len(r.rhs),1)

    # Verify correct token counts
    self.assertEqual([len(c) for c in r.lhs],[2,2])
    self.assertEqual([len(c) for c in r.rhs],[4])



if __name__ == '__main__':
    unittest.main()
