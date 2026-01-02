//! # zen-canvas High-Level API
//!
//! Provides two complementary approaches for chart rendering:
//!
//! ## 1. Builder Pattern (Simple)
//!
//! For quick, simple charts with method chaining:
//!
//! ```rust,ignore
//! use zengeld_canvas::api::Chart;
//!
//! let svg = Chart::new(800, 600)
//!     .bars(&bars)
//!     .candlesticks()
//!     .sma(20, "#2196F3")
//!     .rsi(14)
//!     .render_svg();
//! ```
//!
//! ## 2. Configuration Pattern (Full Control)
//!
//! For complex charts with declarative configuration:
//!
//! ```rust,ignore
//! use zengeld_canvas::api::{ChartConfig, SeriesConfig};
//! use zengeld_canvas::model::Indicator;
//!
//! let config = ChartConfig {
//!     width: 1200,
//!     height: 800,
//!     series: SeriesConfig::candlestick(),
//!     indicators: vec![
//!         // Overlays (on main chart)
//!         Indicator::sma("sma_20", 20, "#2196F3"),
//!         Indicator::bollinger("bb_20", 20),
//!         // Subpanes (separate panels)
//!         Indicator::rsi("rsi_14", 14),
//!         Indicator::macd("macd", 12, 26, 9),
//!     ],
//!     primitives: vec![
//!         PrimitiveConfig::trend_line((10.0, 100.0), (50.0, 120.0)),
//!         PrimitiveConfig::fib_retracement((20.0, 90.0), (40.0, 130.0)),
//!     ],
//!     signals: vec![
//!         SignalConfig::buy(25, 105.0),
//!         SignalConfig::sell(45, 125.0),
//!     ],
//!     ..Default::default()
//! };
//!
//! let svg = ChartRenderer::new(&config, &bars).render_svg();
//! ```
//!
//! ## Coverage
//!
//! The configuration API covers 100% of library functionality:
//! - **12 Series Types**: Candlestick, HollowCandlestick, HeikinAshi, Bar, HlcArea,
//!   Line, StepLine, LineWithMarkers, Area, Baseline, Histogram, Columns
//! - **50+ Indicators**: All momentum, volume, volatility, trend indicators
//!   (each with VectorStyle for proper rendering: Line, Histogram, Area, Dots, etc.)
//! - **96 Primitives**: Lines, Fibonacci, Gann, Pitchforks, Patterns, Elliott, etc.
//! - **7 Signal Types**: Buy, Sell, Entry, Exit, TakeProfit, StopLoss, Custom
//! - **Multichart Layouts**: Grid 2x2, 3x3, 1+3, vertical/horizontal stacks

mod chart;
mod config;

// Simple builder API
pub use chart::{Chart, ChartRenderer, MultichartRenderer};

// Full configuration API
pub use config::{
    ChartConfig, ExtendMode, LayoutConfig, LayoutType, LevelConfig, LineStyleType, PrimitiveConfig,
    SeriesConfig, SeriesStyleConfig, SignalConfig, ThemeConfig,
};

// Re-export Indicator types from model
pub use crate::model::{
    Indicator, IndicatorLevel, IndicatorPlacement, IndicatorRange, IndicatorVector, VectorStyle,
};
