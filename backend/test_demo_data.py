"""
测试数据生成器 - 用于网页显示demo
基于当前数据结构生成完整的测试设计
"""

from data import (
    DesignInfo, ModuleInfo, PortInfo, InstanceInfo, ParameterInfo,
    PortDirection, create_design, create_module,
    create_input_port, create_output_port, create_inout_port,
    create_instance, create_parameter
)

def create_demo_design() -> DesignInfo:
    """创建完整的demo设计 - 基于GPIO模块的层次结构"""
    design = create_design()
    
    # 1. 创建基础模块：时钟生成器
    clk_gen = create_module("clk_generator")
    clk_gen.add_port(create_input_port("rst_n"))
    clk_gen.add_port(create_output_port("clk_out"))
    clk_gen.add_port(create_output_port("clk_div2"))
    clk_gen.add_parameter(create_parameter("FREQ_HZ", 100000000, "integer"))
    design.add_module(clk_gen)
    
    # 2. 创建GPIO控制器（基于test.v）
    gpio_ctrl = create_module("cmsdk_iop_gpio")
    
    # 添加端口（基于test.v的端口定义）
    gpio_ctrl.add_port(create_input_port("FCLK"))
    gpio_ctrl.add_port(create_input_port("HCLK"))
    gpio_ctrl.add_port(create_input_port("HRESETn"))
    gpio_ctrl.add_port(create_input_port("i_IOSEL"))
    gpio_ctrl.add_port(create_input_port("i_IOADDR", 12))
    gpio_ctrl.add_port(create_input_port("i_IOWRITE"))
    gpio_ctrl.add_port(create_input_port("i_IOSIZE", 2))
    gpio_ctrl.add_port(create_input_port("i_IOTRANS"))
    gpio_ctrl.add_port(create_input_port("i_IOWDATA", 32))
    gpio_ctrl.add_port(create_input_port("ECOREVNUM", 4))
    gpio_ctrl.add_port(create_input_port("PORTIN", 16))
    
    gpio_ctrl.add_port(create_output_port("o_IORDATA", 32))
    gpio_ctrl.add_port(create_output_port("PORTOUT", 16))
    gpio_ctrl.add_port(create_output_port("PORTEN", 16))
    gpio_ctrl.add_port(create_output_port("PORTFUNC", 16))
    gpio_ctrl.add_port(create_output_port("GPIOINT", 16))
    gpio_ctrl.add_port(create_output_port("o_COMBINT"))
    
    # 添加参数（基于test.v的参数定义）
    gpio_ctrl.add_parameter(create_parameter("ALTERNATE_FUNC_MASK", "16'hFFFF", "integer"))
    gpio_ctrl.add_parameter(create_parameter("ALTERNATE_FUNC_DEFAULT", "16'h0000", "integer"))
    gpio_ctrl.add_parameter(create_parameter("BE", 0, "integer"))
    gpio_ctrl.add_parameter(create_parameter("IOADDR_WIDTH", 12, "integer"))
    gpio_ctrl.add_parameter(create_parameter("GPIO_WIDTH", 16, "integer"))
    
    design.add_module(gpio_ctrl)
    
    # 3. 创建中断控制器
    irq_ctrl = create_module("interrupt_controller")
    irq_ctrl.add_port(create_input_port("clk"))
    irq_ctrl.add_port(create_input_port("rst_n"))
    irq_ctrl.add_port(create_input_port("irq_in", 16))
    irq_ctrl.add_port(create_output_port("irq_out"))
    irq_ctrl.add_port(create_output_port("irq_ack"))
    irq_ctrl.add_parameter(create_parameter("IRQ_WIDTH", 16, "integer"))
    design.add_module(irq_ctrl)
    
    # 4. 创建总线桥接器
    bus_bridge = create_module("ahb_to_apb_bridge")
    bus_bridge.add_port(create_input_port("hclk"))
    bus_bridge.add_port(create_input_port("hresetn"))
    bus_bridge.add_port(create_input_port("haddr", 32))
    bus_bridge.add_port(create_input_port("htrans", 2))
    bus_bridge.add_port(create_input_port("hwrite"))
    bus_bridge.add_port(create_input_port("hsize", 3))
    bus_bridge.add_port(create_input_port("hburst", 3))
    bus_bridge.add_port(create_input_port("hwdata", 32))
    bus_bridge.add_port(create_input_port("hsel"))
    
    bus_bridge.add_port(create_output_port("hrdata", 32))
    bus_bridge.add_port(create_output_port("hready"))
    bus_bridge.add_port(create_output_port("hresp"))
    
    bus_bridge.add_port(create_output_port("paddr", 32))
    bus_bridge.add_port(create_output_port("psel"))
    bus_bridge.add_port(create_output_port("penable"))
    bus_bridge.add_port(create_output_port("pwrite"))
    bus_bridge.add_port(create_output_port("pwdata", 32))
    bus_bridge.add_port(create_input_port("prdata", 32))
    bus_bridge.add_port(create_input_port("pready"))
    
    design.add_module(bus_bridge)
    
    # 5. 创建LED驱动器
    led_driver = create_module("led_driver")
    led_driver.add_port(create_input_port("clk"))
    led_driver.add_port(create_input_port("rst_n"))
    led_driver.add_port(create_input_port("gpio_data", 8))
    led_driver.add_port(create_input_port("enable"))
    led_driver.add_port(create_output_port("led_out", 8))
    led_driver.add_parameter(create_parameter("BLINK_RATE", 1000, "integer"))
    design.add_module(led_driver)
    
    # 6. 创建顶层模块
    top_module = create_module("gpio_demo_top", is_top=True)
    
    # 顶层端口
    top_module.add_port(create_input_port("sys_clk"))
    top_module.add_port(create_input_port("sys_rst_n"))
    top_module.add_port(create_input_port("ahb_haddr", 32))
    top_module.add_port(create_input_port("ahb_htrans", 2))
    top_module.add_port(create_input_port("ahb_hwrite"))
    top_module.add_port(create_input_port("ahb_hsize", 3))
    top_module.add_port(create_input_port("ahb_hwdata", 32))
    top_module.add_port(create_input_port("ahb_hsel"))
    top_module.add_port(create_inout_port("gpio_pins", 16))
    
    top_module.add_port(create_output_port("ahb_hrdata", 32))
    top_module.add_port(create_output_port("ahb_hready"))
    top_module.add_port(create_output_port("ahb_hresp"))
    top_module.add_port(create_output_port("led_display", 8))
    top_module.add_port(create_output_port("system_irq"))
    
    # 添加实例化
    # 时钟生成器实例
    clk_inst = create_instance("u_clk_gen", "clk_generator")
    clk_inst.add_connection("rst_n", "sys_rst_n")
    clk_inst.add_connection("clk_out", "internal_clk")
    clk_inst.add_connection("clk_div2", "slow_clk")
    clk_inst.set_parameter("FREQ_HZ", 50000000)
    top_module.add_instance(clk_inst)
    
    # 总线桥接器实例
    bridge_inst = create_instance("u_ahb_apb_bridge", "ahb_to_apb_bridge")
    bridge_inst.add_connection("hclk", "internal_clk")
    bridge_inst.add_connection("hresetn", "sys_rst_n")
    bridge_inst.add_connection("haddr", "ahb_haddr")
    bridge_inst.add_connection("htrans", "ahb_htrans")
    bridge_inst.add_connection("hwrite", "ahb_hwrite")
    bridge_inst.add_connection("hsize", "ahb_hsize")
    bridge_inst.add_connection("hwdata", "ahb_hwdata")
    bridge_inst.add_connection("hsel", "ahb_hsel")
    bridge_inst.add_connection("hrdata", "ahb_hrdata")
    bridge_inst.add_connection("hready", "ahb_hready")
    bridge_inst.add_connection("hresp", "ahb_hresp")
    bridge_inst.add_connection("paddr", "apb_paddr")
    bridge_inst.add_connection("psel", "apb_psel")
    bridge_inst.add_connection("penable", "apb_penable")
    bridge_inst.add_connection("pwrite", "apb_pwrite")
    bridge_inst.add_connection("pwdata", "apb_pwdata")
    bridge_inst.add_connection("prdata", "apb_prdata")
    bridge_inst.add_connection("pready", "apb_pready")
    top_module.add_instance(bridge_inst)
    
    # GPIO控制器实例
    gpio_inst = create_instance("u_gpio_ctrl", "cmsdk_iop_gpio")
    gpio_inst.add_connection("FCLK", "internal_clk")
    gpio_inst.add_connection("HCLK", "internal_clk")
    gpio_inst.add_connection("HRESETn", "sys_rst_n")
    gpio_inst.add_connection("i_IOSEL", "apb_psel")
    gpio_inst.add_connection("i_IOADDR", "apb_paddr[11:0]")
    gpio_inst.add_connection("i_IOWRITE", "apb_pwrite")
    gpio_inst.add_connection("i_IOSIZE", "", True, "2'b10")  # 常量连接
    gpio_inst.add_connection("i_IOTRANS", "apb_penable")
    gpio_inst.add_connection("i_IOWDATA", "apb_pwdata")
    gpio_inst.add_connection("ECOREVNUM", "", True, "4'h0")  # 常量连接
    gpio_inst.add_connection("PORTIN", "gpio_pins")
    gpio_inst.add_connection("o_IORDATA", "apb_prdata")
    gpio_inst.add_connection("PORTOUT", "gpio_out")
    gpio_inst.add_connection("PORTEN", "gpio_oen")
    gpio_inst.add_connection("PORTFUNC", "gpio_func")
    gpio_inst.add_connection("GPIOINT", "gpio_interrupts")
    gpio_inst.add_connection("o_COMBINT", "gpio_combined_int")
    # 参数重写
    gpio_inst.set_parameter("GPIO_WIDTH", 16)
    gpio_inst.set_parameter("IOADDR_WIDTH", 12)
    top_module.add_instance(gpio_inst)
    
    # 中断控制器实例
    irq_inst = create_instance("u_irq_ctrl", "interrupt_controller")
    irq_inst.add_connection("clk", "internal_clk")
    irq_inst.add_connection("rst_n", "sys_rst_n")
    irq_inst.add_connection("irq_in", "gpio_interrupts")
    irq_inst.add_connection("irq_out", "system_irq")
    irq_inst.add_connection("irq_ack", "irq_ack_signal")
    irq_inst.set_parameter("IRQ_WIDTH", 16)
    top_module.add_instance(irq_inst)
    
    # LED驱动器实例
    led_inst = create_instance("u_led_driver", "led_driver")
    led_inst.add_connection("clk", "slow_clk")
    led_inst.add_connection("rst_n", "sys_rst_n")
    led_inst.add_connection("gpio_data", "gpio_out[7:0]")
    led_inst.add_connection("enable", "gpio_oen[0]")
    led_inst.add_connection("led_out", "led_display")
    led_inst.set_parameter("BLINK_RATE", 500)
    top_module.add_instance(led_inst)
    
    design.add_module(top_module)
    
    # 添加文件信息
    design.add_file("/home/zhhe/work/sv_parser/rtl/clk_generator.v")
    design.add_file("/home/zhhe/work/sv_parser/rtl/cmsdk_iop_gpio.v")
    design.add_file("/home/zhhe/work/sv_parser/rtl/interrupt_controller.v")
    design.add_file("/home/zhhe/work/sv_parser/rtl/ahb_to_apb_bridge.v")
    design.add_file("/home/zhhe/work/sv_parser/rtl/led_driver.v")
    design.add_file("/home/zhhe/work/sv_parser/rtl/gpio_demo_top.v")
    
    return design

def create_simple_demo_design() -> DesignInfo:
    """创建简化的demo设计 - 用于快速测试"""
    design = create_design()
    
    # 简单的计数器模块
    counter = create_module("counter")
    counter.add_port(create_input_port("clk"))
    counter.add_port(create_input_port("rst_n"))
    counter.add_port(create_input_port("enable"))
    counter.add_port(create_output_port("count", 8))
    counter.add_parameter(create_parameter("WIDTH", 8, "integer"))
    design.add_module(counter)
    
    # 简单的多路选择器
    mux = create_module("mux2to1")
    mux.add_port(create_input_port("sel"))
    mux.add_port(create_input_port("in0", 8))
    mux.add_port(create_input_port("in1", 8))
    mux.add_port(create_output_port("out", 8))
    design.add_module(mux)
    
    # 简单顶层
    simple_top = create_module("simple_top", is_top=True)
    simple_top.add_port(create_input_port("clk"))
    simple_top.add_port(create_input_port("rst"))
    simple_top.add_port(create_input_port("select"))
    simple_top.add_port(create_input_port("data_in", 8))
    simple_top.add_port(create_output_port("data_out", 8))
    
    # 实例化
    cnt_inst = create_instance("u_counter", "counter")
    cnt_inst.add_connection("clk", "clk")
    cnt_inst.add_connection("rst_n", "~rst")
    cnt_inst.add_connection("enable", "", True, "1'b1")
    cnt_inst.add_connection("count", "counter_value")
    simple_top.add_instance(cnt_inst)
    
    mux_inst = create_instance("u_mux", "mux2to1")
    mux_inst.add_connection("sel", "select")
    mux_inst.add_connection("in0", "counter_value")
    mux_inst.add_connection("in1", "data_in")
    mux_inst.add_connection("out", "data_out")
    simple_top.add_instance(mux_inst)
    
    design.add_module(simple_top)
    
    return design

def safe_get_validation_info(validation_result):
    """安全获取验证信息，处理不同的数据结构"""
    if isinstance(validation_result, dict):
        return {
            'error_count': validation_result.get('error_count', len(validation_result.get('errors', []))),
            'warning_count': validation_result.get('warning_count', len(validation_result.get('warnings', []))),
            'missing_modules': validation_result.get('missing_modules', validation_result.get('errors', []))
        }
    elif isinstance(validation_result, list):
        # 如果返回的是错误列表
        errors = [item for item in validation_result if item.get('type') == 'error']
        warnings = [item for item in validation_result if item.get('type') == 'warning']
        return {
            'error_count': len(errors),
            'warning_count': len(warnings),
            'missing_modules': [item.get('message', str(item)) for item in errors]
        }
    else:
        # 默认情况
        return {
            'error_count': 0,
            'warning_count': 0,
            'missing_modules': []
        }

def test_demo_data_export():
    """测试数据导出功能"""
    # 创建完整demo设计
    design = create_demo_design()
    
    # 导出为JSON
    design.export_json("gpio_demo_design.json", include_flow_data=True)
    
    # 获取React Flow数据
    flow_data = design.generate_flow_data()
    
    # 获取层次结构
    hierarchy = design.build_hierarchy()
    
    # 获取统计信息
    stats = design.stats
    
    # 获取验证结果（安全处理）
    try:
        validation_raw = design.validate_design()
        validation = safe_get_validation_info(validation_raw)
    except Exception as e:
        print(f"验证过程出错: {e}")
        validation = {
            'error_count': 0,
            'warning_count': 1,
            'missing_modules': [f"验证功能异常: {str(e)}"]
        }
    
    print("=== Demo设计统计 ===")
    print(f"模块数量: {stats['modules']['total']}")
    print(f"实例数量: {stats['instances']['total']}")
    print(f"端口数量: {stats['ports']['total']}")
    print(f"层次深度: {stats['hierarchy']['max_depth']}")
    print(f"顶层模块: {stats['modules']['top_module']}")
    
    print("\n=== React Flow 数据 ===")
    print(f"节点数量: {len(flow_data['nodes'])}")
    print(f"边数量: {len(flow_data['edges'])}")
    
    print("\n=== 验证结果 ===")
    print(f"错误数量: {validation['error_count']}")
    print(f"警告数量: {validation['warning_count']}")
    if validation['missing_modules']:
        print(f"问题列表: {validation['missing_modules']}")
    
    return design, flow_data, hierarchy, stats, validation

def create_test_api_response():
    """创建用于前端API测试的响应数据"""
    design = create_demo_design()
    
    # 安全获取验证结果
    try:
        validation_raw = design.validate_design()
        validation = safe_get_validation_info(validation_raw)
    except Exception as e:
        validation = {
            'error_count': 0,
            'warning_count': 1,
            'missing_modules': [f"验证功能异常: {str(e)}"],
            'errors': [],
            'warnings': [{'message': f"验证功能异常: {str(e)}", 'type': 'warning'}]
        }
    
    # 模拟API响应格式
    api_response = {
        "status": "success",
        "message": "Design loaded successfully",
        "data": {
            "design_info": design.to_dict(),
            "flow_data": design.generate_flow_data(),
            "hierarchy": design.build_hierarchy().to_dict(),
            "stats": design.stats,
            "validation": validation
        },
        "metadata": {
            "parse_time": "0.125s",
            "file_count": len(design.file_list),
            "total_lines": 1250,
            "timestamp": "2025-06-20T10:30:00Z"
        }
    }
    
    return api_response

if __name__ == "__main__":
    # 运行测试
    print("生成Demo测试数据...")
    
    try:
        # 测试完整设计
        design, flow_data, hierarchy, stats, validation = test_demo_data_export()
        
        # 测试简化设计
        print("\n=== 简化设计测试 ===")
        simple_design = create_simple_demo_design()
        simple_stats = simple_design.stats
        print(f"简化设计模块数: {simple_stats['modules']['total']}")
        
        # 生成API响应测试数据
        print("\n=== 生成API测试数据 ===")
        api_data = create_test_api_response()
        
        # 保存测试数据
        import json
        with open("demo_api_response.json", "w", encoding="utf-8") as f:
            json.dump(api_data, f, indent=2, ensure_ascii=False)
        
        with open("simple_design.json", "w", encoding="utf-8") as f:
            json.dump(simple_design.to_dict(), f, indent=2, ensure_ascii=False)
        
        print("测试数据已生成:")
        print("- gpio_demo_design.json (完整GPIO设计)")
        print("- demo_api_response.json (API响应格式)")
        print("- simple_design.json (简化设计)")
        
        print("\n✅ Demo测试数据生成完成!")
        
    except Exception as e:
        print(f"❌ 生成过程中出现错误: {e}")
        import traceback
        traceback.print_exc()