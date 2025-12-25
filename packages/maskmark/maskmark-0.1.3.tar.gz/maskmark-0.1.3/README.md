# 项目简介

本项目提供了一个具备**数据脱敏**和**数据水印**功能的 SDK 包，基于Python语言开发

## 安装说明

### 环境要求
- Python 3.7 及以上版本

### 安装方式
通过 pip 安装 SDK：
```bash
pip install maskmark
```

### 第三方库依赖
SDK 依赖以下第三方库：
- pymupdf>=1.24.11 - 用于 PDF 文件处理
- pillow>=10.4.0 - 用于图像处理
- filetype>=1.2.0 - 用于文件类型识别
- toml>=0.10.2 - 用于配置文件解析
- python-docx>=1.1.2 - 用于 Word 文件处理
- gmssl>=3.2.2 - 用于加密算法实现
- setuptools>=75.1.0 - 用于包安装

## SDK功能说明

### 数据脱敏功能矩阵
|   脱敏类型 | 字符串 | 数值 | KV数据 | JSON数据 | 备注 |
|   :-:    |:----:|:----:|:----:|:-:|:-:|
| 遮蔽脱敏 | ✅ | ✅</br>返回值为字符串形式 | ✅</br>支持对指定键的值处理 |✅|支持逐一（例如："12345"==>"#####"）或全局遮蔽（例如"12345"==>"#"）|
| 哈希脱敏 | ✅ | ✅</br>返回值为字符串形式 | ✅</br>支持对指定键的值处理 |✅ |支持SHA256与SM3算法|
| 截断脱敏 | ✅ |         ❌          |          ✅           | ✅  |已支持首部截断（例如："12345"==>"345"）、尾部截断（例如："12345"==>"12"）、以及首尾截断保留（例如："12345"==>"15"）|
| 取整脱敏 | ❌ | ✅ | ✅ |✅ |仅支持数值类型的数据|
| 偏移脱敏 | ❌ | ✅ | ✅ |✅ |仅支持数值类型的数据|

注：✅: 已支持 | ❌: 不支持

### 数据水印功能矩阵

| 数据类型 | 文本水印   | 备注 |
| :------:| :------: | :--: |
|   png     |    ✅     |      |
|   jpg     |    ✅     |      |
|   pdf     |    ✅     |      |
|   docx    |    ✅     |      |

注1：文本水印支持`Date`与`Time`关键词，可自动填充当前日期与时间

### 通用功能矩阵

|                        功能                         | 目前状态 | 备注                               |
| :-------------------------------------------------: | :------: | ---------------------------------- |
|   支持临时规则配置，可避免命中多个规则导致误处理    |    ✅     | 通过在函数中指定规则结构体加载配置 |
|         支持基于配置文件进行脱敏与水印处理          |    ✅     | 配置文件为toml格式                 |
|      水印内容可自定义，默认可记录日期、时刻等       |    ✅     | 详见“水印模板说明”           |
|                      最佳实践                       | ✅  |将SDK打包为了一个Web服务供调用            |

# 规则配置说明

项目支持使用TOML格式的配置文件（rule.toml）来批量定义数据脱敏和水印规则。下面详细介绍配置文件的结构和各配置项的含义。

## 配置文件结构

配置文件包含三个主要部分：
1. Common - 通用配置
2. MaskRule - 脱敏规则（可包含多个规则）
3. MarkRule - 水印规则（可包含多个规则）

## Common部分

```toml
[Common]
Version = 1.0
```
- `Version`: 配置文件版本号

## 脱敏规则（MaskRule）

脱敏规则用于定义数据的脱敏方式，支持多种类型的数据脱敏。每个脱敏规则包含以下配置项：

```toml
[[MaskRule]]
RuleDes = '规则描述'
Type = '规则类型'
Target = '匹配目标'
Method = '处理方法'
Content = { 处理内容配置 }
```

### 配置项说明

- `RuleDes`: 规则描述，用于标识规则的用途
- `Type`: 规则类型，支持的值：
  - `str`: 字符串类型数据
  - `digit`: 数值类型数据
  - `kv`: 键值对类型数据，包括json数据
- `Target`: 匹配目标，使用正则表达式匹配需要处理的数据
- `Method`: 处理方法，根据数据类型不同支持不同的处理方法
- `Content`: 处理内容配置，根据Method的不同而不同

### 各数据类型支持的处理方法及配置参数

#### 字符串类型 (str)

支持的处理方法：
- `mask`: 遮蔽处理
  - 配置参数：
    - `m_type`: 遮蔽方式，可选值: "text" (逐个替换), "re" (正则表达式替换)
    - `char`: 遮蔽字符
    - `pattern`: 遮蔽部分的正则表达式
- `hash`: 哈希处理
  - 配置参数：
    - `hash_type`: 哈希算法类型
- `truncate`: 截断处理
  - 配置参数：
    - `start`: 保留数据开始位置 (未指定则从头开始)
    - `end`: 保留数据结束位置 (未指定则保留到字符串末尾)
    - `inverse`: 是否反选，可选值: true (反选)，false (默认)

#### 数值类型 (digit)

支持的处理方法：
- `round`: 取整处理
  - 配置参数：
    - `place`: 保留位数，1代表第一个小数位，0代表取整，-1代表个位，以此类推
- `offset`: 偏移处理
  - 配置参数：
    - `offset`: 偏移量
- `hash`: 哈希处理
  - 配置参数：
    - `hash_type`: 哈希算法类型

#### 键值对类型 (kv)

支持的处理方法：
- `rule`: 引用其他规则
  - 配置参数：
    - `rule`: 引用的规则名称
- 其他方法: kv类型可以使用字符串和数值类型支持的所有方法，会根据值的类型自动调用对应的处理函数
  - 配置参数：与对应的数据类型处理方法相同

### 常见脱敏规则示例

1. **中文姓名脱敏** (mask 方法示例)

```toml
[[MaskRule]]
RuleDes = '中文姓名脱敏规则（两个字：李#）'
Type = 'str'
Target = "^[\\u4e00-\\u9fa5]{2}$"
Method = 'mask'
Content = { m_type = 're', char = '\1#', pattern = '^(\S)\S$' }
```

2. **身份证号脱敏**

```toml
[[MaskRule]]
RuleDes = '身份证号'
Type = 'str'
Target = '^[1-9]\d{5}(18|19|([23]\d))\d{2}((0[1-9])|(10|11|12))(([0-2][1-9])|10|20|30|31)\d{3}[0-9Xx]$
Method = 'mask'
Content = { m_type = 're', char = '\1*********\2', pattern = '^(\d{6})\d{9}(\d{3})$' }
```

3. **手机号脱敏**

```toml
[[MaskRule]]
RuleDes = '手机号，满足三大运营商格式要求,遮蔽规则'
Type = 'str'
Target = '^(13[0-9]|14[5-9]|15[0-3,5-9]|16[2,5-7]|17[0-8]|18[0-9]|19[1,8,9])\d{8}$'
Method = 'mask'
Content = { m_type = 're', char = '\1****\2', pattern = '^(\d{3})\d{4}(\d{4})$' }
```

4. **数值取整处理**

```toml
[[MaskRule]]
RuleDes = '对任意整数值保留到指定位数'
Type = 'digit'
Target = '^-?\d+$'
Method = 'round'
Content = { place = -1 }
```

5. **浮点数保留指定位数** (round 方法示例)

```toml
[[MaskRule]]
RuleDes = '浮点数保留指定位数'
Type = 'digit'
Target = '^[-+]?\d+\.\d*([eE][-+]?\d+)?$'
Method = 'round'
Content = { place = 1 }
```

6. **字符串截断处理** (truncate 方法示例)

```toml
[[MaskRule]]
RuleDes = '字符串首部截断（保留后3位）'
Type = 'str'
Target = '^\d{5}$'
Method = 'truncate'
Content = { start = 2 }
```

7. **字符串哈希处理** (hash 方法示例)

```toml
[[MaskRule]]
RuleDes = '字符串哈希处理'
Type = 'str'
Target = '^user_\d+$'
Method = 'hash'
Content = { hash_type = 'sha256' }
```

8. **数值偏移处理** (offset 方法示例)

```toml
[[MaskRule]]
RuleDes = '数值偏移处理'
Type = 'digit'
Target = '^\d+$'
Method = 'offset'
Content = { offset = 100 }
```

9. **KV规则**

```toml
[[MaskRule]]
RuleDes = 'KV规则-基于已有规则'
Type = 'kv'
Target = 'user_name'
Method = 'rule'
Content = { rule = '中文姓名脱敏规则（两个字：李#）' }
```

## 水印规则（MarkRule）

水印规则用于定义文件的水印添加方式，支持多种类型的文件水印。每个水印规则包含以下配置项：

```toml
[[MarkRule]]
RuleDes = '规则描述'
Type = '文件类型'
Target = '目标文件'
Method = '水印类型'
Content = { 水印配置 }
```

### 配置项说明

- `RuleDes`: 规则描述，用于标识规则的用途
- `Type`: 文件类型，支持的值：
  - `image`: 图片文件
  - `pdf`: PDF文件
  - `docx`: Word文件
- `Target`: 目标文件，如果为空则代表该规则为同类文件的默认规则
- `Method`: 水印类型，目前仅支持文本水印
- `Content`: 水印配置，根据Method的不同而不同

### 各文件类型支持的水印类型及配置参数

#### 图片文件 (image)

支持的水印类型：
- `text`: 文本水印
  - 配置参数：
    - `d`: 自定义占位数据，字典类型
    - `template`: 水印模板，支持内置占位符和自定义占位符

#### PDF文件 (pdf)

支持的水印类型：
- `text`: 文本水印
  - 配置参数：
    - `d`: 自定义占位数据，字典类型
    - `template`: 水印模板，支持内置占位符和自定义占位符

#### Word文件 (docx)

支持的水印类型：
- `text`: 文本水印
  - 配置参数：
    - `d`: 自定义占位数据，字典类型
    - `template`: 水印模板，支持内置占位符和自定义占位符

### 常见水印规则示例

1. **图片文本水印** (text 方法示例)

```toml
[[MarkRule]]
RuleDes = '对图片添加水印'
Type = 'image'
Target = 'testpng.png'
Method = 'text'
Content = { d = { 'name' = '测试员' }, template = '{name}-{Date}-{Time}' }
```

2. **PDF文本水印**

```toml
[[MarkRule]]
RuleDes = '对PDF添加水印'
Type = 'pdf'
Target = 'test.pdf'
Method = 'text'
Content = { d = { 'name' = '测试员' }, template = '{name}-{Date}-{Time}' }
```
3. **Word文本水印** (text 方法示例)

```toml
[[MarkRule]]
RuleDes = '对Word文档添加文本水印'
Type = 'docx'
Target = 'test.docx'
Method = 'text'
Content = { d = { 'name' = '测试员' }, template = '{name}-{Date}-{Time}' }
```

### 水印模板说明

文本水印支持自定义模板，模板中可以包含以下内容：

1. **内置占位符**：
   - `{Date}`: 自动填充当前日期
   - `{Time}`: 自动填充当前时间

2. **自定义占位符**：
   通过在`Content.d`中定义的字典，可以在模板中使用自定义占位符
   例如：`d = { 'name' = '测试员' }`，则模板中可以使用`{name}`

3. **模板示例**：
   - `template = '{name}-{Date}-{Time}'`
   - `template = '机密文件-{Date}'`

### 使用说明

配置文件默认路径为项目内的`default_rules.py`，也可以在初始化SDK时指定自定义的配置文件路径，配置文件需为`toml`格式。

# SDK使用示例

## 数据脱敏SDK使用示例

### 基本使用

```python
from maskmark.api import DataMaskingSDK

# 初始化SDK（不指定规则文件，使用默认规则）
sdk = DataMaskingSDK()

# 字符串脱敏（如手机号脱敏）
result = sdk.mask("13812345678")
print(f"手机号脱敏结果: {result}")

# 数值脱敏（如数值取整）
result = sdk.mask(123.456)
print(f"数值脱敏结果: {result}")

# 字典数据脱敏
result = sdk.mask({"name": "张三", "phone": "13812345678"})
print(f"字典数据脱敏结果: {result}")

# JSON字符串脱敏
json_str = '{"name": "张三", "phone": "13812345678"}'
result = sdk.mask(json_str)
print(f"JSON字符串脱敏结果: {result}")
```

### 使用自定义规则文件

```python
from maskmark.api import DataMaskingSDK

# 使用自定义规则文件初始化SDK
sdk = DataMaskingSDK(rule_file="path/to/your/rule.toml")

# 使用自定义规则进行数据脱敏
result = sdk.mask("13812345678")
print(f"使用自定义规则的脱敏结果: {result}")
```

### 使用临时规则

```python
from maskmark.api import DataMaskingSDK

# 初始化SDK
sdk = DataMaskingSDK()

# 定义临时规则
临时规则 = {
    "RuleDes": "临时手机号脱敏规则",
    "Type": "str",
    "Target": '^(13[0-9]|14[5-9]|15[0-3,5-9]|16[2,5-7]|17[0-8]|18[0-9]|19[1,8,9])\\d{8}$',
    "Method": "mask",
    "Content": {"m_type": "re", "char": "\\1****\\2", "pattern": '^(\\d{3})\\d{4}(\\d{4})$'}
}

# 使用临时规则进行脱敏
result = sdk.mask("13812345678", rule=临时规则)
print(f"使用临时规则的脱敏结果: {result}")
```

## 数据水印SDK使用示例

### 基本使用

```python
from maskmark.api import DataMarkingSDK

# 初始化SDK（不指定规则文件，使用默认规则）
sdk = DataMarkingSDK()

# 为图片添加水印
result = sdk.mark("path/to/your/image.jpg")
print(f"图片水印处理结果: {'成功' if result == 0 else '失败'}")

# 为PDF添加水印
result = sdk.mark("path/to/your/document.pdf")
print(f"PDF水印处理结果: {'成功' if result == 0 else '失败'}")

# 为Word文档添加水印
result = sdk.mark("path/to/your/document.docx")
print(f"Word水印处理结果: {'成功' if result == 0 else '失败'}")
```

### 使用自定义规则文件

```python
from maskmark.api import DataMarkingSDK

# 使用自定义规则文件初始化SDK
sdk = DataMarkingSDK(rule_file="path/to/your/rule.toml")

# 使用自定义规则添加水印
result = sdk.mark("path/to/your/image.jpg")
print(f"使用自定义规则的水印处理结果: {'成功' if result == 0 else '失败'}")
```

### 使用临时规则

```python
from maskmark.api import DataMarkingSDK

# 初始化SDK
sdk = DataMarkingSDK()

# 定义临时水印规则
临时规则 = {
    "RuleDes": "临时图片水印规则",
    "Type": "image",
    "Target": "",  # Target会在mark方法中被设置为文件路径
    "Method": "text",
    "Content": {"d": {"name": "测试用户"}, "template": "{name}-{Date}-{Time}"}
}

# 使用临时规则添加水印
result = sdk.mark("path/to/your/image.jpg", rule=临时规则)
print(f"使用临时规则的水印处理结果: {'成功' if result == 0 else '失败'}")
```

## 注意事项

1. 使用前请确保所有依赖库已正确安装
2. 对于大规模数据处理，建议合理设置批处理大小，避免内存溢出
3. 添加水印可能会修改原始文件，请确保有文件备份
4. 自定义规则时，请确保正则表达式正确无误
5. 对于特殊字符或格式的文件，可能需要进行额外的预处理

