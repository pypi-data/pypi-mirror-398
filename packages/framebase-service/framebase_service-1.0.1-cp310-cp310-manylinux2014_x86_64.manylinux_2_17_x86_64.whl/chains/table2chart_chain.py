# cython: annotation_typing = False
from typing import Any,  Type, List
import traceback
import pydantic, copy, time, itertools,asyncio
import json, re, jsonref
import jsonschema, commentjson
from dataclasses import dataclass
from enum import Enum

import numpy as np
import pandas as pd
from pandas.api.types import is_integer_dtype, is_numeric_dtype
from pandas.core.groupby.generic import DataFrameGroupBy

import plotly.express as px
from pyecharts.charts import Bar,Scatter,Pie,Line,Grid
from pyecharts.charts.chart import Chart
from pyecharts import options as opts 
from pyecharts.commons.utils import JsCode

from textwrap import dedent
from langchain.schema import BaseMessage, AIMessage, HumanMessage, SystemMessage
from langchain_core.runnables import (
    RunnablePassthrough,
    RunnableBinding,RunnableBranch,
    chain as chain_decorator,
    RunnableSequence,
    RunnableGenerator,
    RunnableParallel,
    RunnablePick
)
from langchain.prompts import PromptTemplate

from framebase.models import models
from framebase.prompts import chain as prompt
from framebase.values import RunnableValue
from framebase.protocol import ChartType
from utils.logger import logger
from itertools import product
from collections import defaultdict 
from framebase import config_map
from configs import get_configs

def description(
    df: pd.DataFrame, description_strategy: str = "head", num_rows: int = 5
) -> str:
    """Returns a description of the given data for LLM"""

    if description_strategy == "head":
        return description_by_head(df, num_rows)
    elif description_strategy == "dtypes":
        return description_by_dtypes(df)
    else:
        raise ValueError(f"Unknown description_strategy: {description_strategy}")


def description_by_head(df: pd.DataFrame, num_rows: int = 5) -> str:
    if len(df) < num_rows:
        head_part = str(df.to_markdown())
    else:
        head_part = str(df.sample(num_rows, random_state=0).to_markdown())

    return dedent(
        f"""
        This is the result of `print(df.head())`:

        {head_part}
        """
    )


def description_by_dtypes(df: pd.DataFrame) -> str:
    return dedent(
        f"""
        This is the result of `print(df.dtypes)`:

        {str(df.dtypes.to_markdown())}
        """
    )


def remove_field_recursively(d: Any, field: str) -> Any:
    if isinstance(d, dict):
        if field in d:
            del d[field]
        for k in d.keys():
            d[k] = remove_field_recursively(d[k], field)
        return d
    elif isinstance(d, list):
        return [remove_field_recursively(e, field) for e in d]
    else:
        return d


def flatten_single_element_allof(d: Any) -> Any:
    if isinstance(d, dict):
        if "allOf" in d and len(d["allOf"]) == 1:
            for k, v in d["allOf"][0].items():
                if k not in d:
                    d[k] = v
            del d["allOf"]
        for k in d.keys():
            d[k] = flatten_single_element_allof(d[k])
        return d
    elif isinstance(d, list):
        return [flatten_single_element_allof(e) for e in d]
    else:
        return d


def delete_null_field(d: Any) -> Any:
    if isinstance(d, dict):
        remove_keys = []
        for k in d.keys():
            if d[k] is None:
                remove_keys.append(k)
            else:
                d[k] = delete_null_field(d[k])
        for k in remove_keys:
            del d[k]
        return d
    elif isinstance(d, list):
        return [delete_null_field(e) for e in d]
    else:
        return d


def get_schema_of_chart_config(
    target_schema: Type[pydantic.BaseModel],
    inlining_refs: bool = True,
    remove_title: bool = True,
    as_function: bool = False,
) -> dict[str, Any]:
    defs = jsonref.loads(target_schema.schema_json()) if inlining_refs else target_schema.schema()  # type: ignore

    if remove_title:
        defs = remove_field_recursively(defs, "title")

    defs = flatten_single_element_allof(defs)

    defs = copy.deepcopy(defs)

    if as_function:
        return {
            "name": "generate_chart",
            "description": "Generate the chart with given parameters",
            "parameters": defs,
        }

    return defs  # type: ignore

class XAxis(pydantic.BaseModel):
    column: str = pydantic.Field(
        description="name of the column in the df used for the x-axis, or label column for pie chart."
    )

    @classmethod
    def parse_from_llm(cls, d: dict[str, str | float | dict[str, str]]) -> "XAxis":
        return XAxis(
            column=d.get("column") or None,  # type: ignore
        )


class YAxis(pydantic.BaseModel):
    columns: List[str] = pydantic.Field(
        description="name of the column in the df used for the y-axis"
    )
   
    @classmethod
    def parse_from_llm(
        cls, d: dict[str, str | float | dict[str, str]], needs_aggregation: bool = False
    ) -> "YAxis":

        return YAxis(
            columns=d.get("columns") or [],  # type: ignore
        )

class Filter(pydantic.BaseModel):
    column: List[str] = pydantic.Field(
        description="name of the column in the df used for the filter"
    )
   
    @classmethod
    def parse_from_llm(
        cls, d: dict[str, str | float | dict[str, str]], needs_aggregation: bool = False
    ) -> "Filter":

        return Filter(
            column=d.get("column") or [],  # type: ignore
        )

class SqlTablePlotConfig(pydantic.BaseModel):
    chart_type: ChartType = pydantic.Field(
        description=("The type of the chart.")
    )
    x: XAxis | None = pydantic.Field(
        description="X-axis for the chart, or label column for pie chart. Empty is available only when PIE chart."
    )
    y: YAxis = pydantic.Field(
        description="Must required. Y-axis for the chart, or the wedge sizes for pie chart.",
    )
    filter: Filter | None = pydantic.Field(
        description="Optional. Data fields used to filter out data.",
    )
    title: str  = pydantic.Field(
        description="Must required. The title for chart."
    )
    @classmethod
    def from_json(cls, json_data: dict[str, Any]):
        assert "chart_type" in json_data

        json_data = copy.deepcopy(json_data)

        if not json_data["chart_type"] or json_data["chart_type"].lower() == "none":
            # treat chart as bar if x-axis does not exist
            chart_type = ChartType.BAR
        else:
            chart_type = ChartType(json_data["chart_type"])

        if not json_data.get("x") and (chart_type == ChartType.PIE or chart_type == ChartType.RING):
            # LLM sometimes forget to fill x in pie-chart
            json_data["x"] = {'column':json_data["y"]['columns'][0]}
        
        if json_data.get("filter") and not json_data["y"]:
            json_data["y"]=json_data["filter"]
        if json_data["x"] and not json_data["y"]:
            json_data["y"]=[json_data["x"]]

        # 修正parse_from_llm参数类型，确保为dict
        def ensure_dict(val, key):
            if isinstance(val, dict):
                return val
            elif isinstance(val, list):
                # x: 只取第一个元素
                if key == 'x':
                    return {'column': val[0] if val else ''}
                # y: 直接赋值
                elif key == 'y':
                    return {'columns': val}
                elif key == 'filter':
                    return {'column': val}
            elif isinstance(val, str):
                if key == 'x':
                    return {'column': val}
                elif key == 'y':
                    return {'columns': [val]}
                elif key == 'filter':
                    return {'column': [val]}
            return {}
        return cls(
            chart_type=chart_type,
            x=XAxis.parse_from_llm(ensure_dict(json_data["x"], 'x')) if json_data.get("x") else XAxis(column=""),
            y=YAxis.parse_from_llm(ensure_dict(json_data["y"], 'y')) if json_data.get("y") else YAxis(columns=[]),
            filter=Filter.parse_from_llm(ensure_dict(json_data["filter"], 'filter')) if json_data.get("filter") else Filter(column=[]),
            title=json_data.get('title','')
        )

def extract_numbers(x, default=None):  
    if not isinstance(x, str):  
        return x  
    x=x.strip()
    pattern = r'-?\b\d{1,3}(?:(?:,\d{3})*|\d*)(?:\.\d+)?\b'
    numbers = re.findall(pattern, x)  
    if numbers:  
        number_str = numbers[0]  
        number_str_no_commas = number_str.replace(',', '')  
        decimal_places = len(number_str.split('.')[-1]) if '.' in number_str else 0  
        return round(float(number_str_no_commas), decimal_places)  
    else:  
        return default or x

def str_2_number(array,default=None):
    result=[]
    for x in array:
        result.append(extract_numbers(x,default))
    return result


def draw_echarts_v2(df: pd.DataFrame, config, max_legends_limit):
    try:
        chart_type = config.chart_type
        x = config.x.column if config.x and config.x.column in df.columns else None
        y = [f for f in config.y.columns if f in df.columns]
        filter_cols = [f for f in df.columns if f not in y and f != x and len(df[f].unique()) > 1]
        if filter_cols and not y:
            y = filter_cols
            filter_cols = []
        filter_cols = [f for f in filter_cols if f not in y]
        if x and not y:
            y = [x]
        if not x and y:
            x = y[0]

        legend_counter = 0
        max_legend_num = 12
        legend_dict = defaultdict(lambda: True)

        colors = [
            "#A7C7E7", "#FFDAC1", "#B5EAD7", "#E2F0CB", "#FFB7B2", "#C7CEEA",
            "#FF9AA2", "#FFB7B2", "#FFDAC1", "#E2F0CB", "#B5EAD7", "#C7CEEA"
        ]
        font_family = "'HarmonyOS Sans SC', 'PingFang SC', 'Microsoft YaHei', 'Source Han Sans SC', 'Noto Sans SC', Arial, Helvetica, sans-serif"
        bg_color = "#fff"
        font_color = "#000"
        axis_color = "#000"
        splitline_color = "#eaeaea"
        legend_dot_size = 12

        title_font_family = "'Pacifico', 'HarmonyOS Sans SC', 'PingFang SC', 'Microsoft YaHei', 'Source Han Sans SC', 'Noto Sans SC', Arial, Helvetica, sans-serif"

        # 柱状图
        if chart_type == ChartType.BAR:
            fig = Bar(init_opts=opts.InitOpts(bg_color=bg_color))
            x_data = df[x].apply(str).unique().tolist()
            fig.add_xaxis(x_data)
            # 动态设置x轴标签样式
            if len(x_data) > 5:
                axislabel_opts = opts.LabelOpts(
                    color="#000",
                    font_size=10,
                    font_family=font_family,
                    font_style="italic",
                    interval=0,
                    rotate=45
                )
            else:
                axislabel_opts = opts.LabelOpts(
                    color="#000",
                    font_size=13,
                    font_family=font_family,
                    font_style="normal",
                    interval=0,
                    rotate=0
                )
            for idx, column_y in enumerate(y):
                y_raw = str_2_number(df[column_y].to_list())
                if len(y_raw) < len(x_data):
                    y_raw.extend([0] * (len(x_data) - len(y_raw)))
                elif len(y_raw) > len(x_data):
                    y_raw = y_raw[:len(x_data)]
                bar_colors = [colors[i % len(colors)] for i in range(len(x_data))]
                y_data = [opts.BarItem(name=x_data[i], value=v, itemstyle_opts=opts.ItemStyleOpts(color=bar_colors[i])) for i, v in enumerate(y_raw)]
                fig.add_yaxis(
                    f'{column_y}',
                    y_data,
                    itemstyle_opts=opts.ItemStyleOpts(
                        border_color=None,
                        border_width=0,
                        border_radius=6
                    ),
                    emphasis_opts=opts.EmphasisOpts(
                        itemstyle_opts=opts.ItemStyleOpts(
                            border_color='#fff',
                            border_width=2
                        )
                    ),
                    label_opts=opts.LabelOpts(
                        color="#000",
                        font_size=15,
                        font_weight="bold",
                        font_family=font_family
                    )
                )
                legend_counter += len(df[column_y])
                if legend_counter > max_legend_num and legend_dict[f'{column_y}']:
                    legend_dict[f'{column_y}'] = False
            fig.set_colors(colors)
            fig.set_series_opts(label_opts=opts.LabelOpts(is_show=False))

        # 折线图/面积图
        elif chart_type in [ChartType.LINE, ChartType.AREA]:
            fig = Line(init_opts=opts.InitOpts(bg_color=bg_color))
            x_data = df[x].apply(str).unique().tolist()
            fig.add_xaxis(x_data)
            # 动态设置x轴标签样式
            if len(x_data) > 6:
                axislabel_opts = opts.LabelOpts(
                    color="#000",
                    font_size=10,
                    font_family=font_family,
                    font_style="italic",
                    interval=0,
                    rotate=45
                )
            else:
                axislabel_opts = opts.LabelOpts(
                    color="#000",
                    font_size=13,
                    font_family=font_family,
                    font_style="normal",
                    interval=0,
                    rotate=0
                )
            for idx, column_y in enumerate(y):
                fig.add_yaxis(
                    f'{column_y}',
                    str_2_number(df[column_y].to_list()),
                    is_smooth=True,
                    linestyle_opts=opts.LineStyleOpts(
                        color=colors[idx % len(colors)],
                        width=4
                    ),
                    itemstyle_opts=opts.ItemStyleOpts(
                        color=colors[idx % len(colors)],
                        border_color=None,
                        border_width=0
                    ),
                    label_opts=opts.LabelOpts(
                        color=colors[idx % len(colors)],
                        font_size=15,
                        font_weight="bold",
                        font_family=font_family
                    ),
                    symbol="circle",
                    symbol_size=14,
                    areastyle_opts=opts.AreaStyleOpts(
                        opacity=0.10,
                        color=colors[idx % len(colors)]
                    ) if chart_type == ChartType.AREA else None
                )
                legend_counter += len(df[column_y])
                if legend_counter > max_legend_num and legend_dict[f'{column_y}']:
                    legend_dict[f'{column_y}'] = False
            fig.set_series_opts(label_opts=opts.LabelOpts(is_show=False), linestyle_opts=opts.LineStyleOpts(width=4))

        # 饼图/环形图
        elif chart_type in [ChartType.PIE, ChartType.RING]:
            fig = Pie(init_opts=opts.InitOpts(bg_color=bg_color))
            data_pair = list(zip(df[x].apply(str).tolist(), str_2_number(df[y[0]].to_list(), default=1)))
            if len(data_pair) == 0:
                data_pair = [("无数据", 1)]
            fig.add(
                '',
                data_pair=data_pair,
                radius=["60%", "80%"] if chart_type == ChartType.RING else ["50%", "70%"],
                center=["50%", "54%"],
                label_opts=opts.LabelOpts(
                    font_size=16,
                    font_weight="bold",
                    font_family=font_family,
                    formatter="{b}: {c}",
                    position="outside",
                    background_color=None,
                    border_color=None,
                    border_width=0,
                    border_radius=0,
                    padding=2
                )
            )
            fig.set_colors(colors)

        else:
            raise ValueError(f"暂不支持的图表类型: {chart_type}")

        # 图例过多报错
        if legend_counter >= max_legends_limit:
            logger.error(f'too much legends:{config}\n{df}\nmax_legends_limit:{max_legends_limit}')
            raise ValueError('too much legends')

        # 全局配置
        fig.set_global_opts(
            title_opts=opts.TitleOpts(
                title=config.title,
                is_show=True,
                title_textstyle_opts=opts.TextStyleOpts(
                    color=font_color,
                    font_size=20,
                    font_weight="bold",
                    font_family=title_font_family,
                ),
                pos_left="center",
                pos_top="2%"
            ),
            legend_opts=opts.LegendOpts(
                pos_top="90%",
                pos_left="center",
                orient="horizontal",
                textstyle_opts=opts.TextStyleOpts(color=font_color, font_size=14, font_weight="normal", font_family=font_family),
                background_color=None,
                border_color=None,
                border_width=0,
                item_width=legend_dot_size,
                item_height=legend_dot_size,
                item_gap=16,
                selected_mode="multiple"
            ),
            xaxis_opts=opts.AxisOpts(
                name=x,
                name_location="end",
                name_gap=2,
                name_textstyle_opts=opts.TextStyleOpts(color="#000", font_size=13, font_family=font_family, font_style="italic"),
                axislabel_opts=axislabel_opts,
                axisline_opts=opts.AxisLineOpts(
                    is_show=True,
                    linestyle_opts=opts.LineStyleOpts(color=splitline_color, width=1, opacity=1)
                ),
                splitline_opts=opts.SplitLineOpts(is_show=True, linestyle_opts=opts.LineStyleOpts(color=splitline_color, width=1))
            ),
            yaxis_opts=opts.AxisOpts(
                name="&".join(y),
                name_location="center",
                name_gap=20,
                is_scale=False,
                name_textstyle_opts=opts.TextStyleOpts(color="#000", font_size=13, font_family=font_family, font_style="italic"),
                axislabel_opts=opts.LabelOpts(color="#000", font_size=13, font_family=font_family, font_style="italic", margin=2),
                axisline_opts=opts.AxisLineOpts(
                    is_show=True,
                    linestyle_opts=opts.LineStyleOpts(color=splitline_color, width=1, opacity=1)
                ),
                splitline_opts=opts.SplitLineOpts(is_show=True, linestyle_opts=opts.LineStyleOpts(color=splitline_color, width=1))
            ),
            datazoom_opts=opts.DataZoomOpts(is_show=True, type_="inside", range_start=0, range_end=100),
            tooltip_opts=opts.TooltipOpts(
                is_show=True,
                background_color="#fff",
                border_color=splitline_color,
                border_width=1,
                textstyle_opts=opts.TextStyleOpts(color=font_color, font_size=14, font_family=font_family)
            ),
            toolbox_opts=opts.ToolboxOpts(
                is_show=True,
                orient='vertical',
                pos_top="20%",
                pos_left="93%",
                feature=opts.ToolBoxFeatureOpts(
                    save_as_image=opts.ToolBoxFeatureSaveAsImageOpts(is_show=True, background_color=bg_color),
                    data_zoom=opts.ToolBoxFeatureDataZoomOpts(is_show=False),
                    restore=opts.ToolBoxFeatureRestoreOpts(is_show=True),
                    data_view=opts.ToolBoxFeatureDataViewOpts(is_show=False, title='图表数据编辑'),
                    magic_type=opts.ToolBoxFeatureMagicTypeOpts(is_show=True, type_=["line", "bar", "stack", "tiled"])
                )
            )
        )
        grid = Grid(init_opts=opts.InitOpts(bg_color=bg_color))
        grid.add(fig, grid_opts=opts.GridOpts(pos_top="8%", pos_bottom="18%", pos_left="8%", pos_right="8%", height="74%", width="84%"))
        grid._prepare_render()
        return grid
    except BaseException as e:
        logger.error('chart generation error:' + str(e))
        logger.error("".join(traceback.format_exception(e)))
        raise


def draw_echarts(df: pd.DataFrame, config, max_legends_limit):
    try:
        chart_type = config.chart_type
        x = config.x.column if config.x.column in df.columns else None
        y = [f for f in config.y.columns if f in df.columns]
        filter = [f for f in df.columns if f not in y and f != x and len(df[f].unique())>1]
        if filter and not y:
            y=filter
            filter=[]
        filter=[f for f in filter if f not in y]
        if x and not y:
            y=[x]
        if not x: x=y[0]

        legend_counter=0  
        max_legend_num=12
        legend_dict=defaultdict(lambda : True)   
        if chart_type in [ChartType.BAR]: 
            fig=Bar()
            x_data=df[x].apply(str).unique().tolist()
            fig.add_xaxis(x_data)
            if filter:
                for conditions in product(*[[(k,v) for v in df[k].unique()] for k in filter]): 
                    query=" & ".join([f"`{k}`=='{v}'" for k,v in conditions])
                    condition_label=" ".join([f"{v}" for k,v in conditions])
                    filtered_df=df.query(query)
                    
                    for column_y in y:
                        if len(y)==1:
                            legend=condition_label
                        else:
                            legend=column_y+"("+condition_label+")"
                        filtered_df[column_y]=str_2_number(filtered_df[column_y].to_list())
                        y_data=[filtered_df[filtered_df[x]==_x].iloc[0][column_y] if _x in filtered_df[x].tolist() else 0 for _x in x_data ]
                        fig.add_yaxis(legend,y_data)
                        legend_counter+=len(filtered_df[column_y])
                        if legend_counter>max_legend_num and legend_dict[legend]:
                            legend_dict[legend]=False
                    if legend_counter>max_legend_num and legend_dict[legend]:
                            legend_dict[legend]=False
            else:
                for column_y in y:
                    fig.add_yaxis(f'{column_y}',str_2_number(df[column_y].to_list()))
                    legend_counter+=len(df[column_y])
                    if legend_counter>max_legend_num and legend_dict[f'{column_y}']:
                        legend_dict[f'{column_y}']=False
            fig.set_series_opts(
                label_opts=opts.LabelOpts(
                    formatter=lambda value: f"{value.data:.1e}" if value>=10000 else f"{value}"
                )
            )

        elif chart_type in [ChartType.LINE, ChartType.AREA]:
            fig=Line()
            x_data=df[x].apply(str).unique().tolist()
            fig.add_xaxis(x_data)
            if filter:
                for conditions in product(*[[(k,v) for v in df[k].unique()] for k in filter]): 
                    query=" & ".join([f"`{k}`=='{v}'" for k,v in conditions])
                    #condition_label=" ".join([f"{k}:{v}" for k,v in conditions])
                    condition_label=" ".join([f"{v}" for k,v in conditions])
                    filtered_df=df.query(query)
                    for column_y in y:
                        if len(y)==1:
                            legend=condition_label
                        else:
                            legend=column_y+"("+condition_label+")"
                        filtered_df[column_y]=str_2_number(filtered_df[column_y].to_list())
                        y_data=[filtered_df[filtered_df[x]==_x].iloc[0][column_y] if _x in filtered_df[x].tolist() else 0 for _x in x_data ]
                        fig.add_yaxis(legend,y_data)
                        legend_counter+=len(filtered_df[column_y])
                        if legend_counter>max_legend_num and legend_dict[legend]:
                            legend_dict[legend]=False
                    if legend_counter>max_legend_num and legend_dict[legend]:
                            legend_dict[legend]=False
            else:
                for column_y in y:
                    fig.add_yaxis(f'{column_y}',str_2_number(df[column_y].to_list()))
                    legend_counter+=len(df[column_y])
                    if legend_counter>max_legend_num and legend_dict[f'{column_y}']:
                        legend_dict[f'{column_y}']=False
        if chart_type in [ChartType.PIE,ChartType.RING]:
            fig = Pie()
            def get_center(subplot_id, total_columns, total_subplots):  
                # total rows 
                total_rows = total_subplots // total_columns  
                total_rows += 1 if total_subplots % total_columns != 0 else 0  
                
                # subplot row id and col id
                row = (subplot_id - 1) // total_columns  
                column = (subplot_id - 1) % total_columns  
                
                # center
                center_x = (column + 0.5) / total_columns  *100
                center_y = (1 - (row + 0.5) / total_rows)  *100
                
                return f"{center_x}%", f"{center_y}%"  
            
            if len(df)==1:
                data_pair=[[x,str_2_number(df[x].to_list(),default=1)[0]]]
                for column_y in y:
                    data_pair.append([column_y,str_2_number(df[column_y].to_list(),default=1)[0]])
                fig.add('',data_pair=data_pair)
                y=[x,*y]
            elif filter:
                data_pair=[]
                for conditions in product(*[[(k,v) for v in df[k].unique()] for k in filter]): 
                    query=" & ".join([f"`{k}`=='{v}'" for k,v in conditions])
                    condition_label=" ".join([f"{k}:{v}" for k,v in conditions])
                    filtered_df=df.query(query)
                    for i,column_y in enumerate(y):
                        pair_key=[f'{column_y}({x}:{a} {condition_label})' for a,b in zip(df[x],df[column_y])]      
                        data_pair+=list(zip(pair_key,str_2_number(filtered_df[column_y].to_list(),default=1)))                      
                        fig.add('',data_pair=data_pair,center=get_center(i+1,2,len(y)),radius=["0%","45%"])
                        legend_counter+=len(data_pair)

            else:
                for i,column_y in enumerate(y):
                    pair_key=[f'{column_y}({x}:{a})' for a,b in zip(df[x],df[column_y])]
                    fig.add('',data_pair=list(zip(pair_key,str_2_number(df[column_y].to_list(),default=1))),center=get_center(i+1,2,len(y)),radius=["0%","45%"])
                    legend_counter+=len(df[x])
        if legend_counter>=max_legends_limit:
            logger.error(f'too much legends:{config}\n{df}\nmax_legends_limit:{max_legends_limit}')
            raise ValueError('too much legends')
        if chart_type == ChartType.AREA:
            fig.set_series_opts(areastyle_opts=opts.AreaStyleOpts(opacity=0.5))
        if chart_type == ChartType.RING:
            fig.set_series_opts(radius=["50%", "70%"])
        if legend_counter>=max_legend_num:
            legend_opts=opts.LegendOpts(type_='scroll',selector=True,pos_top="5%",pos_right="20%")
        else:
            legend_opts=opts.LegendOpts(pos_top="5%",pos_right="20%")
        fig.set_series_opts(label_opts=opts.LabelOpts(is_show=False))
        fig.set_global_opts(
            title_opts=opts.TitleOpts(title=config.title,is_show=True),
            legend_opts=legend_opts,
            xaxis_opts=opts.AxisOpts(name=x,name_location="end",name_gap=10,axislabel_opts=opts.LabelOpts(overflow='break',text_width=30,interval=0)),
            yaxis_opts=opts.AxisOpts(name="&".join(y),name_location="center",name_gap=60,is_scale=False,
                                     splitline_opts=opts.SplitLineOpts(is_show=True)),
            datazoom_opts=opts.DataZoomOpts(is_show=True,type_="inside",range_start=0,range_end=100,),
            toolbox_opts=opts.ToolboxOpts(is_show=True, orient='vertical',pos_top="20%",pos_left="90%",
                feature=opts.ToolBoxFeatureOpts(
                    save_as_image=opts.ToolBoxFeatureSaveAsImageOpts(is_show=True,background_color='#fff'),
                    data_zoom=opts.ToolBoxFeatureDataZoomOpts(is_show=False),
                    restore=opts.ToolBoxFeatureRestoreOpts(is_show=True),
                    data_view=opts.ToolBoxFeatureDataViewOpts(is_show=False,title='图表数据编辑'),
                    magic_type=opts.ToolBoxFeatureMagicTypeOpts(is_show=True, type_=["line", "bar", "stack", "tiled"])
                ))
            )  
        grid=Grid()
        grid.add(fig,grid_opts=opts.GridOpts(pos_top="20%", pos_bottom="20%", pos_left="13%", pos_right="20%", height="60%", width="60%"))
        grid._prepare_render()
        return grid

    except BaseException as e:
        logger.error('chart generation error:'+str(e))
        logger.error("".join(traceback.format_exception(e)))
        raise
    
def _extract_tag_content(s: str, tag: str, end:str) -> str:
    m = re.search(rf"{tag}(.*){end}", s, re.MULTILINE | re.DOTALL) 
    if m:
        return m.group(1)
    else:
        m = re.search(rf"```(.*)```", s, re.MULTILINE | re.DOTALL)
        if m:
            return m.group(1)
    return ""


schema_json=json.dumps(
            get_schema_of_chart_config(
               SqlTablePlotConfig , inlining_refs=True, remove_title=False
            ),
            indent=2,
        ).replace("{", "{{").replace("}", "}}")

async def chart_json_output_parser(chunks):
    json_response=''
    max_legends_limit=100
    draw_echarts_version='DEFAULT'
    async for chunk in chunks:
       
        if "model_output" in chunk:
            yield chunk

        if 'response_variables' in chunk:
            yield chunk

        if 'chart_json' in chunk:
            if type(chunk['chart_json'])==dict and 'token_usage' in chunk['chart_json']:
                yield chunk['chart_json']
            else:
                json_response+=chunk['chart_json'].content
        
        if 'table_df' in chunk:
            df=chunk['table_df']

        if 'df_all_data' in chunk:
            df_all_data=chunk['df_all_data']

        if 'max_legends_limit' in chunk:
            max_legends_limit=chunk['max_legends_limit']
            
        if 'draw_echarts_version' in chunk:
            draw_echarts_version=chunk['draw_echarts_version']

    try:
        json_data =_extract_tag_content(json_response,'```json','```')
        json_data = delete_null_field(commentjson.loads(json_data))
        if 'x' in json_data and 'y' not in json_data:
            json_data['y']=copy.deepcopy(json_data['x'])
            del json_data['x']
        try:
            config = SqlTablePlotConfig.from_json(json_data)
        except BaseException as e:
            # To reduce the number of failure cases as much as possible,
            # only check against the json schema when instantiation fails.
            jsonschema.validate(json_data, SqlTablePlotConfig.schema())
            logger.error("".join(traceback.format_exception(e)))

        logger.debug(config.dict())

        df=df.astype(str)
        df_all_data=df_all_data.astype(str)
        if len(df)==1:
            config.chart_type=ChartType.BAR
        try:
            if draw_echarts_version == 'v2':
                figure = draw_echarts_v2(df_all_data, config, max_legends_limit)
            else:
                figure = draw_echarts(df_all_data, config, max_legends_limit)
            echarts_json=json.loads(figure.dump_options())
        except ValueError as e:
            logger.error('chart dump error:'+str(e))
            echarts_json={}

        result=echarts_json
        if config.x:
            result['x']=config.x.column
        else:
            result['x']=None
        result['y']=config.y.columns
        result['chart_type']=config.chart_type.value
        logger.debug(f"echarts:\n{str(result)}")
        yield {'response_variables':{'chart':result}}
        yield {'figure':figure,'chart_config':config,'chart_json':json_response,'result':result}
    except BaseException as e:
        if isinstance(e,GeneratorExit):
            return
        logger.error('chart generation error:'+str(e))
        logger.error("".join(traceback.format_exception(e)))


@chain_decorator
def make_chart(x):
    try:
        if x['table']:
            chart_service_config = get_configs('service').get('chart_service')
            df = pd.DataFrame(x['table'])
            df_all_data = pd.DataFrame(x['all_data'])
            record_num = len(df)
            column_num = len(df.columns)
            max_records = x['display_max_lines']
            max_columns = x['display_max_columns']
            max_legends = x['display_max_legends']
            draw_echarts_version = chart_service_config.get('draw_echarts_version', 'DEFAULT')
            if x['text2metric']:
                max_legends=100000000
            if len(df_all_data)>max_records:
                df_all_data=df_all_data.iloc[:max_records]
            if len(df_all_data.columns)>max_columns:
                df_all_data=df_all_data[df_all_data.columns[:max_columns]]
            if record_num>max_records or column_num>max_columns and not x['text2metric']:
                return RunnablePassthrough()
            if record_num==1 and column_num>2 and not x['text2metric']:
                df=df.transpose()
                df['id']=df.index
                df.columns=['y','x']
            for col in df.columns:  
                if df[col].dtype == float or df[col].dtype == int:  
                    df[col].fillna(0, inplace=True)  
                elif df[col].dtype == object: 
                    df[col].fillna('', inplace=True)  
            task_prompt=RunnablePassthrough.assign(
                template_name=RunnableValue(value='table_to_chart_task_definition_template'),
                dataset=lambda x,v=df:description(v, 'head'),
                dataset_description=RunnableValue(value=str(df.columns)),
                chart_schema=RunnableValue(value=schema_json)
                ) | prompt
           
            return RunnablePassthrough.assign(**{
                'response_variables':lambda x:x.get('response_variables',{}),
                'chart_json':task_prompt|models['table_to_chart_llm'],
                'table_df':lambda x,v=df:v,
                "df_all_data":lambda x,v=df_all_data:v,
                "max_legends_limit":lambda x,v=max_legends:v,
                "draw_echarts_version":lambda x,v=draw_echarts_version:v
            })|RunnableGenerator(chart_json_output_parser)
        else:
            return RunnablePassthrough()
    except BaseException as e:
        logger.error('chart generation error:'+str(e))
        logger.error("".join(traceback.format_exception(e)))
        return RunnablePassthrough()

inputs = {
    "question":lambda x:x.get("question"),
    "table": lambda x: x.get('table'),
    "all_data":lambda x:x.get("all_data") or x.get('table'),
    "text2metric":lambda x: x.get('text2metric'),
    "draw_echarts_version":lambda x: x.get('draw_echarts_version', 'DEFAULT')
}

chain = RunnablePassthrough.assign(**inputs, **config_map)|make_chart



async def table2chart_interface(x, config):
    async def process_chunk(chunk):
        output = {}
        if 'response_variables' in chunk:
            output.update(chunk)
            async for part in RunnableBranch(
                    (
                            lambda x: 'table' in x.get('response_variables', {}).get('data_source_query', {}).get(
                                'dbQueryResult', {}).get('showType', []),
                            RunnablePassthrough.assign(**
                                                       {
                                                           'table': lambda x: [dict(zip(
                                                               x['response_variables'].get('data_source_query', {}).get(
                                                                   'dbQueryResult', {}).get('queryResult').get(
                                                                   'headers'),
                                                               data)
                                                           )
                                                               for data in
                                                               x['response_variables'].get('data_source_query', {}).get(
                                                                   'dbQueryResult', {}).get('queryResult').get('data')],
                                                           # 'dataset_description':lambda x:"This dataset related to the below subject:\n"+"\n".join(
                                                           #    [ y for v in x['llm_result_table_select'].values()  for y in  x['data_src_data'].get(v,[])[-1]]
                                                           # ),
                                                       }
                                                       ) | chain.with_config(config=config)),
                    # else
                    lambda x: {}
            ).astream(chunk):
                output['response_variables'].update(part.get('response_variables', {}))
        return output

    tasks = []
    async for chunk in x:
        if 'model_output' in chunk:
            yield {'model_output': chunk['model_output']}
        if 'response_variables' in chunk:
            tasks.append(process_chunk(chunk))
    for completed_task in asyncio.as_completed(tasks):
        result = await completed_task
        yield result

async def table2chart_interface_for_cypher(x, config):
    async def process_chunk(chunk):
        output = {}
        if 'response_variables' in chunk:
            output.update(chunk)
            async for part in chain.with_config(config=config).astream(chunk):
                output['response_variables'].update(part.get('response_variables', {}))
        return output

    tasks = []
    async for chunk in x:
        if 'model_output' in chunk:
            yield {'model_output': chunk['model_output']}
        if 'response_variables' in chunk:
            tasks.append(process_chunk(chunk))
    for completed_task in asyncio.as_completed(tasks):
        result = await completed_task
        yield result