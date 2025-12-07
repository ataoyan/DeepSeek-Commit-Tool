"""
PyInstaller打包脚本
将Python应用程序打包为单个exe文件
"""

import PyInstaller.__main__
import os
import sys
from pathlib import Path

def build():
    """执行打包"""
    print("=" * 50)
    print("DeepSeek Commit Tool - 打包脚本（CLI版）")
    print("=" * 50)
    
    # 获取项目根目录
    project_root = Path(__file__).parent.resolve()
    
    # 检查必要文件
    required_files = ['main.py', 'config.py', 'git_helper.py', 'deepseek_api.py']
    for file in required_files:
        if not (project_root / file).exists():
            print(f"错误: 未找到文件 {file}")
            sys.exit(1)
    
    # 图标路径
    icon_path = project_root / 'icon.ico'
    icon_arg = []
    if icon_path.exists():
        icon_arg = [f'--icon={icon_path}']
        print(f"使用图标: {icon_path}")
    else:
        print("警告: 未找到 icon.ico，将使用默认图标")
    
    # PyInstaller参数
    args = [
        'main.py',  # 主入口文件
        '--name=dsc',  # 输出exe名称
        '--onefile',  # 打包为单个文件
        '--clean',  # 清理临时文件
        '--noconfirm',  # 覆盖输出目录
        
        # 隐藏导入（确保包含）
        '--hidden-import=requests',
        '--hidden-import=json',
        '--hidden-import=subprocess',
        '--hidden-import=pathlib',
        '--hidden-import=logging',
        '--hidden-import=queue',
        '--hidden-import=threading',
        '--hidden-import=winreg',  # Windows注册表访问
        
        # 排除不需要的模块（减小体积）
        '--exclude-module=matplotlib',
        '--exclude-module=numpy',
        '--exclude-module=pandas',
        '--exclude-module=scipy',
        '--exclude-module=PIL',
        
        # 添加数据文件（如果需要）
        # '--add-data=icon.ico;.',  # Windows格式
        
        # 版本信息（可选）
        # '--version-file=version.txt',
    ]
    
    # 添加图标参数
    args.extend(icon_arg)
    
    # UPX压缩（如果可用）
    upx_dir = os.environ.get('UPX_DIR')
    if upx_dir and Path(upx_dir).exists():
        args.append(f'--upx-dir={upx_dir}')
        print(f"使用UPX压缩: {upx_dir}")
    else:
        print("提示: 未设置UPX_DIR环境变量，跳过UPX压缩")
    
    print("\n开始打包...")
    print(f"PyInstaller参数: {' '.join(args)}")
    print("-" * 50)
    
    try:
        # 执行打包
        PyInstaller.__main__.run(args)
        
        print("-" * 50)
        print("打包完成！")
        print(f"输出文件: {project_root / 'dist' / 'dsc.exe'}")
        print("\n提示:")
        print("1. 生成的exe文件在 dist 目录中")
        print("2. 首次运行可能需要几秒钟解压")
        print("3. 可以将exe文件复制到任何位置使用")
        
    except Exception as e:
        print(f"\n打包失败: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == '__main__':
    build()

