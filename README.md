# Light-Fuzz-Gen

基于大语言模型的轻量级C/C++程序Fuzzing Harness生成工具。

## 项目简介

Light-Fuzz-Gen 是一个利用大语言模型（如 GPT-3.5、GPT-4 等）自动生成 Fuzzing Harness 代码的工具。该工具通过提供目标函数的签名、参数类型和返回类型等信息，自动生成适用于模糊测试（Fuzzing）的测试用例。

## 目录结构

```
light-fuzz-gen/
├── agent/                   # 代理模块，处理与大语言模型的交互
│   ├── model.py             # 大模型 API 交互
│   ├── config.py            # 配置文件处理
│   ├── utils.py             # 工具函数
│   └── __init__.py          # 模块初始化
├── benchmark-sets/          # 存放目标函数配置文件
│   └── cups.yaml            # CUPS 库相关函数配置示例
├── harness/                 # 生成的 Harness 代码输出目录
├── logs/                    # 日志输出目录
├── prompts/                 # 存放prompt模板
│   └── multi_function_harness.txt
├── main.py                  # 主程序入口
├── README.md                # 项目说明文档
└── .gitignore               # Git 忽略配置
```

## 使用方法

1. 安装依赖:

```bash
pip install -r requirements.txt
```

2. 设置环境变量:

创建 `.env` 文件并添加以下内容:

```
OPENAI_API_KEY=your_api_key_here
OPENAI_BASE_URL=https://api.openai.com/v1  # 可选使用自定义 API
```

3. 运行程序:

```bash
python main.py cups  # 使用 benchmark-sets/cups.yaml 配置文件
```

## 配置文件格式

在 `benchmark-sets` 目录下创建 YAML 格式的配置文件，例如:

```yaml
functions:
  - name: ippReadIO
    params:
      - name: src
        type: void *
      - name: cb
        type: ipp_io_cb_t
      - name: blocking
        type: int
      - name: parent
        type: ipp_t *
      - name: ipp
        type: ipp_t *
    return_type: ipp_state_t
    signature: ipp_state_t ippReadIO(void *, ipp_io_cb_t, int, ipp_t *, ipp_t *)
  - name: cupsFileOpen
    params:
      - name: filename
        type: const char *
      - name: mode
        type: const char *
    return_type: cups_file_t *
    signature: cups_file_t * cupsFileOpen(const char *, const char *)
  - name: cupsFileClose
    params:
      - name: fp
        type: cups_file_t *
    return_type: int
    signature: int cupsFileClose(cups_file_t *)
language: c
project: cups
target_name: fuzz_ipp_gen
target_path: /src/cups/ossfuzz/fuzz_ipp_gen.c
```

## 提示模板

提示模板位于 `prompts/multi_function_harness.txt`，其中使用 `{placeholder}` 格式的占位符，会被实际的函数信息替换。

## 多函数处理

系统会分析配置文件中的多个函数，理解它们之间的关系，并生成一个能够合理调用这些函数的harness代码：

1. 系统会自动提取YAML文件中定义的所有函数信息
2. 分析函数之间的可能调用关系，并生成一个能够有效测试这些函数的harness
3. 对于有明显调用关系的函数（如初始化/处理/清理），生成的harness会按照逻辑顺序调用这些函数
