## 现状与问题
- 模块导入即打印信息，产生副作用：`e:\src\vxutils\src\vxutils\logger.py:19-23`
- 在未安装 colorama 时仍引用 `Style.RESET_ALL`，会导致运行时报错：`e:\src\vxutils\src\vxutils\logger.py:50-53`
- 为文件日志做了 `'%(log_color)s'/'%(reset)s'` 替换，但当前格式并未使用这些占位符，逻辑不一致：`e:\src\vxutils\src\vxutils\logger.py:104`
- 异步日志未提供停止机制，`QueueListener` 未被持有；`QueueHandler` 等级用字符串不够规范：`e:\src\vxutils\src\vxutils\logger.py:120-129`
- 使用命名 logger 时可能出现重复输出（与父 logger 叠加），未控制 `propagate`。
- 文件轮转策略固定（按天、间隔 7、保留 7），缺乏可配置性：`e:\src\vxutils\src\vxutils\logger.py:112-114`

## 改进目标
- 无副作用的模块导入；仅在配置时初始化彩色输出
- 在无 colorama 环境下安全退化为无色输出
- 异步日志更易用：可持有并停止监听器
- 控制台彩色、文件无色，逻辑一致且清晰
- 防止重复日志（合理设置 `propagate`）
- 文件轮转与日期格式可配置，默认值合理

## 修改方案
1. 移除导入时的 `print`，延迟初始化 colorama
   - 在 `loggerConfig` 里按 `colored=True` 才尝试加载 colorama
   - 未安装时设置 `reset_code=''`，避免对 `Style` 的依赖
2. 重写 `VXColoredFormatter`
   - 根据实例注入的 `reset_code` 与颜色映射工作；不再直接引用模块级 `Style`
   - 当不支持彩色或 `colored=False` 时返回原始消息
3. 增强 `loggerConfig`
   - 对命名 logger 设置 `logger.propagate=False`，避免与根 logger 重复输出
   - 统一使用 `logging.DEBUG` 等级常量；`QueueListener` 启动后将其挂到 `logger`（如 `logger._vx_listener`）
   - 移除对 `'%(log_color)s'/'%(reset)s'` 的替换，或改为真正支持占位符（建议移除，改由 Formatter 统一包裹颜色）
   - 新增文件轮转参数：`when='D'`, `interval=7`, `backup_count=7` 可配置
   - 设置默认 `datefmt='%Y-%m-%d %H:%M:%S'`
   - 可选支持 `stream` 参数以指定控制台输出流
4. 提供停止监听器的辅助函数（例如 `stop_logger(logger)`）以优雅关闭异步日志

## 验证方案
- 在安装与未安装 colorama 两种环境下运行示例，确认无异常、控制台着色正确
- 开启/关闭异步模式，验证日志均被处理，程序退出时可停止监听器
- 指定 `filename` 后检查文件内容无 ANSI 码，轮转与保留策略生效
- 使用命名 logger 验证无重复输出

## 兼容性与影响
- 保持现有 API，不破坏调用方式；新增参数均有默认值，与当前行为一致或更合理
- 控制台与文件输出的格式统一且更健壮；无 colorama 环境不再报错

## 交付
- 更新的 `logger.py` 实现
- 简短示例脚本用于本地验证（不引入额外依赖）

请确认上述方案，确认后我将直接完成改动并进行本地验证。