try:
    from math import nan, isnan, inf
    from signum import sign
    import unittest
except ImportError as e:
    print(e)
    print("To pass these signum tests, you should have 'math', 'signum', and 'unittest' modules installed")
    print("Terminated, no tests passed")
    exit(1)

class TestSignum(unittest.TestCase):
    
    def trace(self, pcnt, cnt, what):
        delta = cnt - pcnt
        pl = 's' if delta > 1 else ''
        print(f"{delta} test{pl} for {what} passed, total {cnt} tests passed")

    def test_sign(self):
        counter = 0
        # --- int
        prev_counter = counter
        self.assertEqual(sign(-5), -1); counter += 1
        self.assertEqual(sign(-1), -1); counter += 1
        self.assertEqual(sign(0), 0); counter += 1
        self.assertEqual(sign(1), 1); counter += 1
        self.assertEqual(sign(5), 1); counter += 1
        self.trace(prev_counter, counter, "'int'")
        # ------ bool
        prev_counter = counter
        self.assertEqual(sign(True), 1); counter += 1
        self.assertEqual(sign(False), 0); counter += 1
        self.trace(prev_counter, counter, "'bool'")
        # ------ big numbers
        prev_counter = counter
        self.assertEqual(sign(10**1000), 1); counter += 1
        self.assertEqual(sign(-10**1000), -1); counter += 1
        self.assertEqual(sign(10**1000-10**1000), 0); counter += 1
        self.trace(prev_counter, counter, "big 'int'")

        # --- float
        prev_counter = counter
        self.assertEqual(sign(-5.0), -1); counter += 1
        self.assertEqual(sign(-1.0), -1); counter += 1
        self.assertEqual(sign(0.0), 0); counter += 1
        self.assertEqual(sign(1.0), 1); counter += 1
        self.assertEqual(sign(5.0), 1); counter += 1
        self.trace(prev_counter, counter, "'float'")
        # ------ -0.0 and +0.0
        prev_counter = counter
        self.assertEqual(sign(float('-0.0')), 0); counter += 1
        self.assertEqual(sign(float('+0.0')), 0); counter += 1
        self.trace(prev_counter, counter, "±0.0")
        # ------ -inf and inf
        prev_counter = counter
        self.assertEqual(sign(-inf), -1); counter += 1
        self.assertEqual(sign(inf), 1); counter += 1
        self.trace(prev_counter, counter, "infinity")
        # ------ -nan (the same as nan), nan
        prev_counter = counter
        self.assertTrue(isnan(sign(float('-nan')))); counter += 1
        self.assertTrue(isnan(sign(nan))); counter += 1
        self.assertTrue(isnan(sign(0.0*nan))); counter += 1
        self.trace(prev_counter, counter, "NaN")

        # --- Fraction
        try:
            from fractions import Fraction
            have_fractions = True
        except ImportError as e:
            have_fractions = False
            print(e)
            print("No 'fractions' module found in your installation. Tests for 'Fraction' are skipped")
        if have_fractions:
            prev_counter = counter
            self.assertEqual(sign(Fraction(-5, 2)), -1); counter += 1
            self.assertEqual(sign(Fraction(-1, 2)), -1); counter += 1
            self.assertEqual(sign(Fraction(0, 2)), 0); counter += 1
            self.assertEqual(sign(Fraction(1, 2)), 1); counter += 1
            self.assertEqual(sign(Fraction(5, 2)), 1); counter += 1
            self.trace(prev_counter, counter, "'Fraction'")

        # --- Decimal
        try:
            from decimal import Decimal
            have_decimal = True
        except ImportError as e:
            have_decimal = False
            print(e)
            print("No 'decimal' module found in your installation. Tests for 'Decimal' are skipped")
        if have_decimal:
            prev_counter = counter
            self.assertEqual(sign(Decimal(-5.5)), -1); counter += 1
            self.assertEqual(sign(Decimal(-1.5)), -1); counter += 1
            self.assertEqual(sign(Decimal(0.0)), 0); counter += 1
            self.assertEqual(sign(Decimal(1.5)), 1); counter += 1
            self.assertEqual(sign(Decimal(5.5)), 1); counter += 1
            self.trace(prev_counter, counter, "'Decimal'")
            # ------ Decimal NaN
            prev_counter = counter
            self.assertTrue(isnan(sign(Decimal('NaN')))); counter += 1
            self.trace(prev_counter, counter, "Decimal NaN")

        # --- sympy
        try:
            import sympy
            have_sympy = True
        except ImportError as e:
            have_sympy = False
            print(e)
            print("No 'sympy' module found in your installation. Tests for 'sympy' are skipped")
        if have_sympy:
            x_sym = sympy.Symbol('x')
            expr = x_sym
            val = expr.subs(x_sym, -3.14)
            prev_counter = counter
            self.assertEqual(sign(val), -1); counter += 1
            self.assertEqual(sign(sympy.Rational(3, 4)), 1); counter += 1
            self.trace(prev_counter, counter, "sympy")
            # ------ sympy.nan
            prev_counter = counter
            self.assertTrue(isnan(sign(sympy.nan))); counter += 1
            self.trace(prev_counter, counter, "sympy.nan")

        # --- New custom class (testing possible future extentions)
        #     This class has no __float__ that tests one subtle branch in the C++ code
        class MyNumber:
            def __init__(self, value):
                self.value = value
            def __gt__(self, other):
                return self.value > other
            def __lt__(self, other):
                return self.value < other
            def __eq__(self, other):
                return self.value == other
            def __repr__(self):
                return f'MyNumber({self.value})'

        prev_counter = counter
        self.assertEqual(sign(MyNumber(-5)), -1); counter += 1
        self.assertEqual(sign(MyNumber(-1)), -1); counter += 1
        self.assertEqual(sign(MyNumber(0)), 0); counter += 1
        self.assertEqual(sign(MyNumber(1)), 1); counter += 1
        self.assertEqual(sign(MyNumber(5)), 1); counter += 1
        with self.assertRaisesRegex(TypeError, r'signum\.sign: invalid argument `MyNumber\(nan\)`'):
            sign(MyNumber(nan))
        counter += 1
        self.trace(prev_counter, counter, "new custom class")

        # Testing inappropriate arguments and types (non-scalar, non-comparable, etc.)
        # --- No arguments and three arguments
        prev_counter = counter
        with self.assertRaisesRegex(TypeError, r'signum\.sign\(\) takes exactly one argument \(0 given\)'):
            sign()
        counter += 1
        with self.assertRaisesRegex(TypeError, r'signum\.sign\(\) takes exactly one argument \(3 given\)'):
            sign(-1, 0, 1)
        counter += 1
        self.trace(prev_counter, counter, "invalid number of arguments")
        
        # --- None, str, list, complex, set
        tests = [(r"`None`", None),
                 (r"`'5\.0'`", '5.0'),
                 (r"`'nan'`", 'nan'),
                 (r"`'number 5'`", 'number 5'),
                 (r"`\[-8\.75\]`", [-8.75]),
                 (r"`\(-1\+1j\)`", -1+1j),
                 (r"`\{-3\.14\}`", {-3.14}),
                ]

        prev_counter = counter
        for msg, obj in tests:
            with self.subTest(obj=obj):
                with self.assertRaisesRegex(TypeError,
                                            r'signum\.sign: invalid argument ' + msg):
                    sign(obj)
                counter += 1
        self.trace(prev_counter, counter, "inappropriate types")
                
        print(f'Success, {counter} tests passed.')

# print('--- int')
# print("sign(-5):", sign(-5))
# print("sign(-1):", sign(-1))
# print("sign(0):", sign(0))
# print("sign(1):", sign(1))
# print("sign(5):", sign(5))
#
# print('------ bool')
# print("sign(True):", sign(True))
# print("sign(False):", sign(False))
#
# print('------ big numbers')
# print('sign(10**1000):', sign(10**1000))
# print('sign(-10**1000):', sign(-10**1000))
# print('sign(10**1000-10**1000):', sign(10**1000-10**1000))
#
# print('\n--- float')
# print("sign(-5.0):", sign(-5.0))
# print("sign(-1.0):", sign(-1.0))
# print("sign(0.0):", sign(0.0))
# print("sign(1.0):", sign(1.0))
# print("sign(5.0):", sign(5.0))
# print('------ -0.0 and +0.0')
# print("sign(float('-0.0')):", sign(float('-0.0')))
# print("sign(float('+0.0')):", sign(float('+0.0')))
# print('------ -inf and inf')
# print("sign(-inf):", sign(-inf))
# print("sign(inf):", sign(inf))
# print('------ -nan and nan')
# print("sign(float('-nan')):", sign(float('-nan')))
# print("sign(nan):", sign(nan))
# print("sign(0.0*nan):", sign(0.0*nan))
#
# print('\n--- Fraction')
# print("sign(Fraction(-5, 2)):", sign(Fraction(-5, 2)))
# print("sign(Fraction(-1, 2)):", sign(Fraction(-1, 2)))
# print("sign(Fraction(0, 2)):", sign(Fraction(0, 2)))
# print("sign(Fraction(1, 2)):", sign(Fraction(1, 2)))
# print("sign(Fraction(5, 2)):", sign(Fraction(5, 2)))
#
# print('\n--- Decimal')
# print("sign(Decimal(-5.5)):", sign(Decimal(-5.5)))
# print("sign(Decimal(-1.5)):", sign(Decimal(-1.5)))
# print("sign(Decimal(0.0)):", sign(Decimal(0.0)))
# print("sign(Decimal(1.5)):", sign(Decimal(1.5)))
# print("sign(Decimal(5.5)):", sign(Decimal(5.5)))
#
# print("------ Decimal('NaN')")
# print("sign(Decimal('NaN')):", sign(Decimal('NaN')))
#
# print('\n--- sympy (substitution and Rational)')
# x_sym = sympy.Symbol('x')
# expr = x_sym
# val = expr.subs(x_sym, -3.14)
# print(f"Type of val is {type(val)}")
# print(f"Type of (val > 0) is {type(val > 0)}")
# print("sign(val):", sign(val))
# print("sign(sympy.Rational(3, 4)):", sign(sympy.Rational(3, 4)))
#
# print('------ sympy.nan')
# print("sign(sympy.nan):", sign(sympy.nan))
#
# print('\n--- My Custom Class That Have >, <, == With Numbers But Nothing Else')
# print("sign(MyNumber(-5)):", sign(MyNumber(-5)))
# print("sign(MyNumber(-1)):", sign(MyNumber(-1)))
# print("sign(MyNumber(0)):", sign(MyNumber(0)))
# print("sign(MyNumber(1)):", sign(MyNumber(1)))
# print("sign(MyNumber(5.1)):", sign(MyNumber(5.1)))
# try:
#     print("sign(MyNumber(nan)):", sign(MyNumber(nan)))
# except TypeError as e:
#     print(e)
#
# print('\n--- No arguments')
# try:
#     print("sign():", sign())
# except TypeError as e:
#     print(e)
#
# print('\n--- Three arguments')
# try:
#     print("sign(-1, 0, 1):", sign(-1, 0, 1))
# except TypeError as e:
#     print(e)
#
# print('\n--- None')
# try:
#     print("sign(None):", sign(None))
# except TypeError as e:
#     print(e)
#
# print('\n--- str')
# try:
#     print("sign('5.0'):", sign('5.0'))
# except TypeError as e:
#     print(e)
#
# try:
#     print("sign('nan'):", sign('nan'))
# except TypeError as e:
#     print(e)
#
# try:
#     print("sign('number 5'):", sign('number 5'))
# except TypeError as e:
#     print(e)
#
# print('\n--- list')
# try:
#     print("sign([-8.75]):", sign([-8.75]))
# except TypeError as e:
#     print(e)
#
# print('\n--- complex')
# try:
#     print("sign(-1+1j):", sign(-1+1j))
# except TypeError as e:
#     print(e)
#
# print('\n--- set')
# try:
#     print("sign({-3.14}):", sign({-3.14}))
# except TypeError as e:
#     print(e)

if __name__ == '__main__':
    unittest.main()
