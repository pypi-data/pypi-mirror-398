
#!/usr/bin/env python3
"""
环境变量管理模块集成测试

验证模块在项目中的集成情况
"""

import sys
import os
from pathlib import Path

# 确保可以导入项目模块
project_root = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(project_root))

def test_import():
    """测试模块导入"""
    try:
        # 测试直接导入
        from src.autocoder.common.env_manager import (
            EnvManager, Environment,
            get_environment, is_production, is_development
        )
        print("✓ 模块导入成功")
        return True
    except ImportError as e:
        print(f"✗ 模块导入失败: {e}")
        return False

def test_basic_functionality():
    """测试基本功能"""
    try:
        from src.autocoder.common.env_manager import (
            get_environment, is_production, is_development,
            get_env, set_env
        )
        
        # 测试环境检测
        env = get_environment()
        print(f"✓ 当前环境: {env.value}")
        
        # 测试环境变量设置和获取
        test_key = "TEST_INTEGRATION_VAR"
        test_value = "integration_test_value"
        
        set_env(test_key, test_value)
        retrieved_value = get_env(test_key)
        
        if retrieved_value == test_value:
            print("✓ 环境变量设置和获取功能正常")
        else:
            print(f"✗ 环境变量功能异常: 期望 {test_value}, 实际 {retrieved_value}")
            return False
        
        # 清理测试环境变量
        if test_key in os.environ:
            del os.environ[test_key]
        
        return True
        
    except Exception as e:
        print(f"✗ 基本功能测试失败: {e}")
        return False

def test_with_existing_project_modules():
    """测试与现有项目模块的兼容性"""
    try:
        # 测试与现有的 detect_env 函数兼容性
        from src.autocoder.common import detect_env
        from src.autocoder.common.env_manager import get_env_info
        
        # 获取现有的环境信息
        existing_env_info = detect_env()
        print(f"✓ 现有环境检测正常: {existing_env_info.os_name}")
        
        # 获取新模块的环境信息
        new_env_info = get_env_info()
        print(f"✓ 新环境管理模块正常: {new_env_info['environment']}")
        
        return True
        
    except Exception as e:
        print(f"✗ 项目模块兼容性测试失败: {e}")
        return False

def test_environment_switching():
    """测试环境切换功能"""
    try:
        from src.autocoder.common.env_manager import (
            get_environment, is_production, is_development, set_env
        )
        
        # 保存原始环境
        original_env = os.environ.get("AUTO_CODER_ENV")
        
        # 测试切换到生产环境
        set_env("AUTO_CODER_ENV", "production")
        if is_production() and not is_development():
            print("✓ 生产环境切换成功")
        else:
            print("✗ 生产环境切换失败")
            return False
        
        # 测试切换到开发环境
        set_env("AUTO_CODER_ENV", "development")
        if is_development() and not is_production():
            print("✓ 开发环境切换成功")
        else:
            print("✗ 开发环境切换失败")
            return False
        
        # 恢复原始环境
        if original_env:
            os.environ["AUTO_CODER_ENV"] = original_env
        elif "AUTO_CODER_ENV" in os.environ:
            del os.environ["AUTO_CODER_ENV"]
        
        return True
        
    except Exception as e:
        print(f"✗ 环境切换测试失败: {e}")
        return False

def main():
    """主测试函数"""
    print("环境变量管理模块集成测试")
    print("=" * 50)
    
    tests = [
        test_import,
        test_basic_functionality,
        test_with_existing_project_modules,
        test_environment_switching,
    ]
    
    passed = 0
    total = len(tests)
    
    for test in tests:
        print(f"\n运行测试: {test.__name__}")
        if test():
            passed += 1
        else:
            print(f"测试 {test.__name__} 失败")
    
    print(f"\n测试结果: {passed}/{total} 通过")
    
    if passed == total:
        print("\u2713 所有集成测试通过！")
        return True
    else:
        print("\u2717 部分集成测试失败")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)

