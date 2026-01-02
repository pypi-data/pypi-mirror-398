//! Core primitive trait - the foundation for all drawing primitives
//!
//! This trait-based architecture allows adding new primitives without
//! modifying the DrawingManager.

use super::config::{
    ConfigProperty, PropertyCategory, PropertyValue, SelectOption, TimeframeVisibilityConfig,
};
use super::render::{RenderContext, crisp};
use super::types::{LineStyle, PrimitiveColor, PrimitiveText, TextAlign, TextAnchor};
use serde::{Deserialize, Serialize};

/// Category of primitive for toolbar organization
#[derive(Clone, Copy, Debug, PartialEq, Eq, Hash, Serialize, Deserialize)]
pub enum PrimitiveKind {
    /// Lines: trend line, horizontal, vertical, ray, extended
    Line,
    /// Channels: parallel channel, regression trend, flat top/bottom
    Channel,
    /// Shapes: rectangle, ellipse, triangle, arc, polyline
    Shape,
    /// Fibonacci: retracement, extension, channel, circles, spiral
    Fibonacci,
    /// Gann: fan, square, box
    Gann,
    /// Patterns: head & shoulders, elliott wave, harmonic
    Pattern,
    /// Annotations: text, note, callout, user notes
    Annotation,
    /// Measurement: price range, date range, bars pattern
    Measurement,
    /// Trading: position, long/short, risk/reward
    Trading,
    /// Signal markers: buy/sell arrows, strategy indicators
    /// Programmatically placed by strategies, minimal configuration (color, size only)
    Signal,
}

/// Sync mode for primitives across charts
#[derive(Clone, Copy, Debug, Default, PartialEq, Eq, Serialize, Deserialize)]
pub enum SyncMode {
    /// Don't sync to other charts
    #[default]
    None,
    /// Sync to all charts of the same symbol
    SameSymbol,
    /// Sync everywhere
    Everywhere,
}

/// Core primitive data that all primitives share
#[derive(Clone, Debug, Serialize, Deserialize)]
pub struct PrimitiveData {
    /// Unique identifier
    pub id: u64,
    /// Primitive type ID (e.g., "trend_line", "fib_retracement")
    pub type_id: String,
    /// Display name for UI
    pub display_name: String,
    /// Color configuration
    pub color: PrimitiveColor,
    /// Line width in pixels
    pub width: f64,
    /// Line style
    pub style: LineStyle,
    /// Optional text label
    pub text: Option<PrimitiveText>,
    /// Is primitive locked (can't be edited)
    pub locked: bool,
    /// Is primitive visible
    pub visible: bool,
    /// Z-order layer
    pub z_order: i32,
    /// Timeframe visibility settings
    #[serde(default)]
    pub timeframe_visibility: Option<TimeframeVisibilityConfig>,
    /// Sync mode across charts
    #[serde(default)]
    pub sync_mode: SyncMode,
    /// Pane ID where primitive was created (None = main chart, Some(id) = sub-pane indicator instance id)
    #[serde(default)]
    pub pane_id: Option<u64>,
    /// Window ID where primitive was created (for multi-window support)
    #[serde(default)]
    pub window_id: Option<u64>,
}

impl Default for PrimitiveData {
    fn default() -> Self {
        Self {
            id: 0,
            type_id: String::new(),
            display_name: String::new(),
            color: PrimitiveColor::default(),
            width: 2.0,
            style: LineStyle::Solid,
            text: None,
            locked: false,
            visible: true,
            z_order: 0,
            timeframe_visibility: None,
            sync_mode: SyncMode::None,
            pane_id: None,
            window_id: None,
        }
    }
}

impl PrimitiveData {
    /// Get base config properties (common to all primitives)
    pub fn base_properties(&self) -> Vec<ConfigProperty> {
        vec![
            ConfigProperty::color("stroke_color", "Line Color", &self.color.stroke)
                .with_category(PropertyCategory::Style)
                .with_order(0),
            ConfigProperty::number("width", "Line Width", self.width, Some(1.0), Some(10.0))
                .with_category(PropertyCategory::Style)
                .with_order(1),
            ConfigProperty::line_style("style", "Line Style", self.style.as_str())
                .with_category(PropertyCategory::Style)
                .with_order(2),
            ConfigProperty::boolean("locked", "Locked", self.locked)
                .with_category(PropertyCategory::Style)
                .with_order(100),
            ConfigProperty::boolean("visible", "Visible", self.visible)
                .with_category(PropertyCategory::Visibility)
                .with_order(0),
        ]
    }

    /// Get text properties (if primitive has text configured)
    ///
    /// Note: Property names use English as default for serialization.
    /// Use `localized_property_label()` from config module for UI display.
    pub fn text_properties(&self) -> Vec<ConfigProperty> {
        let mut props = Vec::new();
        if let Some(ref text) = self.text {
            props.push(
                ConfigProperty::text_content("text_content", "Text", &text.content).with_order(0),
            );
            props.push(
                ConfigProperty::number(
                    "text_font_size",
                    "Font Size",
                    text.font_size,
                    Some(8.0),
                    Some(72.0),
                )
                .with_category(PropertyCategory::Text)
                .with_order(1),
            );
            props.push(
                ConfigProperty::color(
                    "text_color",
                    "Text Color",
                    text.color.as_deref().unwrap_or(&self.color.stroke),
                )
                .with_category(PropertyCategory::Text)
                .with_order(2),
            );
            props.push(
                ConfigProperty::boolean("text_bold", "Bold", text.bold)
                    .with_category(PropertyCategory::Text)
                    .with_order(3),
            );
            props.push(
                ConfigProperty::boolean("text_italic", "Italic", text.italic)
                    .with_category(PropertyCategory::Text)
                    .with_order(4),
            );
            props.push(
                ConfigProperty::select(
                    "text_h_align",
                    "Horizontal Align",
                    text.h_align.as_str(),
                    vec![
                        SelectOption::new("start", "Left"),
                        SelectOption::new("center", "Center"),
                        SelectOption::new("end", "Right"),
                    ],
                )
                .with_category(PropertyCategory::Text)
                .with_order(5),
            );
            props.push(
                ConfigProperty::select(
                    "text_v_align",
                    "Vertical Align",
                    text.v_align.as_str(),
                    vec![
                        SelectOption::new("start", "Top"),
                        SelectOption::new("center", "Center"),
                        SelectOption::new("end", "Bottom"),
                    ],
                )
                .with_category(PropertyCategory::Text)
                .with_order(6),
            );
        }
        props
    }

    /// Apply a property value to base data
    pub fn apply_property(&mut self, id: &str, value: &PropertyValue) -> bool {
        match id {
            "stroke_color" => {
                if let Some(c) = value.as_color() {
                    self.color.stroke = c.to_string();
                    return true;
                }
            }
            "fill_color" => {
                if let Some(c) = value.as_color() {
                    self.color.fill = Some(c.to_string());
                    return true;
                }
            }
            "width" => {
                if let Some(w) = value.as_number() {
                    self.width = w.clamp(1.0, 10.0);
                    return true;
                }
            }
            "style" => {
                if let Some(s) = value.as_string() {
                    self.style = LineStyle::parse(s);
                    return true;
                }
            }
            "locked" => {
                if let Some(b) = value.as_bool() {
                    self.locked = b;
                    return true;
                }
            }
            "visible" => {
                if let Some(b) = value.as_bool() {
                    self.visible = b;
                    return true;
                }
            }
            // Text properties
            "text_content" => {
                if let Some(s) = value.as_string() {
                    if let Some(ref mut text) = self.text {
                        text.content = s.to_string();
                    } else {
                        self.text = Some(PrimitiveText::new(s));
                    }
                    return true;
                }
            }
            "text_font_size" => {
                if let Some(size) = value.as_number() {
                    if let Some(ref mut text) = self.text {
                        text.font_size = size.clamp(8.0, 72.0);
                        return true;
                    }
                }
            }
            "text_color" => {
                if let Some(c) = value.as_color() {
                    if let Some(ref mut text) = self.text {
                        text.color = Some(c.to_string());
                        return true;
                    }
                }
            }
            "text_bold" => {
                if let Some(b) = value.as_bool() {
                    if let Some(ref mut text) = self.text {
                        text.bold = b;
                        return true;
                    }
                }
            }
            "text_italic" => {
                if let Some(b) = value.as_bool() {
                    if let Some(ref mut text) = self.text {
                        text.italic = b;
                        return true;
                    }
                }
            }
            "text_h_align" => {
                if let Some(s) = value.as_string() {
                    if let Some(ref mut text) = self.text {
                        text.h_align = match s {
                            "start" => TextAlign::Start,
                            "center" => TextAlign::Center,
                            "end" => TextAlign::End,
                            _ => TextAlign::Center,
                        };
                        return true;
                    }
                }
            }
            "text_v_align" => {
                if let Some(s) = value.as_string() {
                    if let Some(ref mut text) = self.text {
                        text.v_align = match s {
                            "start" => TextAlign::Start,
                            "center" => TextAlign::Center,
                            "end" => TextAlign::End,
                            _ => TextAlign::Start,
                        };
                        return true;
                    }
                }
            }
            _ => {}
        }
        false
    }

    /// Initialize text if primitive supports it (call in new() of primitives)
    pub fn init_text(&mut self, default_content: &str) {
        if self.text.is_none() {
            self.text = Some(PrimitiveText::new(default_content));
        }
    }

    /// Check if text is enabled
    pub fn has_text(&self) -> bool {
        self.text.is_some()
    }
}

/// The core primitive trait
///
/// All drawing primitives must implement this trait. The DrawingManager
/// works with `Box<dyn Primitive>` to support any primitive type.
pub trait Primitive: Send + Sync {
    // =========================================================================
    // Identity & Metadata
    // =========================================================================

    /// Get the primitive type ID (e.g., "trend_line", "fib_retracement")
    fn type_id(&self) -> &'static str;

    /// Get display name for UI (can be localized)
    fn display_name(&self) -> &str;

    /// Get the category for toolbar organization
    fn kind(&self) -> PrimitiveKind;

    // =========================================================================
    // Common Data Access
    // =========================================================================

    /// Get shared primitive data
    fn data(&self) -> &PrimitiveData;

    /// Get mutable shared primitive data
    fn data_mut(&mut self) -> &mut PrimitiveData;

    // =========================================================================
    // Geometry
    // =========================================================================

    /// Get all coordinate points as (bar, price) pairs
    fn points(&self) -> Vec<(f64, f64)>;

    /// Set coordinate points (for creation and editing)
    fn set_points(&mut self, points: &[(f64, f64)]);

    /// Translate the primitive by bar/price delta
    fn translate(&mut self, bar_delta: f64, price_delta: f64);

    // =========================================================================
    // Rendering
    // =========================================================================

    /// Render the primitive using the provided render context
    ///
    /// The primitive should use ctx.bar_to_x() and ctx.price_to_y() to convert
    /// its data coordinates to screen coordinates, then draw using the
    /// path operations (begin_path, move_to, line_to, etc.) and fill/stroke.
    ///
    /// Default implementation draws lines connecting all points - override for
    /// custom rendering (shapes, fills, text, etc.)
    fn render(&self, ctx: &mut dyn RenderContext, is_selected: bool) {
        // Inline default implementation to avoid Sized bound issues
        let data = self.data();
        let points = self.points();
        let kind = self.kind();
        let dpr = ctx.dpr();

        if points.is_empty() {
            return;
        }

        // Convert to screen coordinates
        let screen_points: Vec<(f64, f64)> = points
            .iter()
            .map(|(bar, price)| (ctx.bar_to_x(*bar), ctx.price_to_y(*price)))
            .collect();

        // Set stroke style
        ctx.set_stroke_color(&data.color.stroke);
        ctx.set_stroke_width(data.width);

        // Set line dash based on style
        match data.style {
            LineStyle::Solid => ctx.set_line_dash(&[]),
            LineStyle::Dashed => ctx.set_line_dash(&[8.0, 4.0]),
            LineStyle::Dotted => ctx.set_line_dash(&[2.0, 2.0]),
            LineStyle::LargeDashed => ctx.set_line_dash(&[12.0, 6.0]),
            LineStyle::SparseDotted => ctx.set_line_dash(&[2.0, 8.0]),
        }

        // Render based on kind
        match kind {
            PrimitiveKind::Line | PrimitiveKind::Channel => {
                if screen_points.len() >= 2 {
                    ctx.begin_path();
                    let (x0, y0) = screen_points[0];
                    ctx.move_to(crisp(x0, dpr), crisp(y0, dpr));
                    for (x, y) in screen_points.iter().skip(1) {
                        ctx.line_to(crisp(*x, dpr), crisp(*y, dpr));
                    }
                    ctx.stroke();
                }
            }
            PrimitiveKind::Shape => {
                if screen_points.len() >= 2 {
                    let (x1, y1) = screen_points[0];
                    let (x2, y2) = screen_points[1];
                    let rx = x1.min(x2);
                    let ry = y1.min(y2);
                    let rw = (x2 - x1).abs();
                    let rh = (y2 - y1).abs();

                    if let Some(ref fill) = data.color.fill {
                        ctx.set_fill_color(fill);
                        ctx.fill_rect(rx, ry, rw, rh);
                    }
                    ctx.stroke_rect(rx, ry, rw, rh);
                }
            }
            PrimitiveKind::Annotation => {
                if let Some((x, y)) = screen_points.first() {
                    ctx.set_fill_color(&data.color.stroke);
                    ctx.begin_path();
                    ctx.arc(*x, *y, 6.0, 0.0, std::f64::consts::TAU);
                    ctx.fill();
                }
            }
            _ => {
                // Default: draw lines connecting all points
                if screen_points.len() >= 2 {
                    ctx.begin_path();
                    let (x0, y0) = screen_points[0];
                    ctx.move_to(crisp(x0, dpr), crisp(y0, dpr));
                    for (x, y) in screen_points.iter().skip(1) {
                        ctx.line_to(crisp(*x, dpr), crisp(*y, dpr));
                    }
                    ctx.stroke();
                }

                ctx.set_fill_color(&data.color.stroke);
                for (x, y) in &screen_points {
                    ctx.begin_path();
                    ctx.arc(*x, *y, 3.0, 0.0, std::f64::consts::TAU);
                    ctx.fill();
                }
            }
        }

        ctx.set_line_dash(&[]);

        let _ = is_selected; // Selection rendering handled by UI layer
    }

    /// Get text anchor point for centralized text rendering
    ///
    /// Return Some(TextAnchor) if this primitive has text that should be rendered.
    /// The actual text rendering is done centrally after render() is called.
    ///
    /// Default returns None - override for primitives with text.
    fn text_anchor(&self, ctx: &dyn RenderContext) -> Option<TextAnchor> {
        let _ = ctx; // suppress unused warning
        None
    }

    // =========================================================================
    // Level Configuration (for Fibonacci, Gann, Pitchfork)
    // =========================================================================

    /// Get level configurations (for primitives with levels like Fibonacci, Gann, Pitchfork)
    /// Returns None for primitives that don't support level configuration
    fn level_configs(&self) -> Option<Vec<super::config::FibLevelConfig>> {
        None
    }

    /// Set level configurations
    /// Returns true if the primitive supports levels and they were set
    fn set_level_configs(&mut self, _configs: Vec<super::config::FibLevelConfig>) -> bool {
        false
    }

    // =========================================================================
    // Serialization
    // =========================================================================

    /// Serialize to JSON for storage
    fn to_json(&self) -> String;

    /// Clone into a boxed trait object
    fn clone_box(&self) -> Box<dyn Primitive>;
}

/// Helper trait for cloning boxed primitives
impl Clone for Box<dyn Primitive> {
    fn clone(&self) -> Self {
        self.clone_box()
    }
}
