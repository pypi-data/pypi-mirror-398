"""
기술적 분석 지표를 계산하는 모듈입니다.

이 모듈은 주식 시장의 기술적 분석에 사용되는 다양한 지표들을 계산하는 기능을 제공합니다.
pandas DataFrame을 기반으로 하여 효율적인 계산을 수행하며, 두 가지 구현 방식을 제공합니다:
- Indicators: pandas 기반의 표준 구현
- FastIndicators: numpy 기반의 고성능 구현

주요 지표:
- ROC (Rate of Change): 가격 변화율
- ATR (Average True Range): 평균 실질 범위
- Bollinger Bands: 볼린저 밴드
- MACD (Moving Average Convergence Divergence): 이동평균 수렴/발산
- RSI (Relative Strength Index): 상대강도지수
- RSI Cutler: 상대강도지수를 산술평균을 사용하여 계산한 값 (**주의** 한국의 증권사 차트에서는 RSI Cutler가 지수평균을 사용하고, RSI가 산술평균을 사용하도록 반대로 표시된 경우가 있음)
- OBV (On-Balance Volume): 거래량 균형
- ADX (Average Directional Index): 평균 방향성 지수
- Stochastic RSI: 가격 대신 RSI에 스토캐스틱 오실레이터 적용
- Williams %R: 윌리엄스 %R
- Stochastic: 스토캐스틱 오실레이터
- Ichimoku: 일목균형표
"""

import pandas as pd
import numpy as np


class Indicators:
    """
    기술적 분석 지표를 계산하는 클래스입니다.
    
    이 클래스는 pandas DataFrame을 기반으로 하여 다양한 기술적 분석 지표를 계산합니다.
    주식 시장의 가격 데이터를 분석하여 트레이딩 신호를 생성하는 데 사용됩니다.
    
    Attributes:
        df (pd.DataFrame): OHLCV 데이터를 포함하는 DataFrame. 시간 순 정렬
    """
    
    def __init__(self, df: pd.DataFrame):
        """
        Indicators 클래스 초기화
        
        Args:
            df (pd.DataFrame): OHLCV 데이터를 포함하는 DataFrame.
                               반드시 'close', 'high', 'low', 'volume' 컬럼을 포함해야 함
        
        Raises:
            KeyError: 필수 컬럼이 없는 경우 발생합니다.
        """
        required_columns = ['close', 'high', 'low', 'volume']
        missing_columns = [col for col in required_columns if col not in df.columns]
        if missing_columns:
            raise KeyError(f"필수 컬럼이 누락되었습니다: {missing_columns}")
        
        self.df = df.copy()

    # -----------------------
    # 1. Rate of Change (ROC)
    # -----------------------
    def roc(self, period: int = 12) -> pd.Series:
        """
        Rate of Change (ROC) 지표를 계산합니다.
        
        ROC는 현재 가격이 N기간 전 가격 대비 얼마나 변했는지를 백분율로 나타내는 지표입니다.
        가격의 모멘텀을 측정하는 데 사용되며, 0보다 크면 상승 모멘텀, 0보다 작으면 하락 모멘텀을 의미합니다.
        
        Args:
            period (int, optional): 계산 기간. 기본값은 12입니다.
        
        Returns:
            pd.Series: ROC 값이 포함된 Series. 인덱스는 원본 DataFrame과 동일합니다.
        
        Examples:
            >>> indicators = Indicators(df)
            >>> roc_values = indicators.roc(period=12)
            >>> df["roc"] = roc_values
        """
        return (self.df['close'].diff(period) / self.df['close'].shift(period)) * 100

    # -----------------------
    # 2. ATR (Average True Range)
    # -----------------------
    def atr(self, period: int = 14) -> pd.Series:
        """
        Average True Range (ATR) 지표를 계산합니다.
        
        ATR은 주어진 기간 동안의 평균 실질 범위를 나타내는 지표입니다.
        가격의 변동성을 측정하는 데 사용되며, 높은 ATR 값은 높은 변동성을 의미합니다.
        
        Args:
            period (int, optional): 계산 기간. 기본값은 14입니다.
        
        Returns:
            pd.Series: ATR 값이 포함된 Series. 인덱스는 원본 DataFrame과 동일합니다.
        
        Examples:
            >>> indicators = Indicators(df)
            >>> atr_values = indicators.atr(period=14)
            >>> df["atr"] = atr_values
        """
        high, low, close = self.df['high'], self.df['low'], self.df['close']
        tr1 = high - low
        tr2 = (high - close.shift()).abs()
        tr3 = (low - close.shift()).abs()
        tr = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)
        atr = tr.ewm(alpha=1 / period, min_periods=period, adjust=False).mean()
        return atr

    # -----------------------
    # 3. Bollinger Bands
    # -----------------------
    def bollinger(self, period: int = 20, k: float = 2.0) -> pd.DataFrame:
        """
        Bollinger Bands 지표를 계산합니다.
        
        볼린저 밴드는 이동평균선을 중심으로 표준편차의 배수만큼 떨어진 상한선과 하한선을 그린 지표입니다.
        가격이 상한선 근처에 있으면 과매수 상태, 하한선 근처에 있으면 과매도 상태로 판단할 수 있습니다.
        밴드의 폭이 좁아지면 변동성이 낮아지고, 폭이 넓어지면 변동성이 높아진다는 신호로 해석됩니다.
        
        Args:
            period (int, optional): 이동평균 계산 기간. 기본값은 20입니다.
            k (float, optional): 표준편차 배수. 기본값은 2.0입니다.
        
        Returns:
            pd.DataFrame: 다음 컬럼을 포함하는 DataFrame:
                - bb_middle: 중간선 (이동평균)
                - bb_upper: 상한선 (중간선 + k * 표준편차)
                - bb_lower: 하한선 (중간선 - k * 표준편차)
        
        Examples:
            >>> indicators = Indicators(df)
            >>> bb = indicators.bollinger(period=20, k=2.0)
            >>> df["bb_middle"] = bb["bb_middle"]
            >>> df["bb_upper"] = bb["bb_upper"]
            >>> df["bb_lower"] = bb["bb_lower"]
        """
        middle = self.df['close'].rolling(window=period).mean()
        std = self.df['close'].rolling(window=period).std(ddof=0)  # TradingView 호환
        upper = middle + k * std
        lower = middle - k * std
        return pd.DataFrame({"bb_middle": middle, "bb_upper": upper, "bb_lower": lower})

    # -----------------------
    # 4. MACD
    # -----------------------
    def macd(self, fast: int = 12, slow: int = 26, signal: int = 9) -> pd.DataFrame:
        """
        MACD (Moving Average Convergence Divergence) 지표를 계산합니다.
        
        MACD는 두 개의 지수이동평균선의 차이를 나타내는 지표입니다.
        트렌드의 변화와 모멘텀을 파악하는 데 사용되며, 다음과 같이 해석됩니다:
        - MACD선이 시그널선을 상향 돌파하면 매수 신호
        - MACD선이 시그널선을 하향 돌파하면 매도 신호
        - 히스토그램이 0선을 상향 돌파하면 상승 모멘텀
        - 히스토그램이 0선을 하향 돌파하면 하락 모멘텀
        
        Args:
            fast (int, optional): 빠른 지수이동평균 기간. 기본값은 12입니다.
            slow (int, optional): 느린 지수이동평균 기간. 기본값은 26입니다.
            signal (int, optional): 시그널선 기간. 기본값은 9입니다.
        
        Returns:
            pd.DataFrame: 다음 컬럼을 포함하는 DataFrame:
                - macd: MACD선 (빠른 EMA - 느린 EMA)
                - macd_signal: 시그널선 (MACD선의 EMA)
                - macd_histogram: 히스토그램 (MACD선 - 시그널선)
        
        Examples:
            >>> indicators = Indicators(df)
            >>> macd_data = indicators.macd(fast=12, slow=26, signal=9)
            >>> df["macd"] = macd_data["macd"]
            >>> df["macd_signal"] = macd_data["macd_signal"]
            >>> df["macd_histogram"] = macd_data["macd_histogram"]
        """
        ema_fast = self.df['close'].ewm(span=fast, adjust=False).mean()
        ema_slow = self.df['close'].ewm(span=slow, adjust=False).mean()
        macd_line = ema_fast - ema_slow
        signal_line = macd_line.ewm(span=signal, adjust=False).mean()
        hist = macd_line - signal_line
        return pd.DataFrame({"macd": macd_line, "macd_signal": signal_line, "macd_histogram": hist})

    def macd_histogram_color(self, hist: pd.Series) -> pd.Series:
        """
        MACD 히스토그램의 색상을 결정합니다.
        
        히스토그램의 값과 이전 값과의 비교를 통해 색상을 결정합니다:
        - PI (Positive Increasing): 양수이면서 증가
        - PD (Positive Decreasing): 양수이면서 감소
        - NI (Negative Increasing): 음수이면서 증가
        - ND (Negative Decreasing): 음수이면서 감소
        
        Args:
            hist (pd.Series): MACD 히스토그램 값이 포함된 Series
        
        Returns:
            pd.Series: 색상 코드가 포함된 Series ('PI', 'PD', 'NI', 'ND')
        
        Examples:
            >>> indicators = Indicators(df)
            >>> macd_data = indicators.macd(fast=12, slow=26, signal=9)
            >>> hist = macd_data['macd_histogram']
            >>> colors = indicators.macd_histogram_color(hist)
            >>> df["macd_histogram_colors"] = colors
        """
        hist_color = pd.Series(index=hist.index, dtype=object)
        for i in range(len(hist)):
            if i == 0:
                hist_color.iloc[i] = 'PI' if hist.iloc[i] > 0 else 'NI'
            else:
                if hist.iloc[i] > 0:
                    hist_color.iloc[i] = 'PI' if hist.iloc[i] > hist.iloc[i - 1] else 'PD'
                else:
                    hist_color.iloc[i] = 'NI' if hist.iloc[i] > hist.iloc[i - 1] else 'ND'
        return hist_color

    # -----------------------
    # 5. RSI (Wilder's method)
    # -----------------------
    def rsi(self, period: int = 14, signal: int = 9) -> pd.DataFrame:
        """
        RSI (Relative Strength Index) 지표를 Wilder 방법으로 계산합니다.
        
        RSI는 주가의 상승과 하락의 상대적 강도를 0-100 사이의 값으로 나타내는 지표입니다.
        Wilder의 방법은 지수이동평균을 사용하여 계산하며, 다음과 같이 해석됩니다:
        - 70 이상: 과매수 상태 (매도 신호)
        - 30 이하: 과매도 상태 (매수 신호)
        - 50 근처: 중립 상태
        
        Args:
            period (int, optional): 계산 기간. 기본값은 14입니다.
            signal (int, optional): 시그널선 기간. 기본값은 9입니다.
        
        Returns:
            pd.DataFrame: 다음 컬럼을 포함하는 DataFrame:
                - rsi: RSI 값 (0-100)
                - rsi_signal: RSI 시그널선 (RSI의 EMA)
        
        Examples:
            >>> indicators = Indicators(df)
            >>> rsi_data = indicators.rsi(period=14, signal=9)
            >>> df["rsi"] = rsi_data["rsi"]
            >>> df["rsi_signal"] = rsi_data["rsi_signal"]
            >>> rsi30_data = indicators.rsi(period=30, signal=9)
            >>> df["rsi30"] = rsi30_data["rsi"]
        """
        delta = self.df['close'].diff()
        gain = delta.clip(lower=0)
        loss = -delta.clip(upper=0)
        avg_gain = gain.ewm(alpha=1 / period, min_periods=period, adjust=False).mean()
        avg_loss = loss.ewm(alpha=1 / period, min_periods=period, adjust=False).mean()
        rs = avg_gain / avg_loss
        rsi = 100 - (100 / (1 + rs))
        rsi_signal = rsi.ewm(span=signal, adjust=False).mean()
        return pd.DataFrame({"rsi": rsi, "rsi_signal": rsi_signal})
    
    # -----------------------
    # 6. RSI (Cutler's method)
    # -----------------------
    def rsi_cutler(self, period: int = 14, signal: int = 9) -> pd.DataFrame:
        """
        RSI (Relative Strength Index) 지표를 Cutler 방법으로 계산합니다.
        
        Cutler의 방법은 단순이동평균을 사용하여 RSI를 계산합니다.
        Wilder 방법과 달리 더 단순한 계산 방식을 사용하며, 다음과 같이 해석됩니다:
        - 70 이상: 과매수 상태 (매도 신호)
        - 30 이하: 과매도 상태 (매수 신호)
        - 50 근처: 중립 상태
        
        Args:
            period (int, optional): 계산 기간. 기본값은 14입니다.
            signal (int, optional): 시그널선 기간. 기본값은 9입니다.
        
        Returns:
            pd.DataFrame: 다음 컬럼을 포함하는 DataFrame:
                - rsi_cutler: RSI 값 (0-100)
                - rsi_cutler_signal: RSI 시그널선 (RSI의 EMA)
        
        Examples:
            >>> indicators = Indicators(df)
            >>> rsi_data = indicators.rsi_cutler(period=14, signal=9)
        """
        delta = self.df['close'].diff()
        gain = delta.clip(lower=0)
        loss = -delta.clip(upper=0)
        avg_gain = gain.rolling(window=period).mean()
        avg_loss = loss.rolling(window=period).mean()
        rs = avg_gain / avg_loss
        rsi = 100 - (100 / (1 + rs))
        rsi_signal = rsi.ewm(span=signal, adjust=False).mean()
        return pd.DataFrame({"rsi_cutler": rsi, "rsi_cutler_signal": rsi_signal})

    # -----------------------
    # 7. OBV (On-Balance Volume)
    # -----------------------
    def obv(self) -> pd.Series:
        """
        OBV (On-Balance Volume) 지표를 계산합니다.
        
        OBV는 거래량을 누적하여 가격의 움직임을 예측하는 지표입니다.
        종가가 상승하면 거래량을 더하고, 하락하면 거래량을 빼서 누적합니다.
        OBV가 상승하면 매수 압력이 강하고, 하락하면 매도 압력이 강하다고 해석됩니다.
        OBV는 데이터의 시작 시점에 따라 값은 변경되므로 값 대신 변화량을 사용하는 지표입니다.
        
        Returns:
            pd.Series: OBV 값이 포함된 Series. 인덱스는 원본 DataFrame과 동일합니다.
        
        Examples:
            >>> indicators = Indicators(df)
            >>> obv_values = indicators.obv()
            >>> df["obv"] = obv_values
        """
        direction = np.sign(self.df['close'].diff()).fillna(0)
        obv = (direction * self.df['volume']).cumsum()
        return obv

    # -----------------------
    # 8. ADX (Average Directional Index)
    # -----------------------
    def adx(self, period: int = 14) -> pd.DataFrame:
        """
        ADX (Average Directional Index) 지표를 계산합니다.
        
        ADX는 트렌드의 강도를 측정하는 지표로, 방향성 지수(DI)와 함께 사용됩니다.
        ADX 값이 높을수록 강한 트렌드가 형성되어 있다고 해석됩니다:
        - ADX > 25: 강한 트렌드
        - ADX < 20: 약한 트렌드 또는 횡보
        - +DI > -DI: 상승 트렌드
        - -DI > +DI: 하락 트렌드
        
        Args:
            period (int, optional): 계산 기간. 기본값은 14입니다.
        
        Returns:
            pd.DataFrame: 다음 컬럼을 포함하는 DataFrame:
                - plus_di: +DI (상승 방향성 지수)
                - minus_di: -DI (하락 방향성 지수)
                - adx: ADX (평균 방향성 지수)
        
        Examples:
            >>> indicators = Indicators(df)
            >>> adx_data = indicators.adx(period=14)
            >>> df["plus_di"] = adx_data["plus_di"]
            >>> df["minus_di"] = adx_data["minus_di"]
            >>> df["adx"] = adx_data["adx"]
        """
        high, low, close = self.df['high'], self.df['low'], self.df['close']

        # 1. up_move, down_move 정의
        up_move = high.diff()
        down_move = -low.diff()  # = low.shift() - low

        # 2. +DM, -DM 계산
        plus_dm = np.where((up_move > down_move) & (up_move > 0), up_move, 0.0)
        minus_dm = np.where((down_move > up_move) & (down_move > 0), down_move, 0.0)

        plus_dm = pd.Series(plus_dm, index=high.index)
        minus_dm = pd.Series(minus_dm, index=high.index)

        # 3. True Range (TR)
        tr1 = high - low
        tr2 = (high - close.shift()).abs()
        tr3 = (low - close.shift()).abs()
        tr = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)

        # 4. Smoothed averages (Wilder 방식 → alpha=1/period)
        atr = tr.ewm(alpha=1 / period, min_periods=period, adjust=False).mean()
        plus_di = 100 * (plus_dm.ewm(alpha=1 / period, min_periods=period, adjust=False).mean() / atr)
        minus_di = 100 * (minus_dm.ewm(alpha=1 / period, min_periods=period, adjust=False).mean() / atr)

        # 5. DX와 ADX
        dx = ((plus_di - minus_di).abs() / (plus_di + minus_di)) * 100
        adx = dx.ewm(alpha=1/period, min_periods=period, adjust=False).mean()

        return pd.DataFrame({"plus_di": plus_di, "minus_di": minus_di, "adx": adx})

    # -----------------------
    # 9. Stochastic RSI
    # -----------------------
    def stoch_rsi(self, period: int = 14, smooth_k: int = 3, smooth_d: int = 3) -> pd.DataFrame:
        """
        Stochastic RSI 지표를 계산합니다.
        
        Stochastic RSI는 RSI를 스토캐스틱 공식에 적용한 지표입니다.
        RSI의 과매수/과매도 상태를 더 민감하게 감지할 수 있으며, 다음과 같이 해석됩니다:
        - 80 이상: 과매수 상태 (매도 신호)
        - 20 이하: 과매도 상태 (매수 신호)
        - %K가 %D를 상향 돌파: 매수 신호
        - %K가 %D를 하향 돌파: 매도 신호
        
        Args:
            period (int, optional): RSI 계산 기간. 기본값은 14입니다.
            smooth_k (int, optional): %K 스무딩 기간. 기본값은 3입니다.
            smooth_d (int, optional): %D 스무딩 기간. 기본값은 3입니다.
        
        Returns:
            pd.DataFrame: 다음 컬럼을 포함하는 DataFrame:
                - stochrsi: Stochastic RSI 원본 값
                - stochrsi_%K: %K 값 (스무딩된 Stochastic RSI)
                - stochrsi_%D: %D 값 (%K의 이동평균)
        
        Examples:
            >>> indicators = Indicators(df)
            >>> stoch_rsi_data = indicators.stoch_rsi(period=14, smooth_k=3, smooth_d=3)
            >>> df["stochrsi"] = stoch_rsi_data["stochrsi"]
            >>> df["stochrsi_K"] = stoch_rsi_data["stochrsi_%K"]
            >>> df["stochrsi_D"] = stoch_rsi_data["stochrsi_%D"]
        """
        rsi_series = self.rsi(period=period)["rsi"]
        min_rsi = rsi_series.rolling(window=period).min()
        max_rsi = rsi_series.rolling(window=period).max()
        stoch_rsi = 100 * (rsi_series - min_rsi) / (max_rsi - min_rsi)
        k = stoch_rsi.rolling(window=smooth_k).mean()
        d = k.rolling(window=smooth_d).mean()
        return pd.DataFrame({"stochrsi": stoch_rsi, "stochrsi_%K": k, "stochrsi_%D": d})

    # -----------------------
    # 10. Williams %R
    # -----------------------
    def williams_r(self, period: int = 14) -> pd.Series:
        """
        Williams %R 지표를 계산합니다.
        
        Williams %R은 주어진 기간 내에서 현재 가격이 최고가(0)와 최저가(-100) 사이에서 어느 위치에 있는지를 나타내는 지표입니다.
        스토캐스틱 오실레이터와 유사하지만 반대 방향으로 계산됩니다:
        - -20 이상: 과매수 상태 (매도 신호)
        - -80 이하: 과매도 상태 (매수 신호)
        - -50 근처: 중립 상태
        
        Args:
            period (int, optional): 계산 기간. 기본값은 14입니다.
        
        Returns:
            pd.Series: Williams %R 값이 포함된 Series. 인덱스는 원본 DataFrame과 동일합니다.
        
        Examples:
            >>> indicators = Indicators(df)
            >>> williams_r_values = indicators.williams_r(period=14)
            >>> df["williams_r"] = williams_r_values
        """
        highest_high = self.df['high'].rolling(window=period).max()
        lowest_low = self.df['low'].rolling(window=period).min()
        wr = (highest_high - self.df['close']) / (highest_high - lowest_low) * -100
        return wr

    # -----------------------
    # 11. Stochastic Oscillator
    # -----------------------
    def stochastic(self, period: int = 14, smooth_k: int = 3, smooth_d: int = 3) -> pd.DataFrame:
        """
        Stochastic Oscillator (%K, %D) 지표를 계산합니다.
        
        스토캐스틱 오실레이터는 주어진 기간 내에서 현재 가격이 최고가와 최저가 사이에서 어느 위치에 있는지를 나타내는 지표입니다.
        과매수/과매도 상태를 판단하는 데 사용되며, 다음과 같이 해석됩니다:
        - 80 이상: 과매수 상태 (매도 신호)
        - 20 이하: 과매도 상태 (매수 신호)
        - %K가 %D를 상향 돌파: 매수 신호
        - %K가 %D를 하향 돌파: 매도 신호
        
        Args:
            period (int, optional): 계산 기간. 기본값은 14입니다.
            smooth_k (int, optional): %K 스무딩 기간. 기본값은 3입니다.
            smooth_d (int, optional): %D 스무딩 기간. 기본값은 3입니다.
        
        Returns:
            pd.DataFrame: 다음 컬럼을 포함하는 DataFrame:
                - stoch_fast_%K: Fast %K 값 (원본)
                - stoch_%K: Slow %K 값 (스무딩된 %K)
                - stoch_%D: %D 값 (Slow %K의 이동평균)
        
        Examples:
            >>> indicators = Indicators(df)
            >>> stoch_data = indicators.stochastic(period=14, smooth_k=3, smooth_d=3)
            >>> df["stoch_fast_K"] = stoch_data["stoch_fast_%K"]
            >>> df["stoch_K"] = stoch_data["stoch_%K"]
            >>> df["stoch_D"] = stoch_data["stoch_%D"]
        """
        low_min = self.df['low'].rolling(window=period).min()
        high_max = self.df['high'].rolling(window=period).max()
        
        # %K 원본
        k_fast = 100 * (self.df['close'] - low_min) / (high_max - low_min)
        
        # Slow %K (보통 3일 SMA)
        k_slow = k_fast.rolling(window=smooth_k).mean()
        
        # %D (Slow %K의 이동평균)
        d = k_slow.rolling(window=smooth_d).mean()
        
        return pd.DataFrame({"stoch_fast_%K": k_fast, "stoch_%K": k_slow, "stoch_%D": d})

    # -----------------------
    # 12. Ichimoku Kinko Hyo
    # -----------------------
    def ichimoku(self, tenkan_period: int = 9, kijun_period: int = 26, senkou_period: int = 52, displacement: int = 26) -> pd.DataFrame:
        """
        Ichimoku Kinko Hyo (일목균형표) 지표를 계산합니다.
        
        일목균형표는 일본의 기술적 분석 도구로, 5개의 선으로 구성되어 있습니다:
        - 전환선 (Tenkan-sen): 9일간의 최고가와 최저가의 중간값
        - 기준선 (Kijun-sen): 26일간의 최고가와 최저가의 중간값
        - 선행스팬A (Senkou Span A): 전환선과 기준선의 중간값을 26일 앞으로 이동
        - 선행스팬B (Senkou Span B): 52일간의 최고가와 최저가의 중간값을 26일 앞으로 이동
        - 후행스팬 (Chikou Span): 현재 종가를 26일 뒤로 이동
        
        해석 방법:
        - 가격이 구름대(선행스팬A, B 사이) 위에 있으면 상승 추세
        - 가격이 구름대 아래에 있으면 하락 추세
        - 전환선이 기준선을 상향 돌파하면 매수 신호
        - 전환선이 기준선을 하향 돌파하면 매도 신호
        
        Args:
            tenkan_period (int, optional): 전환선 기간. 기본값은 9입니다.
            kijun_period (int, optional): 기준선 기간. 기본값은 26입니다.
            senkou_period (int, optional): 선행스팬B 기간. 기본값은 52입니다.
            displacement (int, optional): 선행스팬 이동 기간. 기본값은 26입니다.
        
        Returns:
            pd.DataFrame: 다음 컬럼을 포함하는 DataFrame:
                - tenkan: 전환선
                - kijun: 기준선
                - senkou_a: 선행스팬A
                - senkou_b: 선행스팬B
                - chikou: 후행스팬
        
        Examples:
            >>> indicators = Indicators(df)
            >>> ichimoku_data = indicators.ichimoku(tenkan_period=9, kijun_period=26, senkou_period=52, displacement=26)
            >>> df["tenkan"] = ichimoku_data["tenkan"]
            >>> df["kijun"] = ichimoku_data["kijun"]
            >>> df["senkou_a"] = ichimoku_data["senkou_a"]
            >>> df["senkou_b"] = ichimoku_data["senkou_b"]
            >>> df["chikou"] = ichimoku_data["chikou"]
        """

        high = self.df["high"]
        low = self.df["low"]
        close = self.df["close"]

        # 전환선 (Tenkan-sen)
        tenkan = (high.rolling(window=tenkan_period).max() + low.rolling(window=tenkan_period).min()) / 2

        # 기준선 (Kijun-sen)
        kijun = (high.rolling(window=kijun_period).max() + low.rolling(window=kijun_period).min()) / 2

        # 선행스팬1 (Senkou Span A)
        senkou_a = ((tenkan + kijun) / 2).shift(displacement - 1)

        # 선행스팬2 (Senkou Span B)
        senkou_b = ((high.rolling(window=senkou_period).max() + low.rolling(window=senkou_period).min()) / 2).shift(displacement - 1)

        # 후행스팬 (Chikou Span)
        chikou = close.shift(-displacement)

        return pd.DataFrame({
            "tenkan": tenkan,
            "kijun": kijun,
            "senkou_a": senkou_a,
            "senkou_b": senkou_b,
            "chikou": chikou
        })


class FastIndicators:
    """
    고성능 기술적 분석 지표를 계산하는 클래스입니다.
    
    이 클래스는 numpy 배열을 기반으로 하여 pandas 기반 구현보다 빠른 계산을 제공합니다.
    대용량 데이터나 실시간 계산이 필요한 경우에 사용하는 것이 좋습니다.
    Indicators 클래스와 동일한 지표들을 제공하지만, 내부적으로 numpy를 사용하여 최적화되었습니다.
    
    Attributes:
        df (pd.DataFrame): 원본 OHLCV 데이터를 포함하는 DataFrame
    """
    
    def __init__(self, df: pd.DataFrame):
        """
        FastIndicators 클래스를 초기화합니다.
        
        Args:
            df (pd.DataFrame): OHLCV 데이터를 포함하는 DataFrame.
                              반드시 'close', 'high', 'low', 'volume' 컬럼을 포함해야 합니다.
        
        Raises:
            KeyError: 필수 컬럼이 없는 경우 발생합니다.
        """
        required_columns = ['close', 'high', 'low', 'volume']
        missing_columns = [col for col in required_columns if col not in df.columns]
        if missing_columns:
            raise KeyError(f"필수 컬럼이 누락되었습니다: {missing_columns}")
        
        self.df = df.copy()
        self.close = self.df['close'].to_numpy(dtype=float)
        self.high = self.df['high'].to_numpy(dtype=float)
        self.low = self.df['low'].to_numpy(dtype=float)
        self.volume = self.df['volume'].to_numpy(dtype=float)
        self.index = self.df.index

    # -----------------------
    # Helper: EMA, RMA
    # -----------------------
    def _ema(self, arr: np.ndarray, span: int) -> np.ndarray:
        """
        지수이동평균(EMA)을 계산합니다.
        
        Args:
            arr (np.ndarray): 입력 데이터 배열
            span (int): EMA 계산 기간
        
        Returns:
            np.ndarray: EMA 값이 포함된 배열
        """
        out = np.full_like(arr, np.nan, dtype=float)
        alpha = 2 / (span + 1)
        n = len(arr)
        # 첫 유효값 찾기
        mask = ~np.isnan(arr)
        if not mask.any() or mask.sum() < span:
            return out
        first = np.argmax(mask)  # 처음 NaN 아닌 값
        out[first + span - 1] = np.nanmean(arr[first:first+span])  # 초기값: SMA
        for i in range(first + span, n):
            prev = out[i-1] if not np.isnan(out[i-1]) else arr[i-1]
            out[i] = prev + alpha * (arr[i] - prev)
        return out

    def _rma(self, arr: np.ndarray, period: int) -> np.ndarray:
        """
        Wilder's RMA (Running Moving Average)를 계산합니다.
        
        RMA는 Wilder의 방법을 사용한 지수이동평균으로, alpha = 1 / period 를 사용합니다.
        초기값은 첫 period 구간의 단순이동평균으로 설정됩니다.
        
        Args:
            arr (np.ndarray): 입력 데이터 배열
            period (int): RMA 계산 기간
        
        Returns:
            np.ndarray: RMA 값이 포함된 배열
        """
        out = np.full_like(arr, np.nan, dtype=float)
        n = len(arr)
        if period <= 0 or n == 0:
            return out

        finite = np.isfinite(arr)
        csum = np.cumsum(finite.astype(int))

        # 첫 'period'개가 연속으로 유효한 구간의 끝 인덱스 찾기
        first_idx = None
        for j in range(period - 1, n):
            cnt = csum[j] - (csum[j - period] if j - period >= 0 else 0)
            if cnt == period:
                start = j - period + 1
                first_idx = j
                first_avg = np.nanmean(arr[start: j + 1])
                out[first_idx] = first_avg
                break

        if first_idx is None:
            return out

        alpha = 1.0 / period
        for i in range(first_idx + 1, n):
            x = arr[i]
            if np.isnan(x):
                out[i] = out[i-1]  # 결측은 이전값 유지(일반적 구현)
            else:
                out[i] = out[i-1] + alpha * (x - out[i-1])
        return out

    # -----------------------
    # 1. Rate of Change (ROC)
    # -----------------------
    def roc(self, period: int = 12) -> pd.Series:
        """
        Rate of Change (ROC) 지표를 계산합니다.
        
        Args:
            period (int, optional): 계산 기간. 기본값은 12입니다.
        
        Returns:
            pd.Series: ROC 값이 포함된 Series.
        """
        result = np.full_like(self.close, np.nan, dtype=float)
        result[period:] = (self.close[period:] - self.close[:-period]) / self.close[:-period] * 100
        return pd.Series(result, index=self.index)

    # -----------------------
    # 2. ATR (Average True Range)
    # -----------------------
    def atr(self, period: int = 14) -> pd.Series:
        """
        Average True Range (ATR) 지표를 계산합니다.
        
        Args:
            period (int, optional): 계산 기간. 기본값은 14입니다.
        
        Returns:
            pd.Series: ATR 값이 포함된 Series.
        """
        high, low, close = self.high, self.low, self.close
        n = len(close)

        tr = np.zeros(n, dtype=float)
        for i in range(1, n):
            tr1 = high[i] - low[i]
            tr2 = abs(high[i] - close[i-1])
            tr3 = abs(low[i] - close[i-1])
            tr[i] = max(tr1, tr2, tr3)

        atr = self._rma(tr, period)
        return pd.Series(atr, index=self.index)

    # -----------------------
    # 3. Bollinger Bands
    # -----------------------
    def bollinger(self, period: int = 20, k: float = 2.0) -> pd.DataFrame:
        """
        Bollinger Bands 지표를 계산합니다.
        
        Args:
            period (int, optional): 이동평균 계산 기간. 기본값은 20입니다.
            k (float, optional): 표준편차 배수. 기본값은 2.0입니다.
        
        Returns:
            pd.DataFrame: 볼린저 밴드 값이 포함된 DataFrame.
        """
        middle = pd.Series(self.close, index=self.index).rolling(window=period).mean().to_numpy()
        std = pd.Series(self.close, index=self.index).rolling(window=period).std(ddof=0).to_numpy()
        upper = middle + k * std
        lower = middle - k * std
        return pd.DataFrame({"bb_middle": middle, "bb_upper": upper, "bb_lower": lower}, index=self.index)

    # -----------------------
    # 4. MACD
    # -----------------------
    def macd(self, fast: int = 12, slow: int = 26, signal: int = 9) -> pd.DataFrame:
        """
        MACD 지표를 계산합니다.
        
        Args:
            fast (int, optional): 빠른 지수이동평균 기간. 기본값은 12입니다.
            slow (int, optional): 느린 지수이동평균 기간. 기본값은 26입니다.
            signal (int, optional): 시그널선 기간. 기본값은 9입니다.
        
        Returns:
            pd.DataFrame: MACD 값이 포함된 DataFrame.
        """
        ema_fast = self._ema(self.close, fast)
        ema_slow = self._ema(self.close, slow)
        macd_line = ema_fast - ema_slow
        signal_line = self._ema(macd_line, signal)
        hist = macd_line - signal_line
        return pd.DataFrame({"macd": macd_line, "macd_signal": signal_line, "macd_histogram": hist}, index=self.index)

    def macd_histogram_color(self, hist: pd.Series) -> pd.Series:
        """
        MACD 히스토그램의 색상을 결정합니다.
        
        Args:
            hist (pd.Series): MACD 히스토그램 값이 포함된 Series
        
        Returns:
            pd.Series: 색상 코드가 포함된 Series ('PI', 'PD', 'NI', 'ND')
        """
        hist_color = pd.Series(index=hist.index, dtype=object)
        for i in range(len(hist)):
            if i == 0:
                hist_color.iloc[i] = 'PI' if hist.iloc[i] > 0 else 'NI'
            else:
                if hist.iloc[i] > 0:
                    hist_color.iloc[i] = 'PI' if hist.iloc[i] > hist.iloc[i - 1] else 'PD'
                else:
                    hist_color.iloc[i] = 'NI' if hist.iloc[i] > hist.iloc[i - 1] else 'ND'
        return hist_color

    # -----------------------
    # 5. RSI (Wilder's method)
    # -----------------------
    def rsi(self, period: int = 14, signal: int = 9) -> pd.DataFrame:
        """
        RSI 지표를 Wilder 방법으로 계산합니다.
        
        Args:
            period (int, optional): 계산 기간. 기본값은 14입니다.
            signal (int, optional): 시그널선 기간. 기본값은 9입니다.
        
        Returns:
            pd.DataFrame: RSI 값이 포함된 DataFrame.
        """
        deltas = np.diff(self.close)
        gains = np.where(deltas > 0, deltas, 0.0)
        losses = np.where(deltas < 0, -deltas, 0.0)

        rsi = np.full_like(self.close, np.nan, dtype=float)

        avg_gain = np.sum(gains[:period]) / period
        avg_loss = np.sum(losses[:period]) / period
        rs = avg_gain / avg_loss if avg_loss != 0 else np.inf
        rsi[period] = 100 - (100 / (1 + rs))

        for i in range(period + 1, len(self.close)):
            avg_gain = (avg_gain * (period - 1) + gains[i - 1]) / period
            avg_loss = (avg_loss * (period - 1) + losses[i - 1]) / period
            rs = avg_gain / avg_loss if avg_loss != 0 else np.inf
            rsi[i] = 100 - (100 / (1 + rs))

        rsi_signal = self._ema(rsi, signal)
        return pd.DataFrame({"rsi": rsi, "rsi_signal": rsi_signal}, index=self.index)

    # -----------------------
    # 6. RSI (Cutler's method)
    # -----------------------
    def rsi_cutler(self, period: int = 14, signal: int = 9) -> pd.DataFrame:
        """
        RSI 지표를 Cutler 방법으로 계산합니다.
        
        Args:
            period (int, optional): 계산 기간. 기본값은 14입니다.
            signal (int, optional): 시그널선 기간. 기본값은 9입니다.
        
        Returns:
            pd.DataFrame: RSI 값이 포함된 DataFrame.
        """
        deltas = np.diff(self.close)
        gains = np.where(deltas > 0, deltas, 0.0)
        losses = np.where(deltas < 0, -deltas, 0.0)

        avg_gain = np.convolve(gains, np.ones(period)/period, mode='valid')
        avg_loss = np.convolve(losses, np.ones(period)/period, mode='valid')

        rs = avg_gain / avg_loss
        rsi = 100 - (100 / (1 + rs))

        result = np.full_like(self.close, np.nan, dtype=float)
        result[period:] = rsi
        rsi_signal = self._ema(result, signal)
        return pd.DataFrame({"rsi_cutler": result, "rsi_cutler_signal": rsi_signal}, index=self.index)

    # -----------------------
    # 7. OBV (On-Balance Volume)
    # -----------------------
    def obv(self) -> pd.Series:
        """
        OBV 지표를 계산합니다.
        
        Returns:
            pd.Series: OBV 값이 포함된 Series.
        """
        diff = np.diff(self.close)
        direction = np.sign(diff)
        direction = np.insert(direction, 0, 0)
        obv = np.cumsum(direction * self.volume)
        return pd.Series(obv, index=self.index)

    # -----------------------
    # 8. ADX (Average Directional Index)
    # -----------------------
    def adx(self, period: int = 14) -> pd.DataFrame:
        """
        ADX 지표를 계산합니다.
        
        Args:
            period (int, optional): 계산 기간. 기본값은 14입니다.
        
        Returns:
            pd.DataFrame: ADX 값이 포함된 DataFrame.
        """
        high, low, close = self.high, self.low, self.close
        n = len(close)

        # Up/Down move
        up_move = np.empty(n);   up_move[0] = np.nan;   up_move[1:] = high[1:] - high[:-1]
        down_move = np.empty(n); down_move[0] = np.nan; down_move[1:] = low[:-1] - low[1:]

        plus_dm = np.where((up_move > down_move) & (up_move > 0), up_move, 0.0)
        minus_dm = np.where((down_move > up_move) & (down_move > 0), down_move, 0.0)
        plus_dm[0] = np.nan; minus_dm[0] = np.nan  # 선행 NaN 유지

        # True Range
        prev_close = np.empty_like(close)
        prev_close[0] = np.nan
        prev_close[1:] = close[:-1]

        tr = np.maximum.reduce([
            high - low,
            np.abs(high - prev_close),
            np.abs(low - prev_close)
        ])

        # Wilder smoothing (RMA)
        atr = self._rma(tr, period)
        plus_dm_sm = self._rma(plus_dm, period)
        minus_dm_sm = self._rma(minus_dm, period)

        # DI
        with np.errstate(divide='ignore', invalid='ignore'):
            plus_di = 100.0 * (plus_dm_sm / atr)
            minus_di = 100.0 * (minus_dm_sm / atr)

            den = plus_di + minus_di
            dx = 100.0 * np.abs(plus_di - minus_di) / den
            dx[~np.isfinite(dx)] = np.nan  # 분모 0 등 처리

        # ADX (RMA of DX)
        adx = self._rma(dx, period)

        return pd.DataFrame(
            {"plus_di": plus_di, "minus_di": minus_di, "adx": adx},
            index=self.index
        )

    # -----------------------
    # 9. Stochastic RSI
    # -----------------------
    def stoch_rsi(self, period: int = 14, smooth_k: int = 3, smooth_d: int = 3) -> pd.DataFrame:
        """
        Stochastic RSI 지표를 계산합니다.
        
        Args:
            period (int, optional): RSI 계산 기간. 기본값은 14입니다.
            smooth_k (int, optional): %K 스무딩 기간. 기본값은 3입니다.
            smooth_d (int, optional): %D 스무딩 기간. 기본값은 3입니다.
        
        Returns:
            pd.DataFrame: Stochastic RSI 값이 포함된 DataFrame.
        """
        rsi_vals = self.rsi(period=period)["rsi"].to_numpy()
        min_rsi = pd.Series(rsi_vals).rolling(window=period).min().to_numpy()
        max_rsi = pd.Series(rsi_vals).rolling(window=period).max().to_numpy()
        with np.errstate(divide='ignore', invalid='ignore'):
            stoch_rsi = 100 * (rsi_vals - min_rsi) / (max_rsi - min_rsi)
            stoch_rsi[~np.isfinite(stoch_rsi)] = np.nan  # 분모 0 등 처리
        k = pd.Series(stoch_rsi).rolling(window=smooth_k).mean().to_numpy()
        d = pd.Series(k).rolling(window=smooth_d).mean().to_numpy()
        return pd.DataFrame({"stochrsi": stoch_rsi, "stochrsi_%K": k, "stochrsi_%D": d}, index=self.index)

    # -----------------------
    # 10. Williams %R
    # -----------------------
    def williams_r(self, period: int = 14) -> pd.Series:
        """
        Williams %R 지표를 계산합니다.
        
        Args:
            period (int, optional): 계산 기간. 기본값은 14입니다.
        
        Returns:
            pd.Series: Williams %R 값이 포함된 Series.
        """
        highest_high = pd.Series(self.high).rolling(window=period).max().to_numpy()
        lowest_low = pd.Series(self.low).rolling(window=period).min().to_numpy()
        with np.errstate(divide='ignore', invalid='ignore'):
            wr = (highest_high - self.close) / (highest_high - lowest_low) * -100
            wr[~np.isfinite(wr)] = np.nan  # 분모 0 등 처리
        return pd.Series(wr, index=self.index)

    # -----------------------
    # 11. Stochastic Oscillator
    # -----------------------
    def stochastic(self, period: int = 14, smooth_k: int = 3, smooth_d: int = 3) -> pd.DataFrame:
        """
        Stochastic Oscillator 지표를 계산합니다.
        
        Args:
            period (int, optional): 계산 기간. 기본값은 14입니다.
            smooth_k (int, optional): %K 스무딩 기간. 기본값은 3입니다.
            smooth_d (int, optional): %D 스무딩 기간. 기본값은 3입니다.
        
        Returns:
            pd.DataFrame: Stochastic Oscillator 값이 포함된 DataFrame.
        """
        low_min = pd.Series(self.low).rolling(window=period).min().to_numpy()
        high_max = pd.Series(self.high).rolling(window=period).max().to_numpy()
        k_fast = 100 * (self.close - low_min) / (high_max - low_min)
        k_slow = pd.Series(k_fast).rolling(window=smooth_k).mean().to_numpy()
        d = pd.Series(k_slow).rolling(window=smooth_d).mean().to_numpy()
        return pd.DataFrame({"stoch_fast_%K": k_fast, "stoch_%K": k_slow, "stoch_%D": d}, index=self.index)

    # -----------------------
    # 12. Ichimoku Kinko Hyo
    # -----------------------
    def ichimoku(self, tenkan_period: int = 9, kijun_period: int = 26,
                 senkou_period: int = 52, displacement: int = 26) -> pd.DataFrame:
        """
        Ichimoku Kinko Hyo (일목균형표) 지표를 계산합니다.
        
        Args:
            tenkan_period (int, optional): 전환선 기간. 기본값은 9입니다.
            kijun_period (int, optional): 기준선 기간. 기본값은 26입니다.
            senkou_period (int, optional): 선행스팬B 기간. 기본값은 52입니다.
            displacement (int, optional): 선행스팬 이동 기간. 기본값은 26입니다.
        
        Returns:
            pd.DataFrame: Ichimoku 값이 포함된 DataFrame.
        """
        tenkan = (pd.Series(self.high).rolling(window=tenkan_period).max() +
                  pd.Series(self.low).rolling(window=tenkan_period).min()) / 2
        kijun = (pd.Series(self.high).rolling(window=kijun_period).max() +
                 pd.Series(self.low).rolling(window=kijun_period).min()) / 2
        senkou_a = ((tenkan + kijun) / 2).shift(displacement - 1)
        senkou_b = ((pd.Series(self.high).rolling(window=senkou_period).max() +
                     pd.Series(self.low).rolling(window=senkou_period).min()) / 2).shift(displacement - 1)
        chikou = pd.Series(self.close).shift(-displacement)
        return pd.DataFrame({
            "tenkan": tenkan.to_numpy(),
            "kijun": kijun.to_numpy(),
            "senkou_a": senkou_a.to_numpy(),
            "senkou_b": senkou_b.to_numpy(),
            "chikou": chikou.to_numpy()
        }, index=self.index)
