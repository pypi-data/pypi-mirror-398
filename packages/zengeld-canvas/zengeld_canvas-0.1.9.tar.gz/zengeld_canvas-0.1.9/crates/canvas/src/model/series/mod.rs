//! Series types and options
//!
//! This module implements various series types for chart visualization:
//!
//! ## OHLC Series (require Bar data)
//! - Candlestick: Classic OHLC candles with body and wicks
//! - HollowCandlestick: Bullish candles are hollow, bearish are filled
//! - HeikinAshi: Smoothed candlesticks using averaged values
//! - Bar: OHLC bars with horizontal ticks
//! - HlcArea: High-Low-Close with filled area
//!
//! ## Value Series (require single value per point)
//! - Line: Simple, stepped, or curved lines
//! - StepLine: Staircase/step chart
//! - LineWithMarkers: Line with dot markers at each point
//! - Area: Gradient-filled area charts
//! - Baseline: Split fill above/below a baseline
//! - Histogram: Vertical bars from a base value
//! - Columns: Vertical bars (alias for histogram with different styling)

pub mod data;
pub mod enums;
pub mod options;

// Re-export main types
pub use data::{
    AreaData, BarData, BaselineData, CandlestickData, HistogramData, LineData, SeriesData,
    SingleValue,
};
pub use enums::{LineStyle, LineType, PriceLineSource};
pub use options::{
    AreaSeriesOptions, AreaStyleOptions, BarSeriesOptions, BarStyleOptions, BaselineSeriesOptions,
    BaselineStyleOptions, CandlestickSeriesOptions, CandlestickStyleOptions,
    HistogramSeriesOptions, HistogramStyleOptions, LineSeriesOptions, LineStyleOptions,
    SeriesOptions, SeriesOptionsCommon,
};

/// Series type enum - all 12 chart visualization types
#[derive(Clone, Copy, Debug, PartialEq, Eq, Default, serde::Serialize, serde::Deserialize)]
#[serde(rename_all = "snake_case")]
pub enum SeriesType {
    // === OHLC Series (require Bar data) ===
    /// Candlestick chart (OHLC with body and wicks)
    #[default]
    Candlestick,
    /// Hollow candlesticks (bullish=outline, bearish=filled)
    HollowCandlestick,
    /// Heikin Ashi smoothed candlesticks
    HeikinAshi,
    /// Bar chart (OHLC vertical line with ticks)
    Bar,
    /// HLC Area (high-low-close with filled area)
    HlcArea,

    // === Value Series (single value per point) ===
    /// Line chart (connects points)
    Line,
    /// Step line (staircase chart)
    StepLine,
    /// Line with dot markers at each point
    LineWithMarkers,
    /// Area chart with gradient fill
    Area,
    /// Baseline chart with split fill above/below
    Baseline,
    /// Histogram (vertical bars from baseline)
    Histogram,
    /// Columns (vertical bars, similar to histogram)
    Columns,
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_series_type_enum() {
        assert_eq!(SeriesType::Line, SeriesType::Line);
        assert_ne!(SeriesType::Line, SeriesType::Area);
    }

    #[test]
    fn test_single_value() {
        let val = SingleValue::new(1699920000, 100.0);
        assert_eq!(val.timestamp, 1699920000);
        assert_eq!(val.value, 100.0);
    }

    #[test]
    fn test_line_data_creation() {
        let data = LineData {
            point: SingleValue::new(0, 50.0),
            color: None,
        };
        assert_eq!(data.point.value, 50.0);
    }

    #[test]
    fn test_line_style_options() {
        let opts = LineStyleOptions::default();
        assert_eq!(opts.line_type, LineType::Simple);
        assert_eq!(opts.line_style, LineStyle::Solid);
    }
}
