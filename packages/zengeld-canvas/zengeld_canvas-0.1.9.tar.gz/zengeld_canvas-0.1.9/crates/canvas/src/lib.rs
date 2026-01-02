//! zen-canvas: Platform-agnostic financial chart rendering engine
//!
//! This crate provides the core rendering primitives for financial charts,
//! designed to work across multiple platforms (native, WASM, Python, etc.).
//!
//! # Architecture
//!
//! ```text
//! ┌─────────────────────────────────────────────────────────────────────┐
//! │  zen-canvas                                                          │
//! ├─────────────────────────────────────────────────────────────────────┤
//! │                                                                      │
//! │  core/          coords/          model/           primitives/        │
//! │  ──────         ──────           ─────            ───────────        │
//! │  Bar            Viewport         series/          TrendLine          │
//! │  Theme          PriceScale       overlays/        Fibonacci          │
//! │  constants      TimeScale        annotations/     Gann, Patterns     │
//! │                                                   Elliott, Channels  │
//! │                                                   70+ tools          │
//! │                                                                      │
//! │  layout/                         render/                             │
//! │  ───────                         ───────────────────────────         │
//! │  Pane, SubPane                   engine/ (types, commands, batch)    │
//! │  PaneManager                     chart/ (series, overlays, etc.)     │
//! │  MultichartLayout                                                    │
//! │                                                                      │
//! └─────────────────────────────────────────────────────────────────────┘
//! ```
//!
//! # Modules
//!
//! - **core** - Foundational types (Bar, Theme) and utilities (color parsing, math)
//! - **coords** - Coordinate systems (Viewport, PriceScale, TimeScale)
//! - **model** - Data models and configurations (series, overlays, annotations)
//! - **primitives** - Interactive drawing tools (70+ primitives)
//! - **layout** - Chart layout (panes, multichart grids)
//! - **render** - Rendering engine and chart element rendering
//!
//! # License
//!
//! Licensed under either of Apache License, Version 2.0 or MIT license at your option.

// =============================================================================
// Module Declarations
// =============================================================================

/// Core types and utilities
pub mod core;

/// Coordinate systems
pub mod coords;

/// Data models
pub mod model;

/// Interactive primitives (drawing tools)
pub mod primitives;

/// Layout system (panes, multichart)
pub mod layout;

/// Rendering engine
pub mod render;

/// High-level API for chart rendering
pub mod api;

// =============================================================================
// Re-exports for convenient access
// =============================================================================

// Core types and utilities
pub use core::{
    BOTTOM_SIDEBAR_HEIGHT,
    BOTTOM_TOOLBAR_HEIGHT,
    Bar,
    // Sidebar & toolbar constants
    LEFT_SIDEBAR_WIDTH,
    LEFT_TOOLBAR_WIDTH,
    // Price scale constants
    PRICE_SCALE_BORDER_SIZE,
    PRICE_SCALE_FONT,
    PRICE_SCALE_FONT_SIZE,
    PRICE_SCALE_FONT_SIZE_MAX,
    PRICE_SCALE_FONT_SIZE_MIN,
    PRICE_SCALE_LABEL_OFFSET,
    PRICE_SCALE_MIN_WIDTH,
    PRICE_SCALE_PADDING_INNER,
    PRICE_SCALE_PADDING_OUTER,
    PRICE_SCALE_TICK_LENGTH,
    PRICE_SCALE_WIDTH,
    RIGHT_SIDEBAR_WIDTH,
    RIGHT_TOOLBAR_WIDTH,
    STATUS_BAR_HEIGHT,
    TIME_SCALE_FONT_SIZE,
    TIME_SCALE_HEIGHT,
    TOP_TOOLBAR_HEIGHT,
    Theme,
    catmull_rom_spline,
    crisp,
    crisp_rect,
    format_indicator_value,
    parse_css_color,
};

// Configuration system
pub use core::{
    AreaConfig, CandlestickConfig, ChartConfig, ConfigColor, CrosshairConfig, FontConfig,
    FontWeight, GridConfig, HistogramConfig, LegendConfig, LineConfig, LineStyleType,
    PriceScaleConfig, PrimitiveConfig, TimeScaleConfig, WatermarkConfig,
};

// Full theme system
pub use core::{
    // Static theme (compile-time, &'static str)
    ChartColors,
    // Runtime theme (modifiable, owned String, JSON support)
    RuntimeChartColors,
    RuntimeEffects,
    RuntimeFonts,
    RuntimeSeriesColors,
    RuntimeSizing,
    RuntimeTheme,
    RuntimeUIColors,
    SeriesColors,
    UIColors,
    UIEffects,
    UIFonts,
    UISizing,
    UITheme,
};

// Coordinate systems
pub use coords::{
    DAY, HOUR, MINUTE, NICE_MULTIPLIERS, PriceScale, PriceScaleMode, TickMarkWeight, TimeScale,
    TimeTick, Viewport, format_price, format_time_by_weight, format_time_full, lwc_nice_number,
    nice_number, nice_price_step, price_precision,
};

// Model - Series
pub use model::{
    AreaData, AreaSeriesOptions, AreaStyleOptions, BarData, BarSeriesOptions, BarStyleOptions,
    BaselineData, BaselineSeriesOptions, BaselineStyleOptions, CandlestickData,
    CandlestickSeriesOptions, CandlestickStyleOptions, HistogramData, HistogramSeriesOptions,
    HistogramStyleOptions, LineData, LineSeriesOptions, LineStyleOptions, LineType,
    PriceLineSource, SeriesData, SeriesOptions, SeriesOptionsCommon, SeriesType, SingleValue,
};

// Model - Overlays
pub use model::{
    COMPARE_COLORS,
    // Compare overlay
    CompareOverlay,
    CompareSeries,
    FontStyle,
    GridLineOptions,
    GridOptions,
    HorzAlign,
    Legend,
    LegendData,
    LegendPosition,
    VertAlign,
    Watermark,
    WatermarkLine,
    get_compare_color,
};

// Model - Annotations
pub use model::{
    LineStyle, Marker, MarkerCoordinates, MarkerManager, MarkerPosition, MarkerShape, PriceLine,
    PriceLineOptions,
};

// Layout - Panes
pub use layout::{MAIN_PANE, Pane, PaneGeometry, PaneId, PaneManager, SubPane};

// Layout - Multichart
pub use layout::{CellBounds, CellId, LayoutCell, MultichartLayout};

// Primitives (Drawing System)
pub use primitives::{
    // Control points (data types only, not UI)
    ControlPoint,
    ControlPointType,
    // Icons
    EmojiType,
    ExtendMode,
    LineStyle as DrawingLineStyle,
    // Styling
    PrimitiveColor,
    PrimitiveData,
    PrimitiveFactory,
    PrimitiveKind,
    PrimitiveMetadata,
    PrimitiveRegistry,
    PrimitiveText,
    // Primitive trait and registry
    PrimitiveTrait,
    // Rendering
    RenderContext,
    RenderOp,
    RenderOps,
    SignalManager,
    SignalType,
    StrategySignalConfig,
    // System signals
    SystemSignal,
    TextAlign,
    TextAnchor,
    TextBaseline,
    // Trade visualization
    Trade,
    TradeDirection,
    TradeManager,
    execute_ops,
    // Point label generation
    get_point_labels,
    // Geometry helpers
    point_to_line_distance,
    render_crisp,
    render_crisp_rect,
    render_primitive_text,
    render_primitive_text_rotated,
    render_text_with_background,
};

// =============================================================================
// Tests
// =============================================================================

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_overlays_integration() {
        let watermark = Watermark::simple("Test");
        assert!(watermark.visible);

        let legend = Legend::default();
        assert!(legend.visible);

        let grid = GridOptions::default();
        assert!(grid.vert_lines.visible);
    }

    #[test]
    fn test_viewport_basics() {
        let viewport = Viewport::default();
        assert!(viewport.chart_width() > 0.0);
        assert!(viewport.chart_height > 0.0);
    }

    #[test]
    fn test_multichart_layouts() {
        let layout = MultichartLayout::quad();
        assert_eq!(layout.chart_count(), 4);

        let presets = MultichartLayout::presets();
        assert!(presets.len() >= 10);
    }

    #[test]
    fn test_pane_manager() {
        let manager = PaneManager::new();
        assert_eq!(manager.pane_count(), 1);
        assert!(!manager.has_sub_panes());
    }
}
