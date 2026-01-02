//! Render backend trait - platform abstraction layer
//!
//! RenderBackend defines the interface that platform-specific
//! renderers must implement (Canvas2D, WebGL, egui, Skia, etc.)

use super::batch::RenderBatch;
use super::commands::RenderCommand;
use super::path::{Path, PathBuilder};
use super::types::{Color, FillStyle, LineStyle, Point, Rect, TextStyle, Transform2D};

/// Result type for rendering operations
pub type RenderResult<T> = Result<T, RenderError>;

/// Rendering errors
#[derive(Clone, Debug)]
pub enum RenderError {
    /// Backend not initialized
    NotInitialized,

    /// Invalid state (mismatched push/pop)
    InvalidState(String),

    /// Resource not found (image, font)
    ResourceNotFound(String),

    /// Platform-specific error
    Platform(String),
}

impl std::fmt::Display for RenderError {
    fn fmt(&self, f: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        match self {
            RenderError::NotInitialized => write!(f, "Render backend not initialized"),
            RenderError::InvalidState(msg) => write!(f, "Invalid render state: {}", msg),
            RenderError::ResourceNotFound(id) => write!(f, "Resource not found: {}", id),
            RenderError::Platform(msg) => write!(f, "Platform error: {}", msg),
        }
    }
}

impl std::error::Error for RenderError {}

/// Text measurement result
#[derive(Clone, Copy, Debug, Default)]
pub struct TextMetrics {
    /// Width of the text
    pub width: f64,

    /// Height of the text (based on font metrics)
    pub height: f64,

    /// Distance from baseline to top
    pub ascent: f64,

    /// Distance from baseline to bottom (positive value)
    pub descent: f64,
}

/// Image information
#[derive(Clone, Debug)]
pub struct ImageInfo {
    /// Original width in pixels
    pub width: u32,

    /// Original height in pixels
    pub height: u32,

    /// Whether the image is fully loaded
    pub loaded: bool,
}

/// Parameters for drawing a candlestick
#[derive(Clone, Copy, Debug)]
pub struct DrawCandlestickParams {
    /// X position (center of candlestick)
    pub x: f64,
    /// Open price Y coordinate
    pub open_y: f64,
    /// High price Y coordinate
    pub high_y: f64,
    /// Low price Y coordinate
    pub low_y: f64,
    /// Close price Y coordinate
    pub close_y: f64,
    /// Width of the candlestick body
    pub width: f64,
    /// Color for the candlestick body
    pub body_color: Color,
    /// Color for the wick (high-low line)
    pub wick_color: Color,
}

/// Render backend trait
///
/// Platform-specific renderers implement this trait to provide
/// actual drawing capabilities. The trait is designed to be:
/// - Stateless where possible (styles passed per-call)
/// - Efficient (minimal allocations, batch-friendly)
/// - Complete (all operations needed for charts)
pub trait RenderBackend {
    // =========================================================================
    // Lifecycle
    // =========================================================================

    /// Begin a new frame
    fn begin_frame(&mut self, width: f64, height: f64, dpr: f64);

    /// End the current frame
    fn end_frame(&mut self);

    /// Get current device pixel ratio
    fn dpr(&self) -> f64;

    /// Get current canvas size
    fn size(&self) -> (f64, f64);

    // =========================================================================
    // Clear
    // =========================================================================

    /// Clear entire canvas with color
    fn clear(&mut self, color: Color);

    /// Clear a specific region
    fn clear_rect(&mut self, rect: Rect);

    // =========================================================================
    // Path drawing
    // =========================================================================

    /// Fill a path
    fn fill_path(&mut self, path: &Path, style: &FillStyle);

    /// Stroke a path
    fn stroke_path(&mut self, path: &Path, style: &LineStyle);

    // =========================================================================
    // Shape shortcuts (can use default implementations)
    // =========================================================================

    /// Fill rectangle
    fn fill_rect(&mut self, rect: Rect, color: Color) {
        self.fill_path(&Path::rect(rect), &FillStyle::solid(color));
    }

    /// Stroke rectangle
    fn stroke_rect(&mut self, rect: Rect, style: &LineStyle) {
        self.stroke_path(&Path::rect(rect), style);
    }

    /// Draw line
    fn line(&mut self, from: Point, to: Point, style: &LineStyle) {
        self.stroke_path(&Path::line(from, to), style);
    }

    /// Draw polyline
    fn polyline(&mut self, points: &[Point], style: &LineStyle) {
        if points.len() >= 2 {
            self.stroke_path(&Path::polyline(points), style);
        }
    }

    /// Fill circle
    fn fill_circle(&mut self, center: Point, radius: f64, color: Color) {
        self.fill_path(&Path::circle(center, radius), &FillStyle::solid(color));
    }

    /// Stroke circle
    fn stroke_circle(&mut self, center: Point, radius: f64, style: &LineStyle) {
        self.stroke_path(&Path::circle(center, radius), style);
    }

    /// Fill ellipse
    fn fill_ellipse(&mut self, center: Point, rx: f64, ry: f64, rotation: f64, color: Color) {
        self.fill_path(
            &Path::ellipse(center, rx, ry, rotation, 0.0, std::f64::consts::TAU),
            &FillStyle::solid(color),
        );
    }

    /// Stroke ellipse
    fn stroke_ellipse(
        &mut self,
        center: Point,
        rx: f64,
        ry: f64,
        rotation: f64,
        style: &LineStyle,
    ) {
        self.stroke_path(
            &Path::ellipse(center, rx, ry, rotation, 0.0, std::f64::consts::TAU),
            style,
        );
    }

    // =========================================================================
    // Text
    // =========================================================================

    /// Draw text at position
    fn text(&mut self, text: &str, pos: Point, style: &TextStyle);

    /// Draw rotated text
    fn text_rotated(&mut self, text: &str, pos: Point, angle: f64, style: &TextStyle) {
        self.push_transform(Transform2D::rotation(angle, pos.x, pos.y));
        self.text(text, pos, style);
        self.pop_transform();
    }

    /// Measure text dimensions
    fn measure_text(&self, text: &str, style: &TextStyle) -> TextMetrics;

    // =========================================================================
    // Images
    // =========================================================================

    /// Draw image (or portion of it)
    fn image(&mut self, id: &str, src: Option<Rect>, dst: Rect);

    /// Get image info (returns None if not loaded)
    fn image_info(&self, id: &str) -> Option<ImageInfo>;

    /// Preload an image from URL or data URL
    fn preload_image(&mut self, id: &str, url: &str);

    // =========================================================================
    // State management
    // =========================================================================

    /// Push a clip rectangle (intersects with current clip)
    fn push_clip(&mut self, rect: Rect);

    /// Pop clip rectangle
    fn pop_clip(&mut self);

    /// Push a transform matrix
    fn push_transform(&mut self, transform: Transform2D);

    /// Pop transform matrix
    fn pop_transform(&mut self);

    /// Push a layer with opacity
    fn push_layer(&mut self, opacity: f64);

    /// Pop layer
    fn pop_layer(&mut self);

    /// Set global alpha (affects all subsequent drawing)
    fn set_alpha(&mut self, alpha: f64);

    /// Save current state (transform, clip, alpha) to stack
    fn save(&mut self);

    /// Restore previously saved state from stack
    fn restore(&mut self);

    // =========================================================================
    // Batch rendering
    // =========================================================================

    /// Execute a single render command
    fn execute(&mut self, cmd: &RenderCommand) {
        match cmd {
            RenderCommand::FillPath { path, style } => {
                self.fill_path(path, style);
            }
            RenderCommand::StrokePath { path, style } => {
                self.stroke_path(path, style);
            }
            RenderCommand::FillRect { rect, color } => {
                self.fill_rect(*rect, *color);
            }
            RenderCommand::StrokeRect { rect, style } => {
                self.stroke_rect(*rect, style);
            }
            RenderCommand::Line { from, to, style } => {
                self.line(*from, *to, style);
            }
            RenderCommand::Polyline { points, style } => {
                self.polyline(points, style);
            }
            RenderCommand::FillCircle {
                center,
                radius,
                color,
            } => {
                self.fill_circle(*center, *radius, *color);
            }
            RenderCommand::StrokeCircle {
                center,
                radius,
                style,
            } => {
                self.stroke_circle(*center, *radius, style);
            }
            RenderCommand::FillEllipse {
                center,
                rx,
                ry,
                rotation,
                color,
            } => {
                self.fill_ellipse(*center, *rx, *ry, *rotation, *color);
            }
            RenderCommand::StrokeEllipse {
                center,
                rx,
                ry,
                rotation,
                style,
            } => {
                self.stroke_ellipse(*center, *rx, *ry, *rotation, style);
            }
            RenderCommand::StrokeArc {
                center,
                radius,
                start_angle,
                end_angle,
                style,
            } => {
                let path = Path::arc(*center, *radius, *start_angle, *end_angle);
                self.stroke_path(&path, style);
            }
            RenderCommand::Text { text, pos, style } => {
                self.text(text, *pos, style);
            }
            RenderCommand::TextRotated {
                text,
                pos,
                angle,
                style,
            } => {
                self.text_rotated(text, *pos, *angle, style);
            }
            RenderCommand::TextWithBackground {
                text,
                pos,
                style,
                background,
                padding,
            } => {
                let metrics = self.measure_text(text, style);
                let bg_rect = Rect::new(
                    pos.x - padding,
                    pos.y - metrics.ascent - padding,
                    metrics.width + padding * 2.0,
                    metrics.height + padding * 2.0,
                );
                self.fill_rect(bg_rect, *background);
                self.text(text, *pos, style);
            }
            RenderCommand::Image { id, src, dst } => {
                self.image(id, *src, *dst);
            }
            RenderCommand::PushClip { rect } => {
                self.push_clip(*rect);
            }
            RenderCommand::PopClip => {
                self.pop_clip();
            }
            RenderCommand::PushTransform { transform } => {
                self.push_transform(*transform);
            }
            RenderCommand::PopTransform => {
                self.pop_transform();
            }
            RenderCommand::PushLayer { opacity } => {
                self.push_layer(*opacity);
            }
            RenderCommand::PopLayer => {
                self.pop_layer();
            }
            RenderCommand::SetAlpha { alpha } => {
                self.set_alpha(*alpha);
            }
            RenderCommand::Candlestick {
                x,
                open_y,
                high_y,
                low_y,
                close_y,
                width,
                body_color,
                wick_color,
            } => {
                self.draw_candlestick(DrawCandlestickParams {
                    x: *x,
                    open_y: *open_y,
                    high_y: *high_y,
                    low_y: *low_y,
                    close_y: *close_y,
                    width: *width,
                    body_color: *body_color,
                    wick_color: *wick_color,
                });
            }
            RenderCommand::HistogramBar {
                x,
                y,
                width,
                height,
                color,
            } => {
                self.fill_rect(Rect::new(*x, *y, *width, *height), *color);
            }
            RenderCommand::GridLine {
                is_horizontal,
                pos,
                start,
                end,
                color,
            } => {
                let style = LineStyle::solid(*color, 1.0);
                if *is_horizontal {
                    self.line(Point::new(*start, *pos), Point::new(*end, *pos), &style);
                } else {
                    self.line(Point::new(*pos, *start), Point::new(*pos, *end), &style);
                }
            }
            RenderCommand::Save => {
                self.save();
            }
            RenderCommand::Restore => {
                self.restore();
            }
            RenderCommand::QuadraticCurveTo {
                start,
                control,
                end,
                style,
            } => {
                let mut builder = PathBuilder::new();
                builder.move_to(*start);
                builder.quad_to(*control, *end);
                self.stroke_path(&builder.build(), style);
            }
            RenderCommand::BezierCurveTo {
                start,
                control1,
                control2,
                end,
                style,
            } => {
                let mut builder = PathBuilder::new();
                builder.move_to(*start);
                builder.cubic_to(*control1, *control2, *end);
                self.stroke_path(&builder.build(), style);
            }
            RenderCommand::FillPolygon { points, style } => {
                if points.len() >= 3 {
                    self.fill_path(&Path::polygon(points), style);
                }
            }
            RenderCommand::StrokePolygon { points, style } => {
                if points.len() >= 3 {
                    self.stroke_path(&Path::polygon(points), style);
                }
            }
            RenderCommand::FillRoundedRect {
                rect,
                radius,
                color,
            } => {
                self.fill_path(
                    &Path::rounded_rect(*rect, *radius),
                    &FillStyle::solid(*color),
                );
            }
            RenderCommand::StrokeRoundedRect {
                rect,
                radius,
                style,
            } => {
                self.stroke_path(&Path::rounded_rect(*rect, *radius), style);
            }
            RenderCommand::FillArc {
                center,
                radius,
                start_angle,
                end_angle,
                color,
            } => {
                // Create pie slice path
                let mut builder = PathBuilder::new();
                builder.move_to(*center);
                builder.arc(*center, *radius, *start_angle, *end_angle);
                builder.close();
                self.fill_path(&builder.build(), &FillStyle::solid(*color));
            }
        }
    }

    /// Execute a batch of render commands
    fn execute_batch(&mut self, batch: &RenderBatch) {
        for cmd in batch.commands() {
            self.execute(cmd);
        }
    }

    // =========================================================================
    // Composite primitives (optimized implementations)
    // =========================================================================

    /// Draw a candlestick (optimized for chart rendering)
    fn draw_candlestick(&mut self, params: DrawCandlestickParams) {
        // Wick (high-low line)
        let wick_style = LineStyle::solid(params.wick_color, 1.0);
        self.line(
            Point::new(params.x, params.high_y),
            Point::new(params.x, params.low_y),
            &wick_style,
        );

        // Body
        let body_top = params.open_y.min(params.close_y);
        let body_height = (params.open_y - params.close_y).abs().max(1.0);
        self.fill_rect(
            Rect::new(
                params.x - params.width / 2.0,
                body_top,
                params.width,
                body_height,
            ),
            params.body_color,
        );
    }
}

/// Null backend for testing - does nothing
#[derive(Default)]
pub struct NullBackend {
    dpr: f64,
    width: f64,
    height: f64,
}

impl NullBackend {
    pub fn new() -> Self {
        Self {
            dpr: 1.0,
            width: 0.0,
            height: 0.0,
        }
    }
}

impl RenderBackend for NullBackend {
    fn begin_frame(&mut self, width: f64, height: f64, dpr: f64) {
        self.width = width;
        self.height = height;
        self.dpr = dpr;
    }

    fn end_frame(&mut self) {}

    fn dpr(&self) -> f64 {
        self.dpr
    }

    fn size(&self) -> (f64, f64) {
        (self.width, self.height)
    }

    fn clear(&mut self, _color: Color) {}
    fn clear_rect(&mut self, _rect: Rect) {}

    fn fill_path(&mut self, _path: &Path, _style: &FillStyle) {}
    fn stroke_path(&mut self, _path: &Path, _style: &LineStyle) {}

    fn text(&mut self, _text: &str, _pos: Point, _style: &TextStyle) {}

    fn measure_text(&self, text: &str, _style: &TextStyle) -> TextMetrics {
        // Rough approximation
        TextMetrics {
            width: text.len() as f64 * 7.0,
            height: 14.0,
            ascent: 11.0,
            descent: 3.0,
        }
    }

    fn image(&mut self, _id: &str, _src: Option<Rect>, _dst: Rect) {}
    fn image_info(&self, _id: &str) -> Option<ImageInfo> {
        None
    }
    fn preload_image(&mut self, _id: &str, _url: &str) {}

    fn push_clip(&mut self, _rect: Rect) {}
    fn pop_clip(&mut self) {}
    fn push_transform(&mut self, _transform: Transform2D) {}
    fn pop_transform(&mut self) {}
    fn push_layer(&mut self, _opacity: f64) {}
    fn pop_layer(&mut self) {}
    fn set_alpha(&mut self, _alpha: f64) {}
    fn save(&mut self) {}
    fn restore(&mut self) {}
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_null_backend() {
        let mut backend = NullBackend::new();
        backend.begin_frame(800.0, 600.0, 2.0);

        assert_eq!(backend.dpr(), 2.0);
        assert_eq!(backend.size(), (800.0, 600.0));

        backend.clear(Color::BLACK);
        backend.fill_rect(Rect::new(0.0, 0.0, 100.0, 100.0), Color::WHITE);

        backend.end_frame();
    }

    #[test]
    fn test_text_metrics() {
        let backend = NullBackend::new();
        let style = TextStyle::default();
        let metrics = backend.measure_text("Hello", &style);

        assert!(metrics.width > 0.0);
        assert!(metrics.height > 0.0);
    }
}
