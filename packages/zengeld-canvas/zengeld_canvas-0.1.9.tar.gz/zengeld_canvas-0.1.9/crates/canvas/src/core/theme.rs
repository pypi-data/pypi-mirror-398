//! UI Theme - Complete theme system for chart styling
//!
//! This module provides both static (`UITheme`) and runtime (`RuntimeTheme`) theme types.
//!
//! # Architecture
//!
//! The theme controls:
//! - **UI Colors**: Toolbars, buttons, dropdowns, status bar
//! - **Chart Colors**: Background, grid, scales, crosshair, watermark
//! - **Series Colors**: Candles, line, area, histogram, baseline, bars
//! - **Fonts**: Family, sizes, weights for every element type
//! - **Sizing**: Toolbar dimensions, button sizes, spacing
//! - **Effects**: Transitions, shadows, hover effects
//!
//! # Usage
//!
//! ```rust
//! use zengeld_canvas::{UITheme, RuntimeTheme};
//!
//! // Static theme (compile-time, &'static str)
//! let dark = UITheme::dark();
//! let light = UITheme::light();
//!
//! // Runtime theme (owned String, modifiable)
//! let mut theme = RuntimeTheme::dark();
//! theme.colors.toolbar_bg = "#ff0000".to_string();
//! ```

use serde::{Deserialize, Serialize};

// =============================================================================
// Static Theme (compile-time, &'static str)
// =============================================================================

/// Complete UI theme definition - the master style controller
#[derive(Clone, Debug)]
pub struct UITheme {
    pub name: &'static str,

    /// UI Colors (toolbars, buttons, etc.)
    pub colors: UIColors,

    /// Chart-specific colors (grid, scales, background)
    pub chart: ChartColors,

    /// Series colors (candles, line, area, etc.)
    pub series: SeriesColors,

    /// Typography for all elements
    pub fonts: UIFonts,

    /// Sizing
    pub sizing: UISizing,

    /// Effects
    pub effects: UIEffects,
}

/// Color palette for UI elements
#[derive(Clone, Debug)]
pub struct UIColors {
    // Backgrounds
    pub toolbar_bg: &'static str,
    pub button_bg: &'static str,
    pub button_bg_hover: &'static str,
    pub button_bg_active: &'static str,
    pub dropdown_bg: &'static str,
    pub button_hover_stroke: &'static str,
    pub button_active_stroke: &'static str,
    pub button_rounding: f32,
    pub status_bar_bg: &'static str,

    // Text
    pub text_primary: &'static str,
    pub text_secondary: &'static str,
    pub text_muted: &'static str,

    // Borders
    pub border: &'static str,
    pub border_light: &'static str,
    pub divider: &'static str,
    pub toolbar_divider: &'static str,
    pub ui_border: &'static str,

    // Accents
    pub accent: &'static str,
    pub accent_hover: &'static str,
    pub success: &'static str,
    pub danger: &'static str,
    pub warning: &'static str,
}

/// Chart-specific colors (background, grid, scales, crosshair)
#[derive(Clone, Debug)]
pub struct ChartColors {
    // Background
    pub background: &'static str,

    // Grid
    pub grid_line: &'static str,
    pub grid_line_horz: Option<&'static str>,
    pub grid_line_vert: Option<&'static str>,

    // Price scale (right axis)
    pub scale_bg: &'static str,
    pub scale_border: &'static str,
    pub scale_text: &'static str,
    pub scale_text_muted: &'static str,

    // Time scale (bottom axis)
    pub time_scale_bg: &'static str,
    pub time_scale_border: &'static str,
    pub time_scale_text: &'static str,
    pub time_scale_text_medium: &'static str,
    pub time_scale_text_muted: &'static str,

    // Crosshair
    pub crosshair_line: &'static str,
    pub crosshair_label_bg: &'static str,
    pub crosshair_label_text: &'static str,

    // Legend (OHLC display)
    pub legend_text: &'static str,
    pub legend_value_up: &'static str,
    pub legend_value_down: &'static str,

    // Watermark
    pub watermark_text: &'static str,

    // Sidebar panels
    pub sidebar_bg: &'static str,
    pub sidebar_border: &'static str,
    pub sidebar_header_bg: &'static str,
    pub sidebar_text: &'static str,

    // Chart frame borders
    pub chart_border: &'static str,
    pub frame_border: &'static str,
}

/// Series/data visualization colors
#[derive(Clone, Debug)]
pub struct SeriesColors {
    // Candlestick
    pub candle_up_body: &'static str,
    pub candle_up_wick: &'static str,
    pub candle_up_border: Option<&'static str>,
    pub candle_down_body: &'static str,
    pub candle_down_wick: &'static str,
    pub candle_down_border: Option<&'static str>,

    // Line series
    pub line_color: &'static str,
    pub line_width: f64,

    // Area series
    pub area_line: &'static str,
    pub area_top: &'static str,
    pub area_bottom: &'static str,

    // Histogram
    pub histogram_positive: &'static str,
    pub histogram_negative: &'static str,

    // Baseline
    pub baseline_top_line: &'static str,
    pub baseline_top_fill: &'static str,
    pub baseline_bottom_line: &'static str,
    pub baseline_bottom_fill: &'static str,
    pub baseline_line: &'static str,

    // Bar series (OHLC bars)
    pub bar_up: &'static str,
    pub bar_down: &'static str,

    // Moving averages
    pub ma_fast: &'static str,
    pub ma_slow: &'static str,
    pub ma_third: &'static str,

    // Volume
    pub volume_up: &'static str,
    pub volume_down: &'static str,
}

/// Font settings
#[derive(Clone, Debug)]
pub struct UIFonts {
    // Font families
    pub family: &'static str,
    pub family_mono: &'static str,
    pub family_chart: &'static str,

    // Base sizes
    pub size_small: f64,
    pub size_normal: f64,
    pub size_large: f64,

    // Weights
    pub weight_light: u16,
    pub weight_normal: u16,
    pub weight_medium: u16,
    pub weight_bold: u16,

    // Scale-specific font settings
    pub price_scale_size_min: f64,
    pub price_scale_size_max: f64,
    pub price_scale_weight: u16,

    pub time_scale_size: f64,
    pub time_scale_weight: u16,

    // Legend font
    pub legend_size: f64,
    pub legend_weight: u16,

    // Crosshair label font
    pub crosshair_label_size: f64,
    pub crosshair_label_weight: u16,

    // Watermark font
    pub watermark_size: f64,
    pub watermark_weight: u16,

    // Status bar font
    pub status_bar_size: f64,
    pub status_bar_weight: u16,
}

/// Size settings
#[derive(Clone, Debug)]
pub struct UISizing {
    // Toolbar dimensions
    pub top_toolbar_height: f32,
    pub left_toolbar_width: f32,

    // Button sizing
    pub button_height: f32,
    pub button_padding_x: f32,
    pub button_padding_y: f32,

    // Other
    pub border_radius: f32,
    pub dropdown_min_width: f32,
    pub kbd_padding: f32,
}

/// Visual effects
#[derive(Clone, Debug)]
pub struct UIEffects {
    pub transition_duration: &'static str,
    pub shadow_dropdown: &'static str,
    pub shadow_floating: &'static str,
    pub hover_scale: f64,
}

impl Default for UITheme {
    fn default() -> Self {
        Self::dark()
    }
}

impl UITheme {
    /// Dark theme (TradingView-like)
    pub fn dark() -> Self {
        Self {
            name: "Dark",
            colors: UIColors {
                toolbar_bg: "#131722",
                button_bg: "#1e222d",
                button_bg_hover: "#2a2e39",
                button_bg_active: "#2962ff",
                button_hover_stroke: "transparent",
                button_active_stroke: "transparent",
                button_rounding: 4.0,
                dropdown_bg: "#1e222d",
                status_bar_bg: "#131722",

                text_primary: "#d1d4dc",
                text_secondary: "#b2b5be",
                text_muted: "#787b86",

                border: "#131722",
                border_light: "#2a2e39",
                divider: "#363a45",
                toolbar_divider: "#363a45",
                ui_border: "#363a45",

                accent: "#2962ff",
                accent_hover: "#1e53e4",
                success: "#26a69a",
                danger: "#f23645",
                warning: "#ff9800",
            },
            chart: ChartColors {
                background: "#131722",

                grid_line: "#2a2e3999",
                grid_line_horz: None,
                grid_line_vert: None,

                scale_bg: "#1e222d",
                scale_border: "#2a2e39",
                scale_text: "#b2b5be",
                scale_text_muted: "#787b86",

                time_scale_bg: "#1e222d",
                time_scale_border: "#2a2e39",
                time_scale_text: "#b2b5be",
                time_scale_text_medium: "#9598a1",
                time_scale_text_muted: "#787b86",

                crosshair_line: "#758696",
                crosshair_label_bg: "#363a45",
                crosshair_label_text: "#d1d4dc",

                legend_text: "#b2b5be",
                legend_value_up: "#26a69a",
                legend_value_down: "#ef5350",

                watermark_text: "rgba(120, 123, 134, 0.3)",

                sidebar_bg: "#1e222d",
                sidebar_border: "#363a45",
                sidebar_header_bg: "#131722",
                sidebar_text: "#b2b5be",

                chart_border: "#363a45",
                frame_border: "#2a2e39",
            },
            series: SeriesColors {
                candle_up_body: "#26a69a",
                candle_up_wick: "#26a69a",
                candle_up_border: None,
                candle_down_body: "#ef5350",
                candle_down_wick: "#ef5350",
                candle_down_border: None,

                line_color: "#2962ff",
                line_width: 2.0,

                area_line: "#2962ff",
                area_top: "rgba(41, 98, 255, 0.28)",
                area_bottom: "rgba(41, 98, 255, 0.05)",

                histogram_positive: "#26a69a",
                histogram_negative: "#ef5350",

                baseline_top_line: "#26a69a",
                baseline_top_fill: "rgba(38, 166, 154, 0.28)",
                baseline_bottom_line: "#ef5350",
                baseline_bottom_fill: "rgba(239, 83, 80, 0.28)",
                baseline_line: "#758696",

                bar_up: "#26a69a",
                bar_down: "#ef5350",

                ma_fast: "#2962ff",
                ma_slow: "#ff6d00",
                ma_third: "#e040fb",

                volume_up: "rgba(38, 166, 154, 0.5)",
                volume_down: "rgba(239, 83, 80, 0.5)",
            },
            fonts: UIFonts {
                family: "-apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif",
                family_mono: "'Share Tech Mono', 'Consolas', monospace",
                family_chart: "'Trebuchet MS', Arial, sans-serif",

                size_small: 11.0,
                size_normal: 13.0,
                size_large: 14.0,

                weight_light: 300,
                weight_normal: 400,
                weight_medium: 500,
                weight_bold: 600,

                price_scale_size_min: 9.0,
                price_scale_size_max: 13.0,
                price_scale_weight: 400,

                time_scale_size: 12.0,
                time_scale_weight: 400,

                legend_size: 12.0,
                legend_weight: 500,

                crosshair_label_size: 11.0,
                crosshair_label_weight: 400,

                watermark_size: 52.0,
                watermark_weight: 700,

                status_bar_size: 11.0,
                status_bar_weight: 400,
            },
            sizing: UISizing {
                top_toolbar_height: 40.0,
                left_toolbar_width: 50.0,
                button_height: 28.0,
                button_padding_x: 12.0,
                button_padding_y: 6.0,
                border_radius: 4.0,
                dropdown_min_width: 160.0,
                kbd_padding: 4.0,
            },
            effects: UIEffects {
                transition_duration: "0.15s",
                shadow_dropdown: "0 8px 24px rgba(0,0,0,0.4)",
                shadow_floating: "0 4px 12px rgba(0,0,0,0.3)",
                hover_scale: 0.97,
            },
        }
    }

    /// Light theme
    pub fn light() -> Self {
        Self {
            name: "Light",
            colors: UIColors {
                toolbar_bg: "#f8f9fa",
                button_bg: "#e9ecef",
                button_bg_hover: "#dee2e6",
                button_bg_active: "#2962ff",
                button_hover_stroke: "transparent",
                button_active_stroke: "transparent",
                button_rounding: 4.0,
                dropdown_bg: "#ffffff",
                status_bar_bg: "#f8f9fa",

                text_primary: "#131722",
                text_secondary: "#434651",
                text_muted: "#787b86",

                border: "#f8f9fa",
                border_light: "#e9ecef",
                divider: "#dee2e6",
                toolbar_divider: "#dee2e6",
                ui_border: "#dee2e6",

                accent: "#2962ff",
                accent_hover: "#1e53e4",
                success: "#26a69a",
                danger: "#f23645",
                warning: "#ff9800",
            },
            chart: ChartColors {
                background: "#ffffff",

                grid_line: "#0000000f",
                grid_line_horz: None,
                grid_line_vert: None,

                scale_bg: "#f8f9fa",
                scale_border: "#dee2e6",
                scale_text: "#434651",
                scale_text_muted: "#787b86",

                time_scale_bg: "#f8f9fa",
                time_scale_border: "#dee2e6",
                time_scale_text: "#434651",
                time_scale_text_medium: "#5d606b",
                time_scale_text_muted: "#787b86",

                crosshair_line: "#9598a1",
                crosshair_label_bg: "#131722",
                crosshair_label_text: "#ffffff",

                legend_text: "#434651",
                legend_value_up: "#26a69a",
                legend_value_down: "#ef5350",

                watermark_text: "rgba(0, 0, 0, 0.06)",

                sidebar_bg: "#f8f9fa",
                sidebar_border: "#dee2e6",
                sidebar_header_bg: "#e9ecef",
                sidebar_text: "#434651",

                chart_border: "#dee2e6",
                frame_border: "#ced4da",
            },
            series: SeriesColors {
                candle_up_body: "#26a69a",
                candle_up_wick: "#26a69a",
                candle_up_border: None,
                candle_down_body: "#ef5350",
                candle_down_wick: "#ef5350",
                candle_down_border: None,

                line_color: "#2962ff",
                line_width: 2.0,

                area_line: "#2962ff",
                area_top: "rgba(41, 98, 255, 0.28)",
                area_bottom: "rgba(41, 98, 255, 0.05)",

                histogram_positive: "#26a69a",
                histogram_negative: "#ef5350",

                baseline_top_line: "#26a69a",
                baseline_top_fill: "rgba(38, 166, 154, 0.28)",
                baseline_bottom_line: "#ef5350",
                baseline_bottom_fill: "rgba(239, 83, 80, 0.28)",
                baseline_line: "#9598a1",

                bar_up: "#26a69a",
                bar_down: "#ef5350",

                ma_fast: "#2962ff",
                ma_slow: "#ff6d00",
                ma_third: "#e040fb",

                volume_up: "rgba(38, 166, 154, 0.5)",
                volume_down: "rgba(239, 83, 80, 0.5)",
            },
            fonts: UIFonts {
                family: "-apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif",
                family_mono: "'Share Tech Mono', 'Consolas', monospace",
                family_chart: "'Trebuchet MS', Arial, sans-serif",

                size_small: 11.0,
                size_normal: 12.0,
                size_large: 14.0,

                weight_light: 300,
                weight_normal: 400,
                weight_medium: 500,
                weight_bold: 600,

                price_scale_size_min: 9.0,
                price_scale_size_max: 13.0,
                price_scale_weight: 400,

                time_scale_size: 12.0,
                time_scale_weight: 400,

                legend_size: 12.0,
                legend_weight: 500,

                crosshair_label_size: 11.0,
                crosshair_label_weight: 400,

                watermark_size: 52.0,
                watermark_weight: 700,

                status_bar_size: 11.0,
                status_bar_weight: 400,
            },
            sizing: UISizing {
                top_toolbar_height: 44.0,
                left_toolbar_width: 48.0,
                button_height: 28.0,
                button_padding_x: 12.0,
                button_padding_y: 6.0,
                border_radius: 4.0,
                dropdown_min_width: 160.0,
                kbd_padding: 4.0,
            },
            effects: UIEffects {
                transition_duration: "0.15s",
                shadow_dropdown: "0 8px 24px rgba(0,0,0,0.15)",
                shadow_floating: "0 4px 12px rgba(0,0,0,0.1)",
                hover_scale: 0.97,
            },
        }
    }

    /// High contrast theme (accessibility)
    pub fn high_contrast() -> Self {
        Self {
            name: "High Contrast",
            colors: UIColors {
                toolbar_bg: "#000000",
                button_bg: "#1a1a1a",
                button_bg_hover: "#333333",
                button_bg_active: "#0066ff",
                button_hover_stroke: "transparent",
                button_active_stroke: "transparent",
                button_rounding: 4.0,
                dropdown_bg: "#000000",
                status_bar_bg: "#000000",

                text_primary: "#ffffff",
                text_secondary: "#cccccc",
                text_muted: "#999999",

                border: "#000000",
                border_light: "#666666",
                divider: "#ffffff",
                toolbar_divider: "#ffffff",
                ui_border: "#ffffff",

                accent: "#0066ff",
                accent_hover: "#0055dd",
                success: "#00ff00",
                danger: "#ff0000",
                warning: "#ffff00",
            },
            chart: ChartColors {
                background: "#000000",

                grid_line: "#333333",
                grid_line_horz: None,
                grid_line_vert: None,

                scale_bg: "#000000",
                scale_border: "#ffffff",
                scale_text: "#ffffff",
                scale_text_muted: "#cccccc",

                time_scale_bg: "#000000",
                time_scale_border: "#ffffff",
                time_scale_text: "#ffffff",
                time_scale_text_medium: "#dddddd",
                time_scale_text_muted: "#cccccc",

                crosshair_line: "#ffffff",
                crosshair_label_bg: "#0066ff",
                crosshair_label_text: "#ffffff",

                legend_text: "#ffffff",
                legend_value_up: "#00ff00",
                legend_value_down: "#ff0000",

                watermark_text: "rgba(255, 255, 255, 0.1)",

                sidebar_bg: "#000000",
                sidebar_border: "#ffffff",
                sidebar_header_bg: "#1a1a1a",
                sidebar_text: "#ffffff",

                chart_border: "#ffffff",
                frame_border: "#808080",
            },
            series: SeriesColors {
                candle_up_body: "#00ff00",
                candle_up_wick: "#00ff00",
                candle_up_border: None,
                candle_down_body: "#ff0000",
                candle_down_wick: "#ff0000",
                candle_down_border: None,

                line_color: "#0066ff",
                line_width: 2.0,

                area_line: "#0066ff",
                area_top: "rgba(0, 102, 255, 0.4)",
                area_bottom: "rgba(0, 102, 255, 0.1)",

                histogram_positive: "#00ff00",
                histogram_negative: "#ff0000",

                baseline_top_line: "#00ff00",
                baseline_top_fill: "rgba(0, 255, 0, 0.3)",
                baseline_bottom_line: "#ff0000",
                baseline_bottom_fill: "rgba(255, 0, 0, 0.3)",
                baseline_line: "#ffffff",

                bar_up: "#00ff00",
                bar_down: "#ff0000",

                ma_fast: "#0066ff",
                ma_slow: "#ffff00",
                ma_third: "#ff00ff",

                volume_up: "rgba(0, 255, 0, 0.5)",
                volume_down: "rgba(255, 0, 0, 0.5)",
            },
            fonts: UIFonts {
                family: "-apple-system, sans-serif",
                family_mono: "'Consolas', monospace",
                family_chart: "Arial, sans-serif",

                size_small: 12.0,
                size_normal: 14.0,
                size_large: 16.0,

                weight_light: 400,
                weight_normal: 400,
                weight_medium: 600,
                weight_bold: 700,

                price_scale_size_min: 11.0,
                price_scale_size_max: 14.0,
                price_scale_weight: 600,

                time_scale_size: 13.0,
                time_scale_weight: 600,

                legend_size: 14.0,
                legend_weight: 600,

                crosshair_label_size: 12.0,
                crosshair_label_weight: 600,

                watermark_size: 60.0,
                watermark_weight: 700,

                status_bar_size: 12.0,
                status_bar_weight: 600,
            },
            sizing: UISizing {
                top_toolbar_height: 48.0,
                left_toolbar_width: 56.0,
                button_height: 32.0,
                button_padding_x: 14.0,
                button_padding_y: 8.0,
                border_radius: 2.0,
                dropdown_min_width: 180.0,
                kbd_padding: 5.0,
            },
            effects: UIEffects {
                transition_duration: "0s",
                shadow_dropdown: "none",
                shadow_floating: "none",
                hover_scale: 1.0,
            },
        }
    }

    /// Cyberpunk/neon theme
    pub fn cyberpunk() -> Self {
        Self {
            name: "Cyberpunk",
            colors: UIColors {
                toolbar_bg: "#0a0a0f",
                button_bg: "#1a1a2e",
                button_bg_hover: "#16213e",
                button_bg_active: "#e94560",
                button_hover_stroke: "transparent",
                button_active_stroke: "transparent",
                button_rounding: 4.0,
                dropdown_bg: "#0f0f1a",
                status_bar_bg: "#0a0a0f",

                text_primary: "#eaeaea",
                text_secondary: "#a0a0a0",
                text_muted: "#606060",

                border: "#0a0a0f",
                border_light: "#533483",
                divider: "#e94560",
                toolbar_divider: "#e94560",
                ui_border: "#e94560",

                accent: "#e94560",
                accent_hover: "#ff6b6b",
                success: "#0f3460",
                danger: "#e94560",
                warning: "#f9ed69",
            },
            chart: ChartColors {
                background: "#0a0a0f",

                grid_line: "#e9456026",
                grid_line_horz: None,
                grid_line_vert: None,

                scale_bg: "#0f0f1a",
                scale_border: "#533483",
                scale_text: "#00fff5",
                scale_text_muted: "#606060",

                time_scale_bg: "#0f0f1a",
                time_scale_border: "#533483",
                time_scale_text: "#00fff5",
                time_scale_text_medium: "#a0a0a0",
                time_scale_text_muted: "#606060",

                crosshair_line: "#e94560",
                crosshair_label_bg: "#e94560",
                crosshair_label_text: "#0a0a0f",

                legend_text: "#eaeaea",
                legend_value_up: "#00fff5",
                legend_value_down: "#e94560",

                watermark_text: "rgba(233, 69, 96, 0.1)",

                sidebar_bg: "#0f0f1a",
                sidebar_border: "#e94560",
                sidebar_header_bg: "#0a0a0f",
                sidebar_text: "#eaeaea",

                chart_border: "#e94560",
                frame_border: "#1a1a2e",
            },
            series: SeriesColors {
                candle_up_body: "#00fff5",
                candle_up_wick: "#00fff5",
                candle_up_border: None,
                candle_down_body: "#e94560",
                candle_down_wick: "#e94560",
                candle_down_border: None,

                line_color: "#00fff5",
                line_width: 2.0,

                area_line: "#00fff5",
                area_top: "rgba(0, 255, 245, 0.28)",
                area_bottom: "rgba(0, 255, 245, 0.05)",

                histogram_positive: "#00fff5",
                histogram_negative: "#e94560",

                baseline_top_line: "#00fff5",
                baseline_top_fill: "rgba(0, 255, 245, 0.28)",
                baseline_bottom_line: "#e94560",
                baseline_bottom_fill: "rgba(233, 69, 96, 0.28)",
                baseline_line: "#533483",

                bar_up: "#00fff5",
                bar_down: "#e94560",

                ma_fast: "#00fff5",
                ma_slow: "#f9ed69",
                ma_third: "#e94560",

                volume_up: "rgba(0, 255, 245, 0.5)",
                volume_down: "rgba(233, 69, 96, 0.5)",
            },
            fonts: UIFonts {
                family: "'Share Tech Mono', 'Orbitron', monospace",
                family_mono: "'Share Tech Mono', monospace",
                family_chart: "'Share Tech Mono', monospace",

                size_small: 10.0,
                size_normal: 11.0,
                size_large: 13.0,

                weight_light: 400,
                weight_normal: 400,
                weight_medium: 400,
                weight_bold: 400,

                price_scale_size_min: 9.0,
                price_scale_size_max: 12.0,
                price_scale_weight: 400,

                time_scale_size: 11.0,
                time_scale_weight: 400,

                legend_size: 11.0,
                legend_weight: 400,

                crosshair_label_size: 10.0,
                crosshair_label_weight: 400,

                watermark_size: 48.0,
                watermark_weight: 400,

                status_bar_size: 10.0,
                status_bar_weight: 400,
            },
            sizing: UISizing {
                top_toolbar_height: 40.0,
                left_toolbar_width: 44.0,
                button_height: 26.0,
                button_padding_x: 10.0,
                button_padding_y: 5.0,
                border_radius: 0.0,
                dropdown_min_width: 150.0,
                kbd_padding: 3.0,
            },
            effects: UIEffects {
                transition_duration: "0.1s",
                shadow_dropdown: "0 0 20px rgba(233,69,96,0.3)",
                shadow_floating: "0 0 15px rgba(233,69,96,0.2)",
                hover_scale: 1.02,
            },
        }
    }

    // =========================================================================
    // Helper methods
    // =========================================================================

    /// Get the price scale font string for canvas/egui
    pub fn price_scale_font(&self, size: f64) -> String {
        format!("{}px {}", size as i32, self.fonts.family_chart)
    }

    /// Get the time scale font string
    pub fn time_scale_font(&self) -> String {
        format!(
            "{}px {}",
            self.fonts.time_scale_size as i32, self.fonts.family_chart
        )
    }

    /// Get the legend font string
    pub fn legend_font(&self) -> String {
        format!("{}px {}", self.fonts.legend_size as i32, self.fonts.family)
    }

    /// Get crosshair label font string
    pub fn crosshair_font(&self) -> String {
        format!(
            "{}px {}",
            self.fonts.crosshair_label_size as i32, self.fonts.family_chart
        )
    }

    /// Get candle up color (body)
    pub fn candle_up(&self) -> &str {
        self.series.candle_up_body
    }

    /// Get candle down color (body)
    pub fn candle_down(&self) -> &str {
        self.series.candle_down_body
    }

    /// Get grid line color (with optional directional override)
    pub fn grid_color(&self, horizontal: bool) -> &str {
        if horizontal {
            self.chart.grid_line_horz.unwrap_or(self.chart.grid_line)
        } else {
            self.chart.grid_line_vert.unwrap_or(self.chart.grid_line)
        }
    }
}

// =============================================================================
// Runtime Theme (dynamic, owned String values)
// =============================================================================

/// Runtime-modifiable theme with owned String values
#[derive(Clone, Debug, Serialize, Deserialize)]
pub struct RuntimeTheme {
    pub name: String,
    pub colors: RuntimeUIColors,
    pub chart: RuntimeChartColors,
    pub series: RuntimeSeriesColors,
    pub fonts: RuntimeFonts,
    pub sizing: RuntimeSizing,
    pub effects: RuntimeEffects,
}

/// UI element colors (owned)
#[derive(Clone, Debug, Serialize, Deserialize)]
pub struct RuntimeUIColors {
    pub toolbar_bg: String,
    pub button_bg: String,
    pub button_bg_hover: String,
    pub button_bg_active: String,
    pub dropdown_bg: String,
    pub button_hover_stroke: String,
    pub button_active_stroke: String,
    pub button_rounding: f32,
    pub status_bar_bg: String,

    pub text_primary: String,
    pub text_secondary: String,
    pub text_muted: String,

    pub border: String,
    pub border_light: String,
    pub divider: String,
    pub toolbar_divider: String,
    pub ui_border: String,

    pub accent: String,
    pub accent_hover: String,
    pub success: String,
    pub danger: String,
    pub warning: String,
}

/// Chart-specific colors (owned)
#[derive(Clone, Debug, Serialize, Deserialize)]
pub struct RuntimeChartColors {
    pub background: String,

    pub grid_line: String,
    #[serde(skip_serializing_if = "Option::is_none")]
    pub grid_line_horz: Option<String>,
    #[serde(skip_serializing_if = "Option::is_none")]
    pub grid_line_vert: Option<String>,

    pub scale_bg: String,
    pub scale_border: String,
    pub scale_text: String,
    pub scale_text_muted: String,

    pub time_scale_bg: String,
    pub time_scale_border: String,
    pub time_scale_text: String,
    pub time_scale_text_medium: String,
    pub time_scale_text_muted: String,

    pub crosshair_line: String,
    pub crosshair_label_bg: String,
    pub crosshair_label_text: String,

    pub legend_text: String,
    pub legend_value_up: String,
    pub legend_value_down: String,

    pub watermark_text: String,

    pub sidebar_bg: String,
    pub sidebar_border: String,
    pub sidebar_header_bg: String,
    pub sidebar_text: String,

    pub chart_border: String,
    pub frame_border: String,
}

/// Series/data visualization colors (owned)
#[derive(Clone, Debug, Serialize, Deserialize)]
pub struct RuntimeSeriesColors {
    pub candle_up_body: String,
    pub candle_up_wick: String,
    #[serde(skip_serializing_if = "Option::is_none")]
    pub candle_up_border: Option<String>,
    pub candle_down_body: String,
    pub candle_down_wick: String,
    #[serde(skip_serializing_if = "Option::is_none")]
    pub candle_down_border: Option<String>,

    pub line_color: String,
    pub line_width: f64,

    pub area_line: String,
    pub area_top: String,
    pub area_bottom: String,

    pub histogram_positive: String,
    pub histogram_negative: String,

    pub baseline_top_line: String,
    pub baseline_top_fill: String,
    pub baseline_bottom_line: String,
    pub baseline_bottom_fill: String,
    pub baseline_line: String,

    pub bar_up: String,
    pub bar_down: String,

    pub ma_fast: String,
    pub ma_slow: String,
    pub ma_third: String,

    pub volume_up: String,
    pub volume_down: String,
}

/// Font settings (owned)
#[derive(Clone, Debug, Serialize, Deserialize)]
pub struct RuntimeFonts {
    pub family: String,
    pub family_mono: String,
    pub family_chart: String,

    pub size_small: f64,
    pub size_normal: f64,
    pub size_large: f64,

    pub weight_light: u16,
    pub weight_normal: u16,
    pub weight_medium: u16,
    pub weight_bold: u16,

    pub price_scale_size_min: f64,
    pub price_scale_size_max: f64,
    pub price_scale_weight: u16,

    pub time_scale_size: f64,
    pub time_scale_weight: u16,

    pub legend_size: f64,
    pub legend_weight: u16,

    pub crosshair_label_size: f64,
    pub crosshair_label_weight: u16,

    pub watermark_size: f64,
    pub watermark_weight: u16,

    pub status_bar_size: f64,
    pub status_bar_weight: u16,
}

/// Sizing settings (owned)
#[derive(Clone, Debug, Serialize, Deserialize)]
pub struct RuntimeSizing {
    pub top_toolbar_height: f32,
    pub left_toolbar_width: f32,
    pub right_toolbar_width: f32,
    pub bottom_toolbar_height: f32,

    pub button_height: f32,
    pub button_padding_x: f32,
    pub button_padding_y: f32,

    pub border_radius: f32,
    pub dropdown_min_width: f32,
}

/// Visual effects (owned)
#[derive(Clone, Debug, Serialize, Deserialize)]
pub struct RuntimeEffects {
    pub transition_duration: String,
    pub shadow_dropdown: String,
    pub shadow_floating: String,
    pub hover_scale: f64,
}

// =============================================================================
// Conversions: UITheme -> RuntimeTheme
// =============================================================================

impl From<&UITheme> for RuntimeTheme {
    fn from(theme: &UITheme) -> Self {
        Self {
            name: theme.name.to_string(),
            colors: RuntimeUIColors {
                toolbar_bg: theme.colors.toolbar_bg.to_string(),
                button_bg: theme.colors.button_bg.to_string(),
                button_bg_hover: theme.colors.button_bg_hover.to_string(),
                button_bg_active: theme.colors.button_bg_active.to_string(),
                button_hover_stroke: theme.colors.button_hover_stroke.to_string(),
                button_active_stroke: theme.colors.button_active_stroke.to_string(),
                button_rounding: theme.colors.button_rounding,
                dropdown_bg: theme.colors.dropdown_bg.to_string(),
                status_bar_bg: theme.colors.status_bar_bg.to_string(),
                text_primary: theme.colors.text_primary.to_string(),
                text_secondary: theme.colors.text_secondary.to_string(),
                text_muted: theme.colors.text_muted.to_string(),
                border: theme.colors.border.to_string(),
                border_light: theme.colors.border_light.to_string(),
                divider: theme.colors.divider.to_string(),
                toolbar_divider: theme.colors.toolbar_divider.to_string(),
                ui_border: theme.colors.ui_border.to_string(),
                accent: theme.colors.accent.to_string(),
                accent_hover: theme.colors.accent_hover.to_string(),
                success: theme.colors.success.to_string(),
                danger: theme.colors.danger.to_string(),
                warning: theme.colors.warning.to_string(),
            },
            chart: RuntimeChartColors {
                background: theme.chart.background.to_string(),
                grid_line: theme.chart.grid_line.to_string(),
                grid_line_horz: theme.chart.grid_line_horz.map(|s| s.to_string()),
                grid_line_vert: theme.chart.grid_line_vert.map(|s| s.to_string()),
                scale_bg: theme.chart.scale_bg.to_string(),
                scale_border: theme.chart.scale_border.to_string(),
                scale_text: theme.chart.scale_text.to_string(),
                scale_text_muted: theme.chart.scale_text_muted.to_string(),
                time_scale_bg: theme.chart.time_scale_bg.to_string(),
                time_scale_border: theme.chart.time_scale_border.to_string(),
                time_scale_text: theme.chart.time_scale_text.to_string(),
                time_scale_text_medium: theme.chart.time_scale_text_medium.to_string(),
                time_scale_text_muted: theme.chart.time_scale_text_muted.to_string(),
                crosshair_line: theme.chart.crosshair_line.to_string(),
                crosshair_label_bg: theme.chart.crosshair_label_bg.to_string(),
                crosshair_label_text: theme.chart.crosshair_label_text.to_string(),
                legend_text: theme.chart.legend_text.to_string(),
                legend_value_up: theme.chart.legend_value_up.to_string(),
                legend_value_down: theme.chart.legend_value_down.to_string(),
                watermark_text: theme.chart.watermark_text.to_string(),
                sidebar_bg: theme.chart.sidebar_bg.to_string(),
                sidebar_border: theme.chart.sidebar_border.to_string(),
                sidebar_header_bg: theme.chart.sidebar_header_bg.to_string(),
                sidebar_text: theme.chart.sidebar_text.to_string(),
                chart_border: theme.chart.chart_border.to_string(),
                frame_border: theme.chart.frame_border.to_string(),
            },
            series: RuntimeSeriesColors {
                candle_up_body: theme.series.candle_up_body.to_string(),
                candle_up_wick: theme.series.candle_up_wick.to_string(),
                candle_up_border: theme.series.candle_up_border.map(|s| s.to_string()),
                candle_down_body: theme.series.candle_down_body.to_string(),
                candle_down_wick: theme.series.candle_down_wick.to_string(),
                candle_down_border: theme.series.candle_down_border.map(|s| s.to_string()),
                line_color: theme.series.line_color.to_string(),
                line_width: theme.series.line_width,
                area_line: theme.series.area_line.to_string(),
                area_top: theme.series.area_top.to_string(),
                area_bottom: theme.series.area_bottom.to_string(),
                histogram_positive: theme.series.histogram_positive.to_string(),
                histogram_negative: theme.series.histogram_negative.to_string(),
                baseline_top_line: theme.series.baseline_top_line.to_string(),
                baseline_top_fill: theme.series.baseline_top_fill.to_string(),
                baseline_bottom_line: theme.series.baseline_bottom_line.to_string(),
                baseline_bottom_fill: theme.series.baseline_bottom_fill.to_string(),
                baseline_line: theme.series.baseline_line.to_string(),
                bar_up: theme.series.bar_up.to_string(),
                bar_down: theme.series.bar_down.to_string(),
                ma_fast: theme.series.ma_fast.to_string(),
                ma_slow: theme.series.ma_slow.to_string(),
                ma_third: theme.series.ma_third.to_string(),
                volume_up: theme.series.volume_up.to_string(),
                volume_down: theme.series.volume_down.to_string(),
            },
            fonts: RuntimeFonts {
                family: theme.fonts.family.to_string(),
                family_mono: theme.fonts.family_mono.to_string(),
                family_chart: theme.fonts.family_chart.to_string(),
                size_small: theme.fonts.size_small,
                size_normal: theme.fonts.size_normal,
                size_large: theme.fonts.size_large,
                weight_light: theme.fonts.weight_light,
                weight_normal: theme.fonts.weight_normal,
                weight_medium: theme.fonts.weight_medium,
                weight_bold: theme.fonts.weight_bold,
                price_scale_size_min: theme.fonts.price_scale_size_min,
                price_scale_size_max: theme.fonts.price_scale_size_max,
                price_scale_weight: theme.fonts.price_scale_weight,
                time_scale_size: theme.fonts.time_scale_size,
                time_scale_weight: theme.fonts.time_scale_weight,
                legend_size: theme.fonts.legend_size,
                legend_weight: theme.fonts.legend_weight,
                crosshair_label_size: theme.fonts.crosshair_label_size,
                crosshair_label_weight: theme.fonts.crosshair_label_weight,
                watermark_size: theme.fonts.watermark_size,
                watermark_weight: theme.fonts.watermark_weight,
                status_bar_size: theme.fonts.status_bar_size,
                status_bar_weight: theme.fonts.status_bar_weight,
            },
            sizing: RuntimeSizing {
                top_toolbar_height: theme.sizing.top_toolbar_height,
                left_toolbar_width: theme.sizing.left_toolbar_width,
                right_toolbar_width: 48.0,
                bottom_toolbar_height: 32.0,
                button_height: theme.sizing.button_height,
                button_padding_x: theme.sizing.button_padding_x,
                button_padding_y: theme.sizing.button_padding_y,
                border_radius: theme.sizing.border_radius,
                dropdown_min_width: theme.sizing.dropdown_min_width,
            },
            effects: RuntimeEffects {
                transition_duration: theme.effects.transition_duration.to_string(),
                shadow_dropdown: theme.effects.shadow_dropdown.to_string(),
                shadow_floating: theme.effects.shadow_floating.to_string(),
                hover_scale: theme.effects.hover_scale,
            },
        }
    }
}

impl RuntimeTheme {
    /// Available preset names
    pub const PRESETS: &'static [&'static str] = &["dark", "light", "high_contrast", "cyberpunk"];

    /// Create from a preset name
    pub fn from_preset(name: &str) -> Self {
        match name {
            "dark" => Self::from(&UITheme::dark()),
            "light" => Self::from(&UITheme::light()),
            "high_contrast" => Self::from(&UITheme::high_contrast()),
            "cyberpunk" => Self::from(&UITheme::cyberpunk()),
            _ => Self::from(&UITheme::dark()),
        }
    }

    /// Create default (dark) theme
    pub fn dark() -> Self {
        Self::from_preset("dark")
    }

    /// Create light theme
    pub fn light() -> Self {
        Self::from_preset("light")
    }

    /// Create high contrast theme
    pub fn high_contrast() -> Self {
        Self::from_preset("high_contrast")
    }

    /// Create cyberpunk theme
    pub fn cyberpunk() -> Self {
        Self::from_preset("cyberpunk")
    }

    // === JSON Serialization ===

    /// Serialize to JSON string
    pub fn to_json(&self) -> String {
        serde_json::to_string(self).unwrap_or_default()
    }

    /// Serialize to pretty JSON string
    pub fn to_json_pretty(&self) -> String {
        serde_json::to_string_pretty(self).unwrap_or_default()
    }

    /// Deserialize from JSON string
    pub fn from_json(json: &str) -> Option<Self> {
        serde_json::from_str(json).ok()
    }

    // === Helper methods ===

    /// Get price scale font string
    pub fn price_scale_font(&self, size: f64) -> String {
        format!("{}px {}", size as i32, self.fonts.family_chart)
    }

    /// Get time scale font string
    pub fn time_scale_font(&self) -> String {
        format!(
            "{}px {}",
            self.fonts.time_scale_size as i32, self.fonts.family_chart
        )
    }

    /// Get legend font string
    pub fn legend_font(&self) -> String {
        format!("{}px {}", self.fonts.legend_size as i32, self.fonts.family)
    }

    /// Get crosshair label font string
    pub fn crosshair_font(&self) -> String {
        format!(
            "{}px {}",
            self.fonts.crosshair_label_size as i32, self.fonts.family_chart
        )
    }

    /// Get grid color (with optional directional override)
    pub fn grid_color(&self, horizontal: bool) -> &str {
        if horizontal {
            self.chart
                .grid_line_horz
                .as_deref()
                .unwrap_or(&self.chart.grid_line)
        } else {
            self.chart
                .grid_line_vert
                .as_deref()
                .unwrap_or(&self.chart.grid_line)
        }
    }
}

impl Default for RuntimeTheme {
    fn default() -> Self {
        Self::dark()
    }
}

// =============================================================================
// Tests
// =============================================================================

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_preset_creation() {
        let dark = RuntimeTheme::from_preset("dark");
        assert_eq!(dark.name, "Dark");

        let light = RuntimeTheme::from_preset("light");
        assert_eq!(light.name, "Light");

        let unknown = RuntimeTheme::from_preset("unknown");
        assert_eq!(unknown.name, "Dark");
    }

    #[test]
    fn test_json_roundtrip() {
        let theme = RuntimeTheme::dark();
        let json = theme.to_json();
        let restored = RuntimeTheme::from_json(&json).unwrap();
        assert_eq!(theme.name, restored.name);
        assert_eq!(theme.colors.toolbar_bg, restored.colors.toolbar_bg);
    }

    #[test]
    fn test_color_modification() {
        let mut theme = RuntimeTheme::dark();
        theme.colors.toolbar_bg = "#ff0000".to_string();
        assert_eq!(theme.colors.toolbar_bg, "#ff0000");
    }

    #[test]
    fn test_all_presets() {
        for preset in RuntimeTheme::PRESETS {
            let theme = RuntimeTheme::from_preset(preset);
            assert!(!theme.name.is_empty());
            assert!(!theme.chart.background.is_empty());
        }
    }
}
