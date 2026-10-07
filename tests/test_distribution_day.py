"""Distribution Day (出貨日偵測) 單元測試."""
import pytest
import pandas as pd
from src.vcp_detector import _count_distribution_days


class TestDistributionDay:
    """出貨日偵測邏輯測試."""

    def _make_df(self, closes, volumes, highs=None, lows=None, opens=None):
        """建立測試用 DataFrame."""
        n = len(closes)
        df = pd.DataFrame({
            "Open": opens or closes,
            "High": highs or [c * 1.01 for c in closes],
            "Low": lows or [c * 0.99 for c in closes],
            "Close": closes,
            "Volume": volumes,
        })
        return df

    def test_no_distribution_days(self):
        """量縮價穩 → 0 天出貨日."""
        closes = [100 + i * 0.1 for i in range(60)]  # 穩步上漲
        volumes = [1000 - i * 10 for i in range(60)]  # 量縮
        df = self._make_df(closes, volumes)
        result = _count_distribution_days(df, lookback=25)
        assert result["count"] == 0

    def test_single_distribution_day(self):
        """1 天放量下跌 → 1 天出貨日."""
        closes = [100] * 60
        volumes = [1000] * 60
        # 最後一天放量下跌
        closes[-1] = 99.0  # -1%
        volumes[-1] = 2000  # 量增
        df = self._make_df(closes, volumes)
        result = _count_distribution_days(df, lookback=25)
        assert result["count"] == 1
        assert result["consecutive_recent"] == 1

    def test_consecutive_distribution_days(self):
        """連續 2 天放量下跌 → 嚴重出貨警訊."""
        closes = [100] * 60
        volumes = [1000] * 60
        # 最後 2 天連續放量下跌
        closes[-2] = 99.5
        closes[-1] = 98.5
        volumes[-2] = 2000
        volumes[-1] = 2500
        df = self._make_df(closes, volumes)
        result = _count_distribution_days(df, lookback=25)
        assert result["count"] >= 2
        assert result["consecutive_recent"] >= 2
        assert result["is_heavy_distribution"] is True

    def test_heavy_distribution_threshold(self):
        """25 日內 5 天出貨日 → 達嚴重出貨門檻."""
        closes = [100] * 60
        volumes = [1000] * 60
        # 5 天分散的放量下跌 (最後 25 天內)
        for i in [35, 40, 45, 50, 55]:
            closes[i] = 99.0
            volumes[i] = 2000
        df = self._make_df(closes, volumes)
        result = _count_distribution_days(df, lookback=25)
        assert result["count"] >= 4
        assert result["is_heavy_distribution"] is True

    def test_volume_expansion_but_up_close(self):
        """放量上漲 → 不算出貨日."""
        closes = [100] * 60
        volumes = [1000] * 60
        closes[-1] = 102.0  # +2% 上漲
        volumes[-1] = 3000  # 爆量
        df = self._make_df(closes, volumes)
        result = _count_distribution_days(df, lookback=25)
        # 上漲不算出貨日
        assert result["count"] == 0
