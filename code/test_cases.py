import yaml
import os

def load_constraints():
    """加载代谢物约束知识"""
    yaml_path = os.path.join(os.path.dirname(__file__), "../docs/metabolite_constraints.yaml")
    with open(yaml_path, 'r', encoding='utf-8') as f:
        data = yaml.safe_load(f)
    return data['metabolites']

def run_individual_test(history, metabolite_info):
    """执行单个代谢物的测试用例"""
    name = metabolite_info['name']
    var_names = metabolite_info['variable_names']
    normal_range = metabolite_info['normal_range']
    min_val = normal_range['min']
    max_val = normal_range['max']
    unit = metabolite_info.get('unit', 'mM')
    
    # 统一单位到 mmol/L (假设模拟器单位为 mmol/L)
    if unit in ['μM', 'uM']:
        min_val *= 1e-3
        max_val *= 1e-3
    
    failures = []
    found_var = None
    if not history:
        return False, "无模拟数据"

    for v in var_names:
        if v in history[0]:
            found_var = v
            break
            
    if not found_var:
        return None, f"未在模拟结果中找到变量 {var_names}" # 返回 None 表示跳过该测试（变量未定义）
    
    for entry in history:
        val = entry.get(found_var, 0.0)
        # 容忍浮点数微小误差
        if val < min_val - 1e-7 or val > max_val + 1e-7:
            failures.append(f"时间 {entry['time']:.2f}h: {val:.4f} (范围: [{min_val}, {max_val}] {unit})")
            
    if not failures:
        return True, "通过"
    else:
        # 返回前 2 个失败原因
        reason = "; ".join(failures[:2])
        if len(failures) > 2:
            reason += f" ... (共 {len(failures)} 处超出范围)"
        return False, reason

def get_all_tests():
    """获取所有代谢物测试用例字典"""
    metabolites = load_constraints()
    test_cases = {}
    for m in metabolites:
        # 创建测试函数
        def make_test(info):
            return lambda hist: run_individual_test(hist, info)
        
        test_key = m['name']
        test_cases[test_key] = make_test(m)
    return test_cases
