#!/usr/bin/env python3
"""测试plsm库的功能"""

from plsm import ServiceManager, ServiceConfig

def test_service_manager():
    """测试ServiceManager功能"""
    print("=== 测试ServiceManager功能 ===")
    
    try:
        # 创建服务管理器
        manager = ServiceManager(sudo=True)
        print("✅ ServiceManager创建成功")
        
        # 列出所有可用方法
        methods = [method for method in dir(manager) if not method.startswith('_')]
        print("\n📋 ServiceManager可用方法:")
        for method in sorted(methods):
            print(f"  - {method}")
        
        # 测试列出所有服务
        print("\n🔍 尝试列出所有服务:")
        try:
            services = manager.list_all_services()
            print(f"✅ 找到 {len(services)} 个服务")
            if services:
                for service in services[:3]:  # 只显示前3个
                    print(f"  - {service.name}: {service.status.value}")
        except Exception as e:
            print(f"❌ 列出服务时出错: {e}")
        
        # 检查openssh-sync服务是否存在
        service_name = 'openssh-sync'
        print(f"\n🔎 检查服务 '{service_name}' 是否存在:")
        try:
            # 尝试获取服务信息
            service_info = manager.get_service_info(service_name)
            if service_info:
                print(f"✅ 服务 '{service_name}' 已存在")
                print(f"   状态: {service_info.status.value}")
            else:
                print(f"❌ 服务 '{service_name}' 不存在")
        except Exception as e:
            print(f"❌ 检查服务时出错: {e}")
        
        # 测试ServiceConfig
        print("\n⚙️  测试ServiceConfig功能:")
        try:
            config = ServiceConfig(
                name=service_name,
                description='OpenSSH Synchronization Service',
                exec_start='/usr/local/bin/openssh-sync daemon',
                working_directory='/opt/openssh',
                user='root',
                group='root',
                restart='always'
            )
            print("✅ ServiceConfig创建成功")
            print(f"   服务名称: {config.name}")
            print(f"   服务描述: {config.description}")
            print(f"   启动命令: {config.exec_start}")
            
            # 测试创建服务
            print(f"\n🚀 尝试创建服务 '{service_name}':")
            try:
                result = manager.create_service(config)
                print(f"✅ 服务创建成功: {result}")
            except Exception as e:
                print(f"❌ 服务创建失败: {e}")
                
        except Exception as e:
            print(f"❌ ServiceConfig创建失败: {e}")
            
    except Exception as e:
        print(f"❌ ServiceManager初始化失败: {e}")

if __name__ == "__main__":
    test_service_manager()