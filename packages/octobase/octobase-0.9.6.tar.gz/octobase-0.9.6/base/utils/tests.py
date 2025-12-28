#!/opt/local/bin/python
''' for import order reasons, test cases for the bits and bobs in `utils` need to be
    here, not next to the code they test.

    that writ, i would love to have more test cases here someday
'''

import base

class TestThreadStack(base.TestCase):

  def Run(self):

    class ThreadStackTester(base.Thing, base.utils.ThreadStack):

      ATTRIBUTES    = ['val']

      def __repr__(self):
        return 'T' + str(id(self))[-3:]

      def __init__(self):
        self.val    = 0

    a               = ThreadStackTester.ThreadStack()
    b               = ThreadStackTester.ThreadStack()
    self.Try("a and b and a is not b")

    with ThreadStackTester.ThreadStack() as c:
      x             = ThreadStackTester.ThreadStack()
      self.Try("c and x and c is x")
      self.Try("x is not a and x is not b")

      x.val         = 1

      with ThreadStackTester.ThreadStack() as d:
        z           = ThreadStackTester.ThreadStack()
        self.Try("d and z and d is z")
        self.Try("z is not x")
        self.Try("z.val == 1")

      y             = ThreadStackTester.ThreadStack()
      self.Try("y is x")
      self.Try("x.val == 1")

    self.Try("a.val == 0")

    #base.utils.XYZZY(a, b, c, d, x, y, z)
