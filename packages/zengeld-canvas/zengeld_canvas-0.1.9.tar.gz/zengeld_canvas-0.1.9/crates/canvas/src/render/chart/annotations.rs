//! Annotation rendering functions
//!
//! Renders chart annotations (markers, price lines) to RenderCommands.

use super::super::engine::{
    Color, FillStyle, FontWeight, LineCap, LineJoin, LineStyle, Point, RenderBatch, RenderCommand,
    TextAlign, TextBaseline, TextStyle, crisp_coord,
};
use crate::model::annotations::{
    LineStyle as AnnotationLineStyle, Marker, MarkerPosition, MarkerShape, PriceLine,
};

// =============================================================================
// Marker Rendering
// =============================================================================

/// Render markers (buy/sell signals, etc.)
///
/// # Arguments
/// * `batch` - Render batch to accumulate commands
/// * `markers` - Slice of markers to render
/// * `bar_to_x` - Function to convert bar index to X coordinate
/// * `price_to_y` - Function to convert price to Y coordinate
/// * `bar_high` - Function to get bar high price
/// * `bar_low` - Function to get bar low price
/// * `dpr` - Device pixel ratio for crisp rendering
pub fn render_markers(
    batch: &mut RenderBatch,
    markers: &[Marker],
    bar_to_x: impl Fn(usize) -> f64,
    price_to_y: impl Fn(f64) -> f64,
    bar_high: impl Fn(usize) -> f64,
    bar_low: impl Fn(usize) -> f64,
    _dpr: f64,
) {
    const BASE_SIZE: f64 = 10.0;
    const PADDING: f64 = 3.0;

    for marker in markers {
        // Skip markers without bar index
        let bar_idx = match marker.bar_idx {
            Some(idx) => idx,
            None => continue,
        };

        // Calculate X coordinate (center of bar)
        let x = bar_to_x(bar_idx);

        // Calculate final marker size
        let marker_size = BASE_SIZE * marker.shape.size_multiplier() * marker.size;

        // Skip if size is zero or negative
        if marker_size <= 0.0 {
            continue;
        }

        // Calculate Y coordinate based on position
        let y = match marker.position {
            MarkerPosition::AboveBar => {
                let high = bar_high(bar_idx);
                let price_y = price_to_y(high);
                price_y - marker_size - PADDING
            }
            MarkerPosition::BelowBar => {
                let low = bar_low(bar_idx);
                let price_y = price_to_y(low);
                price_y + marker_size + PADDING
            }
            MarkerPosition::InBar => {
                let high = bar_high(bar_idx);
                let low = bar_low(bar_idx);
                let mid_price = (high + low) / 2.0;
                price_to_y(mid_price)
            }
            MarkerPosition::AtPriceTop => {
                let price = match marker.price {
                    Some(p) => p,
                    None => continue, // Skip if price not specified
                };
                let price_y = price_to_y(price);
                price_y - marker_size / 2.0
            }
            MarkerPosition::AtPriceBottom => {
                let price = match marker.price {
                    Some(p) => p,
                    None => continue,
                };
                let price_y = price_to_y(price);
                price_y + marker_size / 2.0
            }
            MarkerPosition::AtPriceMiddle => {
                let price = match marker.price {
                    Some(p) => p,
                    None => continue,
                };
                price_to_y(price)
            }
        };

        // Parse marker color
        let color = Color::from_css(&marker.color).unwrap_or(Color::rgb(41, 98, 255));

        // Render marker shape
        render_marker_shape(batch, marker.shape, x, y, marker_size, color);

        // Render text if present
        if let Some(ref text) = marker.text {
            if !text.is_empty() {
                let text_x = x + marker_size / 2.0 + 4.0; // Offset right from marker
                let text_style = TextStyle {
                    font_family: "sans-serif".to_string(),
                    font_size: 11.0,
                    font_weight: FontWeight::Normal,
                    color,
                    align: TextAlign::Left,
                    baseline: TextBaseline::Middle,
                };

                batch.push(RenderCommand::Text {
                    text: text.clone(),
                    pos: Point::new(text_x, y),
                    style: text_style,
                });
            }
        }
    }
}

/// Render a single marker shape
///
/// # Arguments
/// * `batch` - Render batch to accumulate commands
/// * `shape` - Marker shape type
/// * `x` - X coordinate of marker center
/// * `y` - Y coordinate of marker center
/// * `size` - Marker size in pixels
/// * `color` - Marker color
fn render_marker_shape(
    batch: &mut RenderBatch,
    shape: MarkerShape,
    x: f64,
    y: f64,
    size: f64,
    color: Color,
) {
    match shape {
        MarkerShape::Circle => {
            // Fill circle
            batch.push(RenderCommand::FillCircle {
                center: Point::new(x, y),
                radius: size / 2.0,
                color,
            });
        }

        MarkerShape::Square => {
            // Fill square (centered)
            let half_size = size / 2.0;
            let points = vec![
                Point::new(x - half_size, y - half_size),
                Point::new(x + half_size, y - half_size),
                Point::new(x + half_size, y + half_size),
                Point::new(x - half_size, y + half_size),
            ];
            batch.push(RenderCommand::FillPolygon {
                points,
                style: FillStyle::Solid(color),
            });
        }

        MarkerShape::ArrowUp => {
            // Triangle pointing up
            let half_width = size / 2.0;
            let height = size * 0.866; // sqrt(3)/2 for equilateral triangle
            let points = vec![
                Point::new(x, y - height * 0.5),              // Top point
                Point::new(x + half_width, y + height * 0.5), // Bottom right
                Point::new(x - half_width, y + height * 0.5), // Bottom left
            ];
            batch.push(RenderCommand::FillPolygon {
                points,
                style: FillStyle::Solid(color),
            });
        }

        MarkerShape::ArrowDown => {
            // Triangle pointing down
            let half_width = size / 2.0;
            let height = size * 0.866;
            let points = vec![
                Point::new(x, y + height * 0.5),              // Bottom point
                Point::new(x - half_width, y - height * 0.5), // Top left
                Point::new(x + half_width, y - height * 0.5), // Top right
            ];
            batch.push(RenderCommand::FillPolygon {
                points,
                style: FillStyle::Solid(color),
            });
        }
    }
}

// =============================================================================
// Price Line Rendering
// =============================================================================

/// Render price lines (horizontal lines at price levels)
///
/// # Arguments
/// * `batch` - Render batch to accumulate commands
/// * `price_lines` - Slice of price lines to render
/// * `price_to_y` - Function to convert price to Y coordinate
/// * `chart_left` - Left edge of chart area
/// * `chart_right` - Right edge of chart area
/// * `dpr` - Device pixel ratio for crisp rendering
pub fn render_price_lines(
    batch: &mut RenderBatch,
    price_lines: &[PriceLine],
    price_to_y: impl Fn(f64) -> f64,
    chart_left: f64,
    chart_right: f64,
    dpr: f64,
) {
    for price_line in price_lines {
        // Skip if line is not visible
        if !price_line.line_visible {
            continue;
        }

        // Calculate Y coordinate for the price level
        let y = price_to_y(price_line.price);

        // Make Y coordinate crisp for 1px lines
        let crisp_y = crisp_coord(y, dpr);

        // Parse color
        let color = Color::from_css(&price_line.color).unwrap_or(Color::rgb(41, 98, 255));

        // Convert annotation line style to render line style
        let line_style = annotation_line_style_to_render(
            price_line.line_style,
            color,
            price_line.line_width as f64,
        );

        // Draw the horizontal line
        batch.push(RenderCommand::Line {
            from: Point::new(chart_left, crisp_y),
            to: Point::new(chart_right, crisp_y),
            style: line_style,
        });

        // Render title text if present
        if !price_line.title.is_empty() {
            let text_x = chart_left + 8.0; // Offset from left edge
            let text_y = crisp_y - 4.0; // Offset above line

            let text_style = TextStyle {
                font_family: "sans-serif".to_string(),
                font_size: 11.0,
                font_weight: FontWeight::Normal,
                color,
                align: TextAlign::Left,
                baseline: TextBaseline::Bottom,
            };

            // Use text with background for better visibility
            let bg_color = Color::rgba(0, 0, 0, 180); // Semi-transparent black
            batch.push(RenderCommand::TextWithBackground {
                text: price_line.title.clone(),
                pos: Point::new(text_x, text_y),
                style: text_style,
                background: bg_color,
                padding: 3.0,
            });
        }
    }
}

/// Convert annotation LineStyle to render LineStyle
///
/// # Arguments
/// * `style` - Annotation line style enum
/// * `color` - Line color
/// * `width` - Line width in pixels
///
/// # Returns
/// Render LineStyle with appropriate dash pattern
fn annotation_line_style_to_render(
    style: AnnotationLineStyle,
    color: Color,
    width: f64,
) -> LineStyle {
    match style {
        AnnotationLineStyle::Solid => LineStyle::solid(color, width),

        AnnotationLineStyle::Dotted => {
            // Pattern: [lineWidth, lineWidth]
            LineStyle {
                color,
                width,
                dash: Some(vec![width, width]),
                cap: LineCap::Round,
                join: LineJoin::Round,
            }
        }

        AnnotationLineStyle::Dashed => {
            // Pattern: [2×lineWidth, 2×lineWidth]
            LineStyle {
                color,
                width,
                dash: Some(vec![2.0 * width, 2.0 * width]),
                cap: LineCap::Butt,
                join: LineJoin::Miter,
            }
        }

        AnnotationLineStyle::LargeDashed => {
            // Pattern: [6×lineWidth, 6×lineWidth]
            LineStyle {
                color,
                width,
                dash: Some(vec![6.0 * width, 6.0 * width]),
                cap: LineCap::Butt,
                join: LineJoin::Miter,
            }
        }

        AnnotationLineStyle::SparseDotted => {
            // Pattern: [lineWidth, 4×lineWidth]
            LineStyle {
                color,
                width,
                dash: Some(vec![width, 4.0 * width]),
                cap: LineCap::Round,
                join: LineJoin::Round,
            }
        }
    }
}

// =============================================================================
// Tests
// =============================================================================

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_annotation_line_style_conversion() {
        let color = Color::rgb(255, 0, 0);
        let width = 2.0;

        // Solid
        let solid = annotation_line_style_to_render(AnnotationLineStyle::Solid, color, width);
        assert_eq!(solid.color, color);
        assert_eq!(solid.width, width);
        assert!(solid.dash.is_none());

        // Dotted
        let dotted = annotation_line_style_to_render(AnnotationLineStyle::Dotted, color, width);
        assert_eq!(dotted.dash, Some(vec![2.0, 2.0]));

        // Dashed
        let dashed = annotation_line_style_to_render(AnnotationLineStyle::Dashed, color, width);
        assert_eq!(dashed.dash, Some(vec![4.0, 4.0]));

        // LargeDashed
        let large = annotation_line_style_to_render(AnnotationLineStyle::LargeDashed, color, width);
        assert_eq!(large.dash, Some(vec![12.0, 12.0]));

        // SparseDotted
        let sparse =
            annotation_line_style_to_render(AnnotationLineStyle::SparseDotted, color, width);
        assert_eq!(sparse.dash, Some(vec![2.0, 8.0]));
    }

    #[test]
    fn test_render_markers_empty() {
        let mut batch = RenderBatch::new();
        let markers: Vec<Marker> = vec![];

        render_markers(
            &mut batch,
            &markers,
            |idx| idx as f64 * 10.0,
            |price| 100.0 - price,
            |_| 50.0,
            |_| 40.0,
            1.0,
        );

        assert_eq!(batch.len(), 0);
    }

    #[test]
    fn test_render_price_lines_empty() {
        let mut batch = RenderBatch::new();
        let price_lines: Vec<PriceLine> = vec![];

        render_price_lines(
            &mut batch,
            &price_lines,
            |price| 100.0 - price,
            0.0,
            1000.0,
            1.0,
        );

        assert_eq!(batch.len(), 0);
    }

    #[test]
    fn test_render_marker_shapes() {
        let mut batch = RenderBatch::new();
        let color = Color::rgb(0, 255, 0);

        // Test each shape
        render_marker_shape(&mut batch, MarkerShape::Circle, 100.0, 100.0, 10.0, color);
        assert_eq!(batch.len(), 1);

        render_marker_shape(&mut batch, MarkerShape::Square, 100.0, 100.0, 10.0, color);
        assert_eq!(batch.len(), 2);

        render_marker_shape(&mut batch, MarkerShape::ArrowUp, 100.0, 100.0, 10.0, color);
        assert_eq!(batch.len(), 3);

        render_marker_shape(
            &mut batch,
            MarkerShape::ArrowDown,
            100.0,
            100.0,
            10.0,
            color,
        );
        assert_eq!(batch.len(), 4);
    }
}
