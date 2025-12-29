def create_test_methods(cls, case_data, func_generator, name_prefix="test_"):
    """
    通用方法：根据case_data动态创建测试方法，并设置为指定的test_name

    :param cls: 测试类
    :param case_data: 测试数据列表，每个元素是一个dict
    :param func_generator: 生成测试函数的方法，接受data参数
    :param name_prefix: 测试方法名前缀，默认"test_"
    """
    # 预处理所有测试数据，避免闭包陷阱
    test_items = []
    for idx, data in enumerate(case_data):
        case_title = data.get("case_title")
        if not case_title:
            raise ValueError(f"第{idx}条测试数据缺少 'case_title' 字段")

        # 清理标题中的特殊字符，确保方法名合法
        clean_title = "".join(c if c.isalnum() or c in ['_', '-'] else '_' for c in case_title)
        test_name = f"{name_prefix}{clean_title}"

        test_items.append((test_name, data))

    # 分离数据处理和方法创建步骤
    for test_name, data in test_items:
        # 使用偏函数解决闭包问题
        import functools
        test_func = func_generator(data)

        # 设置__doc__用于报告展示描述信息
        order_id = data.get("order_id", None)
        if order_id:
            test_func.__doc__ = "customer_id : " + data.get("customer_id") + " | " + "order_id : " + order_id + " | " + data.get('description', case_title)
        else:
            test_func.__doc__ = "customer_id : " + data.get("customer_id") + " | " + data.get('description', case_title)

        # 动态绑定方法到测试类
        setattr(cls, test_name, test_func)
