import ast

import numpy as np
import pandas as pd
from loguru import logger

##### ##### ##### ##### ##### #####
#####   后面将被MyDataFrame替换   #####
##### ##### ##### ##### ##### #####

# 初始化，为DataFrame添加自定义方法
def init_pipe():
    pd.DataFrame.extract_features = extract_features
    pd.DataFrame.format_columns = format_columns


# 根据配置文件对DataFrame做特征提取
def extract_features(self, config: pd.DataFrame) -> pd.DataFrame:
    result = self.copy()
    result.columns = result.columns.str.strip() # 防止列名前后有空格造成难以排查的错误
    for _, row in config.iterrows():
        # 忽略注释行
        if row[0].startswith('#'):
            continue

        feature_name = row['feature']
        if not pd.isna(feature_name):
            feature_name = feature_name.strip()
        else:
            raise ValueError(f"特征名称不能为空 {row}, line: {_}")

        if feature_name == '*':
            continue

        _validate_var_name(feature_name)

        expression = row['expression']
        if not pd.isna(expression):
            expression = expression.strip()
        else:
            result[feature_name] = np.nan
            continue

        # 非数值类型用eval容易报错，这种情况直接赋值
        if feature_name == expression:
            result[feature_name] = result[expression]
            continue

        result[feature_name] = _eval(result, expression)

    # 删除self中存在但config中没有定义的列
    # 但若config里包含*，则表示原始所有列都复制过来，此时跳过删除步骤
    if not '*' in config['feature'].values:
        config_columns = set(config['feature'].dropna())
        original_columns = set(self.columns)
        columns_to_drop = original_columns - config_columns
        result = result.drop(columns=columns_to_drop, errors='ignore')

    result = _sort_columns(result)

    return result


# 先使用numexpr解析，若失败再尝试python解析
def _eval(df: pd.DataFrame, expression: str):
    result = None

    # dataframe的eval()方法不支持where表达式，自己实现
    if expression.startswith('where'):
        args = _parse_where_args(expression)
        if len(args) == 3:
            return np.where(_eval(df, args[0]), _eval(df, args[1]), _eval(df, args[2]))
        else:
            raise ValueError(f"无效的where表达式格式: {expression}")

    try:
        result = df.eval(expression, engine='numexpr')
    except Exception as e:
        # numexpr不支持字符串等操作，此时尝试降级到python解释器（性能较低）
        # 典型错误信息：'unknown type object'、'unknown type datetimedelta64[ns]'
        try:
            result = df.eval(expression, engine='python')
        except Exception as e:
            cols = _extract_column_names(expression)
            print('\n表达式执行失败相关输入数据：')
            print(df[cols])
            raise Exception(f'表达式 {expression} 执行失败(python)： {e}')
    return result


# 确保DataFrame的时间戳和设备列的类型，时间戳作为索引
# 将object类型的列转为string类型，前者不支持eval()
def format_columns(self) -> pd.DataFrame:
    result = self.copy()
    if 'k_ts' in result.columns:
        result['k_ts'] = pd.to_datetime(result['k_ts'])
    if 'k_device' in result.columns:
        result['k_device'] = result['k_device'].astype(str)
    # result = result.set_index(['k_ts'], drop=False)

    object_cols = result.select_dtypes(include=['object']).columns
    result[object_cols] = result[object_cols].astype('string')

    result = _sort_columns(result)

    return result


def _extract_column_names(expr: str):
    if expr.startswith('where'):
        args = _parse_where_args(expr)
        # FIXME: 根据实际情况，选择arg[1]或arg[2]
        return [] # FIXME

    # FIXME：带有@pd的表达式无法解析（如 @pd.shape[0]) ）
    if '@' in expr:
        return [] # FIXME

    tree = ast.parse(expr, mode='eval')
    names = set()

    class NameVisitor(ast.NodeVisitor):
        def visit_Name(self, node):
            names.add(node.id)
            self.generic_visit(node)

    NameVisitor().visit(tree)
    return sorted(names)  # 或直接返回 names（set）


# 列按字母顺序排序
def _sort_columns(df:pd.DataFrame):
    cols = sorted(df.columns)
    if 'k_device' in cols:
        cols = ['k_device'] + [col for col in cols if col != 'k_device']
    if 'k_ts' in cols:
        cols = ['k_ts'] + [col for col in cols if col != 'k_ts']
    return df[cols]


# 为解决嵌套where()的情况，将原来的正则表达式方案改为手动解析方案
def _parse_where_args(s):
    if not s.startswith('where(') or not s.endswith(')'):
        raise ValueError("Not a where expression")
    # 去掉 'where(' 和最后的 ')'
    inner = s[6:-1]
    args = []
    paren_level = 0
    current = []
    for char in inner:
        if char == ',' and paren_level == 0:
            args.append(''.join(current).strip())
            current = []
        else:
            if char == '(':
                paren_level += 1
            elif char == ')':
                paren_level -= 1
            current.append(char)
    args.append(''.join(current).strip())  # 最后一个参数
    return args


def _validate_var_name(var_name: str):
    forbidden_chars = {'.', '[', ']', '-', '+', '*', '/', '\\', '%', '&'}
    if any(char in forbidden_chars for char in var_name):
        raise ValueError(f"变量名 '{var_name}' 包含非法字符")
    return True