//! Chart - High-level API for rendering charts from ChartConfig
//!
//! Provides two approaches:
//! 1. `ChartRenderer` - takes ChartConfig and renders to SVG
//! 2. `Chart` - builder pattern that creates ChartConfig internally

use super::config::{ChartConfig, PrimitiveConfig, SeriesConfig, SignalConfig, ThemeConfig};
use crate::coords::{PriceScale, TickMarkWeight, format_time_by_weight};
use crate::core::{Bar, PRICE_SCALE_WIDTH, TIME_SCALE_HEIGHT};
use crate::model::{
    CandlestickData, CandlestickStyleOptions, Indicator, LineData, LineStyleOptions, SeriesType,
    SingleValue, VectorStyle,
};
use crate::primitives::{EllipseParams, PrimitiveRegistry, RenderContext};
use crate::render::chart::{render_candlesticks, render_line};
use crate::render::engine::{
    Color, FillStyle, FontWeight, LineStyle, Path, Point, Rect, RenderBackend, RenderBatch,
    SvgBackend, TextAlign, TextBaseline, TextStyle,
};

/// Parameters for rendering a subpane indicator
struct SubpaneRenderParams<'a> {
    /// The indicator to render
    indicator: &'a Indicator,
    /// Y offset from the top of the chart
    y_offset: f64,
    /// Height of the subpane
    height: f64,
    /// Width of the subpane in pixels
    width: u32,
    /// Index of this pane (for primitive filtering)
    pane_idx: usize,
}

// =============================================================================
// ChartRenderer - Renders ChartConfig to SVG
// =============================================================================

/// Renderer that takes a ChartConfig and produces SVG output
pub struct ChartRenderer<'a> {
    config: &'a ChartConfig,
    bars: &'a [Bar],
}

impl<'a> ChartRenderer<'a> {
    /// Create a new renderer with config and bar data
    pub fn new(config: &'a ChartConfig, bars: &'a [Bar]) -> Self {
        Self { config, bars }
    }

    /// Render the chart to SVG string
    pub fn render_svg(&self) -> String {
        if self.bars.is_empty() {
            return self.empty_svg();
        }

        let width = self.config.width;
        let height = self.config.height;
        let dpr = self.config.dpr;

        // Reserve space for scales
        let price_scale_width = PRICE_SCALE_WIDTH;
        let time_scale_height = TIME_SCALE_HEIGHT;
        let chart_width = width as f64 - price_scale_width;
        let chart_height = height as f64 - time_scale_height;

        // Separate indicators into overlays, overlay_bottom, and subpanes
        let overlays: Vec<&Indicator> = self
            .config
            .indicators
            .iter()
            .filter(|ind| ind.placement.is_overlay())
            .collect();
        let overlay_bottoms: Vec<&Indicator> = self
            .config
            .indicators
            .iter()
            .filter(|ind| ind.placement.is_overlay_bottom())
            .collect();
        let subpanes: Vec<&Indicator> = self
            .config
            .indicators
            .iter()
            .filter(|ind| ind.placement.is_subpane())
            .collect();

        // Calculate layout - subpanes share height with main chart
        let total_subpane_ratio: f64 = subpanes.iter().map(|s| s.placement.height_ratio()).sum();
        let main_ratio = 1.0 - total_subpane_ratio;
        let main_height = chart_height * main_ratio;
        let gap = 4.0;

        // Create backend
        let mut backend = SvgBackend::new(width, height, dpr);
        backend.begin_frame(width as f64, height as f64, dpr);

        // Background
        let bg_color = &self.config.theme.background;
        let bg = Color::from_css(bg_color).unwrap_or(Color::rgb(19, 23, 34));
        backend.clear(bg);

        // Calculate coordinate system for main chart
        let (price_min, price_max) = self.price_range(&overlays);
        let price_padding = (price_max - price_min) * 0.05;
        let price_low = price_min - price_padding;
        let price_high = price_max + price_padding;

        let bar_count = self.bars.len();
        let bar_spacing = chart_width / bar_count as f64;
        let bar_width = (bar_spacing * 0.8).max(1.0);

        let bar_to_x = |i: usize| -> f64 { bar_spacing * (i as f64 + 0.5) };

        let price_to_y = |price: f64| -> f64 {
            let ratio = (price - price_low) / (price_high - price_low);
            main_height - ratio * main_height
        };

        // Grid (only on main chart, not on subpanes)
        if self.config.theme.show_grid {
            self.draw_grid(
                &mut backend,
                main_height,
                bar_spacing,
                chart_width as u32,
                main_height as u32,
            );
        }

        // Main series
        let mut batch = RenderBatch::new();
        self.render_main_series(&mut batch, &bar_to_x, &price_to_y, bar_width, dpr);
        self.execute_batch(&mut backend, &batch);

        // Overlay indicators (share price scale with main chart)
        self.render_overlay_indicators(&mut backend, &overlays, &bar_to_x, &price_to_y, dpr);

        // Overlay bottom indicators (own Y scale at bottom of main chart)
        self.render_overlay_bottom_indicators(
            &mut backend,
            &overlay_bottoms,
            &bar_to_x,
            main_height,
            chart_width,
            dpr,
        );

        // Primitives on main pane
        self.render_primitives(&mut backend, &bar_to_x, &price_to_y, dpr, None);

        // Signals
        self.render_signals(&mut backend, &bar_to_x, &price_to_y, dpr);

        // Price scale for main chart
        self.render_price_scale(
            &mut backend,
            chart_width,
            0.0,
            main_height,
            price_low,
            price_high,
        );

        // Subpane indicators with their own price scales
        let mut y_offset = main_height + gap;
        for (idx, indicator) in subpanes.iter().enumerate() {
            let pane_height = chart_height * indicator.placement.height_ratio() - gap;
            self.render_subpane_indicator(
                &mut backend,
                SubpaneRenderParams {
                    indicator,
                    y_offset,
                    height: pane_height,
                    width: chart_width as u32,
                    pane_idx: idx,
                },
                &bar_to_x,
            );

            // Price scale for this subpane
            let (sub_min, sub_max) = self.calculate_indicator_range(indicator);
            self.render_price_scale(
                &mut backend,
                chart_width,
                y_offset,
                pane_height,
                sub_min,
                sub_max,
            );

            y_offset += pane_height + gap;
        }

        // Time scale (at bottom, shared)
        self.render_time_scale(&mut backend, chart_width, chart_height, bar_spacing);

        backend.end_frame();
        backend.to_svg()
    }

    // =========================================================================
    // Private helpers
    // =========================================================================

    fn empty_svg(&self) -> String {
        format!(
            r##"<?xml version="1.0" encoding="UTF-8"?>
<svg xmlns="http://www.w3.org/2000/svg" width="{}" height="{}">
<rect width="100%" height="100%" fill="{}"/>
<text x="50%" y="50%" text-anchor="middle" fill="#787b86">No data</text>
</svg>"##,
            self.config.width, self.config.height, self.config.theme.background
        )
    }

    fn price_range(&self, overlays: &[&Indicator]) -> (f64, f64) {
        let mut min = f64::INFINITY;
        let mut max = f64::NEG_INFINITY;

        for bar in self.bars {
            if !bar.low.is_nan() {
                min = min.min(bar.low);
            }
            if !bar.high.is_nan() {
                max = max.max(bar.high);
            }
        }

        // Include overlay indicator values in range
        for indicator in overlays {
            for vector in &indicator.vectors {
                for &v in &vector.values {
                    if !v.is_nan() {
                        min = min.min(v);
                        max = max.max(v);
                    }
                }
            }
        }

        (min, max)
    }

    fn draw_grid(
        &self,
        backend: &mut SvgBackend,
        height: f64,
        bar_spacing: f64,
        width: u32,
        _chart_height: u32,
    ) {
        let grid_color =
            Color::from_css(&self.config.theme.grid_color).unwrap_or(Color::rgb(30, 34, 45));
        let style = LineStyle::solid(grid_color, 1.0);

        // Horizontal lines
        let h_count = 8;
        for i in 1..h_count {
            let y = height * i as f64 / h_count as f64;
            backend.line(Point::new(0.0, y), Point::new(width as f64, y), &style);
        }

        // Vertical lines
        let v_step = (self.bars.len() / 10).max(1);
        for i in (0..self.bars.len()).step_by(v_step) {
            let x = bar_spacing * (i as f64 + 0.5);
            backend.line(Point::new(x, 0.0), Point::new(x, height), &style);
        }
    }

    fn render_main_series(
        &self,
        batch: &mut RenderBatch,
        bar_to_x: &impl Fn(usize) -> f64,
        price_to_y: &impl Fn(f64) -> f64,
        bar_width: f64,
        dpr: f64,
    ) {
        let series = &self.config.series;
        let theme = &self.config.theme;

        match series.series_type {
            SeriesType::Candlestick | SeriesType::HollowCandlestick => {
                let data: Vec<CandlestickData> = self
                    .bars
                    .iter()
                    .map(|b| CandlestickData {
                        bar: *b,
                        color: None,
                        border_color: None,
                        wick_color: None,
                    })
                    .collect();

                let options = CandlestickStyleOptions {
                    up_color: theme.up_color.clone(),
                    down_color: theme.down_color.clone(),
                    wick_visible: true,
                    wick_color: String::new(),
                    wick_up_color: theme.up_color.clone(),
                    wick_down_color: theme.down_color.clone(),
                    border_visible: series.series_type == SeriesType::HollowCandlestick,
                    border_color: String::new(),
                    border_up_color: theme.up_color.clone(),
                    border_down_color: theme.down_color.clone(),
                };

                render_candlesticks(batch, &data, &options, bar_to_x, price_to_y, bar_width, dpr);
            }
            SeriesType::Line => {
                let data: Vec<LineData> = self
                    .bars
                    .iter()
                    .map(|b| LineData {
                        point: SingleValue {
                            timestamp: b.timestamp,
                            value: b.close,
                        },
                        color: None,
                    })
                    .collect();

                let options = LineStyleOptions {
                    color: series
                        .style
                        .color
                        .clone()
                        .unwrap_or_else(|| theme.up_color.clone()),
                    ..Default::default()
                };
                render_line(batch, &data, &options, bar_to_x, price_to_y, dpr);
            }
            SeriesType::Area => {
                // Render as line with fill (simplified)
                let data: Vec<LineData> = self
                    .bars
                    .iter()
                    .map(|b| LineData {
                        point: SingleValue {
                            timestamp: b.timestamp,
                            value: b.close,
                        },
                        color: None,
                    })
                    .collect();

                let options = LineStyleOptions {
                    color: series
                        .style
                        .color
                        .clone()
                        .unwrap_or_else(|| theme.up_color.clone()),
                    ..Default::default()
                };
                render_line(batch, &data, &options, bar_to_x, price_to_y, dpr);
            }
            _ => {
                // Default: candlesticks
                let data: Vec<CandlestickData> = self
                    .bars
                    .iter()
                    .map(|b| CandlestickData {
                        bar: *b,
                        color: None,
                        border_color: None,
                        wick_color: None,
                    })
                    .collect();

                let options = CandlestickStyleOptions {
                    up_color: theme.up_color.clone(),
                    down_color: theme.down_color.clone(),
                    wick_visible: true,
                    wick_color: String::new(),
                    wick_up_color: theme.up_color.clone(),
                    wick_down_color: theme.down_color.clone(),
                    border_visible: false,
                    border_color: String::new(),
                    border_up_color: theme.up_color.clone(),
                    border_down_color: theme.down_color.clone(),
                };

                render_candlesticks(batch, &data, &options, bar_to_x, price_to_y, bar_width, dpr);
            }
        }
    }

    /// Render overlay indicators (on main chart, share price Y scale)
    fn render_overlay_indicators(
        &self,
        backend: &mut SvgBackend,
        overlays: &[&Indicator],
        bar_to_x: &impl Fn(usize) -> f64,
        price_to_y: &impl Fn(f64) -> f64,
        _dpr: f64,
    ) {
        for indicator in overlays {
            for vector in &indicator.vectors {
                self.render_vector(backend, vector, bar_to_x, price_to_y, 0.0);
            }
        }
    }

    /// Render overlay_bottom indicators (at bottom of main chart with own Y scale)
    fn render_overlay_bottom_indicators(
        &self,
        backend: &mut SvgBackend,
        indicators: &[&Indicator],
        bar_to_x: &impl Fn(usize) -> f64,
        main_height: f64,
        _chart_width: f64,
        _dpr: f64,
    ) {
        for indicator in indicators {
            let height_ratio = indicator.placement.height_ratio();
            let indicator_height = main_height * height_ratio;
            let y_bottom = main_height;

            // For Volume-like indicators: if vector.values is empty, use bars data
            let has_data = indicator.vectors.iter().any(|v| !v.values.is_empty());

            if has_data {
                // Use indicator's own values
                let (range_min, range_max) = self.calculate_indicator_range(indicator);
                let value_to_y = |v: f64| -> f64 {
                    if range_max <= range_min {
                        return y_bottom;
                    }
                    let ratio = (v - range_min) / (range_max - range_min);
                    y_bottom - ratio * indicator_height
                };
                let zero_y = value_to_y(0.0);

                for vector in &indicator.vectors {
                    self.render_vector(backend, vector, bar_to_x, &value_to_y, zero_y);
                }
            } else {
                // Auto-populate from bars (Volume indicator)
                self.render_volume_from_bars(
                    backend,
                    indicator,
                    bar_to_x,
                    y_bottom,
                    indicator_height,
                );
            }
        }
    }

    /// Render Volume indicator using bar data directly
    fn render_volume_from_bars(
        &self,
        backend: &mut SvgBackend,
        indicator: &Indicator,
        bar_to_x: &impl Fn(usize) -> f64,
        y_bottom: f64,
        indicator_height: f64,
    ) {
        if self.bars.is_empty() {
            return;
        }

        // Find max volume for scaling
        let max_vol = self
            .bars
            .iter()
            .map(|b| b.volume)
            .filter(|v| !v.is_nan())
            .fold(0.0_f64, f64::max);

        if max_vol <= 0.0 {
            return;
        }

        let value_to_y = |v: f64| -> f64 {
            let ratio = v / max_vol;
            y_bottom - ratio * indicator_height
        };

        // Get histogram style colors
        let (up_color, down_color, bar_width_ratio) = indicator
            .vectors
            .first()
            .map(|v| match &v.style {
                VectorStyle::Histogram {
                    up_color,
                    down_color,
                    bar_width_ratio,
                } => (up_color.clone(), down_color.clone(), *bar_width_ratio),
                _ => ("#26a69a".to_string(), "#ef5350".to_string(), 0.8),
            })
            .unwrap_or(("#26a69a".to_string(), "#ef5350".to_string(), 0.8));

        let up = Color::from_css(&up_color).unwrap_or(Color::rgb(38, 166, 154));
        let down = Color::from_css(&down_color).unwrap_or(Color::rgb(239, 83, 80));

        let bar_spacing = self.config.width as f64 / self.bars.len() as f64;
        let bar_width = bar_spacing * bar_width_ratio;

        for (i, bar) in self.bars.iter().enumerate() {
            let vol = bar.volume;
            if vol.is_nan() || vol <= 0.0 {
                continue;
            }

            let x = bar_to_x(i);
            let y = value_to_y(vol);
            let bar_h = (y_bottom - y).max(1.0);

            // Color based on bar direction
            let color = if bar.close >= bar.open { up } else { down };

            backend.fill_rect(Rect::new(x - bar_width / 2.0, y, bar_width, bar_h), color);
        }
    }

    /// Render a single indicator vector based on its VectorStyle
    fn render_vector(
        &self,
        backend: &mut SvgBackend,
        vector: &crate::model::IndicatorVector,
        bar_to_x: &impl Fn(usize) -> f64,
        value_to_y: &impl Fn(f64) -> f64,
        zero_y: f64, // For histogram bars
    ) {
        match &vector.style {
            VectorStyle::Line {
                color,
                width,
                dashed,
            } => {
                let points: Vec<Point> = vector
                    .values
                    .iter()
                    .enumerate()
                    .filter(|&(_, &v)| !v.is_nan())
                    .map(|(i, &v)| Point::new(bar_to_x(i), value_to_y(v)))
                    .collect();

                if points.len() >= 2 {
                    let c = Color::from_css(color).unwrap_or(Color::WHITE);
                    let style = if *dashed {
                        LineStyle::dashed(c, *width, 4.0, 4.0)
                    } else {
                        LineStyle::solid(c, *width)
                    };
                    backend.polyline(&points, &style);
                }
            }
            VectorStyle::Histogram {
                up_color,
                down_color,
                bar_width_ratio,
            } => {
                let bar_spacing = self.config.width as f64 / self.bars.len().max(1) as f64;
                let bar_width = bar_spacing * bar_width_ratio;

                for (i, &v) in vector.values.iter().enumerate() {
                    if v.is_nan() {
                        continue;
                    }

                    let x = bar_to_x(i);
                    let y = value_to_y(v);

                    // Use directions vector if available, otherwise fallback to value sign
                    let is_up = vector.direction_at(i).unwrap_or(v >= 0.0);
                    let bar_color = if is_up {
                        Color::from_css(up_color).unwrap_or(Color::rgb(38, 166, 154))
                    } else {
                        Color::from_css(down_color).unwrap_or(Color::rgb(239, 83, 80))
                    };

                    let bar_height = (zero_y - y).abs().max(1.0);
                    let bar_y = if v >= 0.0 { y } else { zero_y };

                    backend.fill_rect(
                        Rect::new(x - bar_width / 2.0, bar_y, bar_width, bar_height),
                        bar_color,
                    );
                }
            }
            VectorStyle::Area {
                color,
                fill_alpha: _,
                line_width,
            } => {
                // Draw filled area
                let points: Vec<Point> = vector
                    .values
                    .iter()
                    .enumerate()
                    .filter(|&(_, &v)| !v.is_nan())
                    .map(|(i, &v)| Point::new(bar_to_x(i), value_to_y(v)))
                    .collect();

                if points.len() >= 2 {
                    let c = Color::from_css(color).unwrap_or(Color::WHITE);
                    // Line on top
                    backend.polyline(&points, &LineStyle::solid(c, *line_width));
                    // TODO: fill area below line
                }
            }
            VectorStyle::Dots {
                color,
                radius,
                filled,
            } => {
                let c = Color::from_css(color).unwrap_or(Color::WHITE);
                for (i, &v) in vector.values.iter().enumerate() {
                    if v.is_nan() {
                        continue;
                    }
                    let center = Point::new(bar_to_x(i), value_to_y(v));
                    if *filled {
                        backend.fill_circle(center, *radius, c);
                    } else {
                        backend.stroke_circle(center, *radius, &LineStyle::solid(c, 1.0));
                    }
                }
            }
            VectorStyle::Step { color, width } => {
                let c = Color::from_css(color).unwrap_or(Color::WHITE);
                let style = LineStyle::solid(c, *width);

                let mut prev: Option<(f64, f64)> = None;
                for (i, &v) in vector.values.iter().enumerate() {
                    if v.is_nan() {
                        continue;
                    }
                    let x = bar_to_x(i);
                    let y = value_to_y(v);

                    if let Some((px, py)) = prev {
                        // Horizontal then vertical (step)
                        backend.line(Point::new(px, py), Point::new(x, py), &style);
                        backend.line(Point::new(x, py), Point::new(x, y), &style);
                    }
                    prev = Some((x, y));
                }
            }
            VectorStyle::Cloud { .. } => {
                // Cloud requires two vectors - skip for now
            }
            VectorStyle::Hidden => {
                // Don't render
            }
        }
    }

    fn render_primitives(
        &self,
        backend: &mut SvgBackend,
        bar_to_x: &impl Fn(usize) -> f64,
        price_to_y: &impl Fn(f64) -> f64,
        dpr: f64,
        pane_id: Option<usize>,
    ) {
        let registry = PrimitiveRegistry::global().read().unwrap();

        for prim_config in &self.config.primitives {
            // Filter by pane
            match (pane_id, &prim_config.pane_id) {
                (None, None) => {}                        // Main pane, no pane_id specified
                (Some(id), Some(pid)) if *pid == id => {} // Matching pane
                _ => continue,                            // Skip non-matching
            }

            // Create primitive from registry
            if let Some(primitive) = registry.create(
                &prim_config.type_id,
                &prim_config.points,
                Some(&prim_config.color),
            ) {
                // Create render context adapter
                let mut ctx = SvgRenderContext::new(
                    backend,
                    bar_to_x,
                    price_to_y,
                    dpr,
                    self.config.width as f64,
                    self.config.height as f64,
                );

                // Render the primitive
                primitive.render(&mut ctx, false);
            }
        }
    }

    fn render_signals(
        &self,
        backend: &mut SvgBackend,
        bar_to_x: &impl Fn(usize) -> f64,
        price_to_y: &impl Fn(f64) -> f64,
        _dpr: f64,
    ) {
        for signal in &self.config.signals {
            let x = bar_to_x(signal.bar_index);
            let y = price_to_y(signal.price);

            let default_color = match signal.signal_type {
                crate::primitives::SignalType::Buy | crate::primitives::SignalType::Entry => {
                    "#26a69a"
                }
                crate::primitives::SignalType::Sell | crate::primitives::SignalType::Exit => {
                    "#ef5350"
                }
                crate::primitives::SignalType::TakeProfit => "#26a69a",
                crate::primitives::SignalType::StopLoss => "#ef5350",
                crate::primitives::SignalType::Custom => "#9c27b0",
            };
            let color = signal
                .color
                .as_deref()
                .and_then(Color::from_css)
                .unwrap_or_else(|| Color::from_css(default_color).unwrap());
            let size = signal.size * 12.0; // size is a multiplier

            match signal.signal_type {
                crate::primitives::SignalType::Buy | crate::primitives::SignalType::Entry => {
                    // Up arrow
                    self.draw_arrow_up(backend, x, y, size, color);
                }
                crate::primitives::SignalType::Sell | crate::primitives::SignalType::Exit => {
                    // Down arrow
                    self.draw_arrow_down(backend, x, y, size, color);
                }
                crate::primitives::SignalType::TakeProfit => {
                    // Circle with checkmark feel
                    backend.fill_circle(Point::new(x, y), size / 2.0, Color::rgb(38, 166, 154));
                }
                crate::primitives::SignalType::StopLoss => {
                    // Circle with X feel
                    backend.fill_circle(Point::new(x, y), size / 2.0, Color::rgb(239, 83, 80));
                }
                crate::primitives::SignalType::Custom => {
                    // Diamond shape
                    backend.fill_circle(Point::new(x, y), size / 2.0, color);
                }
            }

            // Label if present
            if let Some(ref label) = signal.label {
                use crate::render::engine::TextStyle;
                backend.text(
                    label,
                    Point::new(x + size, y),
                    &TextStyle {
                        font_family: "sans-serif".into(),
                        font_size: 10.0,
                        font_weight: crate::render::engine::FontWeight::Normal,
                        color,
                        align: crate::render::engine::TextAlign::Left,
                        baseline: crate::render::engine::TextBaseline::Middle,
                    },
                );
            }
        }
    }

    fn draw_arrow_up(&self, backend: &mut SvgBackend, x: f64, y: f64, size: f64, color: Color) {
        let half = size / 2.0;
        let points = vec![
            Point::new(x, y - half),        // top
            Point::new(x - half, y + half), // bottom left
            Point::new(x + half, y + half), // bottom right
        ];
        backend.fill_path(&Path::polygon(&points), &FillStyle::solid(color));
    }

    fn draw_arrow_down(&self, backend: &mut SvgBackend, x: f64, y: f64, size: f64, color: Color) {
        let half = size / 2.0;
        let points = vec![
            Point::new(x, y + half),        // bottom
            Point::new(x - half, y - half), // top left
            Point::new(x + half, y - half), // top right
        ];
        backend.fill_path(&Path::polygon(&points), &FillStyle::solid(color));
    }

    /// Render a subpane indicator (RSI, MACD, Volume, etc.)
    fn render_subpane_indicator(
        &self,
        backend: &mut SvgBackend,
        params: SubpaneRenderParams<'_>,
        bar_to_x: &impl Fn(usize) -> f64,
    ) {
        let SubpaneRenderParams {
            indicator,
            y_offset,
            height,
            width,
            pane_idx,
        } = params;

        // Subpane background
        let subpane_bg =
            Color::from_css(&self.config.theme.background).unwrap_or(Color::rgb(19, 23, 34));
        backend.fill_rect(Rect::new(0.0, y_offset, width as f64, height), subpane_bg);

        // Separator line
        let sep_color =
            Color::from_css(&self.config.theme.grid_color).unwrap_or(Color::rgb(42, 46, 57));
        backend.line(
            Point::new(0.0, y_offset),
            Point::new(width as f64, y_offset),
            &LineStyle::solid(sep_color, 1.0),
        );

        // Calculate range based on indicator's IndicatorRange
        let (range_min, range_max) = self.calculate_indicator_range(indicator);

        let value_to_y = |v: f64| -> f64 {
            let ratio = (v - range_min) / (range_max - range_min);
            y_offset + height - ratio * height
        };

        let zero_y = value_to_y(0.0);

        // Draw indicator levels (reference lines like RSI 30/70, MACD zero line)
        for level in &indicator.levels {
            let y = value_to_y(level.value);
            let color = Color::from_css(&level.color).unwrap_or(Color::rgb(120, 123, 134));
            let style = match level.style.as_str() {
                "dotted" => LineStyle::dashed(color, level.width, 2.0, 2.0),
                "dashed" => LineStyle::dashed(color, level.width, 4.0, 4.0),
                _ => LineStyle::solid(color, level.width),
            };
            backend.line(Point::new(0.0, y), Point::new(width as f64, y), &style);
        }

        // Draw indicator vectors using their VectorStyle
        for vector in &indicator.vectors {
            self.render_vector(backend, vector, bar_to_x, &value_to_y, zero_y);
        }

        // Render primitives for this pane
        self.render_primitives(
            backend,
            bar_to_x,
            &value_to_y,
            self.config.dpr,
            Some(pane_idx),
        );
    }

    /// Calculate the Y-axis range for an indicator based on its IndicatorRange
    fn calculate_indicator_range(&self, indicator: &Indicator) -> (f64, f64) {
        use crate::model::IndicatorRange;

        match &indicator.range {
            IndicatorRange::Fixed { min, max } => (*min, *max),
            IndicatorRange::Symmetric => {
                // Find max absolute value across all vectors
                let mut max_abs = 0.0_f64;
                for vector in &indicator.vectors {
                    for &v in &vector.values {
                        if !v.is_nan() {
                            max_abs = max_abs.max(v.abs());
                        }
                    }
                }
                let padding = max_abs * 0.1;
                (-(max_abs + padding), max_abs + padding)
            }
            IndicatorRange::Price => {
                // Use the same range as the main price chart (from bars)
                let mut min = f64::INFINITY;
                let mut max = f64::NEG_INFINITY;
                for bar in self.bars {
                    if !bar.low.is_nan() {
                        min = min.min(bar.low);
                    }
                    if !bar.high.is_nan() {
                        max = max.max(bar.high);
                    }
                }
                let padding = (max - min) * 0.05;
                (min - padding, max + padding)
            }
            IndicatorRange::Auto => {
                // Auto-calculate from data
                let mut min = f64::INFINITY;
                let mut max = f64::NEG_INFINITY;

                for vector in &indicator.vectors {
                    for &v in &vector.values {
                        if !v.is_nan() {
                            min = min.min(v);
                            max = max.max(v);
                        }
                    }
                }

                // Add padding
                let range = max - min;
                if range > 0.0 {
                    let padding = range * 0.1;
                    (min - padding, max + padding)
                } else {
                    (0.0, 100.0)
                }
            }
        }
    }

    /// Render price scale (Y-axis) on the right side of the chart area
    fn render_price_scale(
        &self,
        backend: &mut SvgBackend,
        chart_width: f64,
        y_offset: f64,
        pane_height: f64,
        price_min: f64,
        price_max: f64,
    ) {
        let scale_x = chart_width;
        let scale_width = PRICE_SCALE_WIDTH;

        // Background for price scale area
        let bg_color =
            Color::from_css(&self.config.theme.background).unwrap_or(Color::rgb(19, 23, 34));
        backend.fill_rect(
            Rect::new(scale_x, y_offset, scale_width, pane_height),
            bg_color,
        );

        // Border line
        let border_color =
            Color::from_css(&self.config.theme.grid_color).unwrap_or(Color::rgb(42, 46, 57));
        backend.line(
            Point::new(scale_x, y_offset),
            Point::new(scale_x, y_offset + pane_height),
            &LineStyle::solid(border_color, 1.0),
        );

        // Generate price ticks using PriceScale
        let price_scale = PriceScale::new(price_min, price_max);
        let ticks = price_scale.generate_ticks(pane_height);

        let text_color =
            Color::from_css(&self.config.theme.text_color).unwrap_or(Color::rgb(180, 180, 180));
        let font_size = price_scale.calc_font_size(pane_height).min(11.0);

        let text_style = TextStyle {
            color: text_color,
            font_size,
            font_weight: FontWeight::Normal,
            align: TextAlign::Left,
            baseline: TextBaseline::Middle,
            ..Default::default()
        };

        // Draw tick marks and labels
        for tick in ticks {
            let ratio = (tick - price_min) / (price_max - price_min);
            let y = y_offset + pane_height - ratio * pane_height;

            // Tick line
            backend.line(
                Point::new(scale_x, y),
                Point::new(scale_x + 4.0, y),
                &LineStyle::solid(border_color, 1.0),
            );

            // Label
            let label = price_scale.format_price(tick, pane_height);
            backend.text(&label, Point::new(scale_x + 6.0, y), &text_style);
        }
    }

    /// Render time scale (X-axis) at the bottom of the chart
    fn render_time_scale(
        &self,
        backend: &mut SvgBackend,
        chart_width: f64,
        chart_height: f64,
        bar_spacing: f64,
    ) {
        let scale_y = chart_height;
        let scale_height = TIME_SCALE_HEIGHT;
        let total_width = chart_width + PRICE_SCALE_WIDTH;

        // Background for time scale area
        let bg_color =
            Color::from_css(&self.config.theme.background).unwrap_or(Color::rgb(19, 23, 34));
        backend.fill_rect(Rect::new(0.0, scale_y, total_width, scale_height), bg_color);

        // Border line at top of time scale
        let border_color =
            Color::from_css(&self.config.theme.grid_color).unwrap_or(Color::rgb(42, 46, 57));
        backend.line(
            Point::new(0.0, scale_y),
            Point::new(chart_width, scale_y),
            &LineStyle::solid(border_color, 1.0),
        );

        let text_color =
            Color::from_css(&self.config.theme.text_color).unwrap_or(Color::rgb(180, 180, 180));
        let text_style = TextStyle {
            color: text_color,
            font_size: 10.0,
            font_weight: FontWeight::Normal,
            align: TextAlign::Center,
            baseline: TextBaseline::Top,
            ..Default::default()
        };

        // Calculate visible bar range and generate time ticks
        let bar_count = self.bars.len();
        if bar_count == 0 {
            return;
        }

        // Determine appropriate tick spacing based on bar_spacing
        let min_label_spacing = 60.0; // Minimum pixels between labels
        let bars_per_tick = (min_label_spacing / bar_spacing).ceil() as usize;
        let bars_per_tick = bars_per_tick.max(1);

        // Find appropriate boundaries
        let mut prev_ts: Option<i64> = None;
        for i in (0..bar_count).step_by(bars_per_tick.max(1)) {
            if i >= self.bars.len() {
                break;
            }

            let ts = self.bars[i].timestamp;
            let x = bar_spacing * (i as f64 + 0.5);

            if x < 10.0 || x > chart_width - 30.0 {
                prev_ts = Some(ts);
                continue;
            }

            let weight = TickMarkWeight::from_timestamp(ts, prev_ts);

            // Only show significant ticks
            if weight >= TickMarkWeight::Hour || i == 0 || (i % (bars_per_tick * 3)) == 0 {
                // Tick mark
                backend.line(
                    Point::new(x, scale_y),
                    Point::new(x, scale_y + 4.0),
                    &LineStyle::solid(border_color, 1.0),
                );

                // Label
                let label = format_time_by_weight(ts, weight);
                backend.text(&label, Point::new(x, scale_y + 6.0), &text_style);
            }

            prev_ts = Some(ts);
        }
    }

    fn execute_batch(&self, backend: &mut SvgBackend, batch: &RenderBatch) {
        use crate::render::engine::RenderCommand;

        for cmd in batch.commands() {
            match cmd {
                RenderCommand::FillRect { rect, color } => {
                    backend.fill_rect(*rect, *color);
                }
                RenderCommand::StrokeRect { rect, style } => {
                    backend.stroke_rect(*rect, style);
                }
                RenderCommand::Line { from, to, style } => {
                    backend.line(*from, *to, style);
                }
                RenderCommand::Polyline { points, style } => {
                    backend.polyline(points, style);
                }
                RenderCommand::FillPath { path, style } => {
                    backend.fill_path(path, style);
                }
                RenderCommand::StrokePath { path, style } => {
                    backend.stroke_path(path, style);
                }
                RenderCommand::FillCircle {
                    center,
                    radius,
                    color,
                } => {
                    backend.fill_circle(*center, *radius, *color);
                }
                RenderCommand::StrokeCircle {
                    center,
                    radius,
                    style,
                } => {
                    backend.stroke_circle(*center, *radius, style);
                }
                RenderCommand::Text { text, pos, style } => {
                    backend.text(text, *pos, style);
                }
                _ => {}
            }
        }
    }
}

// =============================================================================
// MultichartRenderer - Renders multiple charts in a layout
// =============================================================================

use crate::layout::MultichartLayout;

/// Renders multiple charts in a grid layout
pub struct MultichartRenderer<'a> {
    layout: &'a MultichartLayout,
    charts: Vec<(&'a ChartConfig, &'a [Bar])>,
    total_width: u32,
    total_height: u32,
    dpr: f64,
}

impl<'a> MultichartRenderer<'a> {
    /// Create a new multichart renderer
    pub fn new(layout: &'a MultichartLayout, total_width: u32, total_height: u32) -> Self {
        Self {
            layout,
            charts: Vec::new(),
            total_width,
            total_height,
            dpr: 1.0,
        }
    }

    /// Set device pixel ratio
    pub fn dpr(mut self, dpr: f64) -> Self {
        self.dpr = dpr;
        self
    }

    /// Add a chart to a cell
    pub fn chart(mut self, config: &'a ChartConfig, bars: &'a [Bar]) -> Self {
        self.charts.push((config, bars));
        self
    }

    /// Render all charts to SVG
    pub fn render_svg(&self) -> String {
        let width = self.total_width;
        let height = self.total_height;
        let dpr = self.dpr;

        let mut backend = SvgBackend::new(width, height, dpr);
        backend.begin_frame(width as f64, height as f64, dpr);

        // Background
        let bg = Color::rgb(19, 23, 34);
        backend.clear(bg);

        // Calculate cell bounds
        let bounds = self.layout.calculate_bounds(width as f64, height as f64);

        // Render each chart in its cell
        for (idx, (_cell_id, cell_bounds)) in bounds.iter().enumerate() {
            if let Some((config, bars)) = self.charts.get(idx) {
                self.render_chart_in_cell(&mut backend, config, bars, cell_bounds, dpr);
            }
        }

        backend.end_frame();
        backend.to_svg()
    }

    fn render_chart_in_cell(
        &self,
        backend: &mut SvgBackend,
        config: &ChartConfig,
        bars: &[Bar],
        bounds: &crate::layout::CellBounds,
        _dpr: f64,
    ) {
        if bars.is_empty() {
            return;
        }

        let x_offset = bounds.x;
        let y_offset = bounds.y;
        let cell_width = bounds.width;
        let cell_height = bounds.height;

        // Reserve space for scales
        let price_scale_width = PRICE_SCALE_WIDTH;
        let time_scale_height = TIME_SCALE_HEIGHT;
        let chart_width = cell_width - price_scale_width;
        let chart_height = cell_height - time_scale_height;

        // Separate indicators
        let overlays: Vec<&Indicator> = config
            .indicators
            .iter()
            .filter(|ind| ind.placement.is_overlay())
            .collect();
        let overlay_bottoms: Vec<&Indicator> = config
            .indicators
            .iter()
            .filter(|ind| ind.placement.is_overlay_bottom())
            .collect();
        let subpanes: Vec<&Indicator> = config
            .indicators
            .iter()
            .filter(|ind| ind.placement.is_subpane())
            .collect();

        // Calculate layout
        let total_subpane_ratio: f64 = subpanes.iter().map(|s| s.placement.height_ratio()).sum();
        let main_ratio = 1.0 - total_subpane_ratio;
        let main_height = chart_height * main_ratio;
        let gap = 2.0;

        // Calculate price range
        let (price_min, price_max) = Self::calc_price_range(bars, &overlays);
        let price_padding = (price_max - price_min) * 0.05;
        let price_low = price_min - price_padding;
        let price_high = price_max + price_padding;

        let bar_count = bars.len();
        let bar_spacing = chart_width / bar_count as f64;
        let bar_width = (bar_spacing * 0.8).max(1.0);

        // Coordinate transforms with offset
        let bar_to_x = |i: usize| -> f64 { x_offset + bar_spacing * (i as f64 + 0.5) };

        let price_to_y = |price: f64| -> f64 {
            let ratio = (price - price_low) / (price_high - price_low);
            y_offset + main_height - ratio * main_height
        };

        // Cell background
        let bg_color = Color::from_css(&config.theme.background).unwrap_or(Color::rgb(19, 23, 34));
        backend.fill_rect(
            Rect::new(x_offset, y_offset, cell_width, cell_height),
            bg_color,
        );

        // Border
        let border_color =
            Color::from_css(&config.theme.grid_color).unwrap_or(Color::rgb(42, 46, 57));
        backend.stroke_rect(
            Rect::new(x_offset, y_offset, cell_width, cell_height),
            &LineStyle::solid(border_color, 1.0),
        );

        // Render main series
        Self::render_series_simple(backend, bars, config, &bar_to_x, &price_to_y, bar_width);

        // Render overlay indicators (share price Y scale)
        for indicator in &overlays {
            for vector in &indicator.vectors {
                Self::render_vector_simple(
                    backend,
                    vector,
                    &bar_to_x,
                    &price_to_y,
                    price_to_y(0.0),
                );
            }
        }

        // Render overlay_bottom indicators (own Y scale at bottom of main chart)
        Self::render_overlay_bottom_simple(
            backend,
            bars,
            &overlay_bottoms,
            &bar_to_x,
            y_offset,
            main_height,
            config,
        );

        // Price scale
        Self::render_price_scale_simple(
            backend,
            config,
            x_offset + chart_width,
            y_offset,
            main_height,
            price_low,
            price_high,
        );

        // Subpanes
        let mut sub_y_offset = y_offset + main_height + gap;
        for indicator in &subpanes {
            let pane_height = chart_height * indicator.placement.height_ratio() - gap;

            // Subpane background
            backend.fill_rect(
                Rect::new(x_offset, sub_y_offset, chart_width, pane_height),
                bg_color,
            );

            // Separator
            backend.line(
                Point::new(x_offset, sub_y_offset),
                Point::new(x_offset + chart_width, sub_y_offset),
                &LineStyle::solid(border_color, 1.0),
            );

            // Calculate subpane range
            let (sub_min, sub_max) = Self::calc_indicator_range(indicator, bars);
            let value_to_y = |v: f64| -> f64 {
                let ratio = (v - sub_min) / (sub_max - sub_min);
                sub_y_offset + pane_height - ratio * pane_height
            };
            let zero_y = value_to_y(0.0);

            // Render levels
            for level in &indicator.levels {
                let y = value_to_y(level.value);
                let color = Color::from_css(&level.color).unwrap_or(Color::rgb(120, 123, 134));
                let style = match level.style.as_str() {
                    "dotted" => LineStyle::dashed(color, level.width, 2.0, 2.0),
                    "dashed" => LineStyle::dashed(color, level.width, 4.0, 4.0),
                    _ => LineStyle::solid(color, level.width),
                };
                backend.line(
                    Point::new(x_offset, y),
                    Point::new(x_offset + chart_width, y),
                    &style,
                );
            }

            // Render vectors
            for vector in &indicator.vectors {
                Self::render_vector_simple(backend, vector, &bar_to_x, &value_to_y, zero_y);
            }

            // Price scale for subpane
            Self::render_price_scale_simple(
                backend,
                config,
                x_offset + chart_width,
                sub_y_offset,
                pane_height,
                sub_min,
                sub_max,
            );

            sub_y_offset += pane_height + gap;
        }

        // Time scale
        Self::render_time_scale_simple(
            backend,
            config,
            bars,
            x_offset,
            y_offset + chart_height,
            chart_width,
            bar_spacing,
        );
    }

    fn calc_price_range(bars: &[Bar], overlays: &[&Indicator]) -> (f64, f64) {
        let mut min = f64::INFINITY;
        let mut max = f64::NEG_INFINITY;

        for bar in bars {
            if !bar.low.is_nan() {
                min = min.min(bar.low);
            }
            if !bar.high.is_nan() {
                max = max.max(bar.high);
            }
        }

        for indicator in overlays {
            for vector in &indicator.vectors {
                for &v in &vector.values {
                    if !v.is_nan() {
                        min = min.min(v);
                        max = max.max(v);
                    }
                }
            }
        }

        if min.is_infinite() {
            min = 0.0;
        }
        if max.is_infinite() {
            max = 100.0;
        }

        (min, max)
    }

    fn calc_indicator_range(indicator: &Indicator, bars: &[Bar]) -> (f64, f64) {
        use crate::model::IndicatorRange;

        match &indicator.range {
            IndicatorRange::Fixed { min, max } => (*min, *max),
            IndicatorRange::Symmetric => {
                let mut max_abs = 0.0_f64;
                for vector in &indicator.vectors {
                    for &v in &vector.values {
                        if !v.is_nan() {
                            max_abs = max_abs.max(v.abs());
                        }
                    }
                }
                let padding = max_abs * 0.1;
                (-(max_abs + padding), max_abs + padding)
            }
            IndicatorRange::Price => {
                let mut min = f64::INFINITY;
                let mut max = f64::NEG_INFINITY;
                for bar in bars {
                    if !bar.low.is_nan() {
                        min = min.min(bar.low);
                    }
                    if !bar.high.is_nan() {
                        max = max.max(bar.high);
                    }
                }
                let padding = (max - min) * 0.05;
                (min - padding, max + padding)
            }
            IndicatorRange::Auto => {
                let mut min = f64::INFINITY;
                let mut max = f64::NEG_INFINITY;
                for vector in &indicator.vectors {
                    for &v in &vector.values {
                        if !v.is_nan() {
                            min = min.min(v);
                            max = max.max(v);
                        }
                    }
                }
                let range = max - min;
                if range > 0.0 {
                    let padding = range * 0.1;
                    (min - padding, max + padding)
                } else {
                    (0.0, 100.0)
                }
            }
        }
    }

    fn render_series_simple(
        backend: &mut SvgBackend,
        bars: &[Bar],
        config: &ChartConfig,
        bar_to_x: &impl Fn(usize) -> f64,
        price_to_y: &impl Fn(f64) -> f64,
        bar_width: f64,
    ) {
        let up_color = Color::from_css(&config.theme.up_color).unwrap_or(Color::rgb(38, 166, 154));
        let down_color =
            Color::from_css(&config.theme.down_color).unwrap_or(Color::rgb(239, 83, 80));

        match &config.series.series_type {
            SeriesType::Candlestick | SeriesType::HollowCandlestick | SeriesType::HeikinAshi => {
                for (i, bar) in bars.iter().enumerate() {
                    let x = bar_to_x(i);
                    let is_up = bar.close >= bar.open;
                    let color = if is_up { up_color } else { down_color };

                    // Wick
                    backend.line(
                        Point::new(x, price_to_y(bar.high)),
                        Point::new(x, price_to_y(bar.low)),
                        &LineStyle::solid(color, 1.0),
                    );

                    // Body
                    let body_top = price_to_y(bar.open.max(bar.close));
                    let body_bottom = price_to_y(bar.open.min(bar.close));
                    let body_height = (body_bottom - body_top).max(1.0);
                    backend.fill_rect(
                        Rect::new(x - bar_width / 2.0, body_top, bar_width, body_height),
                        color,
                    );
                }
            }
            SeriesType::Line => {
                let points: Vec<Point> = bars
                    .iter()
                    .enumerate()
                    .map(|(i, bar)| Point::new(bar_to_x(i), price_to_y(bar.close)))
                    .collect();
                if points.len() >= 2 {
                    backend.polyline(&points, &LineStyle::solid(up_color, 1.5));
                }
            }
            SeriesType::Area => {
                let line_color = config
                    .series
                    .style
                    .color
                    .as_ref()
                    .and_then(|c| Color::from_css(c))
                    .unwrap_or(up_color);
                let fill_color = line_color.with_alpha(0.3);

                let points: Vec<Point> = bars
                    .iter()
                    .enumerate()
                    .map(|(i, bar)| Point::new(bar_to_x(i), price_to_y(bar.close)))
                    .collect();

                if points.len() >= 2 {
                    // Line
                    backend.polyline(&points, &LineStyle::solid(line_color, 1.5));

                    // Fill
                    let mut fill_points = points.clone();
                    let base_y =
                        price_to_y(bars.iter().map(|b| b.low).fold(f64::INFINITY, f64::min));
                    fill_points.push(Point::new(points.last().unwrap().x, base_y));
                    fill_points.push(Point::new(points.first().unwrap().x, base_y));
                    backend.fill_path(&Path::polygon(&fill_points), &FillStyle::solid(fill_color));
                }
            }
            SeriesType::Bar => {
                for (i, bar) in bars.iter().enumerate() {
                    let x = bar_to_x(i);
                    let is_up = bar.close >= bar.open;
                    let color = if is_up { up_color } else { down_color };

                    // Vertical line (high to low)
                    backend.line(
                        Point::new(x, price_to_y(bar.high)),
                        Point::new(x, price_to_y(bar.low)),
                        &LineStyle::solid(color, 1.0),
                    );
                    // Open tick (left)
                    backend.line(
                        Point::new(x - bar_width / 2.0, price_to_y(bar.open)),
                        Point::new(x, price_to_y(bar.open)),
                        &LineStyle::solid(color, 1.0),
                    );
                    // Close tick (right)
                    backend.line(
                        Point::new(x, price_to_y(bar.close)),
                        Point::new(x + bar_width / 2.0, price_to_y(bar.close)),
                        &LineStyle::solid(color, 1.0),
                    );
                }
            }
            SeriesType::Baseline => {
                let baseline = bars.iter().map(|b| b.close).sum::<f64>() / bars.len() as f64;
                let baseline_y = price_to_y(baseline);

                // Baseline
                let baseline_color = Color::rgb(120, 120, 120);
                backend.line(
                    Point::new(bar_to_x(0) - 10.0, baseline_y),
                    Point::new(bar_to_x(bars.len() - 1) + 10.0, baseline_y),
                    &LineStyle::dashed(baseline_color, 1.0, 4.0, 2.0),
                );

                // Line with color based on above/below
                for (i, bar) in bars.iter().enumerate().skip(1) {
                    let prev = &bars[i - 1];
                    let color = if bar.close >= baseline {
                        up_color
                    } else {
                        down_color
                    };
                    backend.line(
                        Point::new(bar_to_x(i - 1), price_to_y(prev.close)),
                        Point::new(bar_to_x(i), price_to_y(bar.close)),
                        &LineStyle::solid(color, 1.5),
                    );
                }
            }
            _ => {
                // Fallback to line
                let points: Vec<Point> = bars
                    .iter()
                    .enumerate()
                    .map(|(i, bar)| Point::new(bar_to_x(i), price_to_y(bar.close)))
                    .collect();
                if points.len() >= 2 {
                    backend.polyline(&points, &LineStyle::solid(up_color, 1.5));
                }
            }
        }
    }

    fn render_vector_simple(
        backend: &mut SvgBackend,
        vector: &crate::model::IndicatorVector,
        bar_to_x: &impl Fn(usize) -> f64,
        value_to_y: &impl Fn(f64) -> f64,
        zero_y: f64,
    ) {
        match &vector.style {
            VectorStyle::Line {
                color,
                width,
                dashed,
            } => {
                let c = Color::from_css(color).unwrap_or(Color::WHITE);
                let points: Vec<Point> = vector
                    .values
                    .iter()
                    .enumerate()
                    .filter(|&(_, &v)| !v.is_nan())
                    .map(|(i, &v)| Point::new(bar_to_x(i), value_to_y(v)))
                    .collect();
                if points.len() >= 2 {
                    let style = if *dashed {
                        LineStyle::dashed(c, *width, 4.0, 2.0)
                    } else {
                        LineStyle::solid(c, *width)
                    };
                    backend.polyline(&points, &style);
                }
            }
            VectorStyle::Histogram {
                up_color,
                down_color,
                bar_width_ratio,
            } => {
                let up = Color::from_css(up_color).unwrap_or(Color::rgb(38, 166, 154));
                let down = Color::from_css(down_color).unwrap_or(Color::rgb(239, 83, 80));
                let bar_w = 3.0 * bar_width_ratio;

                for (i, &v) in vector.values.iter().enumerate() {
                    if v.is_nan() {
                        continue;
                    }
                    let x = bar_to_x(i);
                    let y = value_to_y(v);
                    // Use directions vector if available, otherwise fallback to value sign
                    let is_up = vector.direction_at(i).unwrap_or(v >= 0.0);
                    let color = if is_up { up } else { down };
                    let h = (zero_y - y).abs();
                    let top_y = if v >= 0.0 { y } else { zero_y };
                    backend.fill_rect(Rect::new(x - bar_w / 2.0, top_y, bar_w, h), color);
                }
            }
            VectorStyle::Area {
                color,
                fill_alpha,
                line_width,
            } => {
                let c = Color::from_css(color).unwrap_or(Color::WHITE);
                let points: Vec<Point> = vector
                    .values
                    .iter()
                    .enumerate()
                    .filter(|&(_, &v)| !v.is_nan())
                    .map(|(i, &v)| Point::new(bar_to_x(i), value_to_y(v)))
                    .collect();
                if points.len() >= 2 {
                    backend.polyline(&points, &LineStyle::solid(c, *line_width));
                    let fill = c.with_alpha(*fill_alpha);
                    let mut fill_pts = points.clone();
                    fill_pts.push(Point::new(points.last().unwrap().x, zero_y));
                    fill_pts.push(Point::new(points.first().unwrap().x, zero_y));
                    backend.fill_path(&Path::polygon(&fill_pts), &FillStyle::solid(fill));
                }
            }
            VectorStyle::Dots {
                color,
                radius,
                filled,
            } => {
                let c = Color::from_css(color).unwrap_or(Color::WHITE);
                for (i, &v) in vector.values.iter().enumerate() {
                    if v.is_nan() {
                        continue;
                    }
                    let center = Point::new(bar_to_x(i), value_to_y(v));
                    if *filled {
                        backend.fill_circle(center, *radius, c);
                    } else {
                        backend.stroke_circle(center, *radius, &LineStyle::solid(c, 1.0));
                    }
                }
            }
            _ => {}
        }
    }

    fn render_price_scale_simple(
        backend: &mut SvgBackend,
        config: &ChartConfig,
        x: f64,
        y_offset: f64,
        height: f64,
        price_min: f64,
        price_max: f64,
    ) {
        let bg_color = Color::from_css(&config.theme.background).unwrap_or(Color::rgb(19, 23, 34));
        let border_color =
            Color::from_css(&config.theme.grid_color).unwrap_or(Color::rgb(42, 46, 57));
        let text_color =
            Color::from_css(&config.theme.text_color).unwrap_or(Color::rgb(180, 180, 180));

        backend.fill_rect(Rect::new(x, y_offset, PRICE_SCALE_WIDTH, height), bg_color);
        backend.line(
            Point::new(x, y_offset),
            Point::new(x, y_offset + height),
            &LineStyle::solid(border_color, 1.0),
        );

        let price_scale = PriceScale::new(price_min, price_max);
        let ticks = price_scale.generate_ticks(height);
        let font_size = price_scale.calc_font_size(height).min(10.0);
        let text_style = TextStyle {
            color: text_color,
            font_size,
            font_weight: FontWeight::Normal,
            align: TextAlign::Left,
            baseline: TextBaseline::Middle,
            ..Default::default()
        };

        for tick in ticks {
            let ratio = (tick - price_min) / (price_max - price_min);
            let y = y_offset + height - ratio * height;
            backend.line(
                Point::new(x, y),
                Point::new(x + 3.0, y),
                &LineStyle::solid(border_color, 1.0),
            );
            let label = price_scale.format_price(tick, height);
            backend.text(&label, Point::new(x + 4.0, y), &text_style);
        }
    }

    /// Render overlay_bottom indicators generically (own Y scale at bottom of main chart)
    fn render_overlay_bottom_simple(
        backend: &mut SvgBackend,
        bars: &[Bar],
        indicators: &[&Indicator],
        bar_to_x: &impl Fn(usize) -> f64,
        y_offset: f64,
        main_height: f64,
        config: &ChartConfig,
    ) {
        for indicator in indicators {
            let height_ratio = indicator.placement.height_ratio();
            let indicator_height = main_height * height_ratio;
            let y_bottom = y_offset + main_height;

            // For Volume-like indicators: if vector.values is empty, use bars data
            let has_data = indicator.vectors.iter().any(|v| !v.values.is_empty());

            if has_data {
                // Calculate range for this indicator
                let (range_min, range_max) = Self::calc_indicator_range(indicator, bars);
                if range_max <= range_min {
                    continue;
                }

                let value_to_y = |v: f64| -> f64 {
                    let ratio = (v - range_min) / (range_max - range_min);
                    y_bottom - ratio * indicator_height
                };
                let zero_y = value_to_y(0.0);

                for vector in &indicator.vectors {
                    Self::render_vector_simple(backend, vector, bar_to_x, &value_to_y, zero_y);
                }
            } else {
                // Auto-populate from bars (Volume indicator)
                Self::render_volume_from_bars_simple(
                    backend,
                    bars,
                    indicator,
                    bar_to_x,
                    y_bottom,
                    indicator_height,
                    config,
                );
            }
        }
    }

    /// Render Volume indicator using bar data directly (for MultichartRenderer)
    fn render_volume_from_bars_simple(
        backend: &mut SvgBackend,
        bars: &[Bar],
        indicator: &Indicator,
        bar_to_x: &impl Fn(usize) -> f64,
        y_bottom: f64,
        indicator_height: f64,
        config: &ChartConfig,
    ) {
        if bars.is_empty() {
            return;
        }

        // Find max volume for scaling
        let max_vol = bars
            .iter()
            .map(|b| b.volume)
            .filter(|v| !v.is_nan())
            .fold(0.0_f64, f64::max);

        if max_vol <= 0.0 {
            return;
        }

        let value_to_y = |v: f64| -> f64 {
            let ratio = v / max_vol;
            y_bottom - ratio * indicator_height
        };

        // Get histogram style colors from indicator, fallback to theme colors
        let (up_color, down_color, bar_width_ratio) = indicator
            .vectors
            .first()
            .map(|v| match &v.style {
                VectorStyle::Histogram {
                    up_color,
                    down_color,
                    bar_width_ratio,
                } => (up_color.clone(), down_color.clone(), *bar_width_ratio),
                _ => (
                    config.theme.up_color.clone(),
                    config.theme.down_color.clone(),
                    0.8,
                ),
            })
            .unwrap_or((
                config.theme.up_color.clone(),
                config.theme.down_color.clone(),
                0.8,
            ));

        let up = Color::from_css(&up_color).unwrap_or(Color::rgb(38, 166, 154));
        let down = Color::from_css(&down_color).unwrap_or(Color::rgb(239, 83, 80));

        let bar_w = 3.0 * bar_width_ratio;

        for (i, bar) in bars.iter().enumerate() {
            let vol = bar.volume;
            if vol.is_nan() || vol <= 0.0 {
                continue;
            }

            let x = bar_to_x(i);
            let y = value_to_y(vol);
            let bar_h = (y_bottom - y).max(1.0);

            // Color based on bar direction
            let color = if bar.close >= bar.open { up } else { down };

            backend.fill_rect(Rect::new(x - bar_w / 2.0, y, bar_w, bar_h), color);
        }
    }

    fn render_time_scale_simple(
        backend: &mut SvgBackend,
        config: &ChartConfig,
        bars: &[Bar],
        x_offset: f64,
        y: f64,
        width: f64,
        bar_spacing: f64,
    ) {
        let bg_color = Color::from_css(&config.theme.background).unwrap_or(Color::rgb(19, 23, 34));
        let border_color =
            Color::from_css(&config.theme.grid_color).unwrap_or(Color::rgb(42, 46, 57));
        let text_color =
            Color::from_css(&config.theme.text_color).unwrap_or(Color::rgb(180, 180, 180));

        backend.fill_rect(
            Rect::new(x_offset, y, width + PRICE_SCALE_WIDTH, TIME_SCALE_HEIGHT),
            bg_color,
        );
        backend.line(
            Point::new(x_offset, y),
            Point::new(x_offset + width, y),
            &LineStyle::solid(border_color, 1.0),
        );

        let text_style = TextStyle {
            color: text_color,
            font_size: 9.0,
            font_weight: FontWeight::Normal,
            align: TextAlign::Center,
            baseline: TextBaseline::Top,
            ..Default::default()
        };

        let min_spacing = 50.0;
        let step = (min_spacing / bar_spacing).ceil() as usize;
        let step = step.max(1);

        let mut prev_ts: Option<i64> = None;
        for i in (0..bars.len()).step_by(step) {
            let ts = bars[i].timestamp;
            let x = x_offset + bar_spacing * (i as f64 + 0.5);
            if x < x_offset + 5.0 || x > x_offset + width - 20.0 {
                prev_ts = Some(ts);
                continue;
            }

            let weight = TickMarkWeight::from_timestamp(ts, prev_ts);
            if weight >= TickMarkWeight::Hour || (i % (step * 2)) == 0 {
                backend.line(
                    Point::new(x, y),
                    Point::new(x, y + 3.0),
                    &LineStyle::solid(border_color, 1.0),
                );
                let label = format_time_by_weight(ts, weight);
                backend.text(&label, Point::new(x, y + 4.0), &text_style);
            }
            prev_ts = Some(ts);
        }
    }
}

// =============================================================================
// SvgRenderContext - Adapter for primitive rendering
// =============================================================================

use crate::render::engine::PathBuilder;

/// Adapter to use SvgBackend with primitive RenderContext trait
struct SvgRenderContext<'a, F1, F2>
where
    F1: Fn(usize) -> f64,
    F2: Fn(f64) -> f64,
{
    backend: &'a mut SvgBackend,
    bar_to_x: &'a F1,
    price_to_y: &'a F2,
    dpr: f64,
    viewport_width: f64,
    viewport_height: f64,
    // Drawing state
    path_builder: PathBuilder,
    stroke_color: Color,
    stroke_width: f64,
    fill_color: Color,
    dash_pattern: Vec<f64>,
    global_alpha: f64,
    font_size: f64,
    text_color: Color,
}

impl<'a, F1, F2> SvgRenderContext<'a, F1, F2>
where
    F1: Fn(usize) -> f64,
    F2: Fn(f64) -> f64,
{
    fn new(
        backend: &'a mut SvgBackend,
        bar_to_x: &'a F1,
        price_to_y: &'a F2,
        dpr: f64,
        viewport_width: f64,
        viewport_height: f64,
    ) -> Self {
        Self {
            backend,
            bar_to_x,
            price_to_y,
            dpr,
            viewport_width,
            viewport_height,
            path_builder: PathBuilder::new(),
            stroke_color: Color::from_css("#2196F3").unwrap_or(Color::WHITE),
            stroke_width: 2.0,
            fill_color: Color::TRANSPARENT,
            dash_pattern: Vec::new(),
            global_alpha: 1.0,
            font_size: 12.0,
            text_color: Color::WHITE,
        }
    }
}

impl<'a, F1, F2> RenderContext for SvgRenderContext<'a, F1, F2>
where
    F1: Fn(usize) -> f64,
    F2: Fn(f64) -> f64,
{
    fn chart_width(&self) -> f64 {
        self.viewport_width
    }

    fn chart_height(&self) -> f64 {
        self.viewport_height
    }

    fn bar_to_x(&self, bar: f64) -> f64 {
        // Interpolate between bar indices for sub-bar precision
        let bar_floor = bar.floor() as usize;
        let bar_ceil = bar.ceil() as usize;
        let frac = bar - bar.floor();

        let x_floor = (self.bar_to_x)(bar_floor);
        if bar_floor == bar_ceil || frac < 0.001 {
            x_floor
        } else {
            let x_ceil = (self.bar_to_x)(bar_ceil);
            x_floor + (x_ceil - x_floor) * frac
        }
    }

    fn price_to_y(&self, price: f64) -> f64 {
        (self.price_to_y)(price)
    }

    fn dpr(&self) -> f64 {
        self.dpr
    }

    fn set_stroke_color(&mut self, color: &str) {
        self.stroke_color = Color::from_css(color).unwrap_or(Color::WHITE);
    }

    fn set_stroke_width(&mut self, width: f64) {
        self.stroke_width = width;
    }

    fn set_fill_color(&mut self, color: &str) {
        self.fill_color = Color::from_css(color).unwrap_or(Color::TRANSPARENT);
    }

    fn set_line_dash(&mut self, pattern: &[f64]) {
        self.dash_pattern = pattern.to_vec();
    }

    fn begin_path(&mut self) {
        self.path_builder.clear();
    }

    fn move_to(&mut self, x: f64, y: f64) {
        self.path_builder.move_to(Point::new(x, y));
    }

    fn line_to(&mut self, x: f64, y: f64) {
        self.path_builder.line_to(Point::new(x, y));
    }

    fn close_path(&mut self) {
        self.path_builder.close();
    }

    fn stroke(&mut self) {
        let path = std::mem::take(&mut self.path_builder).build();
        let dash = if self.dash_pattern.is_empty() {
            None
        } else {
            Some(self.dash_pattern.clone())
        };
        let style = LineStyle {
            color: self.stroke_color.with_alpha(self.global_alpha),
            width: self.stroke_width,
            dash,
            ..Default::default()
        };
        self.backend.stroke_path(&path, &style);
    }

    fn fill(&mut self) {
        let path = std::mem::take(&mut self.path_builder).build();
        let style = FillStyle::Solid(self.fill_color.with_alpha(self.global_alpha));
        self.backend.fill_path(&path, &style);
    }

    fn stroke_rect(&mut self, x: f64, y: f64, w: f64, h: f64) {
        let dash = if self.dash_pattern.is_empty() {
            None
        } else {
            Some(self.dash_pattern.clone())
        };
        let style = LineStyle {
            color: self.stroke_color.with_alpha(self.global_alpha),
            width: self.stroke_width,
            dash,
            ..Default::default()
        };
        self.backend.stroke_rect(Rect::new(x, y, w, h), &style);
    }

    fn fill_rect(&mut self, x: f64, y: f64, w: f64, h: f64) {
        self.backend.fill_rect(
            Rect::new(x, y, w, h),
            self.fill_color.with_alpha(self.global_alpha),
        );
    }

    fn ellipse(&mut self, params: EllipseParams) {
        let EllipseParams { cx, cy, rx, ry, .. } = params;
        // Approximate ellipse with bezier curves
        let kappa = 0.5522847498;
        let ox = rx * kappa;
        let oy = ry * kappa;

        self.path_builder.move_to(Point::new(cx - rx, cy));
        self.path_builder.cubic_to(
            Point::new(cx - rx, cy - oy),
            Point::new(cx - ox, cy - ry),
            Point::new(cx, cy - ry),
        );
        self.path_builder.cubic_to(
            Point::new(cx + ox, cy - ry),
            Point::new(cx + rx, cy - oy),
            Point::new(cx + rx, cy),
        );
        self.path_builder.cubic_to(
            Point::new(cx + rx, cy + oy),
            Point::new(cx + ox, cy + ry),
            Point::new(cx, cy + ry),
        );
        self.path_builder.cubic_to(
            Point::new(cx - ox, cy + ry),
            Point::new(cx - rx, cy + oy),
            Point::new(cx - rx, cy),
        );
        self.path_builder.close();
    }

    fn arc(&mut self, cx: f64, cy: f64, radius: f64, start: f64, end: f64) {
        // Simple arc approximation - just add the arc endpoints
        let start_x = cx + radius * start.cos();
        let start_y = cy + radius * start.sin();
        let end_x = cx + radius * end.cos();
        let end_y = cy + radius * end.sin();

        self.path_builder.move_to(Point::new(start_x, start_y));
        // For now just line to - proper arc would need SVG arc command
        self.path_builder.line_to(Point::new(end_x, end_y));
    }

    fn quadratic_curve_to(&mut self, cpx: f64, cpy: f64, x: f64, y: f64) {
        self.path_builder
            .quad_to(Point::new(cpx, cpy), Point::new(x, y));
    }

    fn bezier_curve_to(&mut self, cp1x: f64, cp1y: f64, cp2x: f64, cp2y: f64, x: f64, y: f64) {
        self.path_builder.cubic_to(
            Point::new(cp1x, cp1y),
            Point::new(cp2x, cp2y),
            Point::new(x, y),
        );
    }

    fn set_font(&mut self, font: &str) {
        // Parse font string like "12px sans-serif"
        if let Some(size_str) = font.split("px").next() {
            if let Ok(size) = size_str.trim().parse::<f64>() {
                self.font_size = size;
            }
        }
    }

    fn set_text_align(&mut self, _align: crate::primitives::core::render::TextAlign) {
        // Store for text rendering
    }

    fn set_text_baseline(&mut self, _baseline: crate::primitives::core::render::TextBaseline) {
        // Store for text rendering
    }

    fn set_global_alpha(&mut self, alpha: f64) {
        self.global_alpha = alpha.clamp(0.0, 1.0);
    }

    fn set_line_cap(&mut self, _cap: &str) {
        // SVG supports this but we ignore for now
    }

    fn set_line_join(&mut self, _join: &str) {
        // SVG supports this but we ignore for now
    }

    fn fill_text(&mut self, text: &str, x: f64, y: f64) {
        use crate::render::engine::TextStyle;
        self.backend.text(
            text,
            Point::new(x, y),
            &TextStyle {
                font_family: "sans-serif".into(),
                font_size: self.font_size,
                font_weight: crate::render::engine::FontWeight::Normal,
                color: self.text_color.with_alpha(self.global_alpha),
                align: crate::render::engine::TextAlign::Left,
                baseline: crate::render::engine::TextBaseline::Top,
            },
        );
    }

    fn stroke_text(&mut self, _text: &str, _x: f64, _y: f64) {
        // Text stroking not commonly needed
    }

    fn measure_text(&self, text: &str) -> f64 {
        // Approximate: average char width is ~0.6 * font_size
        text.len() as f64 * self.font_size * 0.6
    }

    fn save(&mut self) {
        // Would need state stack for proper save/restore
    }

    fn restore(&mut self) {
        // Would need state stack for proper save/restore
    }

    fn clip(&mut self) {
        // SVG clipping requires different approach
    }

    fn translate(&mut self, _x: f64, _y: f64) {
        // Would need transform matrix
    }

    fn rotate(&mut self, _angle: f64) {
        // Would need transform matrix
    }

    fn scale(&mut self, _x: f64, _y: f64) {
        // Would need transform matrix
    }

    fn rect(&mut self, x: f64, y: f64, w: f64, h: f64) {
        self.path_builder.move_to(Point::new(x, y));
        self.path_builder.line_to(Point::new(x + w, y));
        self.path_builder.line_to(Point::new(x + w, y + h));
        self.path_builder.line_to(Point::new(x, y + h));
        self.path_builder.close();
    }
}

// =============================================================================
// Chart Builder - Creates ChartConfig with fluent API
// =============================================================================

/// High-level chart builder that creates ChartConfig
pub struct Chart {
    config: ChartConfig,
    bars: Vec<Bar>,
}

impl Chart {
    /// Create a new chart builder with given dimensions
    pub fn new(width: u32, height: u32) -> Self {
        Self {
            config: ChartConfig {
                width,
                height,
                dpr: 1.0,
                theme: ThemeConfig::default(),
                series: SeriesConfig::candlestick(),
                indicators: Vec::new(),
                primitives: Vec::new(),
                signals: Vec::new(),
                layout: super::config::LayoutConfig::single(),
            },
            bars: Vec::new(),
        }
    }

    /// Set device pixel ratio
    pub fn dpr(mut self, dpr: f64) -> Self {
        self.config.dpr = dpr;
        self
    }

    /// Set OHLCV bar data
    pub fn bars(mut self, bars: &[Bar]) -> Self {
        self.bars = bars.to_vec();
        self
    }

    /// Use candlestick series
    pub fn candlesticks(mut self) -> Self {
        self.config.series = SeriesConfig::candlestick();
        self
    }

    /// Use line series
    pub fn line(mut self) -> Self {
        self.config.series = SeriesConfig::line();
        self
    }

    /// Use area series
    pub fn area(mut self) -> Self {
        self.config.series = SeriesConfig::area();
        self
    }

    /// Set up/down colors
    pub fn colors(mut self, up: &str, down: &str) -> Self {
        self.config.theme.up_color = up.into();
        self.config.theme.down_color = down.into();
        self
    }

    /// Set background color
    pub fn background(mut self, color: &str) -> Self {
        self.config.theme.background = color.into();
        self
    }

    /// Enable/disable grid
    pub fn grid(mut self, show: bool) -> Self {
        self.config.theme.show_grid = show;
        self
    }

    // =========================================================================
    // Overlay Indicators
    // =========================================================================

    /// Add SMA overlay
    pub fn sma(mut self, period: usize, color: &str) -> Self {
        if self.bars.is_empty() || period == 0 {
            return self;
        }
        let values = calculate_sma(&self.bars, period);
        let id = format!("sma_{}", period);
        let mut indicator = Indicator::sma(&id, period as u32, color);
        indicator.vectors[0].values = values;
        self.config.indicators.push(indicator);
        self
    }

    /// Add EMA overlay
    pub fn ema(mut self, period: usize, color: &str) -> Self {
        if self.bars.is_empty() || period == 0 {
            return self;
        }
        let values = calculate_ema(&self.bars, period);
        let id = format!("ema_{}", period);
        let mut indicator = Indicator::ema(&id, period as u32, color);
        indicator.vectors[0].values = values;
        self.config.indicators.push(indicator);
        self
    }

    /// Add Bollinger Bands overlay
    pub fn bollinger(mut self, period: usize, multiplier: f64) -> Self {
        if self.bars.is_empty() || period == 0 {
            return self;
        }
        let (upper, middle, lower) = calculate_bollinger(&self.bars, period, multiplier);
        let id = format!("bb_{}", period);
        let mut indicator = Indicator::bollinger(&id, period as u32);
        // Bollinger has 3 vectors: upper, middle, lower
        if indicator.vectors.len() >= 3 {
            indicator.vectors[0].values = upper;
            indicator.vectors[1].values = middle;
            indicator.vectors[2].values = lower;
        }
        self.config.indicators.push(indicator);
        self
    }

    /// Add custom overlay with values
    pub fn overlay(mut self, name: &str, values: Vec<f64>, color: &str) -> Self {
        use crate::model::{IndicatorRange, IndicatorVector, VectorStyle};
        let id = format!("custom_{}", name.to_lowercase().replace(' ', "_"));
        let indicator = Indicator::new(&id, name)
            .overlay()
            .range(IndicatorRange::Auto)
            .add_vector(
                IndicatorVector::new(name, VectorStyle::line(color, 1.5)).with_values(values),
            );
        self.config.indicators.push(indicator);
        self
    }

    // =========================================================================
    // Subpane Indicators
    // =========================================================================

    /// Add RSI indicator
    pub fn rsi(mut self, period: usize) -> Self {
        if self.bars.is_empty() || period == 0 {
            return self;
        }
        let values = calculate_rsi(&self.bars, period);
        let id = format!("rsi_{}", period);
        let mut indicator = Indicator::rsi(&id, period as u32);
        indicator.vectors[0].values = values;
        self.config.indicators.push(indicator);
        self
    }

    /// Add MACD indicator
    pub fn macd(mut self, fast: usize, slow: usize, signal: usize) -> Self {
        if self.bars.is_empty() {
            return self;
        }
        let (macd_line, signal_line, histogram) = calculate_macd(&self.bars, fast, slow, signal);
        let id = format!("macd_{}_{}", fast, slow);
        let mut indicator = Indicator::macd(&id, fast as u32, slow as u32, signal as u32);
        // MACD has 3 vectors: MACD line, Signal line, Histogram
        if indicator.vectors.len() >= 3 {
            indicator.vectors[0].values = macd_line;
            indicator.vectors[1].values = signal_line;
            indicator.vectors[2].values = histogram;
        }
        self.config.indicators.push(indicator);
        self
    }

    /// Add Volume indicator
    pub fn volume(mut self) -> Self {
        if self.bars.is_empty() {
            return self;
        }
        let values: Vec<f64> = self.bars.iter().map(|b| b.volume).collect();
        let directions: Vec<bool> = self.bars.iter().map(|b| b.close >= b.open).collect();
        let mut indicator = Indicator::volume("volume");
        indicator.vectors[0].values = values;
        indicator.vectors[0].directions = directions;
        self.config.indicators.push(indicator);
        self
    }

    /// Add a pre-configured indicator
    pub fn indicator(mut self, indicator: Indicator) -> Self {
        self.config.indicators.push(indicator);
        self
    }

    // =========================================================================
    // Primitives
    // =========================================================================

    /// Add a primitive drawing
    pub fn primitive(mut self, primitive: PrimitiveConfig) -> Self {
        self.config.primitives.push(primitive);
        self
    }

    /// Add multiple primitives
    pub fn primitives(mut self, primitives: Vec<PrimitiveConfig>) -> Self {
        self.config.primitives.extend(primitives);
        self
    }

    // =========================================================================
    // Signals
    // =========================================================================

    /// Add a signal marker
    pub fn signal(mut self, signal: SignalConfig) -> Self {
        self.config.signals.push(signal);
        self
    }

    /// Add multiple signals
    pub fn signals(mut self, signals: Vec<SignalConfig>) -> Self {
        self.config.signals.extend(signals);
        self
    }

    // =========================================================================
    // Build & Render
    // =========================================================================

    /// Get the built ChartConfig
    pub fn build(self) -> (ChartConfig, Vec<Bar>) {
        (self.config, self.bars)
    }

    /// Render directly to SVG string
    pub fn render_svg(&self) -> String {
        ChartRenderer::new(&self.config, &self.bars).render_svg()
    }
}

// =============================================================================
// Indicator Calculations (same as before)
// =============================================================================

fn calculate_sma(bars: &[Bar], period: usize) -> Vec<f64> {
    let mut result = vec![f64::NAN; bars.len()];

    for i in (period - 1)..bars.len() {
        let sum: f64 = bars[i + 1 - period..=i].iter().map(|b| b.close).sum();
        result[i] = sum / period as f64;
    }

    result
}

fn calculate_ema(bars: &[Bar], period: usize) -> Vec<f64> {
    let mut result = vec![f64::NAN; bars.len()];
    let multiplier = 2.0 / (period as f64 + 1.0);

    if bars.len() >= period {
        let sum: f64 = bars[0..period].iter().map(|b| b.close).sum();
        result[period - 1] = sum / period as f64;

        for i in period..bars.len() {
            result[i] = (bars[i].close - result[i - 1]) * multiplier + result[i - 1];
        }
    }

    result
}

fn calculate_bollinger(
    bars: &[Bar],
    period: usize,
    multiplier: f64,
) -> (Vec<f64>, Vec<f64>, Vec<f64>) {
    let mut upper = vec![f64::NAN; bars.len()];
    let mut middle = vec![f64::NAN; bars.len()];
    let mut lower = vec![f64::NAN; bars.len()];

    for i in (period - 1)..bars.len() {
        let slice: Vec<f64> = bars[i + 1 - period..=i].iter().map(|b| b.close).collect();
        let mean = slice.iter().sum::<f64>() / period as f64;
        let variance = slice.iter().map(|x| (x - mean).powi(2)).sum::<f64>() / period as f64;
        let stddev = variance.sqrt();

        middle[i] = mean;
        upper[i] = mean + multiplier * stddev;
        lower[i] = mean - multiplier * stddev;
    }

    (upper, middle, lower)
}

fn calculate_rsi(bars: &[Bar], period: usize) -> Vec<f64> {
    let mut result = vec![f64::NAN; bars.len()];

    if bars.len() < period + 1 {
        return result;
    }

    let mut gains = Vec::new();
    let mut losses = Vec::new();

    for i in 1..bars.len() {
        let change = bars[i].close - bars[i - 1].close;
        if change > 0.0 {
            gains.push(change);
            losses.push(0.0);
        } else {
            gains.push(0.0);
            losses.push(-change);
        }
    }

    let first_avg_gain: f64 = gains[0..period].iter().sum::<f64>() / period as f64;
    let first_avg_loss: f64 = losses[0..period].iter().sum::<f64>() / period as f64;

    let mut avg_gain = first_avg_gain;
    let mut avg_loss = first_avg_loss;

    result[period] = if avg_loss == 0.0 {
        100.0
    } else {
        100.0 - 100.0 / (1.0 + avg_gain / avg_loss)
    };

    for i in (period + 1)..bars.len() {
        avg_gain = (avg_gain * (period as f64 - 1.0) + gains[i - 1]) / period as f64;
        avg_loss = (avg_loss * (period as f64 - 1.0) + losses[i - 1]) / period as f64;
        result[i] = if avg_loss == 0.0 {
            100.0
        } else {
            100.0 - 100.0 / (1.0 + avg_gain / avg_loss)
        };
    }

    result
}

fn calculate_macd(
    bars: &[Bar],
    fast: usize,
    slow: usize,
    signal: usize,
) -> (Vec<f64>, Vec<f64>, Vec<f64>) {
    let fast_ema = calculate_ema(bars, fast);
    let slow_ema = calculate_ema(bars, slow);

    let macd_line: Vec<f64> = fast_ema
        .iter()
        .zip(slow_ema.iter())
        .map(|(&f, &s)| {
            if f.is_nan() || s.is_nan() {
                f64::NAN
            } else {
                f - s
            }
        })
        .collect();

    let mut signal_line = vec![f64::NAN; bars.len()];
    let multiplier = 2.0 / (signal as f64 + 1.0);

    let first_valid = macd_line
        .iter()
        .position(|&v| !v.is_nan())
        .unwrap_or(bars.len());

    if first_valid + signal <= bars.len() {
        let sum: f64 = macd_line[first_valid..(first_valid + signal)]
            .iter()
            .filter(|v| !v.is_nan())
            .sum();
        signal_line[first_valid + signal - 1] = sum / signal as f64;

        for i in (first_valid + signal)..bars.len() {
            if !macd_line[i].is_nan() && !signal_line[i - 1].is_nan() {
                signal_line[i] =
                    (macd_line[i] - signal_line[i - 1]) * multiplier + signal_line[i - 1];
            }
        }
    }

    let histogram: Vec<f64> = macd_line
        .iter()
        .zip(signal_line.iter())
        .map(|(&m, &s)| {
            if m.is_nan() || s.is_nan() {
                f64::NAN
            } else {
                m - s
            }
        })
        .collect();

    (macd_line, signal_line, histogram)
}

// =============================================================================
// Tests
// =============================================================================

#[cfg(test)]
mod tests {
    use super::*;

    fn sample_bars(n: usize) -> Vec<Bar> {
        let mut bars = Vec::with_capacity(n);
        let mut price = 100.0;

        for i in 0..n {
            let change = (i as f64 * 0.5).sin() * 2.0;
            let vol = 1.0 + (i as f64 * 0.3).sin().abs();

            let open = price;
            let close = price + change;
            let high = open.max(close) + vol;
            let low = open.min(close) - vol;

            bars.push(Bar {
                timestamp: 1700000000 + (i as i64) * 3600,
                open,
                high,
                low,
                close,
                volume: 1000.0 + (i as f64 * 100.0),
            });

            price = close;
        }

        bars
    }

    #[test]
    fn test_empty_chart() {
        let svg = Chart::new(800, 600).render_svg();
        assert!(svg.contains("<svg"));
        assert!(svg.contains("No data"));
    }

    #[test]
    fn test_candlestick_chart() {
        let bars = sample_bars(50);
        let svg = Chart::new(800, 600).bars(&bars).candlesticks().render_svg();
        assert!(svg.contains("<svg"));
        assert!(svg.contains("<rect")); // candle bodies
    }

    #[test]
    fn test_chart_with_sma() {
        let bars = sample_bars(100);
        let svg = Chart::new(800, 600)
            .bars(&bars)
            .sma(20, "#2196F3")
            .render_svg();
        assert!(svg.contains("<svg"));
    }

    #[test]
    fn test_chart_with_rsi() {
        let bars = sample_bars(100);
        let svg = Chart::new(800, 600).bars(&bars).rsi(14).render_svg();
        assert!(svg.contains("<svg"));
    }

    #[test]
    fn test_full_chart() {
        let bars = sample_bars(200);
        let svg = Chart::new(1200, 800)
            .bars(&bars)
            .candlesticks()
            .sma(20, "#2196F3")
            .sma(50, "#FF9800")
            .bollinger(20, 2.0)
            .rsi(14)
            .macd(12, 26, 9)
            .render_svg();

        assert!(svg.contains("<svg"));
        assert!(svg.len() > 1000);
    }

    #[test]
    fn test_chart_renderer_from_config() {
        let bars = sample_bars(100);
        let config = ChartConfig {
            width: 800,
            height: 600,
            dpr: 1.0,
            theme: ThemeConfig::default(),
            series: SeriesConfig::candlestick(),
            indicators: vec![],
            primitives: vec![],
            signals: vec![],
            layout: super::super::config::LayoutConfig::single(),
        };

        let svg = ChartRenderer::new(&config, &bars).render_svg();
        assert!(svg.contains("<svg"));
    }

    #[test]
    fn test_chart_with_primitives() {
        let bars = sample_bars(100);
        let svg = Chart::new(800, 600)
            .bars(&bars)
            .candlesticks()
            .primitive(PrimitiveConfig::trend_line((10.0, 100.0), (50.0, 110.0)))
            .primitive(PrimitiveConfig::horizontal_line(105.0))
            .render_svg();

        assert!(svg.contains("<svg"));
    }

    #[test]
    fn test_chart_with_signals() {
        let bars = sample_bars(100);
        let svg = Chart::new(800, 600)
            .bars(&bars)
            .candlesticks()
            .signal(SignalConfig::buy(25, 100.0))
            .signal(SignalConfig::sell(75, 105.0))
            .render_svg();

        assert!(svg.contains("<svg"));
    }
}
