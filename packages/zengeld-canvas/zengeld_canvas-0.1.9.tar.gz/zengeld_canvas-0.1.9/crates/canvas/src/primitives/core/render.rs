//! Platform-agnostic rendering abstraction for primitives
//!
//! This module provides a `RenderContext` trait that abstracts away
//! platform-specific rendering (Canvas2D, egui, etc.)

/// Parameters for drawing an ellipse
#[derive(Clone, Copy, Debug, Default)]
pub struct EllipseParams {
    /// Center X coordinate
    pub cx: f64,
    /// Center Y coordinate
    pub cy: f64,
    /// Horizontal radius
    pub rx: f64,
    /// Vertical radius
    pub ry: f64,
    /// Rotation angle in radians
    pub rotation: f64,
    /// Start angle in radians
    pub start: f64,
    /// End angle in radians
    pub end: f64,
}

impl EllipseParams {
    /// Create new ellipse parameters
    pub fn new(cx: f64, cy: f64, rx: f64, ry: f64, rotation: f64, start: f64, end: f64) -> Self {
        Self {
            cx,
            cy,
            rx,
            ry,
            rotation,
            start,
            end,
        }
    }

    /// Create a full ellipse (0 to 2*PI)
    pub fn full(cx: f64, cy: f64, rx: f64, ry: f64) -> Self {
        Self {
            cx,
            cy,
            rx,
            ry,
            rotation: 0.0,
            start: 0.0,
            end: std::f64::consts::TAU,
        }
    }
}

/// Platform-agnostic rendering context
///
/// Platforms (WASM Canvas2D, egui, etc.) implement this trait
/// to provide rendering capabilities to primitives.
pub trait RenderContext {
    /// Get chart dimensions
    fn chart_width(&self) -> f64;
    fn chart_height(&self) -> f64;

    /// Coordinate conversion
    fn bar_to_x(&self, bar: f64) -> f64;
    fn price_to_y(&self, price: f64) -> f64;

    /// Set stroke style
    fn set_stroke_color(&mut self, color: &str);
    fn set_stroke_width(&mut self, width: f64);
    fn set_line_dash(&mut self, pattern: &[f64]);

    /// Set fill style
    fn set_fill_color(&mut self, color: &str);

    /// Path operations
    fn begin_path(&mut self);
    fn move_to(&mut self, x: f64, y: f64);
    fn line_to(&mut self, x: f64, y: f64);
    fn close_path(&mut self);

    /// Stroke/fill operations
    fn stroke(&mut self);
    fn fill(&mut self);

    /// Shape helpers
    fn stroke_rect(&mut self, x: f64, y: f64, w: f64, h: f64);
    fn fill_rect(&mut self, x: f64, y: f64, w: f64, h: f64);

    /// Draw ellipse (center, radii, rotation, start_angle, end_angle)
    fn ellipse(&mut self, params: EllipseParams);

    /// Draw arc (for partial circles)
    fn arc(&mut self, cx: f64, cy: f64, radius: f64, start_angle: f64, end_angle: f64);

    /// Quadratic bezier curve
    fn quadratic_curve_to(&mut self, cpx: f64, cpy: f64, x: f64, y: f64);

    /// Bezier curve
    fn bezier_curve_to(&mut self, cp1x: f64, cp1y: f64, cp2x: f64, cp2y: f64, x: f64, y: f64);

    /// Text rendering
    fn set_font(&mut self, font: &str);
    fn set_text_align(&mut self, align: TextAlign);
    fn set_text_baseline(&mut self, baseline: TextBaseline);
    fn fill_text(&mut self, text: &str, x: f64, y: f64);
    fn stroke_text(&mut self, text: &str, x: f64, y: f64);
    fn measure_text(&self, text: &str) -> f64;

    /// Fill text with rotation around the anchor point.
    /// Default implementation uses save/translate/rotate/fill_text/restore.
    /// Platforms that don't support transforms (like egui) should override this.
    fn fill_text_rotated(&mut self, text: &str, x: f64, y: f64, angle: f64) {
        if angle.abs() < 0.001 {
            self.fill_text(text, x, y);
        } else {
            self.save();
            self.translate(x, y);
            self.rotate(angle);
            self.fill_text(text, 0.0, 0.0);
            self.restore();
        }
    }

    /// Device pixel ratio for crisp rendering
    fn dpr(&self) -> f64;

    /// Save/restore state
    fn save(&mut self);
    fn restore(&mut self);

    /// Clipping
    fn clip(&mut self);

    /// Transform operations
    fn translate(&mut self, x: f64, y: f64);
    fn rotate(&mut self, angle: f64);
    fn scale(&mut self, x: f64, y: f64);

    /// Add rect to path (without stroking or filling)
    fn rect(&mut self, x: f64, y: f64, w: f64, h: f64);

    /// Canvas dimensions (full canvas, not just chart area)
    fn canvas_height(&self) -> f64 {
        self.chart_height()
    }
    fn canvas_width(&self) -> f64 {
        self.chart_width()
    }
    fn width(&self) -> u32 {
        self.chart_width() as u32
    }
    fn height(&self) -> u32 {
        self.chart_height() as u32
    }

    /// Global alpha (transparency)
    fn set_global_alpha(&mut self, alpha: f64);

    /// Line cap and join
    fn set_line_cap(&mut self, cap: &str);
    fn set_line_join(&mut self, join: &str);

    /// Draw an image at the specified position
    ///
    /// # Arguments
    /// * `image_id` - Unique identifier for the cached image (URL or data URI)
    /// * `x`, `y` - Top-left corner position
    /// * `width`, `height` - Dimensions to draw the image
    ///
    /// Returns true if the image was drawn, false if not yet loaded/cached.
    /// Platforms should cache images by image_id and handle async loading.
    fn draw_image(&mut self, image_id: &str, x: f64, y: f64, width: f64, height: f64) -> bool {
        // Default implementation does nothing - platform must override
        let _ = (image_id, x, y, width, height);
        false
    }

    /// Line style helper (translates to set_line_dash)
    fn set_line_style(&mut self, style: super::LineStyle) {
        match style {
            super::LineStyle::Solid => self.set_line_dash(&[]),
            super::LineStyle::Dashed => self.set_line_dash(&[8.0, 4.0]),
            super::LineStyle::Dotted => self.set_line_dash(&[2.0, 2.0]),
            super::LineStyle::LargeDashed => self.set_line_dash(&[12.0, 6.0]),
            super::LineStyle::SparseDotted => self.set_line_dash(&[2.0, 8.0]),
        }
    }

    /// Set fill color with alpha transparency
    /// Default implementation uses set_fill_color + set_global_alpha
    fn set_fill_color_alpha(&mut self, color: &str, alpha: f64) {
        self.set_fill_color(color);
        self.set_global_alpha(alpha.clamp(0.0, 1.0));
    }

    /// Reset global alpha to 1.0 (should be called after using set_fill_color_alpha)
    fn reset_alpha(&mut self) {
        self.set_global_alpha(1.0);
    }
}

/// Text alignment for rendering
#[derive(Clone, Copy, Debug, Default)]
pub enum TextAlign {
    #[default]
    Left,
    Center,
    Right,
}

/// Text baseline for rendering
#[derive(Clone, Copy, Debug, Default)]
pub enum TextBaseline {
    Top,
    #[default]
    Middle,
    Bottom,
    Alphabetic,
}

/// Helper to make crisp lines at device pixel boundaries
#[inline]
pub fn crisp(val: f64, dpr: f64) -> f64 {
    (val * dpr).round() / dpr + 0.5 / dpr
}

use super::types::{PrimitiveText, TextAlign as PrimitiveTextAlign};

/// Render text from PrimitiveText configuration
///
/// # Arguments
/// * `ctx` - Render context
/// * `text` - PrimitiveText configuration
/// * `x`, `y` - Position to render at
/// * `fallback_color` - Color to use if text.color is None
pub fn render_primitive_text(
    ctx: &mut dyn RenderContext,
    text: &PrimitiveText,
    x: f64,
    y: f64,
    fallback_color: &str,
) {
    render_primitive_text_rotated(ctx, text, x, y, fallback_color, 0.0);
}

/// Render text from PrimitiveText configuration with rotation
///
/// # Arguments
/// * `ctx` - Render context
/// * `text` - PrimitiveText configuration
/// * `x`, `y` - Position to render at
/// * `fallback_color` - Color to use if text.color is None
/// * `rotation` - Rotation angle in radians
pub fn render_primitive_text_rotated(
    ctx: &mut dyn RenderContext,
    text: &PrimitiveText,
    x: f64,
    y: f64,
    fallback_color: &str,
    rotation: f64,
) {
    if text.content.is_empty() {
        return;
    }

    // Build font string
    let mut font_parts = Vec::new();
    if text.italic {
        font_parts.push("italic".to_string());
    }
    if text.bold {
        font_parts.push("bold".to_string());
    }
    font_parts.push(format!("{}px", text.font_size as i32));
    font_parts.push("sans-serif".to_string());
    let font = font_parts.join(" ");

    ctx.set_font(&font);

    // Set alignment - for rotated text, use center alignment for proper rotation around anchor
    let h_align = match text.h_align {
        PrimitiveTextAlign::Start => TextAlign::Left,
        PrimitiveTextAlign::Center => TextAlign::Center,
        PrimitiveTextAlign::End => TextAlign::Right,
    };
    ctx.set_text_align(h_align);

    // For rotated text, use middle baseline so text rotates around its center
    ctx.set_text_baseline(TextBaseline::Middle);

    // Set color
    let color = text.color.as_deref().unwrap_or(fallback_color);
    ctx.set_fill_color(color);

    // Render text lines with optional rotation
    let line_height = text.font_size * 1.2;
    let lines: Vec<&str> = text.content.lines().collect();

    for (i, line) in lines.iter().enumerate() {
        let line_y = y + (i as f64 * line_height);
        ctx.fill_text_rotated(line, x, line_y, rotation);
    }
}

/// Measure text dimensions from PrimitiveText configuration
/// Returns (width, height)
pub fn measure_primitive_text(ctx: &dyn RenderContext, text: &PrimitiveText) -> (f64, f64) {
    if text.content.is_empty() {
        return (0.0, 0.0);
    }

    let lines: Vec<&str> = text.content.lines().collect();
    let line_height = text.font_size * 1.2;
    let height = lines.len() as f64 * line_height;

    // Measure widest line
    let mut max_width = 0.0f64;
    for line in &lines {
        let w = ctx.measure_text(line);
        if w > max_width {
            max_width = w;
        }
    }

    (max_width, height)
}

/// Render text with optional background
pub fn render_text_with_background(
    ctx: &mut dyn RenderContext,
    text: &PrimitiveText,
    x: f64,
    y: f64,
    fallback_color: &str,
    bg_color: Option<&str>,
    padding: f64,
) {
    if text.content.is_empty() {
        return;
    }

    // Setup font first for measurement
    let mut font_parts = Vec::new();
    if text.italic {
        font_parts.push("italic".to_string());
    }
    if text.bold {
        font_parts.push("bold".to_string());
    }
    font_parts.push(format!("{}px", text.font_size as i32));
    font_parts.push("sans-serif".to_string());
    let font = font_parts.join(" ");
    ctx.set_font(&font);

    // Measure text
    let (text_width, text_height) = measure_primitive_text(ctx, text);

    // Calculate background rect position based on alignment
    let bg_x = match text.h_align {
        PrimitiveTextAlign::Start => x - padding,
        PrimitiveTextAlign::Center => x - text_width / 2.0 - padding,
        PrimitiveTextAlign::End => x - text_width - padding,
    };
    let bg_y = match text.v_align {
        PrimitiveTextAlign::Start => y - padding,
        PrimitiveTextAlign::Center => y - text_height / 2.0 - padding,
        PrimitiveTextAlign::End => y - text_height - padding,
    };

    // Draw background if specified
    if let Some(bg) = bg_color {
        ctx.set_fill_color(bg);
        ctx.fill_rect(
            bg_x,
            bg_y,
            text_width + padding * 2.0,
            text_height + padding * 2.0,
        );
    }

    // Draw text
    render_primitive_text(ctx, text, x, y, fallback_color);
}

/// Helper to make crisp rectangles
#[inline]
pub fn crisp_rect(x: f64, y: f64, w: f64, h: f64, dpr: f64) -> (f64, f64, f64, f64) {
    let x1 = (x * dpr).round() / dpr;
    let y1 = (y * dpr).round() / dpr;
    let x2 = ((x + w) * dpr).round() / dpr;
    let y2 = ((y + h) * dpr).round() / dpr;
    (x1, y1, x2 - x1, y2 - y1)
}

/// Render instructions that primitives generate
///
/// This is an alternative approach - primitives generate instructions
/// that platforms then execute. More portable but less flexible.
#[derive(Clone, Debug)]
pub enum RenderOp {
    // Style
    SetStrokeColor(String),
    SetFillColor(String),
    SetLineWidth(f64),
    SetLineDash(Vec<f64>),

    // Path
    BeginPath,
    MoveTo(f64, f64),
    LineTo(f64, f64),
    QuadraticCurveTo(f64, f64, f64, f64),
    BezierCurveTo(f64, f64, f64, f64, f64, f64),
    Arc(f64, f64, f64, f64, f64),
    Ellipse(EllipseParams),
    ClosePath,

    // Draw
    Stroke,
    Fill,
    StrokeRect(f64, f64, f64, f64),
    FillRect(f64, f64, f64, f64),

    // Text
    SetFont(String),
    SetTextAlign(TextAlign),
    FillText(String, f64, f64),
    StrokeText(String, f64, f64),

    // State
    Save,
    Restore,
    Translate(f64, f64),
    Rotate(f64),
    Scale(f64, f64),
    Clip,
}

/// Collection of render operations
pub type RenderOps = Vec<RenderOp>;

/// Execute render operations on a context
pub fn execute_ops(ctx: &mut dyn RenderContext, ops: &[RenderOp]) {
    for op in ops {
        match op {
            RenderOp::SetStrokeColor(c) => ctx.set_stroke_color(c),
            RenderOp::SetFillColor(c) => ctx.set_fill_color(c),
            RenderOp::SetLineWidth(w) => ctx.set_stroke_width(*w),
            RenderOp::SetLineDash(p) => ctx.set_line_dash(p),
            RenderOp::BeginPath => ctx.begin_path(),
            RenderOp::MoveTo(x, y) => ctx.move_to(*x, *y),
            RenderOp::LineTo(x, y) => ctx.line_to(*x, *y),
            RenderOp::QuadraticCurveTo(cpx, cpy, x, y) => {
                ctx.quadratic_curve_to(*cpx, *cpy, *x, *y)
            }
            RenderOp::BezierCurveTo(cp1x, cp1y, cp2x, cp2y, x, y) => {
                ctx.bezier_curve_to(*cp1x, *cp1y, *cp2x, *cp2y, *x, *y)
            }
            RenderOp::Arc(cx, cy, r, start, end) => ctx.arc(*cx, *cy, *r, *start, *end),
            RenderOp::Ellipse(params) => ctx.ellipse(*params),
            RenderOp::ClosePath => ctx.close_path(),
            RenderOp::Stroke => ctx.stroke(),
            RenderOp::Fill => ctx.fill(),
            RenderOp::StrokeRect(x, y, w, h) => ctx.stroke_rect(*x, *y, *w, *h),
            RenderOp::FillRect(x, y, w, h) => ctx.fill_rect(*x, *y, *w, *h),
            RenderOp::SetFont(f) => ctx.set_font(f),
            RenderOp::SetTextAlign(a) => ctx.set_text_align(*a),
            RenderOp::FillText(t, x, y) => ctx.fill_text(t, *x, *y),
            RenderOp::StrokeText(t, x, y) => ctx.stroke_text(t, *x, *y),
            RenderOp::Save => ctx.save(),
            RenderOp::Restore => ctx.restore(),
            RenderOp::Translate(x, y) => ctx.translate(*x, *y),
            RenderOp::Rotate(a) => ctx.rotate(*a),
            RenderOp::Scale(x, y) => ctx.scale(*x, *y),
            RenderOp::Clip => ctx.clip(),
        }
    }
}
