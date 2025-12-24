# This file is part of pex_config.
#
# Developed for the LSST Data Management System.
# This product includes software developed by the LSST Project
# (http://www.lsst.org).
# See the COPYRIGHT file at the top-level directory of this distribution
# for details of code ownership.
#
# This software is dual licensed under the GNU General Public License and also
# under a 3-clause BSD license. Recipients may choose which of these licenses
# to use; please see the files gpl-3.0.txt and/or bsd_license.txt,
# respectively.  If you choose the GPL option then the following text applies
# (but note that there is still no warranty even if you opt for BSD instead):
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

import io
import itertools
import os
import pickle
import re
import tempfile
import unittest
from types import SimpleNamespace

try:
    import yaml
except ImportError:
    yaml = None

import lsst.pex.config as pexConfig

# Some tests depend on daf_base.
# Skip them if it is not found.
try:
    import lsst.daf.base as dafBase
except ImportError:
    dafBase = None

GLOBAL_REGISTRY = {}


class Simple(pexConfig.Config):
    """A simple config used for testing."""

    i = pexConfig.Field("integer test", int, optional=True)
    f = pexConfig.Field("float test", float, default=3.0)
    b = pexConfig.Field("boolean test", bool, default=False, optional=False)
    c = pexConfig.ChoiceField(
        "choice test", str, default="Hello", allowed={"Hello": "First choice", "World": "second choice"}
    )
    r = pexConfig.RangeField("Range test", float, default=3.0, optional=False, min=3.0, inclusiveMin=True)
    ll = pexConfig.ListField(
        "list test",
        int,
        default=[1, 2, 3],
        maxLength=5,
        itemCheck=lambda x: x is not None and x > 0,
        optional=True,
    )
    d = pexConfig.DictField(
        "dict test", str, str, default={"key": "value"}, itemCheck=lambda x: x.startswith("v")
    )
    n = pexConfig.Field("nan test", float, default=float("NAN"))


GLOBAL_REGISTRY["AAA"] = Simple


class InnerConfig(pexConfig.Config):
    """Inner config used for testing."""

    f = pexConfig.Field("Inner.f", float, default=0.0, check=lambda x: x >= 0, optional=False)


GLOBAL_REGISTRY["BBB"] = InnerConfig


class OuterConfig(InnerConfig, pexConfig.Config):
    """Outer config used for testing."""

    i = pexConfig.ConfigField("Outer.i", InnerConfig)

    def __init__(self):
        pexConfig.Config.__init__(self)
        self.i.f = 5.0

    def validate(self):
        pexConfig.Config.validate(self)
        if self.i.f < 5:
            raise ValueError("validation failed, outer.i.f must be greater than 5")


class Complex(pexConfig.Config):
    """A complex config for testing."""

    c = pexConfig.ConfigField("an inner config", InnerConfig)
    r = pexConfig.ConfigChoiceField(
        "a registry field", typemap=GLOBAL_REGISTRY, default="AAA", optional=False
    )
    p = pexConfig.ConfigChoiceField("another registry", typemap=GLOBAL_REGISTRY, default="BBB", optional=True)


class Deprecation(pexConfig.Config):
    """A test config with a deprecated field."""

    old = pexConfig.Field("Something.", int, default=10, deprecated="not used!")


class ConfigTest(unittest.TestCase):
    """Tests of basic Config functionality."""

    def setUp(self):
        self.simple = Simple()
        self.inner = InnerConfig()
        self.outer = OuterConfig()
        self.comp = Complex()
        self.deprecation = Deprecation()

    def tearDown(self):
        del self.simple
        del self.inner
        del self.outer
        del self.comp

    def testFieldTypeAnnotationRuntime(self):
        # test parsing type annotation for runtime dtype
        testField = pexConfig.Field[str](doc="test")
        self.assertEqual(testField.dtype, str)

        # verify that forward references work correctly
        testField = pexConfig.Field["float"](doc="test")
        self.assertEqual(testField.dtype, float)

        # verify that Field rejects multiple types
        with self.assertRaises(ValueError):
            pexConfig.Field[str, int](doc="test")  # type: ignore

        # verify that Field raises in conflict with dtype:
        with self.assertRaises(ValueError):
            pexConfig.Field[str](doc="test", dtype=int)

        # verify that Field does not raise if dtype agrees
        testField = pexConfig.Field[int](doc="test", dtype=int)
        self.assertEqual(testField.dtype, int)

    def testInit(self):
        self.assertIsNone(self.simple.i)
        self.assertEqual(self.simple.f, 3.0)
        self.assertFalse(self.simple.b)
        self.assertEqual(self.simple.c, "Hello")
        self.assertEqual(list(self.simple.ll), [1, 2, 3])
        self.assertEqual(self.simple.d["key"], "value")
        self.assertEqual(self.inner.f, 0.0)
        self.assertEqual(self.deprecation.old, 10)

        self.assertEqual(self.deprecation._fields["old"].doc, "Something. Deprecated: not used!")

        self.assertEqual(self.outer.i.f, 5.0)
        self.assertEqual(self.outer.f, 0.0)

        self.assertEqual(self.comp.c.f, 0.0)
        self.assertEqual(self.comp.r.name, "AAA")
        self.assertEqual(self.comp.r.active.f, 3.0)
        self.assertEqual(self.comp.r["BBB"].f, 0.0)

    def testDeprecationWarning(self):
        """Test that a deprecated field emits a warning when it is set."""
        with self.assertWarns(FutureWarning) as w:
            self.deprecation.old = 5
            self.assertEqual(self.deprecation.old, 5)

            self.assertIn(self.deprecation._fields["old"].deprecated, str(w.warnings[-1].message))

    def testDeprecationOutput(self):
        """Test that a deprecated field is not written out unless it is set."""
        stream = io.StringIO()
        self.deprecation.saveToStream(stream)
        self.assertNotIn("config.old", stream.getvalue())
        with self.assertWarns(FutureWarning):
            self.deprecation.old = 5
        stream = io.StringIO()
        self.deprecation.saveToStream(stream)
        self.assertIn("config.old=5\n", stream.getvalue())

    def testDocstring(self):
        """Test that the docstring is not allowed to be empty."""
        with self.assertRaises(ValueError):
            pexConfig.Field("", int, default=1)

        with self.assertRaises(ValueError):
            pexConfig.RangeField("", int, default=3, min=3, max=4)

        with self.assertRaises(ValueError):
            pexConfig.DictField("", str, str, default={"key": "value"})

        with self.assertRaises(ValueError):
            pexConfig.ListField("", int, default=[1, 2, 3])

        with self.assertRaises(ValueError):
            pexConfig.ConfigField("", InnerConfig)

        with self.assertRaises(ValueError):
            pexConfig.ConfigChoiceField("", typemap=GLOBAL_REGISTRY, default="AAA")

    def testValidate(self):
        self.simple.validate()

        self.inner.validate()
        self.assertRaises(ValueError, setattr, self.outer.i, "f", -5)
        self.outer.i.f = 10.0
        self.outer.validate()

        with self.assertRaises(pexConfig.FieldValidationError):
            self.simple.d["failKey"] = "failValue"
        self.simple.validate()

        self.outer.i = InnerConfig
        self.assertRaises(ValueError, self.outer.validate)
        self.outer.i = InnerConfig()
        self.assertRaises(ValueError, self.outer.validate)

        self.comp.validate()
        self.comp.r = None
        self.assertRaises(ValueError, self.comp.validate)
        self.comp.r = "BBB"
        self.comp.validate()

    def testRangeFieldConstructor(self):
        """Test RangeField constructor's checking of min, max."""
        val = 3
        self.assertRaises(ValueError, pexConfig.RangeField, "test", int, default=val, min=val, max=val - 1)
        self.assertRaises(
            ValueError, pexConfig.RangeField, "test", float, default=val, min=val, max=val - 1e-15
        )
        for inclusiveMin, inclusiveMax in itertools.product((False, True), (False, True)):
            if inclusiveMin and inclusiveMax:
                # should not raise
                class Cfg1(pexConfig.Config):
                    r1 = pexConfig.RangeField(
                        doc="test",
                        dtype=int,
                        default=val,
                        min=val,
                        max=val,
                        inclusiveMin=inclusiveMin,
                        inclusiveMax=inclusiveMax,
                    )
                    r2 = pexConfig.RangeField(
                        doc="test",
                        dtype=float,
                        default=val,
                        min=val,
                        max=val,
                        inclusiveMin=inclusiveMin,
                        inclusiveMax=inclusiveMax,
                    )

                Cfg1()
            else:
                # raise while constructing the RangeField (hence cannot make
                # it part of a Config)
                self.assertRaises(
                    ValueError,
                    pexConfig.RangeField,
                    doc="test",
                    dtype=int,
                    default=val,
                    min=val,
                    max=val,
                    inclusiveMin=inclusiveMin,
                    inclusiveMax=inclusiveMax,
                )
                self.assertRaises(
                    ValueError,
                    pexConfig.RangeField,
                    doc="test",
                    dtype=float,
                    default=val,
                    min=val,
                    max=val,
                    inclusiveMin=inclusiveMin,
                    inclusiveMax=inclusiveMax,
                )

    def testRangeFieldDefault(self):
        """Test RangeField's checking of the default value."""
        minVal = 3
        maxVal = 4
        for val, inclusiveMin, inclusiveMax, shouldRaise in (
            (minVal, False, True, True),
            (minVal, True, True, False),
            (maxVal, True, False, True),
            (maxVal, True, True, False),
        ):

            class Cfg1(pexConfig.Config):
                r = pexConfig.RangeField(
                    doc="test",
                    dtype=int,
                    default=val,
                    min=minVal,
                    max=maxVal,
                    inclusiveMin=inclusiveMin,
                    inclusiveMax=inclusiveMax,
                )

            class Cfg2(pexConfig.Config):
                r2 = pexConfig.RangeField(
                    doc="test",
                    dtype=float,
                    default=val,
                    min=minVal,
                    max=maxVal,
                    inclusiveMin=inclusiveMin,
                    inclusiveMax=inclusiveMax,
                )

            if shouldRaise:
                self.assertRaises(pexConfig.FieldValidationError, Cfg1)
                self.assertRaises(pexConfig.FieldValidationError, Cfg2)
            else:
                Cfg1()
                Cfg2()

    def testSave(self):
        self.comp.r = "BBB"
        self.comp.p = "AAA"
        self.comp.c.f = 5.0
        with tempfile.TemporaryDirectory(prefix="config-save-test", ignore_cleanup_errors=True) as tmpdir:
            roundtrip_path = os.path.join(tmpdir, "roundtrip.test")
            self.comp.save(roundtrip_path)

            roundTrip = Complex()
            roundTrip.load(roundtrip_path)
            self.assertEqual(self.comp.c.f, roundTrip.c.f)
            self.assertEqual(self.comp.r.name, roundTrip.r.name)
            del roundTrip

            # test saving to an open file
            roundtrip_path = os.path.join(tmpdir, "roundtrip_open.test")
            with open(roundtrip_path, "w") as outfile:
                self.comp.saveToStream(outfile)
            roundTrip = Complex()
            with open(roundtrip_path) as infile:
                roundTrip.loadFromStream(infile)
            self.assertEqual(self.comp.c.f, roundTrip.c.f)
            self.assertEqual(self.comp.r.name, roundTrip.r.name)
            del roundTrip

            # Test an override of the default variable name.
            roundtrip_path = os.path.join(tmpdir, "roundtrip_def.test")
            with open(roundtrip_path, "w") as outfile:
                self.comp.saveToStream(outfile, root="root")
            roundTrip = Complex()
            with self.assertRaises(NameError):
                roundTrip.load(roundtrip_path)
            roundTrip.load(roundtrip_path, root="root")
            self.assertEqual(self.comp.c.f, roundTrip.c.f)
            self.assertEqual(self.comp.r.name, roundTrip.r.name)

        # test saving to a string.
        saved_string = self.comp.saveToString()
        saved_string += "config.c.f = parameters.value"
        namespace = SimpleNamespace(value=7)
        extraLocals = {"parameters": namespace}
        roundTrip = Complex()
        roundTrip.loadFromString(saved_string, extraLocals=extraLocals)
        self.assertEqual(namespace.value, roundTrip.c.f)
        self.assertEqual(self.comp.r.name, roundTrip.r.name)
        with self.assertRaises(ValueError):
            roundTrip.loadFromString(saved_string, root="config", extraLocals={"config": 6})
        del roundTrip

    def testDuplicateRegistryNames(self):
        self.comp.r["AAA"].f = 5.0
        self.assertEqual(self.comp.p["AAA"].f, 3.0)

    def testInheritance(self):
        class AAA(pexConfig.Config):
            a = pexConfig.Field("AAA.a", int, default=4)

        class BBB(AAA):
            b = pexConfig.Field("BBB.b", int, default=3)

        class CCC(BBB):
            c = pexConfig.Field("CCC.c", int, default=2)

        # test multi-level inheritance
        c = CCC()
        self.assertIn("a", c.toDict())
        self.assertEqual(c._fields["a"].dtype, int)
        self.assertEqual(c.a, 4)

        # test conflicting multiple inheritance
        class DDD(pexConfig.Config):
            a = pexConfig.Field("DDD.a", float, default=0.0)

        class EEE(DDD, AAA):
            pass

        e = EEE()
        self.assertEqual(e._fields["a"].dtype, float)
        self.assertIn("a", e.toDict())
        self.assertEqual(e.a, 0.0)

        class FFF(AAA, DDD):
            pass

        f = FFF()
        self.assertEqual(f._fields["a"].dtype, int)
        self.assertIn("a", f.toDict())
        self.assertEqual(f.a, 4)

        # test inheritance from non Config objects
        class GGG:
            a = pexConfig.Field("AAA.a", float, default=10.0)

        class HHH(GGG, AAA):
            pass

        h = HHH()
        self.assertEqual(h._fields["a"].dtype, float)
        self.assertIn("a", h.toDict())
        self.assertEqual(h.a, 10.0)

        # test partial Field redefinition

        class III(AAA):
            pass

        III.a.default = 5

        self.assertEqual(III.a.default, 5)
        self.assertEqual(AAA.a.default, 4)

    @unittest.skipIf(dafBase is None, "lsst.daf.base is required")
    def testConvertPropertySet(self):
        ps = pexConfig.makePropertySet(self.simple)
        self.assertFalse(ps.exists("i"))
        self.assertEqual(ps.getScalar("f"), self.simple.f)
        self.assertEqual(ps.getScalar("b"), self.simple.b)
        self.assertEqual(ps.getScalar("c"), self.simple.c)
        self.assertEqual(list(ps.getArray("ll")), list(self.simple.ll))

        ps = pexConfig.makePropertySet(self.comp)
        self.assertEqual(ps.getScalar("c.f"), self.comp.c.f)

    def testFreeze(self):
        self.comp.freeze()

        self.assertRaises(pexConfig.FieldValidationError, setattr, self.comp.c, "f", 10.0)
        self.assertRaises(pexConfig.FieldValidationError, setattr, self.comp, "r", "AAA")
        self.assertRaises(pexConfig.FieldValidationError, setattr, self.comp, "p", "AAA")
        self.assertRaises(pexConfig.FieldValidationError, setattr, self.comp.p["AAA"], "f", 5.0)

    def checkImportRoundTrip(self, importStatement, searchString, shouldBeThere):
        self.comp.c.f = 5.0

        # Generate a Config through loading
        stream = io.StringIO()
        stream.write(str(importStatement))
        self.comp.saveToStream(stream)
        roundtrip = Complex()
        roundtrip.loadFromStream(stream.getvalue())
        self.assertEqual(self.comp.c.f, roundtrip.c.f)

        # Check the save stream
        stream = io.StringIO()
        roundtrip.saveToStream(stream)
        self.assertEqual(self.comp.c.f, roundtrip.c.f)
        streamStr = stream.getvalue()
        if shouldBeThere:
            self.assertTrue(re.search(searchString, streamStr))
        else:
            self.assertFalse(re.search(searchString, streamStr))

    def testImports(self):
        # A module not used by anything else, but which exists
        importing = "import lsst.pex.config._doNotImportMe\n"
        self.checkImportRoundTrip(importing, importing, True)

    def testBadImports(self):
        dummy = "somethingThatDoesntExist"
        importing = f"""
try:
    import {dummy}
except ImportError:
    pass
"""
        self.checkImportRoundTrip(importing, dummy, False)

    def testPickle(self):
        self.simple.f = 5
        simple = pickle.loads(pickle.dumps(self.simple))
        self.assertIsInstance(simple, Simple)
        self.assertEqual(self.simple.f, simple.f)

        self.comp.c.f = 5
        comp = pickle.loads(pickle.dumps(self.comp))
        self.assertIsInstance(comp, Complex)
        self.assertEqual(self.comp.c.f, comp.c.f)

    @unittest.skipIf(yaml is None, "Test requires pyyaml")
    def testYaml(self):
        self.simple.f = 5
        simple = yaml.safe_load(yaml.dump(self.simple))
        self.assertIsInstance(simple, Simple)
        self.assertEqual(self.simple.f, simple.f)

        self.comp.c.f = 5
        # Use a different loader to check that it also works
        comp = yaml.load(yaml.dump(self.comp), Loader=yaml.FullLoader)
        self.assertIsInstance(comp, Complex)
        self.assertEqual(self.comp.c.f, comp.c.f)

    def testCompare(self):
        comp2 = Complex()
        inner2 = InnerConfig()
        simple2 = Simple()
        self.assertTrue(self.comp.compare(comp2))
        self.assertTrue(comp2.compare(self.comp))
        self.assertTrue(self.comp.c.compare(inner2))
        self.assertTrue(self.simple.compare(simple2))
        self.assertTrue(simple2.compare(self.simple))
        self.assertEqual(self.simple, simple2)
        self.assertEqual(simple2, self.simple)
        outList = []

        def outFunc(msg):
            outList.append(msg)

        simple2.b = True
        simple2.ll.append(4)
        simple2.d["foo"] = "var"
        self.assertFalse(self.simple.compare(simple2, shortcut=True, output=outFunc))
        self.assertEqual(len(outList), 1)
        del outList[:]
        self.assertFalse(self.simple.compare(simple2, shortcut=False, output=outFunc))
        output = "\n".join(outList)
        self.assertIn("b: ", output)
        self.assertIn("ll (len): ", output)
        self.assertIn("d (keys): ", output)
        del outList[:]
        self.simple.d["foo"] = "vast"
        self.simple.ll.append(5)
        self.simple.b = True
        self.simple.f += 1e8
        self.assertFalse(self.simple.compare(simple2, shortcut=False, output=outFunc))
        output = "\n".join(outList)
        self.assertIn("f: ", output)
        self.assertIn("ll[3]: ", output)
        self.assertIn("d['foo']: ", output)
        del outList[:]
        comp2.r["BBB"].f = 1.0  # changing the non-selected item shouldn't break equality
        self.assertTrue(self.comp.compare(comp2))
        comp2.r["AAA"].i = 56  # changing the selected item should break equality
        comp2.c.f = 1.0
        self.assertFalse(self.comp.compare(comp2, shortcut=False, output=outFunc))
        output = "\n".join(outList)
        self.assertIn("c.f: ", output)
        self.assertIn("r['AAA']", output)
        self.assertNotIn("r['BBB']", output)

        # Before DM-16561, this incorrectly returned `True`.
        self.assertFalse(self.inner.compare(self.outer))
        # Before DM-16561, this raised.
        self.assertFalse(self.outer.compare(self.inner))

        outList.clear()
        simple3 = Simple()
        simple3.i = 2
        simple4 = Simple()
        self.assertFalse(simple4.compare(simple3, output=outFunc))
        self.assertEqual(outList[-1], "i: None != 2")
        self.assertFalse(simple3.compare(simple4, output=outFunc))
        self.assertEqual(outList[-1], "i: 2 != None")
        simple3.i = None

        outList.clear()
        self.assertFalse(simple4.compare(comp2, output=outFunc))
        self.assertIn("test_Config.Simple != test_Config.Complex", outList[-1])

        outList.clear()
        self.assertFalse(pexConfig.compareConfigs("s", simple4, None, output=outFunc))
        self.assertIn("!= None", outList[-1])

        outList.clear()
        self.assertFalse(pexConfig.compareConfigs("s", None, simple4, output=outFunc))
        self.assertIn("None !=", outList[-1])

        outList.clear()
        simple3.ll = None
        self.assertFalse(simple4.compare(simple3, output=outFunc))
        self.assertIn("ll", outList[-1])
        outList.clear()
        self.assertFalse(simple3.compare(simple4, output=outFunc))
        self.assertTrue(outList[-1].startswith("ll: None"))

    def testLoadError(self):
        """Check that loading allows errors in the file being loaded to
        propagate.
        """
        self.assertRaises(SyntaxError, self.simple.loadFromStream, "bork bork bork")
        self.assertRaises(NameError, self.simple.loadFromStream, "config.f = bork")

    def testNames(self):
        """Check that the names() method returns valid keys.

        Also check that we have the right number of keys, and as they are
        all known to be valid we know that we got them all.
        """
        names = self.simple.names()
        self.assertEqual(len(names), 8)
        for name in names:
            self.assertTrue(hasattr(self.simple, name))

    def testIteration(self):
        self.assertIn("ll", self.simple)
        self.assertIn("ll", self.simple.keys())
        self.assertIn("Hello", self.simple.values())
        self.assertEqual(len(self.simple.values()), 8)

        for k, v, (k1, v1) in zip(self.simple.keys(), self.simple.values(), self.simple.items(), strict=True):
            self.assertEqual(k, k1)
            if k == "n":
                self.assertNotEqual(v, v1)
            else:
                self.assertEqual(v, v1)

    def test_copy(self):
        """Test the copy method."""
        self.comp.freeze()
        copy1 = self.comp.copy()
        copy1.c.f = 6.0
        self.assertEqual(copy1.c.f, 6.0)
        self.assertEqual(self.comp.c.f, 0.0)
        copy1.r["AAA"].i = 1
        self.assertEqual(copy1.r["AAA"].i, 1)
        self.assertIsNone(self.comp.r["AAA"].i)
        copy1.r["AAA"].f = 2.0
        self.assertEqual(copy1.r["AAA"].f, 2.0)
        self.assertEqual(self.comp.r["AAA"].f, 3.0)
        copy1.r["AAA"].c = "World"
        self.assertEqual(copy1.r["AAA"].c, "World")
        self.assertEqual(self.comp.r["AAA"].c, "Hello")
        copy1.r["AAA"].r = 4.0
        self.assertEqual(copy1.r["AAA"].r, 4.0)
        self.assertEqual(self.comp.r["AAA"].r, 3.0)
        copy1.r["AAA"].ll.append(4)
        self.assertEqual(copy1.r["AAA"].ll, [1, 2, 3, 4])
        self.assertEqual(self.comp.r["AAA"].ll, [1, 2, 3])
        copy1.r["AAA"].d["key2"] = "value2"
        self.assertEqual(copy1.r["AAA"].d, {"key": "value", "key2": "value2"})
        self.assertEqual(self.comp.r["AAA"].d, {"key": "value"})
        copy1.r.name = "BBB"
        self.assertEqual(copy1.r.name, "BBB")
        self.assertEqual(self.comp.r.name, "AAA")
        copy1.p.name = None
        self.assertIsNone(copy1.p.name)
        self.assertEqual(self.comp.p.name, "BBB")
        # Copy again to avoid shortcuts for default nested objects.
        copy1.freeze()
        copy2 = copy1.copy()
        copy2.c.f = 7.0
        self.assertEqual(copy2.c.f, 7.0)
        self.assertEqual(copy1.c.f, 6.0)
        self.assertEqual(self.comp.c.f, 0.0)
        copy2.r["AAA"].ll.append(5)
        self.assertEqual(copy2.r["AAA"].ll, [1, 2, 3, 4, 5])
        self.assertEqual(copy1.r["AAA"].ll, [1, 2, 3, 4])
        self.assertEqual(self.comp.r["AAA"].ll, [1, 2, 3])
        del copy2.r["AAA"].d["key"]
        self.assertEqual(copy2.r["AAA"].d, {"key2": "value2"})
        self.assertEqual(copy1.r["AAA"].d, {"key": "value", "key2": "value2"})
        self.assertEqual(self.comp.r["AAA"].d, {"key": "value"})
        copy2.r.name = "AAA"
        self.assertEqual(copy2.r.name, "AAA")
        self.assertEqual(copy1.r.name, "BBB")
        self.assertEqual(self.comp.r.name, "AAA")
        copy2.p.name = "AAA"
        self.assertEqual(copy2.p.name, "AAA")
        self.assertIsNone(copy1.p.name)
        self.assertEqual(self.comp.p.name, "BBB")


if __name__ == "__main__":
    unittest.main()
