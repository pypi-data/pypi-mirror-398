import sys
import traceback
import os


def error_info(show_details=False) -> str:
    """
    获取用户代码的异常调用链，自动过滤系统库
    
    Args:
        show_details: 是否打印详细信息到控制台
    
    Returns:
        格式化的错误信息字符串
    """
    exc_type, exc_value, exc_tb = sys.exc_info()
    
    if exc_type is None:
        return "No exception occurred"
    
    # 提取完整的调用栈
    tb_list = traceback.extract_tb(exc_tb)
    
    # 过滤出用户代码（排除系统库和site-packages）
    user_frames = []
    for frame in tb_list:
        filepath = frame.filename
        # 排除系统库路径
        if (not filepath.startswith('<') and  # 排除 <stdin> 等
            'site-packages' not in filepath and
            'lib/python' not in filepath and
            '/usr/lib' not in filepath and
            'Python.framework' not in filepath and
            'AppData\\Local' not in filepath):  # Windows路径
            user_frames.append(frame)
    
    # 如果没有用户代码帧，使用全部
    if not user_frames:
        user_frames = tb_list
    
    # 构建错误信息
    error_lines = []
    
    # 显示用户代码调用链
    if len(user_frames) > 1:
        error_lines.append("Error Code Call Chain:")
        for i, frame in enumerate(user_frames, 1):
            filename = os.path.basename(frame.filename)  # 只显示文件名
            error_lines.append(f"  [{i}] {filename}:{frame.lineno} in {frame.name}()")
            if frame.line:
                error_lines.append(f"      → {frame.line.strip()}")
        error_lines.append("")
    
    # 最终错误位置和原因
    last_frame = user_frames[-1]
    error_lines.append(f"✗ Error at: {os.path.basename(last_frame.filename)}:{last_frame.lineno}")
    error_lines.append(f"  Function: {last_frame.name}()")
    if last_frame.line:
        error_lines.append(f"  Code: {last_frame.line.strip()}")
    error_lines.append(f"  Reason: {exc_type.__name__}: {exc_value}")
    
    result = "\n".join(error_lines)
    
    # 可选：打印详细信息
    if show_details:
        print("=" * 70)
        print(result)
        print("=" * 70)
    
    # 返回简化的单行信息（用于日志）
    return result