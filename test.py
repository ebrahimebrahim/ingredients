import unittest
from parse_reductions import *

class TestReductionRuleComponent(unittest.TestCase):

  def setUp(self):
    self.rrc = ReductionRuleComponent(['m1', 'Onion', 'm2', 'Water'], ['m1', 'm2', 'Oil'])

  def test_string_conversion(self):
    self.assertEqual(str(self.rrc), 'm1 Onion m2 Water -> m1 m2 Oil')

class TestReductionRuleMixture(unittest.TestCase):

  def setUp(self):
    self.rrm = ReductionRuleMixture([["m1","Water"],["m4","i7:Grain"]],[["m4", "m1", "i7", "Dough"]])
  
  def test_string_conversion(self):
    self.assertEqual(str(self.rrm),"(m1 Water) + (m4 i7:Grain) -> (m4 m1 i7 Dough)")


if __name__ == '__main__':
    unittest.main()
