"""Control and debug registers lift to something that compiles.

They used to come out as bare identifiers -- `eax = cr2;`, `cr3 = eax;` --
and the chunk failed to build. Fable: The Lost Chapters reads cr2 in its own
page-fault handler and flushes the TLB with mov eax,cr3 / mov cr3,eax. With
no guest paging there is no value to give: reads are 0, writes are no-ops.
"""
import unittest

from .disasm import Instruction, Operand
from .lifter import Lifter


def _lift(mnemonic, op_str, operands):
    lifter = Lifter()
    insn = Instruction(0x000AB1B1, 3, mnemonic, op_str, "",
                       operands=list(operands))
    return lifter, " ".join(lifter.lift_instruction(insn))


def _reg(name):
    return Operand(type="reg", reg=name)


class ControlRegisterTest(unittest.TestCase):

    def test_read_cr2_is_zero(self):
        lifter, out = _lift("mov", "eax, cr2", [_reg("eax"), _reg("cr2")])
        self.assertIn("eax = 0 /* cr2: privileged */;", out)
        self.assertNotRegex(out, r"(?<![/* ])\bcr2\b(?! *:)")
        self.assertEqual(lifter.unimplemented, {})

    def test_write_cr3_is_a_no_op(self):
        lifter, out = _lift("mov", "cr3, eax", [_reg("cr3"), _reg("eax")])
        self.assertNotIn("cr3 =", out)
        self.assertIn("privileged register", out)
        self.assertEqual(lifter.unimplemented, {})

    def test_debug_register_read(self):
        _, out = _lift("mov", "ecx, dr7", [_reg("ecx"), _reg("dr7")])
        self.assertIn("ecx = 0 /* dr7: privileged */;", out)


if __name__ == "__main__":
    unittest.main()
