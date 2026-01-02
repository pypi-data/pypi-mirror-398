//! Python bindings for zengeld-canvas
//!
//! Complete Python API for the zengeld-canvas chart rendering library.
//! Provides 1:1 mapping to Rust API.

use pyo3::prelude::*;

use ::zengeld_canvas::api::{
    Chart as RustChart, ChartConfig as RustChartConfig, PrimitiveConfig, SignalConfig,
};
use ::zengeld_canvas::core::Bar;
use ::zengeld_canvas::model::Indicator;
use ::zengeld_canvas::{RuntimeTheme, Theme, UITheme, Viewport};

// =============================================================================
// Bar - OHLCV data point
// =============================================================================

/// A single OHLCV bar representing one time period of price data.
#[pyclass(name = "Bar")]
#[derive(Clone)]
pub struct PyBar {
    inner: Bar,
}

#[pymethods]
impl PyBar {
    #[new]
    #[pyo3(signature = (timestamp, open, high, low, close, volume=0.0))]
    fn new(timestamp: i64, open: f64, high: f64, low: f64, close: f64, volume: f64) -> Self {
        Self {
            inner: Bar {
                timestamp,
                open,
                high,
                low,
                close,
                volume,
            },
        }
    }

    #[getter]
    fn timestamp(&self) -> i64 {
        self.inner.timestamp
    }
    #[getter]
    fn open(&self) -> f64 {
        self.inner.open
    }
    #[getter]
    fn high(&self) -> f64 {
        self.inner.high
    }
    #[getter]
    fn low(&self) -> f64 {
        self.inner.low
    }
    #[getter]
    fn close(&self) -> f64 {
        self.inner.close
    }
    #[getter]
    fn volume(&self) -> f64 {
        self.inner.volume
    }

    fn is_bullish(&self) -> bool {
        self.inner.close > self.inner.open
    }

    fn __repr__(&self) -> String {
        format!(
            "Bar(ts={}, o={}, h={}, l={}, c={}, v={})",
            self.inner.timestamp,
            self.inner.open,
            self.inner.high,
            self.inner.low,
            self.inner.close,
            self.inner.volume
        )
    }
}

impl PyBar {
    fn to_rust(&self) -> Bar {
        self.inner
    }
}

// =============================================================================
// Chart - Main chart builder API
// =============================================================================

/// High-level chart builder for creating financial charts.
#[pyclass(name = "Chart")]
pub struct PyChart {
    inner: Option<RustChart>,
}

impl PyChart {
    fn take_inner(&mut self) -> RustChart {
        self.inner.take().expect("Chart already consumed")
    }
    fn put_inner(&mut self, chart: RustChart) {
        self.inner = Some(chart);
    }
}

#[pymethods]
impl PyChart {
    #[new]
    #[pyo3(signature = (width, height))]
    fn new(width: u32, height: u32) -> Self {
        Self {
            inner: Some(RustChart::new(width, height)),
        }
    }

    // =========================================================================
    // Configuration
    // =========================================================================

    /// Set device pixel ratio for high-DPI displays
    fn dpr(&mut self, dpr: f64) {
        let chart = self.take_inner().dpr(dpr);
        self.put_inner(chart);
    }

    /// Set OHLCV bar data
    fn bars(&mut self, bars: Vec<PyBar>) {
        let rust_bars: Vec<Bar> = bars.iter().map(|b| b.to_rust()).collect();
        let chart = self.take_inner().bars(&rust_bars);
        self.put_inner(chart);
    }

    // =========================================================================
    // Series Types (12 total)
    // =========================================================================

    /// Candlestick chart (default)
    fn candlesticks(&mut self) {
        let chart = self.take_inner().candlesticks();
        self.put_inner(chart);
    }

    /// Line chart (close prices)
    fn line(&mut self) {
        let chart = self.take_inner().line();
        self.put_inner(chart);
    }

    /// Area chart (filled)
    fn area(&mut self) {
        let chart = self.take_inner().area();
        self.put_inner(chart);
    }

    // Note: Additional series types require extending the Rust Chart builder
    // The following are placeholders for when Rust API is extended:
    // hollow_candlestick, heikin_ashi, bar, hlc_area, step_line,
    // line_with_markers, baseline, histogram, columns

    // =========================================================================
    // Theme & Styling
    // =========================================================================

    /// Set up/down colors
    fn colors(&mut self, up: &str, down: &str) {
        let chart = self.take_inner().colors(up, down);
        self.put_inner(chart);
    }

    /// Set background color
    fn background(&mut self, color: &str) {
        let chart = self.take_inner().background(color);
        self.put_inner(chart);
    }

    /// Enable/disable grid
    fn grid(&mut self, show: bool) {
        let chart = self.take_inner().grid(show);
        self.put_inner(chart);
    }

    /// Apply dark theme
    fn dark_theme(&mut self) {
        let chart = self
            .take_inner()
            .background("#131722")
            .colors("#26a69a", "#ef5350");
        self.put_inner(chart);
    }

    /// Apply light theme
    fn light_theme(&mut self) {
        let chart = self
            .take_inner()
            .background("#ffffff")
            .colors("#26a69a", "#ef5350");
        self.put_inner(chart);
    }

    // =========================================================================
    // Moving Average Indicators (9 types)
    // =========================================================================

    /// Simple Moving Average
    fn sma(&mut self, period: usize, color: &str) {
        let chart = self.take_inner().sma(period, color);
        self.put_inner(chart);
    }

    /// Exponential Moving Average
    fn ema(&mut self, period: usize, color: &str) {
        let chart = self.take_inner().ema(period, color);
        self.put_inner(chart);
    }

    /// Weighted Moving Average
    fn wma(&mut self, period: usize, color: &str) {
        let id = format!("wma_{}", period);
        let indicator = Indicator::wma(&id, period as u32, color);
        let chart = self.take_inner().indicator(indicator);
        self.put_inner(chart);
    }

    /// Hull Moving Average
    fn hma(&mut self, period: usize, color: &str) {
        let id = format!("hma_{}", period);
        let indicator = Indicator::hma(&id, period as u32, color);
        let chart = self.take_inner().indicator(indicator);
        self.put_inner(chart);
    }

    /// Double Exponential Moving Average
    fn dema(&mut self, period: usize, color: &str) {
        let id = format!("dema_{}", period);
        let indicator = Indicator::dema(&id, period as u32, color);
        let chart = self.take_inner().indicator(indicator);
        self.put_inner(chart);
    }

    /// Triple Exponential Moving Average
    fn tema(&mut self, period: usize, color: &str) {
        let id = format!("tema_{}", period);
        let indicator = Indicator::tema(&id, period as u32, color);
        let chart = self.take_inner().indicator(indicator);
        self.put_inner(chart);
    }

    /// Kaufman Adaptive Moving Average
    fn kama(&mut self, period: usize, color: &str) {
        let id = format!("kama_{}", period);
        let indicator = Indicator::kama(&id, period as u32, color);
        let chart = self.take_inner().indicator(indicator);
        self.put_inner(chart);
    }

    /// Triangular Moving Average
    fn trima(&mut self, period: usize, color: &str) {
        let id = format!("trima_{}", period);
        let indicator = Indicator::trima(&id, period as u32, color);
        let chart = self.take_inner().indicator(indicator);
        self.put_inner(chart);
    }

    /// Zero Lag EMA
    fn zlema(&mut self, period: usize, color: &str) {
        let id = format!("zlema_{}", period);
        let indicator = Indicator::zlema(&id, period as u32, color);
        let chart = self.take_inner().indicator(indicator);
        self.put_inner(chart);
    }

    /// McGinley Dynamic
    fn mcginley(&mut self, period: usize, color: &str) {
        let id = format!("mcginley_{}", period);
        let indicator = Indicator::mcginley(&id, period as u32, color);
        let chart = self.take_inner().indicator(indicator);
        self.put_inner(chart);
    }

    // =========================================================================
    // Band Indicators (5 types)
    // =========================================================================

    /// Bollinger Bands
    fn bollinger(&mut self, period: usize, multiplier: f64) {
        let chart = self.take_inner().bollinger(period, multiplier);
        self.put_inner(chart);
    }

    /// Bollinger Bands with filled cloud
    fn bollinger_filled(&mut self, period: usize) {
        let id = format!("bb_filled_{}", period);
        let indicator = Indicator::bollinger_filled(&id, period as u32);
        let chart = self.take_inner().indicator(indicator);
        self.put_inner(chart);
    }

    /// Keltner Channel
    fn keltner(&mut self, period: usize) {
        let id = format!("keltner_{}", period);
        let indicator = Indicator::keltner(&id, period as u32);
        let chart = self.take_inner().indicator(indicator);
        self.put_inner(chart);
    }

    /// Donchian Channel
    fn donchian(&mut self, period: usize) {
        let id = format!("donchian_{}", period);
        let indicator = Indicator::donchian(&id, period as u32);
        let chart = self.take_inner().indicator(indicator);
        self.put_inner(chart);
    }

    /// ATR Bands
    fn atr_bands(&mut self, period: usize, multiplier: f64) {
        let id = format!("atr_bands_{}", period);
        let indicator = Indicator::atr_bands(&id, period as u32, multiplier);
        let chart = self.take_inner().indicator(indicator);
        self.put_inner(chart);
    }

    // =========================================================================
    // Oscillators / Momentum Indicators
    // =========================================================================

    /// Relative Strength Index
    fn rsi(&mut self, period: usize) {
        let chart = self.take_inner().rsi(period);
        self.put_inner(chart);
    }

    /// MACD
    fn macd(&mut self, fast: usize, slow: usize, signal: usize) {
        let chart = self.take_inner().macd(fast, slow, signal);
        self.put_inner(chart);
    }

    /// MACD with default settings (12, 26, 9)
    fn macd_default(&mut self) {
        let indicator = Indicator::macd_default("macd");
        let chart = self.take_inner().indicator(indicator);
        self.put_inner(chart);
    }

    /// Stochastic Oscillator
    fn stochastic(&mut self, k: usize, d: usize) {
        let id = format!("stoch_{}_{}", k, d);
        let indicator = Indicator::stochastic(&id, k as u32, d as u32);
        let chart = self.take_inner().indicator(indicator);
        self.put_inner(chart);
    }

    /// Stochastic RSI
    fn stoch_rsi(&mut self, period: usize) {
        let id = format!("stoch_rsi_{}", period);
        let indicator = Indicator::stoch_rsi(&id, period as u32);
        let chart = self.take_inner().indicator(indicator);
        self.put_inner(chart);
    }

    /// Commodity Channel Index
    fn cci(&mut self, period: usize) {
        let id = format!("cci_{}", period);
        let indicator = Indicator::cci(&id, period as u32);
        let chart = self.take_inner().indicator(indicator);
        self.put_inner(chart);
    }

    /// Williams %R
    fn williams_r(&mut self, period: usize) {
        let id = format!("williams_r_{}", period);
        let indicator = Indicator::williams_r(&id, period as u32);
        let chart = self.take_inner().indicator(indicator);
        self.put_inner(chart);
    }

    /// Momentum
    fn momentum(&mut self, period: usize) {
        let id = format!("momentum_{}", period);
        let indicator = Indicator::momentum(&id, period as u32);
        let chart = self.take_inner().indicator(indicator);
        self.put_inner(chart);
    }

    /// Rate of Change
    fn roc(&mut self, period: usize) {
        let id = format!("roc_{}", period);
        let indicator = Indicator::roc(&id, period as u32);
        let chart = self.take_inner().indicator(indicator);
        self.put_inner(chart);
    }

    /// True Strength Index
    fn tsi(&mut self, r: usize, s: usize) {
        let id = format!("tsi_{}_{}", r, s);
        let indicator = Indicator::tsi(&id, r as u32, s as u32);
        let chart = self.take_inner().indicator(indicator);
        self.put_inner(chart);
    }

    /// Ultimate Oscillator
    fn ultimate_oscillator(&mut self) {
        let indicator = Indicator::ultimate_oscillator("uo");
        let chart = self.take_inner().indicator(indicator);
        self.put_inner(chart);
    }

    /// Awesome Oscillator
    fn awesome_oscillator(&mut self) {
        let indicator = Indicator::awesome_oscillator("ao");
        let chart = self.take_inner().indicator(indicator);
        self.put_inner(chart);
    }

    /// Accelerator Oscillator
    fn accelerator_oscillator(&mut self) {
        let indicator = Indicator::accelerator_oscillator("ac");
        let chart = self.take_inner().indicator(indicator);
        self.put_inner(chart);
    }

    /// Chande Momentum Oscillator
    fn cmo(&mut self, period: usize) {
        let id = format!("cmo_{}", period);
        let indicator = Indicator::cmo(&id, period as u32);
        let chart = self.take_inner().indicator(indicator);
        self.put_inner(chart);
    }

    /// Detrended Price Oscillator
    fn dpo(&mut self, period: usize) {
        let id = format!("dpo_{}", period);
        let indicator = Indicator::dpo(&id, period as u32);
        let chart = self.take_inner().indicator(indicator);
        self.put_inner(chart);
    }

    /// Know Sure Thing
    fn kst(&mut self) {
        let indicator = Indicator::kst("kst");
        let chart = self.take_inner().indicator(indicator);
        self.put_inner(chart);
    }

    /// Relative Vigor Index
    fn rvi(&mut self, period: usize) {
        let id = format!("rvi_{}", period);
        let indicator = Indicator::rvi(&id, period as u32);
        let chart = self.take_inner().indicator(indicator);
        self.put_inner(chart);
    }

    // =========================================================================
    // Volatility Indicators
    // =========================================================================

    /// Average True Range
    fn atr(&mut self, period: usize) {
        let id = format!("atr_{}", period);
        let indicator = Indicator::atr(&id, period as u32);
        let chart = self.take_inner().indicator(indicator);
        self.put_inner(chart);
    }

    /// Standard Deviation
    fn stddev(&mut self, period: usize) {
        let id = format!("stddev_{}", period);
        let indicator = Indicator::stddev(&id, period as u32);
        let chart = self.take_inner().indicator(indicator);
        self.put_inner(chart);
    }

    /// Historical Volatility
    fn historical_volatility(&mut self, period: usize) {
        let id = format!("hv_{}", period);
        let indicator = Indicator::historical_volatility(&id, period as u32);
        let chart = self.take_inner().indicator(indicator);
        self.put_inner(chart);
    }

    /// Choppiness Index
    fn choppiness(&mut self, period: usize) {
        let id = format!("chop_{}", period);
        let indicator = Indicator::choppiness(&id, period as u32);
        let chart = self.take_inner().indicator(indicator);
        self.put_inner(chart);
    }

    /// Mass Index
    fn mass_index(&mut self) {
        let indicator = Indicator::mass_index("mass");
        let chart = self.take_inner().indicator(indicator);
        self.put_inner(chart);
    }

    /// Ulcer Index
    fn ulcer_index(&mut self, period: usize) {
        let id = format!("ulcer_{}", period);
        let indicator = Indicator::ulcer_index(&id, period as u32);
        let chart = self.take_inner().indicator(indicator);
        self.put_inner(chart);
    }

    // =========================================================================
    // Trend Indicators
    // =========================================================================

    /// Average Directional Index
    fn adx(&mut self, period: usize) {
        let id = format!("adx_{}", period);
        let indicator = Indicator::adx(&id, period as u32);
        let chart = self.take_inner().indicator(indicator);
        self.put_inner(chart);
    }

    /// Aroon
    fn aroon(&mut self, period: usize) {
        let id = format!("aroon_{}", period);
        let indicator = Indicator::aroon(&id, period as u32);
        let chart = self.take_inner().indicator(indicator);
        self.put_inner(chart);
    }

    /// Aroon Oscillator
    fn aroon_oscillator(&mut self, period: usize) {
        let id = format!("aroon_osc_{}", period);
        let indicator = Indicator::aroon_oscillator(&id, period as u32);
        let chart = self.take_inner().indicator(indicator);
        self.put_inner(chart);
    }

    /// Vortex Indicator
    fn vortex(&mut self, period: usize) {
        let id = format!("vortex_{}", period);
        let indicator = Indicator::vortex(&id, period as u32);
        let chart = self.take_inner().indicator(indicator);
        self.put_inner(chart);
    }

    /// Linear Regression
    fn linear_regression(&mut self, period: usize, color: &str) {
        let id = format!("linreg_{}", period);
        let indicator = Indicator::linear_regression(&id, period as u32, color);
        let chart = self.take_inner().indicator(indicator);
        self.put_inner(chart);
    }

    /// Linear Regression Slope
    fn linear_regression_slope(&mut self, period: usize) {
        let id = format!("linreg_slope_{}", period);
        let indicator = Indicator::linear_regression_slope(&id, period as u32);
        let chart = self.take_inner().indicator(indicator);
        self.put_inner(chart);
    }

    /// ZigZag
    fn zigzag(&mut self, deviation: f64) {
        let indicator = Indicator::zigzag("zigzag", deviation);
        let chart = self.take_inner().indicator(indicator);
        self.put_inner(chart);
    }

    /// TRIX
    fn trix(&mut self, period: usize) {
        let id = format!("trix_{}", period);
        let indicator = Indicator::trix(&id, period as u32);
        let chart = self.take_inner().indicator(indicator);
        self.put_inner(chart);
    }

    /// Chande Kroll Stop
    fn chande_kroll_stop(&mut self) {
        let indicator = Indicator::chande_kroll_stop("cks");
        let chart = self.take_inner().indicator(indicator);
        self.put_inner(chart);
    }

    /// Parabolic SAR
    fn psar(&mut self) {
        let indicator = Indicator::psar("psar");
        let chart = self.take_inner().indicator(indicator);
        self.put_inner(chart);
    }

    /// Supertrend
    fn supertrend(&mut self, period: usize, multiplier: f64) {
        let id = format!("supertrend_{}", period);
        let indicator = Indicator::supertrend(&id, period as u32, multiplier);
        let chart = self.take_inner().indicator(indicator);
        self.put_inner(chart);
    }

    /// Ichimoku Cloud
    fn ichimoku(&mut self) {
        let indicator = Indicator::ichimoku("ichimoku");
        let chart = self.take_inner().indicator(indicator);
        self.put_inner(chart);
    }

    // =========================================================================
    // Volume Indicators
    // =========================================================================

    /// Volume (subpane)
    fn volume(&mut self) {
        let chart = self.take_inner().volume();
        self.put_inner(chart);
    }

    /// On Balance Volume
    fn obv(&mut self) {
        let indicator = Indicator::obv("obv");
        let chart = self.take_inner().indicator(indicator);
        self.put_inner(chart);
    }

    /// Accumulation/Distribution Line
    fn ad_line(&mut self) {
        let indicator = Indicator::ad_line("ad");
        let chart = self.take_inner().indicator(indicator);
        self.put_inner(chart);
    }

    /// Chaikin Money Flow
    fn cmf(&mut self, period: usize) {
        let id = format!("cmf_{}", period);
        let indicator = Indicator::cmf(&id, period as u32);
        let chart = self.take_inner().indicator(indicator);
        self.put_inner(chart);
    }

    /// Chaikin Oscillator
    fn chaikin_oscillator(&mut self) {
        let indicator = Indicator::chaikin_oscillator("cho");
        let chart = self.take_inner().indicator(indicator);
        self.put_inner(chart);
    }

    /// Volume Price Trend
    fn vpt(&mut self) {
        let indicator = Indicator::vpt("vpt");
        let chart = self.take_inner().indicator(indicator);
        self.put_inner(chart);
    }

    /// Force Index
    fn force_index(&mut self, period: usize) {
        let id = format!("fi_{}", period);
        let indicator = Indicator::force_index(&id, period as u32);
        let chart = self.take_inner().indicator(indicator);
        self.put_inner(chart);
    }

    /// Ease of Movement
    fn eom(&mut self, period: usize) {
        let id = format!("eom_{}", period);
        let indicator = Indicator::eom(&id, period as u32);
        let chart = self.take_inner().indicator(indicator);
        self.put_inner(chart);
    }

    /// Negative Volume Index
    fn nvi(&mut self) {
        let indicator = Indicator::nvi("nvi");
        let chart = self.take_inner().indicator(indicator);
        self.put_inner(chart);
    }

    /// Positive Volume Index
    fn pvi(&mut self) {
        let indicator = Indicator::pvi("pvi");
        let chart = self.take_inner().indicator(indicator);
        self.put_inner(chart);
    }

    /// Money Flow Index
    fn mfi(&mut self, period: usize) {
        let id = format!("mfi_{}", period);
        let indicator = Indicator::mfi(&id, period as u32);
        let chart = self.take_inner().indicator(indicator);
        self.put_inner(chart);
    }

    /// VWAP
    fn vwap(&mut self) {
        let indicator = Indicator::vwap("vwap");
        let chart = self.take_inner().indicator(indicator);
        self.put_inner(chart);
    }

    // =========================================================================
    // Specialized Indicators
    // =========================================================================

    /// Elder Ray
    fn elder_ray(&mut self, period: usize) {
        let id = format!("elder_ray_{}", period);
        let indicator = Indicator::elder_ray(&id, period as u32);
        let chart = self.take_inner().indicator(indicator);
        self.put_inner(chart);
    }

    /// Balance of Power
    fn balance_of_power(&mut self) {
        let indicator = Indicator::balance_of_power("bop");
        let chart = self.take_inner().indicator(indicator);
        self.put_inner(chart);
    }

    /// Connors RSI
    fn connors_rsi(&mut self) {
        let indicator = Indicator::connors_rsi("crsi");
        let chart = self.take_inner().indicator(indicator);
        self.put_inner(chart);
    }

    /// Coppock Curve
    fn coppock_curve(&mut self) {
        let indicator = Indicator::coppock_curve("coppock");
        let chart = self.take_inner().indicator(indicator);
        self.put_inner(chart);
    }

    /// Fisher Transform
    fn fisher_transform(&mut self, period: usize) {
        let id = format!("fisher_{}", period);
        let indicator = Indicator::fisher_transform(&id, period as u32);
        let chart = self.take_inner().indicator(indicator);
        self.put_inner(chart);
    }

    /// SMI Ergodic
    fn smi_ergodic(&mut self) {
        let indicator = Indicator::smi_ergodic("smi");
        let chart = self.take_inner().indicator(indicator);
        self.put_inner(chart);
    }

    /// Schaff Trend Cycle
    fn schaff_trend_cycle(&mut self) {
        let indicator = Indicator::schaff_trend_cycle("stc");
        let chart = self.take_inner().indicator(indicator);
        self.put_inner(chart);
    }

    /// Pretty Good Oscillator
    fn pgo(&mut self, period: usize) {
        let id = format!("pgo_{}", period);
        let indicator = Indicator::pgo(&id, period as u32);
        let chart = self.take_inner().indicator(indicator);
        self.put_inner(chart);
    }

    /// QStick
    fn qstick(&mut self, period: usize) {
        let id = format!("qstick_{}", period);
        let indicator = Indicator::qstick(&id, period as u32);
        let chart = self.take_inner().indicator(indicator);
        self.put_inner(chart);
    }

    /// Pivot Points
    fn pivot_points(&mut self) {
        let indicator = Indicator::pivot_points("pp");
        let chart = self.take_inner().indicator(indicator);
        self.put_inner(chart);
    }

    /// Envelopes
    fn envelopes(&mut self, period: usize, percent: f64) {
        let id = format!("env_{}", period);
        let indicator = Indicator::envelopes(&id, period as u32, percent);
        let chart = self.take_inner().indicator(indicator);
        self.put_inner(chart);
    }

    /// Price Channel
    fn price_channel(&mut self, period: usize) {
        let id = format!("pc_{}", period);
        let indicator = Indicator::price_channel(&id, period as u32);
        let chart = self.take_inner().indicator(indicator);
        self.put_inner(chart);
    }

    /// Custom overlay with pre-calculated values
    fn overlay(&mut self, name: &str, values: Vec<f64>, color: &str) {
        let chart = self.take_inner().overlay(name, values, color);
        self.put_inner(chart);
    }

    // =========================================================================
    // Signals (7 types)
    // =========================================================================

    /// Buy signal
    #[pyo3(signature = (bar_index, price, label=None))]
    fn buy_signal(&mut self, bar_index: usize, price: f64, label: Option<String>) {
        let mut signal = SignalConfig::buy(bar_index, price);
        if let Some(l) = label {
            signal = signal.with_label(&l);
        }
        let chart = self.take_inner().signal(signal);
        self.put_inner(chart);
    }

    /// Sell signal
    #[pyo3(signature = (bar_index, price, label=None))]
    fn sell_signal(&mut self, bar_index: usize, price: f64, label: Option<String>) {
        let mut signal = SignalConfig::sell(bar_index, price);
        if let Some(l) = label {
            signal = signal.with_label(&l);
        }
        let chart = self.take_inner().signal(signal);
        self.put_inner(chart);
    }

    /// Entry signal
    #[pyo3(signature = (bar_index, price, label=None))]
    fn entry_signal(&mut self, bar_index: usize, price: f64, label: Option<String>) {
        let mut signal = SignalConfig::entry(bar_index, price);
        if let Some(l) = label {
            signal = signal.with_label(&l);
        }
        let chart = self.take_inner().signal(signal);
        self.put_inner(chart);
    }

    /// Exit signal
    #[pyo3(signature = (bar_index, price, label=None))]
    fn exit_signal(&mut self, bar_index: usize, price: f64, label: Option<String>) {
        let mut signal = SignalConfig::exit(bar_index, price);
        if let Some(l) = label {
            signal = signal.with_label(&l);
        }
        let chart = self.take_inner().signal(signal);
        self.put_inner(chart);
    }

    /// Take profit signal
    #[pyo3(signature = (bar_index, price, label=None))]
    fn take_profit_signal(&mut self, bar_index: usize, price: f64, label: Option<String>) {
        let mut signal = SignalConfig::take_profit(bar_index, price);
        if let Some(l) = label {
            signal = signal.with_label(&l);
        }
        let chart = self.take_inner().signal(signal);
        self.put_inner(chart);
    }

    /// Stop loss signal
    #[pyo3(signature = (bar_index, price, label=None))]
    fn stop_loss_signal(&mut self, bar_index: usize, price: f64, label: Option<String>) {
        let mut signal = SignalConfig::stop_loss(bar_index, price);
        if let Some(l) = label {
            signal = signal.with_label(&l);
        }
        let chart = self.take_inner().signal(signal);
        self.put_inner(chart);
    }

    /// Custom signal
    #[pyo3(signature = (bar_index, price, label))]
    fn custom_signal(&mut self, bar_index: usize, price: f64, label: &str) {
        let signal = SignalConfig::custom(bar_index, price, label);
        let chart = self.take_inner().signal(signal);
        self.put_inner(chart);
    }

    // =========================================================================
    // Lines (9 primitives)
    // =========================================================================

    /// Horizontal line at price level
    fn horizontal_line(&mut self, price: f64) {
        let primitive = PrimitiveConfig::horizontal_line(price);
        let chart = self.take_inner().primitive(primitive);
        self.put_inner(chart);
    }

    /// Vertical line at bar index
    fn vertical_line(&mut self, bar_index: f64) {
        let primitive = PrimitiveConfig::vertical_line(bar_index);
        let chart = self.take_inner().primitive(primitive);
        self.put_inner(chart);
    }

    /// Trend line between two points
    fn trend_line(&mut self, start: (f64, f64), end: (f64, f64)) {
        let primitive = PrimitiveConfig::trend_line(start, end);
        let chart = self.take_inner().primitive(primitive);
        self.put_inner(chart);
    }

    /// Ray from p1 through p2
    fn ray(&mut self, p1: (f64, f64), p2: (f64, f64)) {
        let primitive = PrimitiveConfig::ray(p1, p2);
        let chart = self.take_inner().primitive(primitive);
        self.put_inner(chart);
    }

    /// Extended line (infinite in both directions)
    fn extended_line(&mut self, p1: (f64, f64), p2: (f64, f64)) {
        let primitive = PrimitiveConfig::extended_line(p1, p2);
        let chart = self.take_inner().primitive(primitive);
        self.put_inner(chart);
    }

    /// Info line with measurements
    fn info_line(&mut self, p1: (f64, f64), p2: (f64, f64)) {
        let primitive = PrimitiveConfig::info_line(p1, p2);
        let chart = self.take_inner().primitive(primitive);
        self.put_inner(chart);
    }

    /// Trend angle
    fn trend_angle(&mut self, p1: (f64, f64), p2: (f64, f64)) {
        let primitive = PrimitiveConfig::trend_angle(p1, p2);
        let chart = self.take_inner().primitive(primitive);
        self.put_inner(chart);
    }

    /// Horizontal ray
    fn horizontal_ray(&mut self, p1: (f64, f64), p2: (f64, f64)) {
        let primitive = PrimitiveConfig::horizontal_ray(p1, p2);
        let chart = self.take_inner().primitive(primitive);
        self.put_inner(chart);
    }

    /// Cross line at position
    fn cross_line(&mut self, position: (f64, f64)) {
        let primitive = PrimitiveConfig::cross_line(position);
        let chart = self.take_inner().primitive(primitive);
        self.put_inner(chart);
    }

    // =========================================================================
    // Channels (4 primitives)
    // =========================================================================

    /// Parallel channel
    fn parallel_channel(&mut self, p1: (f64, f64), p2: (f64, f64), p3: (f64, f64)) {
        let primitive = PrimitiveConfig::parallel_channel(p1, p2, p3);
        let chart = self.take_inner().primitive(primitive);
        self.put_inner(chart);
    }

    /// Regression trend channel
    fn regression_trend(&mut self, p1: (f64, f64), p2: (f64, f64)) {
        let primitive = PrimitiveConfig::regression_trend(p1, p2);
        let chart = self.take_inner().primitive(primitive);
        self.put_inner(chart);
    }

    /// Flat top/bottom channel
    fn flat_top_bottom(&mut self, p1: (f64, f64), p2: (f64, f64), p3: (f64, f64)) {
        let primitive = PrimitiveConfig::flat_top_bottom(p1, p2, p3);
        let chart = self.take_inner().primitive(primitive);
        self.put_inner(chart);
    }

    /// Disjoint channel
    fn disjoint_channel(&mut self, points: Vec<(f64, f64)>) {
        let primitive = PrimitiveConfig::disjoint_channel(points);
        let chart = self.take_inner().primitive(primitive);
        self.put_inner(chart);
    }

    // =========================================================================
    // Shapes (10 primitives)
    // =========================================================================

    /// Rectangle
    fn rectangle(&mut self, p1: (f64, f64), p2: (f64, f64)) {
        let primitive = PrimitiveConfig::rectangle(p1, p2);
        let chart = self.take_inner().primitive(primitive);
        self.put_inner(chart);
    }

    /// Circle
    fn circle(&mut self, center: (f64, f64), edge: (f64, f64)) {
        let primitive = PrimitiveConfig::circle(center, edge);
        let chart = self.take_inner().primitive(primitive);
        self.put_inner(chart);
    }

    /// Ellipse
    fn ellipse(&mut self, center: (f64, f64), edge: (f64, f64)) {
        let primitive = PrimitiveConfig::ellipse(center, edge);
        let chart = self.take_inner().primitive(primitive);
        self.put_inner(chart);
    }

    /// Triangle
    fn triangle(&mut self, p1: (f64, f64), p2: (f64, f64), p3: (f64, f64)) {
        let primitive = PrimitiveConfig::triangle(p1, p2, p3);
        let chart = self.take_inner().primitive(primitive);
        self.put_inner(chart);
    }

    /// Arc
    fn arc(&mut self, p1: (f64, f64), p2: (f64, f64), p3: (f64, f64)) {
        let primitive = PrimitiveConfig::arc(p1, p2, p3);
        let chart = self.take_inner().primitive(primitive);
        self.put_inner(chart);
    }

    /// Polyline
    fn polyline(&mut self, points: Vec<(f64, f64)>) {
        let primitive = PrimitiveConfig::polyline(points);
        let chart = self.take_inner().primitive(primitive);
        self.put_inner(chart);
    }

    /// Path (closed polygon)
    fn path(&mut self, points: Vec<(f64, f64)>) {
        let primitive = PrimitiveConfig::path(points);
        let chart = self.take_inner().primitive(primitive);
        self.put_inner(chart);
    }

    /// Rotated rectangle
    fn rotated_rectangle(&mut self, p1: (f64, f64), p2: (f64, f64), p3: (f64, f64)) {
        let primitive = PrimitiveConfig::rotated_rectangle(p1, p2, p3);
        let chart = self.take_inner().primitive(primitive);
        self.put_inner(chart);
    }

    /// Curve
    fn curve(&mut self, points: Vec<(f64, f64)>) {
        let primitive = PrimitiveConfig::curve(points);
        let chart = self.take_inner().primitive(primitive);
        self.put_inner(chart);
    }

    /// Double curve
    fn double_curve(&mut self, points: Vec<(f64, f64)>) {
        let primitive = PrimitiveConfig::double_curve(points);
        let chart = self.take_inner().primitive(primitive);
        self.put_inner(chart);
    }

    // =========================================================================
    // Fibonacci (11 primitives)
    // =========================================================================

    /// Fibonacci retracement
    fn fib_retracement(&mut self, p1: (f64, f64), p2: (f64, f64)) {
        let primitive = PrimitiveConfig::fib_retracement(p1, p2);
        let chart = self.take_inner().primitive(primitive);
        self.put_inner(chart);
    }

    /// Fibonacci extension
    fn fib_extension(&mut self, p1: (f64, f64), p2: (f64, f64), p3: (f64, f64)) {
        let primitive = PrimitiveConfig::fib_extension(p1, p2, p3);
        let chart = self.take_inner().primitive(primitive);
        self.put_inner(chart);
    }

    /// Fibonacci channel
    fn fib_channel(&mut self, p1: (f64, f64), p2: (f64, f64), p3: (f64, f64)) {
        let primitive = PrimitiveConfig::fib_channel(p1, p2, p3);
        let chart = self.take_inner().primitive(primitive);
        self.put_inner(chart);
    }

    /// Fibonacci time zones
    fn fib_time_zones(&mut self, p1: (f64, f64), p2: (f64, f64)) {
        let primitive = PrimitiveConfig::fib_time_zones(p1, p2);
        let chart = self.take_inner().primitive(primitive);
        self.put_inner(chart);
    }

    /// Fibonacci speed/resistance
    fn fib_speed_resistance(&mut self, p1: (f64, f64), p2: (f64, f64)) {
        let primitive = PrimitiveConfig::fib_speed_resistance(p1, p2);
        let chart = self.take_inner().primitive(primitive);
        self.put_inner(chart);
    }

    /// Fibonacci trend time
    fn fib_trend_time(&mut self, p1: (f64, f64), p2: (f64, f64), p3: (f64, f64)) {
        let primitive = PrimitiveConfig::fib_trend_time(p1, p2, p3);
        let chart = self.take_inner().primitive(primitive);
        self.put_inner(chart);
    }

    /// Fibonacci circles
    fn fib_circles(&mut self, p1: (f64, f64), p2: (f64, f64)) {
        let primitive = PrimitiveConfig::fib_circles(p1, p2);
        let chart = self.take_inner().primitive(primitive);
        self.put_inner(chart);
    }

    /// Fibonacci spiral
    fn fib_spiral(&mut self, p1: (f64, f64), p2: (f64, f64)) {
        let primitive = PrimitiveConfig::fib_spiral(p1, p2);
        let chart = self.take_inner().primitive(primitive);
        self.put_inner(chart);
    }

    /// Fibonacci arcs
    fn fib_arcs(&mut self, p1: (f64, f64), p2: (f64, f64)) {
        let primitive = PrimitiveConfig::fib_arcs(p1, p2);
        let chart = self.take_inner().primitive(primitive);
        self.put_inner(chart);
    }

    /// Fibonacci wedge
    fn fib_wedge(&mut self, p1: (f64, f64), p2: (f64, f64)) {
        let primitive = PrimitiveConfig::fib_wedge(p1, p2);
        let chart = self.take_inner().primitive(primitive);
        self.put_inner(chart);
    }

    /// Fibonacci fan
    fn fib_fan(&mut self, p1: (f64, f64), p2: (f64, f64)) {
        let primitive = PrimitiveConfig::fib_fan(p1, p2);
        let chart = self.take_inner().primitive(primitive);
        self.put_inner(chart);
    }

    // =========================================================================
    // Pitchforks (4 primitives)
    // =========================================================================

    /// Pitchfork
    fn pitchfork(&mut self, p1: (f64, f64), p2: (f64, f64), p3: (f64, f64)) {
        let primitive = PrimitiveConfig::pitchfork(p1, p2, p3);
        let chart = self.take_inner().primitive(primitive);
        self.put_inner(chart);
    }

    /// Schiff Pitchfork
    fn schiff_pitchfork(&mut self, p1: (f64, f64), p2: (f64, f64), p3: (f64, f64)) {
        let primitive = PrimitiveConfig::schiff_pitchfork(p1, p2, p3);
        let chart = self.take_inner().primitive(primitive);
        self.put_inner(chart);
    }

    /// Modified Schiff Pitchfork
    fn modified_schiff(&mut self, p1: (f64, f64), p2: (f64, f64), p3: (f64, f64)) {
        let primitive = PrimitiveConfig::modified_schiff(p1, p2, p3);
        let chart = self.take_inner().primitive(primitive);
        self.put_inner(chart);
    }

    /// Inside Pitchfork
    fn inside_pitchfork(&mut self, p1: (f64, f64), p2: (f64, f64), p3: (f64, f64)) {
        let primitive = PrimitiveConfig::inside_pitchfork(p1, p2, p3);
        let chart = self.take_inner().primitive(primitive);
        self.put_inner(chart);
    }

    // =========================================================================
    // Gann (4 primitives)
    // =========================================================================

    /// Gann Box
    fn gann_box(&mut self, p1: (f64, f64), p2: (f64, f64)) {
        let primitive = PrimitiveConfig::gann_box(p1, p2);
        let chart = self.take_inner().primitive(primitive);
        self.put_inner(chart);
    }

    /// Gann Square Fixed
    fn gann_square_fixed(&mut self, p1: (f64, f64), p2: (f64, f64)) {
        let primitive = PrimitiveConfig::gann_square_fixed(p1, p2);
        let chart = self.take_inner().primitive(primitive);
        self.put_inner(chart);
    }

    /// Gann Square
    fn gann_square(&mut self, p1: (f64, f64), p2: (f64, f64)) {
        let primitive = PrimitiveConfig::gann_square(p1, p2);
        let chart = self.take_inner().primitive(primitive);
        self.put_inner(chart);
    }

    /// Gann Fan
    fn gann_fan(&mut self, p1: (f64, f64), p2: (f64, f64)) {
        let primitive = PrimitiveConfig::gann_fan(p1, p2);
        let chart = self.take_inner().primitive(primitive);
        self.put_inner(chart);
    }

    // =========================================================================
    // Patterns (6 primitives)
    // =========================================================================

    /// XABCD Pattern
    fn xabcd_pattern(&mut self, points: Vec<(f64, f64)>) {
        let primitive = PrimitiveConfig::xabcd_pattern(points);
        let chart = self.take_inner().primitive(primitive);
        self.put_inner(chart);
    }

    /// Cypher Pattern
    fn cypher_pattern(&mut self, points: Vec<(f64, f64)>) {
        let primitive = PrimitiveConfig::cypher_pattern(points);
        let chart = self.take_inner().primitive(primitive);
        self.put_inner(chart);
    }

    /// Head and Shoulders
    fn head_shoulders(&mut self, points: Vec<(f64, f64)>) {
        let primitive = PrimitiveConfig::head_shoulders(points);
        let chart = self.take_inner().primitive(primitive);
        self.put_inner(chart);
    }

    /// ABCD Pattern
    fn abcd_pattern(&mut self, points: Vec<(f64, f64)>) {
        let primitive = PrimitiveConfig::abcd_pattern(points);
        let chart = self.take_inner().primitive(primitive);
        self.put_inner(chart);
    }

    /// Triangle Pattern
    fn triangle_pattern(&mut self, p1: (f64, f64), p2: (f64, f64), p3: (f64, f64)) {
        let primitive = PrimitiveConfig::triangle_pattern(p1, p2, p3);
        let chart = self.take_inner().primitive(primitive);
        self.put_inner(chart);
    }

    /// Three Drives
    fn three_drives(&mut self, points: Vec<(f64, f64)>) {
        let primitive = PrimitiveConfig::three_drives(points);
        let chart = self.take_inner().primitive(primitive);
        self.put_inner(chart);
    }

    // =========================================================================
    // Elliott Waves (5 primitives)
    // =========================================================================

    /// Elliott Impulse Wave
    fn elliott_impulse(&mut self, points: Vec<(f64, f64)>) {
        let primitive = PrimitiveConfig::elliott_impulse(points);
        let chart = self.take_inner().primitive(primitive);
        self.put_inner(chart);
    }

    /// Elliott Correction Wave
    fn elliott_correction(&mut self, points: Vec<(f64, f64)>) {
        let primitive = PrimitiveConfig::elliott_correction(points);
        let chart = self.take_inner().primitive(primitive);
        self.put_inner(chart);
    }

    /// Elliott Triangle
    fn elliott_triangle(&mut self, points: Vec<(f64, f64)>) {
        let primitive = PrimitiveConfig::elliott_triangle(points);
        let chart = self.take_inner().primitive(primitive);
        self.put_inner(chart);
    }

    /// Elliott Double Combo
    fn elliott_double_combo(&mut self, points: Vec<(f64, f64)>) {
        let primitive = PrimitiveConfig::elliott_double_combo(points);
        let chart = self.take_inner().primitive(primitive);
        self.put_inner(chart);
    }

    /// Elliott Triple Combo
    fn elliott_triple_combo(&mut self, points: Vec<(f64, f64)>) {
        let primitive = PrimitiveConfig::elliott_triple_combo(points);
        let chart = self.take_inner().primitive(primitive);
        self.put_inner(chart);
    }

    // =========================================================================
    // Arrows (4 primitives)
    // =========================================================================

    /// Arrow marker
    fn arrow_marker(&mut self, p1: (f64, f64), p2: (f64, f64)) {
        let primitive = PrimitiveConfig::arrow_marker(p1, p2);
        let chart = self.take_inner().primitive(primitive);
        self.put_inner(chart);
    }

    /// Arrow line
    fn arrow_line(&mut self, p1: (f64, f64), p2: (f64, f64)) {
        let primitive = PrimitiveConfig::arrow_line(p1, p2);
        let chart = self.take_inner().primitive(primitive);
        self.put_inner(chart);
    }

    /// Arrow up
    fn arrow_up(&mut self, position: (f64, f64)) {
        let primitive = PrimitiveConfig::arrow_up(position);
        let chart = self.take_inner().primitive(primitive);
        self.put_inner(chart);
    }

    /// Arrow down
    fn arrow_down(&mut self, position: (f64, f64)) {
        let primitive = PrimitiveConfig::arrow_down(position);
        let chart = self.take_inner().primitive(primitive);
        self.put_inner(chart);
    }

    // =========================================================================
    // Annotations (11 primitives)
    // =========================================================================

    /// Text annotation
    fn text(&mut self, position: (f64, f64), content: &str) {
        let primitive = PrimitiveConfig::text(position, content);
        let chart = self.take_inner().primitive(primitive);
        self.put_inner(chart);
    }

    /// Anchored text
    fn anchored_text(&mut self, p1: (f64, f64), p2: (f64, f64), content: &str) {
        let primitive = PrimitiveConfig::anchored_text(p1, p2, content);
        let chart = self.take_inner().primitive(primitive);
        self.put_inner(chart);
    }

    /// Note
    fn note(&mut self, position: (f64, f64), content: &str) {
        let primitive = PrimitiveConfig::note(position, content);
        let chart = self.take_inner().primitive(primitive);
        self.put_inner(chart);
    }

    /// Price note
    fn price_note(&mut self, position: (f64, f64), content: &str) {
        let primitive = PrimitiveConfig::price_note(position, content);
        let chart = self.take_inner().primitive(primitive);
        self.put_inner(chart);
    }

    /// Signpost
    fn signpost(&mut self, position: (f64, f64), content: &str) {
        let primitive = PrimitiveConfig::signpost(position, content);
        let chart = self.take_inner().primitive(primitive);
        self.put_inner(chart);
    }

    /// Callout
    fn callout(&mut self, position: (f64, f64), content: &str) {
        let primitive = PrimitiveConfig::callout(position, content);
        let chart = self.take_inner().primitive(primitive);
        self.put_inner(chart);
    }

    /// Comment
    fn comment(&mut self, position: (f64, f64), content: &str) {
        let primitive = PrimitiveConfig::comment(position, content);
        let chart = self.take_inner().primitive(primitive);
        self.put_inner(chart);
    }

    /// Price label
    fn price_label(&mut self, position: (f64, f64)) {
        let primitive = PrimitiveConfig::price_label(position);
        let chart = self.take_inner().primitive(primitive);
        self.put_inner(chart);
    }

    /// Sign
    fn sign(&mut self, position: (f64, f64)) {
        let primitive = PrimitiveConfig::sign(position);
        let chart = self.take_inner().primitive(primitive);
        self.put_inner(chart);
    }

    /// Flag
    fn flag(&mut self, position: (f64, f64)) {
        let primitive = PrimitiveConfig::flag(position);
        let chart = self.take_inner().primitive(primitive);
        self.put_inner(chart);
    }

    /// Table
    fn table(&mut self, position: (f64, f64)) {
        let primitive = PrimitiveConfig::table(position);
        let chart = self.take_inner().primitive(primitive);
        self.put_inner(chart);
    }

    // =========================================================================
    // Cycles (3 primitives)
    // =========================================================================

    /// Cycle lines
    fn cycle_lines(&mut self, p1: (f64, f64), p2: (f64, f64)) {
        let primitive = PrimitiveConfig::cycle_lines(p1, p2);
        let chart = self.take_inner().primitive(primitive);
        self.put_inner(chart);
    }

    /// Time cycles
    fn time_cycles(&mut self, p1: (f64, f64), p2: (f64, f64)) {
        let primitive = PrimitiveConfig::time_cycles(p1, p2);
        let chart = self.take_inner().primitive(primitive);
        self.put_inner(chart);
    }

    /// Sine wave
    fn sine_wave(&mut self, p1: (f64, f64), p2: (f64, f64)) {
        let primitive = PrimitiveConfig::sine_wave(p1, p2);
        let chart = self.take_inner().primitive(primitive);
        self.put_inner(chart);
    }

    // =========================================================================
    // Projections (6 primitives)
    // =========================================================================

    /// Long position
    fn long_position(&mut self, entry: (f64, f64), tp: (f64, f64), sl: (f64, f64)) {
        let primitive = PrimitiveConfig::long_position(entry, tp, sl);
        let chart = self.take_inner().primitive(primitive);
        self.put_inner(chart);
    }

    /// Short position
    fn short_position(&mut self, entry: (f64, f64), tp: (f64, f64), sl: (f64, f64)) {
        let primitive = PrimitiveConfig::short_position(entry, tp, sl);
        let chart = self.take_inner().primitive(primitive);
        self.put_inner(chart);
    }

    /// Forecast
    fn forecast(&mut self, p1: (f64, f64), p2: (f64, f64)) {
        let primitive = PrimitiveConfig::forecast(p1, p2);
        let chart = self.take_inner().primitive(primitive);
        self.put_inner(chart);
    }

    /// Bars pattern
    fn bars_pattern(&mut self, p1: (f64, f64), p2: (f64, f64)) {
        let primitive = PrimitiveConfig::bars_pattern(p1, p2);
        let chart = self.take_inner().primitive(primitive);
        self.put_inner(chart);
    }

    /// Price projection
    fn price_projection(&mut self, p1: (f64, f64), p2: (f64, f64), p3: (f64, f64)) {
        let primitive = PrimitiveConfig::price_projection(p1, p2, p3);
        let chart = self.take_inner().primitive(primitive);
        self.put_inner(chart);
    }

    /// Projection
    fn projection(&mut self, p1: (f64, f64), p2: (f64, f64)) {
        let primitive = PrimitiveConfig::projection(p1, p2);
        let chart = self.take_inner().primitive(primitive);
        self.put_inner(chart);
    }

    // =========================================================================
    // Volume Tools (3 primitives)
    // =========================================================================

    /// Anchored VWAP
    fn anchored_vwap(&mut self, position: (f64, f64)) {
        let primitive = PrimitiveConfig::anchored_vwap(position);
        let chart = self.take_inner().primitive(primitive);
        self.put_inner(chart);
    }

    /// Fixed volume profile
    fn fixed_volume_profile(&mut self, p1: (f64, f64), p2: (f64, f64)) {
        let primitive = PrimitiveConfig::fixed_volume_profile(p1, p2);
        let chart = self.take_inner().primitive(primitive);
        self.put_inner(chart);
    }

    /// Anchored volume profile
    fn anchored_volume_profile(&mut self, p1: (f64, f64), p2: (f64, f64)) {
        let primitive = PrimitiveConfig::anchored_volume_profile(p1, p2);
        let chart = self.take_inner().primitive(primitive);
        self.put_inner(chart);
    }

    // =========================================================================
    // Measurement (3 primitives)
    // =========================================================================

    /// Price range
    fn price_range(&mut self, p1: (f64, f64), p2: (f64, f64)) {
        let primitive = PrimitiveConfig::price_range(p1, p2);
        let chart = self.take_inner().primitive(primitive);
        self.put_inner(chart);
    }

    /// Date range
    fn date_range(&mut self, p1: (f64, f64), p2: (f64, f64)) {
        let primitive = PrimitiveConfig::date_range(p1, p2);
        let chart = self.take_inner().primitive(primitive);
        self.put_inner(chart);
    }

    /// Price and date range
    fn price_date_range(&mut self, p1: (f64, f64), p2: (f64, f64)) {
        let primitive = PrimitiveConfig::price_date_range(p1, p2);
        let chart = self.take_inner().primitive(primitive);
        self.put_inner(chart);
    }

    // =========================================================================
    // Brushes (2 primitives)
    // =========================================================================

    /// Brush
    fn brush(&mut self, points: Vec<(f64, f64)>) {
        let primitive = PrimitiveConfig::brush(points);
        let chart = self.take_inner().primitive(primitive);
        self.put_inner(chart);
    }

    /// Highlighter
    fn highlighter(&mut self, points: Vec<(f64, f64)>) {
        let primitive = PrimitiveConfig::highlighter(points);
        let chart = self.take_inner().primitive(primitive);
        self.put_inner(chart);
    }

    // =========================================================================
    // Rendering
    // =========================================================================

    /// Render chart to SVG string
    fn render_svg(&self) -> String {
        self.inner
            .as_ref()
            .map(|c| c.render_svg())
            .unwrap_or_default()
    }
}

// =============================================================================
// Viewport, Theme, ChartConfig
// =============================================================================

#[pyclass(name = "Viewport")]
pub struct PyViewport {
    inner: Viewport,
}

#[pymethods]
impl PyViewport {
    #[new]
    fn new(width: f64, height: f64) -> Self {
        Self {
            inner: Viewport::new(width, height),
        }
    }
    #[getter]
    fn chart_width(&self) -> f64 {
        self.inner.chart_width()
    }
    #[getter]
    fn chart_height(&self) -> f64 {
        self.inner.chart_height
    }
    #[getter]
    fn bar_width(&self) -> f64 {
        self.inner.bar_width()
    }
    fn set_size(&mut self, width: f64, height: f64) {
        self.inner.set_size(width, height);
    }
    fn set_bar_count(&mut self, count: usize) {
        self.inner.set_bar_count(count);
    }
    fn scroll_to_end(&mut self) {
        self.inner.scroll_to_end();
    }
    fn scroll_to_start(&mut self) {
        self.inner.scroll_to_start();
    }
}

/// Legacy simple theme (for backwards compatibility)
#[pyclass(name = "Theme")]
pub struct PyTheme {
    inner: Theme,
}

#[pymethods]
impl PyTheme {
    #[staticmethod]
    fn dark() -> Self {
        Self {
            inner: Theme::dark(),
        }
    }
    #[staticmethod]
    fn light() -> Self {
        Self {
            inner: Theme::light(),
        }
    }
    #[getter]
    fn bg_color(&self) -> &str {
        self.inner.bg_color
    }
    #[getter]
    fn text_color(&self) -> &str {
        self.inner.text_color
    }
    #[getter]
    fn grid_color(&self) -> &str {
        self.inner.grid_color
    }
    #[getter]
    fn candle_up(&self) -> &str {
        self.inner.candle_up
    }
    #[getter]
    fn candle_down(&self) -> &str {
        self.inner.candle_down
    }
}

// =============================================================================
// UITheme - Full static theme system
// =============================================================================

/// Complete UI theme with all styling options (static, compile-time).
/// Use RuntimeTheme for modifiable themes.
#[pyclass(name = "UITheme")]
pub struct PyUITheme {
    inner: UITheme,
}

#[pymethods]
impl PyUITheme {
    /// Create dark theme (TradingView-like)
    #[staticmethod]
    fn dark() -> Self {
        Self {
            inner: UITheme::dark(),
        }
    }

    /// Create light theme
    #[staticmethod]
    fn light() -> Self {
        Self {
            inner: UITheme::light(),
        }
    }

    /// Create high contrast theme (accessibility)
    #[staticmethod]
    fn high_contrast() -> Self {
        Self {
            inner: UITheme::high_contrast(),
        }
    }

    /// Create cyberpunk/neon theme
    #[staticmethod]
    fn cyberpunk() -> Self {
        Self {
            inner: UITheme::cyberpunk(),
        }
    }

    // === Basic properties ===

    #[getter]
    fn name(&self) -> &str {
        self.inner.name
    }

    // === Chart colors ===

    #[getter]
    fn background(&self) -> &str {
        self.inner.chart.background
    }

    #[getter]
    fn grid_line(&self) -> &str {
        self.inner.chart.grid_line
    }

    #[getter]
    fn scale_bg(&self) -> &str {
        self.inner.chart.scale_bg
    }

    #[getter]
    fn scale_text(&self) -> &str {
        self.inner.chart.scale_text
    }

    #[getter]
    fn crosshair_line(&self) -> &str {
        self.inner.chart.crosshair_line
    }

    // === Series colors ===

    #[getter]
    fn candle_up_body(&self) -> &str {
        self.inner.series.candle_up_body
    }

    #[getter]
    fn candle_down_body(&self) -> &str {
        self.inner.series.candle_down_body
    }

    #[getter]
    fn line_color(&self) -> &str {
        self.inner.series.line_color
    }

    #[getter]
    fn ma_fast(&self) -> &str {
        self.inner.series.ma_fast
    }

    #[getter]
    fn ma_slow(&self) -> &str {
        self.inner.series.ma_slow
    }

    // === UI colors ===

    #[getter]
    fn toolbar_bg(&self) -> &str {
        self.inner.colors.toolbar_bg
    }

    #[getter]
    fn text_primary(&self) -> &str {
        self.inner.colors.text_primary
    }

    #[getter]
    fn accent(&self) -> &str {
        self.inner.colors.accent
    }

    #[getter]
    fn success(&self) -> &str {
        self.inner.colors.success
    }

    #[getter]
    fn danger(&self) -> &str {
        self.inner.colors.danger
    }
}

// =============================================================================
// RuntimeTheme - Modifiable theme with JSON support
// =============================================================================

/// Runtime-modifiable theme with JSON serialization support.
/// All colors are owned strings that can be modified.
#[pyclass(name = "RuntimeTheme")]
pub struct PyRuntimeTheme {
    inner: RuntimeTheme,
}

#[pymethods]
impl PyRuntimeTheme {
    /// Create from preset name: "dark", "light", "high_contrast", "cyberpunk"
    #[staticmethod]
    fn from_preset(name: &str) -> Self {
        Self {
            inner: RuntimeTheme::from_preset(name),
        }
    }

    /// Create dark theme
    #[staticmethod]
    fn dark() -> Self {
        Self {
            inner: RuntimeTheme::dark(),
        }
    }

    /// Create light theme
    #[staticmethod]
    fn light() -> Self {
        Self {
            inner: RuntimeTheme::light(),
        }
    }

    /// Create high contrast theme
    #[staticmethod]
    fn high_contrast() -> Self {
        Self {
            inner: RuntimeTheme::high_contrast(),
        }
    }

    /// Create cyberpunk theme
    #[staticmethod]
    fn cyberpunk() -> Self {
        Self {
            inner: RuntimeTheme::cyberpunk(),
        }
    }

    /// Deserialize from JSON string
    #[staticmethod]
    fn from_json(json: &str) -> Option<Self> {
        RuntimeTheme::from_json(json).map(|inner| Self { inner })
    }

    /// Serialize to JSON string
    fn to_json(&self) -> String {
        self.inner.to_json()
    }

    /// Serialize to pretty JSON string
    fn to_json_pretty(&self) -> String {
        self.inner.to_json_pretty()
    }

    /// Get available preset names
    #[staticmethod]
    fn presets() -> Vec<&'static str> {
        RuntimeTheme::PRESETS.to_vec()
    }

    // === Basic properties ===

    #[getter]
    fn name(&self) -> &str {
        &self.inner.name
    }

    #[setter]
    fn set_name(&mut self, name: String) {
        self.inner.name = name;
    }

    // === Chart colors (getters and setters) ===

    #[getter]
    fn background(&self) -> &str {
        &self.inner.chart.background
    }

    #[setter]
    fn set_background(&mut self, color: String) {
        self.inner.chart.background = color;
    }

    #[getter]
    fn grid_line(&self) -> &str {
        &self.inner.chart.grid_line
    }

    #[setter]
    fn set_grid_line(&mut self, color: String) {
        self.inner.chart.grid_line = color;
    }

    #[getter]
    fn scale_bg(&self) -> &str {
        &self.inner.chart.scale_bg
    }

    #[setter]
    fn set_scale_bg(&mut self, color: String) {
        self.inner.chart.scale_bg = color;
    }

    #[getter]
    fn scale_text(&self) -> &str {
        &self.inner.chart.scale_text
    }

    #[setter]
    fn set_scale_text(&mut self, color: String) {
        self.inner.chart.scale_text = color;
    }

    #[getter]
    fn crosshair_line(&self) -> &str {
        &self.inner.chart.crosshair_line
    }

    #[setter]
    fn set_crosshair_line(&mut self, color: String) {
        self.inner.chart.crosshair_line = color;
    }

    // === Series colors ===

    #[getter]
    fn candle_up_body(&self) -> &str {
        &self.inner.series.candle_up_body
    }

    #[setter]
    fn set_candle_up_body(&mut self, color: String) {
        self.inner.series.candle_up_body = color;
    }

    #[getter]
    fn candle_down_body(&self) -> &str {
        &self.inner.series.candle_down_body
    }

    #[setter]
    fn set_candle_down_body(&mut self, color: String) {
        self.inner.series.candle_down_body = color;
    }

    #[getter]
    fn line_color(&self) -> &str {
        &self.inner.series.line_color
    }

    #[setter]
    fn set_line_color(&mut self, color: String) {
        self.inner.series.line_color = color;
    }

    #[getter]
    fn ma_fast(&self) -> &str {
        &self.inner.series.ma_fast
    }

    #[setter]
    fn set_ma_fast(&mut self, color: String) {
        self.inner.series.ma_fast = color;
    }

    #[getter]
    fn ma_slow(&self) -> &str {
        &self.inner.series.ma_slow
    }

    #[setter]
    fn set_ma_slow(&mut self, color: String) {
        self.inner.series.ma_slow = color;
    }

    // === UI colors ===

    #[getter]
    fn toolbar_bg(&self) -> &str {
        &self.inner.colors.toolbar_bg
    }

    #[setter]
    fn set_toolbar_bg(&mut self, color: String) {
        self.inner.colors.toolbar_bg = color;
    }

    #[getter]
    fn text_primary(&self) -> &str {
        &self.inner.colors.text_primary
    }

    #[setter]
    fn set_text_primary(&mut self, color: String) {
        self.inner.colors.text_primary = color;
    }

    #[getter]
    fn accent(&self) -> &str {
        &self.inner.colors.accent
    }

    #[setter]
    fn set_accent(&mut self, color: String) {
        self.inner.colors.accent = color;
    }

    #[getter]
    fn success(&self) -> &str {
        &self.inner.colors.success
    }

    #[setter]
    fn set_success(&mut self, color: String) {
        self.inner.colors.success = color;
    }

    #[getter]
    fn danger(&self) -> &str {
        &self.inner.colors.danger
    }

    #[setter]
    fn set_danger(&mut self, color: String) {
        self.inner.colors.danger = color;
    }
}

#[pyclass(name = "ChartConfig")]
pub struct PyChartConfig {
    #[allow(dead_code)]
    inner: RustChartConfig,
}

#[pymethods]
impl PyChartConfig {
    #[new]
    fn new() -> Self {
        Self {
            inner: RustChartConfig::default(),
        }
    }
}

// =============================================================================
// Module
// =============================================================================

#[pyfunction]
fn version() -> &'static str {
    env!("CARGO_PKG_VERSION")
}

#[pymodule]
fn zengeld_canvas(m: &Bound<'_, PyModule>) -> PyResult<()> {
    m.add_function(wrap_pyfunction!(version, m)?)?;
    m.add_class::<PyBar>()?;
    m.add_class::<PyChart>()?;
    m.add_class::<PyViewport>()?;
    // Theme classes
    m.add_class::<PyTheme>()?; // Legacy simple theme
    m.add_class::<PyUITheme>()?; // Full static theme
    m.add_class::<PyRuntimeTheme>()?; // Modifiable theme with JSON
    m.add_class::<PyChartConfig>()?;
    Ok(())
}
