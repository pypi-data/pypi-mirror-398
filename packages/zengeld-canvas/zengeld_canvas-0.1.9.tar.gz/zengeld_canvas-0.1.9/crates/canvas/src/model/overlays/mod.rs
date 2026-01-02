//! Overlays - Visual elements drawn on top of the chart
//!
//! This module contains overlay components:
//! - Grid lines
//! - Legend for OHLC display
//! - Watermark for branding
//! - Compare for symbol comparison overlays

pub mod compare;
pub mod grid;
pub mod legend;
pub mod watermark;

// Re-exports
pub use compare::{COMPARE_COLORS, CompareOverlay, CompareSeries, get_compare_color};
pub use grid::{GridLineOptions, GridOptions};
pub use legend::{Legend, LegendData, LegendPosition};
pub use watermark::{FontStyle, HorzAlign, VertAlign, Watermark, WatermarkLine};
