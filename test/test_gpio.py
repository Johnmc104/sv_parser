"""Test against test.v (ARM CMSDK IOP GPIO)."""
import sys, json
sys.path.insert(0, '.')

from src.verilog_parser import VerilogFileParser
from src.data_model import PortDirection

print("=" * 60)
print("TEST 1: test.v (cmsdk_iop_gpio)")
print("=" * 60)

p = VerilogFileParser()
mods = p.parse_file('test.v')
assert len(mods) == 1
m = mods[0]

# Module
assert m.name == "cmsdk_iop_gpio"
assert m.line_number == 46

# Parameters: 5 + 13 local
module_params = [x for x in m.parameters if x.param_type == "parameter"]
local_params = [x for x in m.parameters if x.param_type == "localparam"]
assert len(module_params) == 5
assert len(local_params) == 13
for ep in ["ALTERNATE_FUNC_MASK", "ALTERNATE_FUNC_DEFAULT", "BE", "IOADDR_WIDTH", "GPIO_WIDTH"]:
    assert any(x.name == ep for x in module_params), "Missing param: " + ep
print("Parameters: 5p + 13lp = 18 OK")

# Ports: 11 in + 6 out
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
print("Ports: 11in + 6out = 17 OK")

# Port classification
cls = m.classify_ports()
assert len(cls["clocks"]) == 2  # FCLK, HCLK
assert cls["resets"][0]["active"] == "low"
print("Classification: 2clk, 1rst(low) OK")

# Wires
assert len(m.wires) >= 40
wn = [w.name for w in m.wires]
for expected in ["read_mux", "read_mux_le", "reg_datain32", "bigendian"]:
    assert expected in wn, "Missing wire: " + expected
print("Wires: %d OK" % len(m.wires))

# No instances
assert len(m.instances) == 0
print("Instances: 0 (leaf) OK")

# Serialization
d = m.to_dict()
fd = m.to_full_dict()
assert len(fd["ports_detail"]) == 17
assert len(d["parameters"]) == 18
print("Serialization OK")

print("\n" + "=" * 60)
print("ALL TESTS PASSED")
print("=" * 60)
