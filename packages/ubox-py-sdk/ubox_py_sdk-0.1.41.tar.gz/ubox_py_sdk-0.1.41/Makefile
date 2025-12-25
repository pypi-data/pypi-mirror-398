.PHONY: help install install-dev test test-cov lint format clean build publish

# 默认目标
help:
	@echo "可用的命令:"
	@echo "  install      - 安装生产依赖"
	@echo "  install-dev  - 安装开发依赖"
	@echo "  test         - 运行测试"
	@echo "  test-cov     - 运行测试并生成覆盖率报告"
	@echo "  lint         - 运行代码检查"
	@echo "  format       - 格式化代码"
	@echo "  clean        - 清理临时文件"
	@echo "  build        - 构建包"
	@echo "  publish      - 发布包到PyPI"

# 安装生产依赖
install:
	uv pip install -e .

# 安装开发依赖
install-dev:
	uv pip install -e ".[dev]"

# 运行代码检查
lint:
	mypy src/

# 格式化代码
format:
	black src/
	isort src/

# 清理临时文件
clean:
	find . -type f -name "*.pyc" -delete
	find . -type d -name "__pycache__" -delete
	find . -type d -name "*.egg-info" -exec rm -rf {} +
	find . -type d -name ".pytest_cache" -exec rm -rf {} +
	find . -type d -name "htmlcov" -exec rm -rf {} +
	find . -type f -name ".coverage" -delete

# 构建包
build:
	uv build

# 发布包到PyPI（需要配置）
publish:
	uv publish

# 运行示例
example:
	python examples/basic_usage.py