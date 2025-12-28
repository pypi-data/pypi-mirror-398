"""Regression tests for mock LLIL control-flow helpers (IF/GOTO/LABEL)."""

import os

os.environ["FORCE_BINJA_MOCK"] = "1"


def test_mock_llil_control_flow_nodes() -> None:
    from binaryninja.lowlevelil import LowLevelILLabel

    from binja_test_mocks import binja_api  # noqa: F401
    from binja_test_mocks.mock_llil import (
        MockGoto,
        MockIfExpr,
        MockLabel,
        MockLowLevelILFunction,
    )

    il = MockLowLevelILFunction()

    label_true = LowLevelILLabel()
    label_false = LowLevelILLabel()

    cond = il.const(1, 1)
    if_expr = il.if_expr(cond, label_true, label_false)

    assert isinstance(if_expr, MockIfExpr)
    assert if_expr.op == "IF"
    assert if_expr.ops == [cond, label_true, label_false]
    assert if_expr.cond is cond
    assert if_expr.t is label_true
    assert if_expr.f is label_false

    il.append(if_expr)
    il.mark_label(label_true)
    goto = il.goto(label_false)
    il.append(goto)
    il.mark_label(label_false)

    assert isinstance(il.ils[1], MockLabel)
    assert il.ils[1].label is label_true

    assert isinstance(il.ils[2], MockGoto)
    assert il.ils[2].op == "GOTO"
    assert il.ils[2].ops == [label_false]
    assert il.ils[2].label is label_false

    assert isinstance(il.ils[3], MockLabel)
    assert il.ils[3].label is label_false
