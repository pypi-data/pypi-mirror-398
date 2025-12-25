from dataclasses import dataclass, field, asdict
from enum import Enum
from typing import Any

from .color import darken_color

ApexChartSeriesType = list[tuple[Any, ...]] | list[tuple[Any, Any]] | list[dict]


@dataclass(kw_only=True)
class ApexChartDataSeries:
    name: str = None
    color: str = None
    data: ApexChartSeriesType = field(default=list)


@dataclass(kw_only=True)
class ApexChartData:
    name: str
    color: str
    series: list[ApexChartDataSeries] = field(default_factory=list)
    columns: list = field(default_factory=list)

    def __post_init__(self):
        for index, series in enumerate(self.series):
            if series.name is None:
                series.name = self.name
            else:
                series.name = f'{self.name} ({series.name})'

            if series.color is None:
                series.color = darken_color(self.color, 1 - 0.1 * index)

    def add_series(self, data: ApexChartSeriesType, name=None, color=None):
        if name is None:
            name = self.name

        if color is None:
            color = self.color

        series = ApexChartDataSeries(data=data, name=name, color=color)
        self.series.append(series)
        return series


@dataclass(kw_only=True)
class ApexChart:
    headers: list[str] = field(default_factory=list)
    formats: list[str] = field(default_factory=list)
    data: list[ApexChartData] = field(default_factory=list)
    categories: list[str] = None

    def add_data(self,
                 name: str,
                 color: str,
                 series: list[ApexChartSeriesType] = None,
                 columns: list = None):
        if series is None:
            series = []

        if columns is None:
            columns = []

        chart_data = ApexChartData(name=name, color=color, series=series, columns=columns)
        self.data.append(chart_data)
        return chart_data

    def asdict(self):
        return asdict(self)


class ValueFormats(str, Enum):
    KV_H = 'kV_h'
    MTV_H = 'MVt_h'
    KVTH = 'kVt*h'
    KVAR_H = 'kVar*h'
    KVR_H = 'kVr_h'
    KVT_H = 'kVt_h'
    SHT = 'sht'
    ED = 'ed'
    MLN_SUM = 'mln_sum'
    TONN = 'tonn'
    TN = 'tn'
    SUM = 'sum'
    M3_H = 'm3_h'
    M3 = 'm3'
    MT_H = 'mt_h'
    MLN_KVT_H = 'mln_kVt_h'
    MLN_M3 = 'mln_m3'
    T_C = '°C'
