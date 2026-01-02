//! Render commands - atomic drawing operations
//!
//! Each command represents a single, self-contained draw operation
//! that can be serialized, batched, or executed directly.

use super::path::Path;
use super::types::{Color, FillStyle, LineStyle, Point, Rect, TextStyle, Transform2D};
use serde::{Deserialize, Serialize};

/// Atomic render command
///
/// Commands are designed to be:
/// - Self-contained (no external state needed)
/// - Serializable (for WASM/PyO3 export)
/// - Efficient (minimal allocations)
#[derive(Clone, Debug, Serialize, Deserialize)]
pub enum RenderCommand {
    // =========================================================================
    // Shape commands (most common, optimized paths)
    // =========================================================================
    /// Fill a path
    FillPath { path: Path, style: FillStyle },

    /// Stroke a path
    StrokePath { path: Path, style: LineStyle },

    /// Fill rectangle (optimized, no path allocation)
    FillRect { rect: Rect, color: Color },

    /// Stroke rectangle
    StrokeRect { rect: Rect, style: LineStyle },

    /// Draw line (optimized for single lines)
    Line {
        from: Point,
        to: Point,
        style: LineStyle,
    },

    /// Draw multiple connected lines (polyline)
    Polyline {
        points: Vec<Point>,
        style: LineStyle,
    },

    /// Fill circle
    FillCircle {
        center: Point,
        radius: f64,
        color: Color,
    },

    /// Stroke circle
    StrokeCircle {
        center: Point,
        radius: f64,
        style: LineStyle,
    },

    /// Fill ellipse
    FillEllipse {
        center: Point,
        rx: f64,
        ry: f64,
        rotation: f64,
        color: Color,
    },

    /// Stroke ellipse
    StrokeEllipse {
        center: Point,
        rx: f64,
        ry: f64,
        rotation: f64,
        style: LineStyle,
    },

    /// Stroke arc
    StrokeArc {
        center: Point,
        radius: f64,
        start_angle: f64,
        end_angle: f64,
        style: LineStyle,
    },

    // =========================================================================
    // Text commands
    // =========================================================================
    /// Draw text
    Text {
        text: String,
        pos: Point,
        style: TextStyle,
    },

    /// Draw rotated text
    TextRotated {
        text: String,
        pos: Point,
        angle: f64,
        style: TextStyle,
    },

    /// Draw text with background
    TextWithBackground {
        text: String,
        pos: Point,
        style: TextStyle,
        background: Color,
        padding: f64,
    },

    // =========================================================================
    // Image commands
    // =========================================================================
    /// Draw image
    Image {
        /// Image identifier (URL, data URL, or cache key)
        id: String,
        /// Source rectangle within image (None = full image)
        src: Option<Rect>,
        /// Destination rectangle on canvas
        dst: Rect,
    },

    // =========================================================================
    // State commands
    // =========================================================================
    /// Push clip rectangle
    PushClip { rect: Rect },

    /// Pop clip (restore previous clip)
    PopClip,

    /// Push transform
    PushTransform { transform: Transform2D },

    /// Pop transform
    PopTransform,

    /// Push layer with opacity
    PushLayer { opacity: f64 },

    /// Pop layer
    PopLayer,

    /// Set global alpha (affects all subsequent commands until reset)
    SetAlpha { alpha: f64 },

    /// Save current state (transform, clip, alpha)
    Save,

    /// Restore previously saved state
    Restore,

    // =========================================================================
    // Curve commands (for complex paths without full Path allocation)
    // =========================================================================
    /// Quadratic bezier curve
    QuadraticCurveTo {
        start: Point,
        control: Point,
        end: Point,
        style: LineStyle,
    },

    /// Cubic bezier curve
    BezierCurveTo {
        start: Point,
        control1: Point,
        control2: Point,
        end: Point,
        style: LineStyle,
    },

    /// Filled polygon (closed shape)
    FillPolygon {
        points: Vec<Point>,
        style: FillStyle,
    },

    /// Stroked polygon (closed shape)
    StrokePolygon {
        points: Vec<Point>,
        style: LineStyle,
    },

    /// Rounded rectangle fill
    FillRoundedRect {
        rect: Rect,
        radius: f64,
        color: Color,
    },

    /// Rounded rectangle stroke
    StrokeRoundedRect {
        rect: Rect,
        radius: f64,
        style: LineStyle,
    },

    /// Fill arc (pie slice)
    FillArc {
        center: Point,
        radius: f64,
        start_angle: f64,
        end_angle: f64,
        color: Color,
    },

    // =========================================================================
    // Composite commands (for complex shapes)
    // =========================================================================
    /// Draw candlestick (optimized for chart rendering)
    Candlestick {
        x: f64,
        open_y: f64,
        high_y: f64,
        low_y: f64,
        close_y: f64,
        width: f64,
        body_color: Color,
        wick_color: Color,
    },

    /// Draw histogram bar
    HistogramBar {
        x: f64,
        y: f64,
        width: f64,
        height: f64,
        color: Color,
    },

    /// Draw grid line (horizontal or vertical)
    GridLine {
        is_horizontal: bool,
        pos: f64,   // Y for horizontal, X for vertical
        start: f64, // X start for horizontal, Y start for vertical
        end: f64,   // X end for horizontal, Y end for vertical
        color: Color,
    },
}

impl RenderCommand {
    /// Get bounding rectangle of this command
    pub fn bounds(&self) -> Option<Rect> {
        match self {
            RenderCommand::FillPath { path, .. } => Some(path.bounds()),
            RenderCommand::StrokePath { path, style } => {
                Some(path.bounds().expand(style.width / 2.0))
            }
            RenderCommand::FillRect { rect, .. } => Some(*rect),
            RenderCommand::StrokeRect { rect, style } => Some(rect.expand(style.width / 2.0)),
            RenderCommand::Line { from, to, style } => {
                Some(Rect::from_points(*from, *to).expand(style.width / 2.0))
            }
            RenderCommand::Polyline { points, style } => {
                if points.is_empty() {
                    return None;
                }
                let mut min_x = f64::INFINITY;
                let mut min_y = f64::INFINITY;
                let mut max_x = f64::NEG_INFINITY;
                let mut max_y = f64::NEG_INFINITY;
                for p in points {
                    min_x = min_x.min(p.x);
                    min_y = min_y.min(p.y);
                    max_x = max_x.max(p.x);
                    max_y = max_y.max(p.y);
                }
                Some(
                    Rect::new(min_x, min_y, max_x - min_x, max_y - min_y).expand(style.width / 2.0),
                )
            }
            RenderCommand::FillCircle { center, radius, .. }
            | RenderCommand::StrokeCircle { center, radius, .. } => Some(Rect::new(
                center.x - radius,
                center.y - radius,
                radius * 2.0,
                radius * 2.0,
            )),
            RenderCommand::FillEllipse { center, rx, ry, .. }
            | RenderCommand::StrokeEllipse { center, rx, ry, .. } => {
                Some(Rect::new(center.x - rx, center.y - ry, rx * 2.0, ry * 2.0))
            }
            RenderCommand::StrokeArc { center, radius, .. } => Some(Rect::new(
                center.x - radius,
                center.y - radius,
                radius * 2.0,
                radius * 2.0,
            )),
            RenderCommand::Text { pos, .. }
            | RenderCommand::TextRotated { pos, .. }
            | RenderCommand::TextWithBackground { pos, .. } => {
                // Text bounds need actual measurement, return approximate
                Some(Rect::new(pos.x, pos.y - 10.0, 100.0, 20.0))
            }
            RenderCommand::Image { dst, .. } => Some(*dst),
            RenderCommand::Candlestick {
                x,
                high_y,
                low_y,
                width,
                ..
            } => Some(Rect::new(x - width / 2.0, *high_y, *width, low_y - high_y)),
            RenderCommand::HistogramBar {
                x,
                y,
                width,
                height,
                ..
            } => Some(Rect::new(*x, *y, *width, *height)),
            RenderCommand::GridLine {
                is_horizontal,
                pos,
                start,
                end,
                ..
            } => {
                if *is_horizontal {
                    Some(Rect::new(*start, *pos, end - start, 1.0))
                } else {
                    Some(Rect::new(*pos, *start, 1.0, end - start))
                }
            }
            // Bezier curves - use bounding box of control points
            RenderCommand::QuadraticCurveTo {
                start,
                control,
                end,
                style,
            } => {
                let min_x = start.x.min(control.x).min(end.x);
                let max_x = start.x.max(control.x).max(end.x);
                let min_y = start.y.min(control.y).min(end.y);
                let max_y = start.y.max(control.y).max(end.y);
                Some(
                    Rect::new(min_x, min_y, max_x - min_x, max_y - min_y).expand(style.width / 2.0),
                )
            }
            RenderCommand::BezierCurveTo {
                start,
                control1,
                control2,
                end,
                style,
            } => {
                let min_x = start.x.min(control1.x).min(control2.x).min(end.x);
                let max_x = start.x.max(control1.x).max(control2.x).max(end.x);
                let min_y = start.y.min(control1.y).min(control2.y).min(end.y);
                let max_y = start.y.max(control1.y).max(control2.y).max(end.y);
                Some(
                    Rect::new(min_x, min_y, max_x - min_x, max_y - min_y).expand(style.width / 2.0),
                )
            }
            RenderCommand::FillPolygon { points, .. }
            | RenderCommand::StrokePolygon { points, .. } => {
                if points.is_empty() {
                    return None;
                }
                let mut min_x = f64::INFINITY;
                let mut min_y = f64::INFINITY;
                let mut max_x = f64::NEG_INFINITY;
                let mut max_y = f64::NEG_INFINITY;
                for p in points {
                    min_x = min_x.min(p.x);
                    min_y = min_y.min(p.y);
                    max_x = max_x.max(p.x);
                    max_y = max_y.max(p.y);
                }
                Some(Rect::new(min_x, min_y, max_x - min_x, max_y - min_y))
            }
            RenderCommand::FillRoundedRect { rect, .. } => Some(*rect),
            RenderCommand::StrokeRoundedRect { rect, style, .. } => {
                Some(rect.expand(style.width / 2.0))
            }
            RenderCommand::FillArc { center, radius, .. } => Some(Rect::new(
                center.x - radius,
                center.y - radius,
                radius * 2.0,
                radius * 2.0,
            )),
            // State commands don't have bounds
            RenderCommand::PushClip { .. }
            | RenderCommand::PopClip
            | RenderCommand::PushTransform { .. }
            | RenderCommand::PopTransform
            | RenderCommand::PushLayer { .. }
            | RenderCommand::PopLayer
            | RenderCommand::SetAlpha { .. }
            | RenderCommand::Save
            | RenderCommand::Restore => None,
        }
    }

    /// Check if this command affects state (needs push/pop)
    pub fn is_state_command(&self) -> bool {
        matches!(
            self,
            RenderCommand::PushClip { .. }
                | RenderCommand::PopClip
                | RenderCommand::PushTransform { .. }
                | RenderCommand::PopTransform
                | RenderCommand::PushLayer { .. }
                | RenderCommand::PopLayer
                | RenderCommand::SetAlpha { .. }
                | RenderCommand::Save
                | RenderCommand::Restore
        )
    }
}

// =============================================================================
// Command builders for common patterns
// =============================================================================

/// Create a horizontal grid line command
#[inline]
pub fn h_grid_line(y: f64, x_start: f64, x_end: f64, color: Color) -> RenderCommand {
    RenderCommand::GridLine {
        is_horizontal: true,
        pos: y,
        start: x_start,
        end: x_end,
        color,
    }
}

/// Create a vertical grid line command
#[inline]
pub fn v_grid_line(x: f64, y_start: f64, y_end: f64, color: Color) -> RenderCommand {
    RenderCommand::GridLine {
        is_horizontal: false,
        pos: x,
        start: y_start,
        end: y_end,
        color,
    }
}

/// Parameters for creating a candlestick command
#[derive(Clone, Copy, Debug)]
pub struct CandlestickParams {
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
    /// Whether this is a bullish (up) candle
    pub is_bullish: bool,
    /// Color for bullish candles
    pub up_color: Color,
    /// Color for bearish candles
    pub down_color: Color,
}

/// Create a candlestick command from parameters
#[inline]
pub fn candlestick(params: CandlestickParams) -> RenderCommand {
    let color = if params.is_bullish {
        params.up_color
    } else {
        params.down_color
    };
    RenderCommand::Candlestick {
        x: params.x,
        open_y: params.open_y,
        high_y: params.high_y,
        low_y: params.low_y,
        close_y: params.close_y,
        width: params.width,
        body_color: color,
        wick_color: color,
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_command_bounds() {
        let cmd = RenderCommand::FillRect {
            rect: Rect::new(10.0, 20.0, 100.0, 50.0),
            color: Color::WHITE,
        };
        assert_eq!(cmd.bounds(), Some(Rect::new(10.0, 20.0, 100.0, 50.0)));
    }

    #[test]
    fn test_line_bounds_with_stroke() {
        let cmd = RenderCommand::Line {
            from: Point::new(0.0, 0.0),
            to: Point::new(100.0, 100.0),
            style: LineStyle::solid(Color::WHITE, 4.0),
        };
        let bounds = cmd.bounds().unwrap();
        // Should include stroke width
        assert!(bounds.x < 0.0);
        assert!(bounds.right() > 100.0);
    }
}
