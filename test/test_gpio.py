"""Test against test.v (ARM CMSDK IOP GPIO)."""
import os
from conftest import FIXTURES_DIR
from src.verilog_parser import VerilogFileParser
from src.data_model import PortDirection

TEST_V = os.path.join(FIXTURES_DIR, "test.v")


def _parse_gpio():
    """Parse test.v and return the single module."""
    p = VerilogFileParser()
    mods = p.parse_file(TEST_V)
    assert len(mods) == 1
    return mods[0]


def test_module_name_and_line():
    m = _parse_gpio()
    assert m.name == "cmsdk_iop_gpio"
    assert m.line_number == 46


def test_parameters():
    m = _parse_gpio()
    module_params = [x for x in m.parameters if x.param_type == "parameter"]
    local_params = [x for x in m.parameters if x.param_type == "localparam"]
    assert len(module_params) == 5
    assert len(local_params) == 13
    for ep in ["ALTERNATE_FUNC_MASK", "ALTERNATE_FUNC_DEFAULT", "BE", "IOADDR_WIDTH", "GPIO_WIDTH"]:
        assert any(x.name == ep for x in module_params), "Missing param: " + ep


def test_ports():
    m = _parse_gpio()
    assert len(m.input_ports) == 11
    assert len(m.output_ports) == 6
    assert len(m.inout_ports) == 0

    pm = {p.name: p for p in m.ports}
    assert pm["i_IOSEL"].net_type == "signed"
    assert pm["i_IOADDR"].net_type == "wire"
    assert pm["i_IOADDR"].range_spec == "[IOADDR_WIDTH-1:0]"
    assert pm["i_IOADDR"].width == 0  # parameterized
    assert pm["i_IOSIZE"].width == 2
    assert pm["i_IOWDATA"].width == 32
    assert pm["o_IORDATA"].width == 32
    assert pm["PORTOUT"].width == 16
    assert pm["o_COMBINT"].width == 1
    assert pm["o_COMBINT"].net_type == "wire"


def test_port_classification():
    m = _parse_gpio()
    cls = m.classify_ports()
    assert len(cls["clocks"]) == 2  # FCLK, HCLK
    assert cls["resets"][0]["active"] == "low"


def test_wires():
    m = _parse_gpio()
    assert len(m.wires) >= 40
    wn = [w.name for w in m.wires]
    for expected in ["read_mux", "read_mux_le", "reg_datain32", "bigendian"]:
        assert expected in wn, "Missing wire: " + expected


def test_no_instances():
    m = _parse_gpio()
    assert len(m.instances) == 0


def test_serialization():
    m = _parse_gpio()
    d = m.to_dict()
    fd = m.to_full_dict()
    assert len(fd["ports_detail"]) == 17
    assert len(d["parameters"]) == 18
