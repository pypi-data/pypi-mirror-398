//! Data Models
//!
//! Data structures and configuration types for chart elements.
//! These are pure data - no rendering logic.
//!
//! # Modules
//!
//! - `series` - Series data and styling options (Candlestick, Line, Area, etc.)
//! - `overlays` - Overlay configurations (Grid, Legend, Watermark)
//! - `annotations` - Data-point annotations (Markers, Price Lines)

pub mod annotations;
pub mod indicators;
pub mod overlays;
pub mod series;

// =============================================================================
// Series re-exports
// =============================================================================
pub use series::{
    // Data types
    AreaData,
    // Options
    AreaSeriesOptions,
    AreaStyleOptions,
    BarData,
    BarSeriesOptions,
    BarStyleOptions,
    BaselineData,
    BaselineSeriesOptions,
    BaselineStyleOptions,
    CandlestickData,
    CandlestickSeriesOptions,
    CandlestickStyleOptions,
    HistogramData,
    HistogramSeriesOptions,
    HistogramStyleOptions,
    LineData,
    LineSeriesOptions,
    // Enums
    LineStyle,
    LineStyleOptions,
    LineType,
    PriceLineSource,
    SeriesData,
    SeriesOptions,
    SeriesOptionsCommon,
    SeriesType,
    SingleValue,
};

// =============================================================================
// Overlays re-exports
// =============================================================================
pub use overlays::{
    COMPARE_COLORS,
    // Compare
    CompareOverlay,
    CompareSeries,
    // Watermark
    FontStyle,
    // Grid
    GridLineOptions,
    GridOptions,
    HorzAlign,
    // Legend
    Legend,
    LegendData,
    LegendPosition,
    VertAlign,
    Watermark,
    WatermarkLine,
    get_compare_color,
};

// =============================================================================
// Annotations re-exports
// =============================================================================
pub use annotations::{
    LineStyle as AnnotationLineStyle, Marker, MarkerCoordinates, MarkerManager, MarkerPosition,
    MarkerShape, PriceLine, PriceLineOptions,
};

// =============================================================================
// Indicators re-exports
// =============================================================================
pub use indicators::{
    ArrowDirection,
    // Core types
    Indicator,
    IndicatorLevel,
    IndicatorPlacement,
    IndicatorRange,
    // Legacy aliases
    IndicatorSeries,
    IndicatorStyle,
    // Vector/style
    IndicatorVector,
    // Signals
    Signal,
    SignalVisual,
    // Strategies
    Strategy,
    StrategyPrimitive,
    StrategyTheme,
    VectorStyle,
};
