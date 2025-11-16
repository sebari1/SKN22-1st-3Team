# src/dashboard/components/charts.py
"""
차트 컴포넌트 모음.

- Plotly Express 기반 래퍼
- Streamlit 용도로 container_width=True 기본 적용
"""

import streamlit as st
import plotly.express as px
import pandas as pd


def line_chart(
    df: pd.DataFrame,
    x,
    y,
    title: str | None = None,
    y_title: str | None = None,
):
    fig = px.line(df, x=x, y=y, markers=True)
    fig.update_layout(
        title=title or "",
        xaxis_title="",
        yaxis_title=y_title or "",
        margin=dict(l=10, r=10, t=40, b=10),
    )
    st.plotly_chart(fig, use_container_width=True)


def bar_chart(
    df: pd.DataFrame,
    x,
    y,
    title: str | None = None,
    x_tick_angle: int | None = None,
    y_title: str | None = None,
):
    fig = px.bar(df, x=x, y=y)
    if x_tick_angle is not None:
        fig.update_layout(xaxis=dict(tickangle=x_tick_angle))
    fig.update_layout(
        title=title or "",
        xaxis_title="",
        yaxis_title=y_title or "",
        margin=dict(l=10, r=10, t=40, b=10),
    )
    st.plotly_chart(fig, use_container_width=True)
