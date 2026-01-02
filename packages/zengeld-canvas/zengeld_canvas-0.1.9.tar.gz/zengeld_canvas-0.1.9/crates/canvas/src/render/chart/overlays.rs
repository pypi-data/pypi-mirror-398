//! Overlay rendering functions
//!
//! Renders chart overlays (grid, legend, watermark) to RenderCommands.

use super::super::engine::{
    Color, FontWeight, LineStyle as RenderLineStyle, Point, Rect, RenderBatch, RenderCommand,
    TextAlign, TextBaseline, TextStyle, crisp_coord,
};
use crate::model::overlays::{GridOptions, Legend, LegendData, Watermark};

// =============================================================================
// Grid Rendering
// =============================================================================

/// Render grid lines
///
/// Draws horizontal (price) and vertical (time) grid lines with configurable
/// dash patterns and colors. Uses GridLine commands for optimized rendering.
///
/// # Arguments
/// * `batch` - Render batch to append commands to
/// * `options` - Grid configuration (colors, visibility, line styles)
/// * `chart_rect` - Chart bounds for line start/end coordinates
/// * `h_lines` - Horizontal grid lines as (y_pixel, price) pairs
/// * `v_lines` - Vertical grid lines as (x_pixel, timestamp) pairs
/// * `dpr` - Device pixel ratio for crisp rendering
pub fn render_grid(
    batch: &mut RenderBatch,
    options: &GridOptions,
    chart_rect: Rect,
    h_lines: &[(f64, f64)],
    v_lines: &[(f64, i64)],
    dpr: f64,
) {
    // Render horizontal lines (price axis)
    if options.horz_lines.visible {
        let color =
            Color::from_css(&options.horz_lines.color).unwrap_or(Color::rgba(42, 46, 57, 153)); // Default grid color

        for &(y, _price) in h_lines {
            if y < chart_rect.y || y > chart_rect.bottom() {
                continue; // Skip out-of-bounds lines
            }

            let y_crisp = crisp_coord(y, dpr);

            // Check if we need dashed line
            let dash = options.horz_lines.style.dash_pattern(1.0);

            if dash.is_empty() {
                // Solid line - use optimized GridLine command
                batch.push(RenderCommand::GridLine {
                    is_horizontal: true,
                    pos: y_crisp,
                    start: chart_rect.x,
                    end: chart_rect.right(),
                    color,
                });
            } else {
                // Dashed line - use Line command with style
                let style = RenderLineStyle {
                    color,
                    width: 1.0,
                    dash: Some(dash),
                    ..Default::default()
                };
                batch.push(RenderCommand::Line {
                    from: Point::new(chart_rect.x, y_crisp),
                    to: Point::new(chart_rect.right(), y_crisp),
                    style,
                });
            }
        }
    }

    // Render vertical lines (time axis)
    if options.vert_lines.visible {
        let color =
            Color::from_css(&options.vert_lines.color).unwrap_or(Color::rgba(42, 46, 57, 153));

        for &(x, _timestamp) in v_lines {
            if x < chart_rect.x || x > chart_rect.right() {
                continue; // Skip out-of-bounds lines
            }

            let x_crisp = crisp_coord(x, dpr);

            let dash = options.vert_lines.style.dash_pattern(1.0);

            if dash.is_empty() {
                // Solid line
                batch.push(RenderCommand::GridLine {
                    is_horizontal: false,
                    pos: x_crisp,
                    start: chart_rect.y,
                    end: chart_rect.bottom(),
                    color,
                });
            } else {
                // Dashed line
                let style = RenderLineStyle {
                    color,
                    width: 1.0,
                    dash: Some(dash),
                    ..Default::default()
                };
                batch.push(RenderCommand::Line {
                    from: Point::new(x_crisp, chart_rect.y),
                    to: Point::new(x_crisp, chart_rect.bottom()),
                    style,
                });
            }
        }
    }
}

// =============================================================================
// Legend Rendering
// =============================================================================

/// Render legend (OHLC display)
///
/// Displays formatted OHLC values, change, and percentage change at a
/// corner of the chart.
///
/// # Arguments
/// * `batch` - Render batch to append commands to
/// * `legend` - Legend configuration (position, visibility, formatting)
/// * `data` - Legend data to display (OHLC values, previous close)
/// * `chart_rect` - Chart bounds for position calculation
/// * `dpr` - Device pixel ratio (currently unused but kept for consistency)
pub fn render_legend(
    batch: &mut RenderBatch,
    legend: &Legend,
    data: &LegendData,
    chart_rect: Rect,
    _dpr: f64,
) {
    if !legend.visible {
        return;
    }

    // Format the legend text
    let price_step = 0.01; // Could be passed as parameter
    let text = data.format(legend, price_step);

    // Measure text width (approximate - would need actual measurement in real implementation)
    let char_width = legend.font_size * 0.6; // Approximate monospace width
    let text_width = text.len() as f64 * char_width;

    // Calculate position based on legend settings
    let (x, y) = legend.calc_position(chart_rect.width, chart_rect.height, text_width);
    let pos = Point::new(chart_rect.x + x, chart_rect.y + y);

    // Determine text color
    let text_color = if let Some(ref color_str) = legend.text_color {
        Color::from_css(color_str).unwrap_or(Color::rgba(178, 181, 190, 255))
    } else {
        Color::rgba(178, 181, 190, 255) // Default theme color
    };

    let text_style = TextStyle {
        font_size: legend.font_size,
        color: text_color,
        align: TextAlign::Left,
        baseline: TextBaseline::Top,
        font_family: "Trebuchet MS, Arial, sans-serif".to_string(),
        ..Default::default()
    };

    // Render with background if specified
    if let Some(ref bg_color_str) = legend.background_color {
        let bg_color = Color::from_css(bg_color_str).unwrap_or(Color::rgba(30, 34, 45, 230));

        batch.push(RenderCommand::TextWithBackground {
            text,
            pos,
            style: text_style,
            background: bg_color,
            padding: legend.padding,
        });
    } else {
        // No background
        batch.push(RenderCommand::Text {
            text,
            pos,
            style: text_style,
        });
    }
}

// =============================================================================
// Watermark Rendering
// =============================================================================

/// Render watermark
///
/// Displays multi-line text watermark with configurable alignment and styling.
/// Supports center, corner, and edge positioning.
///
/// # Arguments
/// * `batch` - Render batch to append commands to
/// * `watermark` - Watermark configuration (lines, alignment, visibility)
/// * `chart_rect` - Chart bounds for position calculation
/// * `dpr` - Device pixel ratio (currently unused but kept for consistency)
pub fn render_watermark(
    batch: &mut RenderBatch,
    watermark: &Watermark,
    chart_rect: Rect,
    _dpr: f64,
) {
    if !watermark.visible || watermark.lines.is_empty() {
        return;
    }

    // Simple text width measurement function (approximate)
    let measure_text = |text: &str, font: &str| -> f64 {
        // Extract font size from CSS font string
        let font_size = font
            .split_whitespace()
            .find_map(|part| {
                if part.ends_with("px") {
                    part.trim_end_matches("px").parse::<f64>().ok()
                } else {
                    None
                }
            })
            .unwrap_or(48.0);

        text.len() as f64 * font_size * 0.6 // Approximate width
    };

    // Calculate positions for all lines
    let positions = watermark.calc_positions(chart_rect.width, chart_rect.height, measure_text);

    // Render each line
    for (x, y, line) in positions {
        let color = Color::from_css(&line.color).unwrap_or(Color::rgba(171, 71, 188, 77)); // Default watermark color with alpha

        let text_style = TextStyle {
            font_family: line.font_family.clone(),
            font_size: line.font_size,
            font_weight: match line.font_style {
                crate::model::overlays::watermark::FontStyle::Bold
                | crate::model::overlays::watermark::FontStyle::BoldItalic => FontWeight::Bold,
                _ => FontWeight::Normal,
            },
            color,
            align: TextAlign::Left, // Position is pre-calculated
            baseline: TextBaseline::Top,
        };

        let pos = Point::new(chart_rect.x + x, chart_rect.y + y);

        // Check if italic (would need TextStyle enhancement for italic support)
        // For now, render as normal text
        batch.push(RenderCommand::Text {
            text: line.text.clone(),
            pos,
            style: text_style,
        });
    }
}

#[cfg(test)]
mod tests {
    use super::*;
    use crate::WatermarkLine;

    #[test]
    fn test_render_grid_horizontal() {
        let mut batch = RenderBatch::new();
        let options = GridOptions::default();
        let chart_rect = Rect::new(0.0, 0.0, 800.0, 600.0);
        let h_lines = vec![(100.0, 50000.0), (200.0, 50100.0)];
        let v_lines = vec![];

        render_grid(&mut batch, &options, chart_rect, &h_lines, &v_lines, 1.0);

        assert_eq!(batch.len(), 2); // Two horizontal lines
    }

    #[test]
    fn test_render_grid_vertical() {
        let mut batch = RenderBatch::new();
        let options = GridOptions::default();
        let chart_rect = Rect::new(0.0, 0.0, 800.0, 600.0);
        let h_lines = vec![];
        let v_lines = vec![(100.0, 1699920000), (200.0, 1699920060)];

        render_grid(&mut batch, &options, chart_rect, &h_lines, &v_lines, 1.0);

        assert_eq!(batch.len(), 2); // Two vertical lines
    }

    // Note: Crosshair tests removed - Crosshair type was moved to UI layer

    #[test]
    fn test_render_legend() {
        let mut batch = RenderBatch::new();
        let legend = Legend::default();
        let data = LegendData {
            open: 50000.0,
            high: 50200.0,
            low: 49800.0,
            close: 50100.0,
            prev_close: Some(50000.0),
        };
        let chart_rect = Rect::new(0.0, 0.0, 800.0, 600.0);

        render_legend(&mut batch, &legend, &data, chart_rect, 1.0);

        assert_eq!(batch.len(), 1); // One text command
    }

    // Note: Tooltip tests removed - Tooltip type was moved to UI layer

    #[test]
    fn test_render_watermark() {
        let mut batch = RenderBatch::new();
        let watermark = Watermark::simple("TEST WATERMARK");
        let chart_rect = Rect::new(0.0, 0.0, 800.0, 600.0);

        render_watermark(&mut batch, &watermark, chart_rect, 1.0);

        assert_eq!(batch.len(), 1); // One text command
    }

    #[test]
    fn test_render_watermark_multiline() {
        let mut batch = RenderBatch::new();
        let lines = vec![
            WatermarkLine::new("Line 1", "#ffffff", 24.0),
            WatermarkLine::new("Line 2", "#ffffff", 20.0),
        ];
        let watermark = Watermark::multi_line(lines);
        let chart_rect = Rect::new(0.0, 0.0, 800.0, 600.0);

        render_watermark(&mut batch, &watermark, chart_rect, 1.0);

        assert_eq!(batch.len(), 2); // Two text commands
    }

    #[test]
    fn test_grid_respects_visibility() {
        let mut batch = RenderBatch::new();
        let mut options = GridOptions::default();
        options.horz_lines.visible = false;
        let chart_rect = Rect::new(0.0, 0.0, 800.0, 600.0);
        let h_lines = vec![(100.0, 50000.0)];
        let v_lines = vec![(100.0, 1699920000)];

        render_grid(&mut batch, &options, chart_rect, &h_lines, &v_lines, 1.0);

        assert_eq!(batch.len(), 1); // Only vertical line
    }
}
