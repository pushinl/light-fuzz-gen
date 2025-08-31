# 快速开始指南

## 🚀 快速开始

### 1. 安装依赖

```bash
pip install -r requirements.txt
```

### 2. 设置API密钥

```bash
export OPENAI_API_KEY="your-openai-api-key"
```

### 3. 生成YAML配置文件

```bash
# 基本用法
python run_agent.py cups-filters --project-name cups-filters

# 指定目标仓库（本地目录下准备）
python run_agent.py cups-filters \
    --project-name cups-filters \
    --target-repo https://github.com/OpenPrinting/cups-filters

# 详细输出
python run_agent.py cups-filters --verbose
```

## 🔧 工作流程

1. **代码扫描** - 读取目标仓库的C/C++源代码
2. **函数提取** - 使用正则表达式提取函数定义和签名
3. **LLM分析** - 调用OpenAI API分析函数功能和分类
4. **YAML生成** - 根据分析结果生成模糊测试配置文件

## 🎯 输出示例

```yaml
"functions":
  - "name": "ppdFilterCUPSWrapper"
    "signature": "int ppdFilterCUPSWrapper(int argc, char *argv[], cf_filter_filter_func_t filter_func, void *parameters, int *JobCanceled);"
  - "name": "cfFilterTextToPDF"
    "signature": "int cfFilterTextToPDF(int inputfd, int outputfd, int inputseekable, cf_filter_data_t *data, void *parameters);"
"additional": "文本处理过滤器，支持文本到PDF的转换"
"language": "c"
"project": "cups-filters"
"target_name": "fuzz_text_processing"
"target_repo": "https://github.com/OpenPrinting/cups-filters"
"target_path": "/src/cups-filters/ossfuzz/fuzz_text_processing.c"
"target_header_files": ["cupsfilters/filter.h", "ppd/ppd-filter.h"]
```

## 🛠️ 高级配置

### 限制处理函数数量

```bash
python run_agent.py cups-filters --max-functions 20
```

### 自定义输出目录

```bash
python run_agent.py cups-filters --output-dir custom-benchmark-sets
```

### 仅分析不生成

```bash
python run_agent.py cups-filters --dry-run
```

## 🐛 故障排除

### 常见问题

1. **API密钥错误**
   ```
   解决：export OPENAI_API_KEY="your-key"
   ```

2. **未找到函数**
   ```
   解决：检查代码格式，确保符合标准C语法
   ```

3. **编码错误**
   ```
   解决：确保文件编码为UTF-8
   ```

## 📊 性能优化

- 单次处理建议不超过50个函数
- 大型项目可分批处理
- 使用 `--max-functions` 参数控制处理量