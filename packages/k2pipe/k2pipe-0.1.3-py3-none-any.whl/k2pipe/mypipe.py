from __future__ import annotations
import ast
import numpy as np
import pandas as pd
from pandas import Series

mydataframes = []

# K2Pipe提供的内置函数，用于解决暂时无法通过eval()实现的常用操作，如时间操作
def time_shift(self: Series, *args, **kwargs):
    return self + pd.to_timedelta(*args, **kwargs)
pd.Series.time_shift = time_shift


# 修改pd.concat()方法
_original_concat = pd.concat
def my_concat(objs, **kwargs):
    result = _original_concat(objs, **kwargs)

    result.name = 'concat'
    result.config = pd.DataFrame()
    # actual_mappings
    result.config['feature'] = list(objs[0].columns)
    for col in objs[0].columns:
        result.actual_mappings.append({'feature': col, 'expression': col,
                                          'feature_value': objs[0][col].copy(),
                                          'expression_values': objs[0][col].copy()})
    # 建立连接关系
    result.input_dfs = objs
    for obj in objs:
        obj.output_df = result

    # 加入到processors列表
    mydataframes.append(result)
    return result
# merge也会调用自定义concat()方法，若覆盖会报错：
# AttributeError: 'Series' object has no attribute 'columns'
# 暂时不覆盖原生concat
# pd.concat = my_concat

class MyDataFrame(pd.DataFrame):
    _metadata = ['name', 'config','actual_mappings','missing_mappings','input_dfs','output_df']

    def __init__(self, *args, name=None, config:pd.DataFrame=None, actual_mappings=None, missing_mappings=None, input_dfs=None, output_df=None,  **kwargs):
        super().__init__(*args, **kwargs)
        self.name = name
        self.config = config
        self.actual_mappings = actual_mappings  # 实际发生的计算关系（例如 * 已经展开）
        self.missing_mappings = missing_mappings  # 未能跟踪到的计算关系（例如未通过配置方式生成的列）
        self.input_dfs = input_dfs
        self.output_df = output_df
        if self.actual_mappings is None:
            self.actual_mappings = []
        if self.missing_mappings is None:
            self.missing_mappings = []

    @property
    def _constructor(self):
        # 确保在 df 操作（如 df.head(), df.copy()）后仍返回 MyDataFrame 类型
        return MyDataFrame


    def merge(self, right, how='inner', on=None, left_on=None, right_on=None,
              left_index=False, right_index=False, sort=False, suffixes=('_x', '_y'),
              copy=True, indicator=False, validate=None):
        result =  super().merge(
            right=right, how=how, on=on, left_on=left_on, right_on=right_on,
            left_index=left_index, right_index=right_index, sort=sort,
            suffixes=suffixes, copy=copy, indicator=indicator, validate=validate
        )

        # FIXME: 重名带有后缀的情况还没有处理
        # actual_mappings
        result.name = 'merge'
        result.config = pd.DataFrame()
        result.config['feature'] = list(self.columns) + list(right.columns)
        for col in self.columns:
            result.actual_mappings.append({'feature': col, 'expression': col,
                                        'feature_value': self[col].copy(),
                                        'expression_values': self[col].copy()})
        for col in right.columns:
            result.actual_mappings.append({'feature': col, 'expression': col,
                                        'feature_value': right[col].copy(),
                                        'expression_values': right[col].copy()})

        # 建立连接关系
        result.input_dfs = [self,right]
        self.output_df = result
        right.output_df = result

        # 加入到processors列表
        mydataframes.append(result)
        return result


    def extract_features(self, config: pd.DataFrame, step_name:str=None):
        result = self.copy()
        result.name = step_name
        result.columns = result.columns.str.strip()  # 防止列名前后有空格造成难以排查的错误

        # 展开第一个 * 为所有列名，并放在最前面
        if '*' in config['feature'].values:
            config.drop(config[config['feature'] == '*'].index, inplace=True)
            new_df = pd.DataFrame(columns=config.columns)
            for col in list(self.columns):
                new_df.loc[len(new_df)] = {'feature':col, 'expression':col, 'comment':'*'}
            for idx, row in config.iterrows():
                new_df.loc[len(new_df)] = row
            config = new_df

        result.config = config

        for _, row in config.iterrows():
            # 忽略注释行
            if row[0].startswith('#'):
                continue

            feature_name = row['feature']
            if not pd.isna(feature_name):
                feature_name = feature_name.strip()
            else:
                raise ValueError(f"特征名称不能为空 {row}, line: {_}")

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
            else :
                result[feature_name] = _eval(result, expression)

            # 记录实际生成的列
            expression_values = {}
            cols = _extract_column_names(expression)
            for col in cols:
                expression_values[col] = result[col]
            result.actual_mappings.append({'feature': feature_name, 'expression': expression,
                                    'feature_value': result[feature_name].copy(),
                                    'expression_values': expression_values})

        # 非通过配置产生的列，也放入mappings信息以备追踪
        # 将 result 中存在但 config.mappings 中缺失的列加入 config.missing_mappings
        if self.config is not None:
            missing_columns = set(self.columns) - set(self.config['feature'])
            for col in missing_columns:
                result.missing_mappings.append({
                    'feature': col,
                    'expression': '(Unknown)',
                    'feature_value': result[col].copy(),
                    'expression_values': {}
                })

        mydataframes.append(result)

        # 删除self中存在但config中没有定义的列
        config_columns = set(config['feature'].dropna())
        original_columns = set(self.columns)
        columns_to_drop = original_columns - config_columns
        result = result.drop(columns=columns_to_drop, errors='ignore')

        result = _sort_columns(result)

        self.output_df = result
        result.input_dfs = [self]

        return result


    # 向前追踪指定df的指定列的计算逻辑
    def trace_column(self, feature_to_trace:str):
        assert isinstance(feature_to_trace, str)

        # start_line: 倒序处理的开始行号（若为None则处理所有行）
        def _build_pipe_tree_recursive(df, feature, depth=0, start_line:int=None):
            if df.input_dfs is None:
                return None

            # 查找当前 processor 中是否生成了目标 feature
            # for mapping in processor.actual_mappings:
            if start_line is None:
                start_line  = len(df.actual_mappings)

            # 倒序遍历
            for idx in range(start_line - 1, -1, -1):
                mapping = df.actual_mappings[idx]
                if mapping['feature'] == feature :
                    expr = mapping['expression']
                    # 避免无限递归（同一个配置文件内部递归查找时）
                    # if df is self and feature == expr:
                    #     continue
                    input_names = _extract_column_names(expr)

                    children = []
                    for name in input_names:

                        # 同一个配置文件内部的递归匹配
                        # 从当前行的上一行继续倒序匹配
                        if idx > 1:
                            child_ast_self = _build_pipe_tree_recursive(df, name, depth + 1, idx -1)
                            if child_ast_self:
                                children.append(child_ast_self)

                        # 前一个配置文件内的递归匹配
                        for input_df in df.input_dfs:
                            child_ast_prev = _build_pipe_tree_recursive(input_df, name, depth + 1)
                            if child_ast_prev:
                                children.append(child_ast_prev)

                    return {
                        "feature": feature,
                        "df": df.copy(),
                        "mapping": mapping,
                        "expression": expr,
                        "children": children,
                        "depth": depth
                    }

        def _print_pipe_tree(ast_node, indent=0):
            if ast_node is None:
                print("└── (empty)")
                return
            spaces = "  " * indent
            expr = ast_node["expression"]
            feature = ast_node['feature']
            df = ast_node["df"]
            missing_features = [item['feature'] for item in df.missing_mappings]
            exp_missing_features = set(_extract_column_names(expr)).intersection(set(missing_features))
            # if feature == expr:
            #     print(f"{spaces}└── [{df.name}] - "+
            #           (f"  // missing: {exp_missing_features}" if exp_missing_features else ""))
            # else:
            print(f"{spaces}└── [{df.name}] {feature} = {expr} "+
                  (f"  // missing: {exp_missing_features}" if exp_missing_features else ""))
            for child in ast_node["children"]:
                _print_pipe_tree(child, indent + 1)

        tree = _build_pipe_tree_recursive(self, feature_to_trace)
        _print_pipe_tree(tree)
        return tree


    # 向前追溯多个列
    def trace_columns(self, features_to_trace:list):
        for feature in features_to_trace:
            print(feature)
            self.trace_column(feature)
            print()


    # 宽表转长表，例如：
    # k_ts, f1_mean_3D, f1_slope_3D, f2_mean_3D, f2_slope_3D
    # 2025 - 01 - 01, 1, 2, 3, 4
    # 2025 - 01 - 02, 5, 6, 7, 8
    # 转为：
    # k_ts, feature, measure, period, value
    # 2025 - 01 - 01, f1, mean, 3D, 1
    # 2025 - 01 - 01, f1, slope, 3D, 2
    # 2025 - 01 - 01, f2, mean, 3D, 3
    # 2025 - 01 - 01, f2, slope, 3D, 4
    # 2025 - 01 - 02, f1, mean, 3D, 5
    # 2025 - 01 - 02, f1, slope, 3D, 6
    # 2025 - 01 - 02, f2, mean, 3D, 7
    # 2025 - 01 - 02, f2, slope, 3D, 8
    def wide_to_long(self):
        id_vars = ['k_ts','k_device']
        value_vars = [col for col in self.columns if col != 'k_ts' and col != 'k_device']
        df_melted = self.melt(id_vars=id_vars, value_vars=value_vars, var_name='feature_measure_period',
                            value_name='value')
        split_cols = df_melted['feature_measure_period'].str.rsplit('_', n=2, expand=True)
        df_melted[['feature', 'measure', 'period']] = split_cols
        result = df_melted[['k_ts', 'k_device', 'feature', 'measure', 'period', 'value']]
        result = result.sort_values(['k_ts', 'feature', 'measure']).reset_index(drop=True)
        return result


    # 长表转宽表
    def long_to_wide(self):
        required_cols = ['k_ts', 'k_device', 'feature', 'measure', 'period', 'value']
        missing_cols = [col for col in required_cols if col not in self.columns]
        if missing_cols:
            raise ValueError(f"缺少必需的列: {missing_cols}")
        wide_df = self.copy()
        wide_df['new_col'] = wide_df['feature'] + '_' + wide_df['measure'] + '_' + wide_df['period']
        wide_df = MyDataFrame(wide_df.pivot(index=['k_ts', 'k_device'], columns='new_col', values='value'))
        wide_df = wide_df.reset_index()
        wide_df.columns.name = None
        return wide_df


    # def trace_unused_columns(self):
    #     """
    #     实现trace_redundant_columns方法，用于识别整个数据处理管道中的冗余列。
    #     返回一个字典，key是processor的名字，value是此processor里未使用的feature列表
    #     """
    #
    #     # 结果字典，key是processor名字，value是未使用的列列表
    #     redundant_dict = {}
    #
    #     # 遍历所有processor
    #     for processor in processors:
    #         # 收集该processor中定义的所有特征列
    #         # if 'feature' in processor.columns:
    #         #     processor_columns = set(processor['feature'].dropna())
    #         #     processor_columns.discard('*')  # 排除通配符
    #         processor_columns = set(pd.DataFrame(processor.actual_mappings)['feature'])
    #
    #         # 收集该processor实际使用的列（即其他特征表达式中引用的列）
    #         used_in_expressions = set()
    #         for proc in processors:
    #             for mapping in proc.actual_mappings:
    #                 expr_cols = _extract_column_names(mapping['expression'])
    #                 used_in_expressions.update(expr_cols)
    #
    #         # 找出该processor中未被使用的列
    #         redundant_columns = processor_columns - used_in_expressions
    #
    #         # 存入结果字典
    #         if processor.name:
    #             redundant_dict[processor.name] = list(sorted(redundant_columns))
    #         else:
    #             redundant_dict[f"Unnamed_Processor_{id(processor)}"] = list(sorted(redundant_columns))
    #
    #     # 输出结果
    #     print("Redundant Columns by Processor:")
    #     for processor_name, columns in redundant_dict.items():
    #         if columns:
    #             print(f"  [{processor_name}]:")
    #             for col in columns:
    #                 print(f"    - {col}")
    #         else:
    #             print(f"  [{processor_name}]: (no redundant columns)")
    #
    #     return redundant_dict


    # 确保DataFrame的时间戳和设备列的类型，时间戳作为索引
    # 将object类型的列转为string类型，前者不支持eval()
    def format_columns(self) -> MyDataFrame:
        result = self.copy()
        if 'k_ts' in result.columns:
            result['k_ts'] = pd.to_datetime(result['k_ts'])
            # 若k_ts同时作为索引和普通列，对merge操作会报错（'k_ts' is both an index level and a column label, which is ambiguous.）
            # 若k_ts仅作为索引，df['k_ts']会报错 （KeyError)
            # result = result.set_index(['k_ts'], drop=True)
        if 'k_device' in result.columns:
            result['k_device'] = result['k_device'].astype(str)

        # 将object类型的列转为string类型，避免eval()里报错
        object_cols = result.select_dtypes(include=['object']).columns
        result[object_cols] = result[object_cols].astype('string')

        # 列名去掉收尾空格，防止难以察觉的错误
        result.columns = result.columns.str.strip()

        # 列名排序，方便调试对比
        result = _sort_columns(result)

        return result


# 输出指定processor指定feature的相关数据
def print_processor(processor_name, feature_name):
    found =  False
    for processor in mydataframes:
        if processor.name == processor_name:
            for mapping in processor.actual_mappings:
                if mapping['feature'] == feature_name:
                    found = True
                    print(f"[{processor.name}]")
                    print(f"{feature_name:<10}{mapping['feature_value'].tolist()}")
                    values = mapping['expression_values']
                    for key, value in values.items():
                        print(f"{key:<10}{value.tolist()}")
    if not found:
        print(f"未找到processor[{processor_name}]中feature[{feature_name}]")



# 检验列名是否合法
def _validate_var_name(var_name: str):
    forbidden_chars = {'.', '[', ']', '-', '+', '*', '/', '\\', '%', '&'}
    if any(char in forbidden_chars for char in var_name):
        raise ValueError(f"变量名 '{var_name}' 包含非法字符")


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
            # 如果python解析器也失败，报错
            cols = _extract_column_names( expression)
            print('\n表达式执行失败相关输入数据：')
            print(df[cols])
            raise Exception(f'表达式 {expression} 执行失败(python)： {e}')
    return result


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
def _sort_columns(df: pd.DataFrame):
    cols = sorted(df.columns)
    if 'k_device' in cols:
        cols = ['k_device'] + [col for col in cols if col != 'k_device']
    if 'k_ts' in cols:
        cols = ['k_ts'] + [col for col in cols if col != 'k_ts']
    return df[cols]
