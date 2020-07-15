from Project.Data.Optimisation.AVSDF import AVSDF
import unittest

class CircularLogicTest(unittest.TestCase):
    def setUp(self):
        self.edge_list1 = [
            ["A","B"]
        ]
        self.order1 = ["A","B"]

        self.edge_list2 = [
            ["B","H"],
            ["H","D"],
            ["C","F"],
            ["D","G"]
        ]
        self.order2 = ["A","B","C","D","E","F","G","H"]

        self.edge_list3 = [
            ["A","B"],
            ["A","C"],
            ["A","D"],
            ["A","E"],
            ["A","F"],
            ["A","G"],
            ["A","H"],
            ["H","B"]
        ]
        self.order3 = ["A","B","C","D","E","F","G","H"]

    def test_total_crossing_number_count1(self):
        self.assertEqual(AVSDF([])._count_all_crossings(self.order1,self.edge_list1),0)

    def test_total_crossing_number_count2(self):
        self.assertEqual(AVSDF([])._count_all_crossings(self.order2,self.edge_list2),2)

    def test_total_crossing_number_count3(self):
        self.assertEqual(AVSDF([])._count_all_crossings(self.order3,self.edge_list3),5)

    def test_edge_crossings_number1(self):
        self.assertEqual(AVSDF([])._count_crossings_edge(self.order2,self.edge_list2,["H","D"]),1)

    def test_edge_crossings_number2(self):
        self.assertEqual(AVSDF([])._count_crossings_edge(self.order2,self.edge_list2,["H","B"]),0)
    
    def test_edge_crossings_number3(self):
        self.assertEqual(AVSDF([])._count_crossings_edge(self.order2,self.edge_list2,["F","C"]),2)

    def test_edge_crossings_number3(self):
        self.assertEqual(AVSDF([])._count_crossings_edge(self.order3,self.edge_list3,["A","C"]),1)