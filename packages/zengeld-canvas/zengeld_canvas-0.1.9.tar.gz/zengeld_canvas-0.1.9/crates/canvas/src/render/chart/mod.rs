//! Chart Element Rendering
//!
//! High-level rendering functions for chart elements.
//! This is the "what we draw" layer - uses engine primitives to render
//! series, overlays, and annotations.
//!
//! # Modules
//!
//! - `series` - Series rendering (all 12 chart types)
//! - `overlays` - Overlay rendering (grid, legend, watermark)
//! - `annotations` - Annotation rendering (markers, price lines)
//! - `indicators` - Indicator and signal rendering

pub mod annotations;
pub mod indicators;
pub mod overlays;
pub mod series;

// Re-exports - Series rendering (12 types)
pub use series::{
    render_area,
    render_bars,
    render_baseline,
    // OHLC series
    render_candlesticks,
    render_columns,
    render_heikin_ashi,
    render_histogram,
    render_hlc_area,
    render_hollow_candles,
    // Value series
    render_line,
    render_line_with_markers,
    render_step_line,
};

// Re-exports - Overlay rendering
pub use overlays::{render_grid, render_legend, render_watermark};

// Re-exports - Annotation rendering
pub use annotations::{render_markers, render_price_lines};

// Re-exports - Indicator and signal rendering
pub use indicators::{render_indicator, render_signals, render_strategy};
