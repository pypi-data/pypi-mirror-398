//! Series rendering functions
//!
//! Renders chart series data to RenderCommands.
//! These functions are platform-agnostic and work by pushing RenderCommands
//! to a RenderBatch, which can then be executed by any backend.

use super::super::engine::{
    Color, FillStyle, LineStyle, Path, PathBuilder, Point, Rect, RenderBatch, RenderCommand,
    crisp_bar_width, crisp_coord, crisp_rect,
};
use crate::core::catmull_rom_spline;
use crate::model::series::{
    AreaData, AreaStyleOptions, BarData, BarStyleOptions, BaselineData, BaselineStyleOptions,
    CandlestickData, CandlestickStyleOptions, HistogramData, HistogramStyleOptions, LineData,
    LineStyleOptions, LineType,
};

// =============================================================================
// Candlestick Series
// =============================================================================

/// Render candlestick series
///
/// # Arguments
/// * `batch` - RenderBatch to push commands to
/// * `data` - Candlestick data points
/// * `options` - Styling options for candlesticks
/// * `bar_to_x` - Function to convert bar index to X coordinate
/// * `price_to_y` - Function to convert price to Y coordinate
/// * `bar_width` - Base width of each candlestick
/// * `dpr` - Device pixel ratio for crisp rendering
pub fn render_candlesticks(
    batch: &mut RenderBatch,
    data: &[CandlestickData],
    options: &CandlestickStyleOptions,
    bar_to_x: impl Fn(usize) -> f64,
    price_to_y: impl Fn(f64) -> f64,
    bar_width: f64,
    dpr: f64,
) {
    if data.is_empty() {
        return;
    }

    let crisp_width = crisp_bar_width(bar_width, dpr);

    for (i, candle) in data.iter().enumerate() {
        let bar = &candle.bar;

        // Skip invalid bars
        if bar.open.is_nan() || bar.high.is_nan() || bar.low.is_nan() || bar.close.is_nan() {
            continue;
        }

        let x = bar_to_x(i);
        let open_y = price_to_y(bar.open);
        let high_y = price_to_y(bar.high);
        let low_y = price_to_y(bar.low);
        let close_y = price_to_y(bar.close);

        let is_bullish = bar.is_bullish();

        // Determine colors (data overrides take precedence)
        let body_color = if let Some(ref color) = candle.color {
            parse_color(color)
        } else if is_bullish {
            parse_color(&options.up_color)
        } else {
            parse_color(&options.down_color)
        };

        let wick_color = if let Some(ref color) = candle.wick_color {
            parse_color(color)
        } else if !options.wick_color.is_empty() {
            parse_color(&options.wick_color)
        } else if is_bullish {
            parse_color(&options.wick_up_color)
        } else {
            parse_color(&options.wick_down_color)
        };

        let border_color = if let Some(ref color) = candle.border_color {
            Some(parse_color(color))
        } else if !options.border_color.is_empty() {
            Some(parse_color(&options.border_color))
        } else if options.border_visible {
            Some(if is_bullish {
                parse_color(&options.border_up_color)
            } else {
                parse_color(&options.border_down_color)
            })
        } else {
            None
        };

        // Draw wick (vertical line from high to low)
        if options.wick_visible {
            let wick_x = crisp_coord(x, dpr);
            let wick_y1 = crisp_coord(high_y, dpr);
            let wick_y2 = crisp_coord(low_y, dpr);

            batch.push(RenderCommand::Line {
                from: Point::new(wick_x, wick_y1),
                to: Point::new(wick_x, wick_y2),
                style: LineStyle::solid(wick_color, 1.0),
            });
        }

        // Draw body (rectangle from open to close)
        let body_top = open_y.min(close_y);
        let body_bottom = open_y.max(close_y);
        let body_height = (body_bottom - body_top).max(1.0 / dpr); // Minimum 1 device pixel

        let (rect_x, rect_y, rect_w, rect_h) = crisp_rect(
            x - crisp_width / 2.0,
            body_top,
            crisp_width,
            body_height,
            dpr,
        );

        let rect = Rect::new(rect_x, rect_y, rect_w, rect_h);

        // Fill body
        batch.push(RenderCommand::FillRect {
            rect,
            color: body_color,
        });

        // Draw border if enabled
        if let Some(border_col) = border_color {
            batch.push(RenderCommand::StrokeRect {
                rect,
                style: LineStyle::solid(border_col, 1.0),
            });
        }
    }
}

// =============================================================================
// Line Series
// =============================================================================

/// Render line series (Simple, Stepped, Curved)
///
/// # Arguments
/// * `batch` - RenderBatch to push commands to
/// * `data` - Line data points
/// * `options` - Styling options for the line
/// * `bar_to_x` - Function to convert bar index to X coordinate
/// * `price_to_y` - Function to convert price to Y coordinate
/// * `dpr` - Device pixel ratio for crisp rendering
pub fn render_line(
    batch: &mut RenderBatch,
    data: &[LineData],
    options: &LineStyleOptions,
    bar_to_x: impl Fn(usize) -> f64,
    price_to_y: impl Fn(f64) -> f64,
    dpr: f64,
) {
    if !options.line_visible || data.is_empty() {
        return;
    }

    // Collect valid points
    let mut points = Vec::new();
    for (i, item) in data.iter().enumerate() {
        if item.point.value.is_nan() {
            continue;
        }
        let x = bar_to_x(i);
        let y = price_to_y(item.point.value);
        points.push(Point::new(x, y));
    }

    if points.is_empty() {
        return;
    }

    let line_color = parse_color(&options.color);
    let line_width = options.line_width as f64;

    // Build path based on line type
    let path = match options.line_type {
        LineType::Simple => build_simple_line_path(&points),
        LineType::WithSteps => build_step_line_path(&points),
        LineType::Curved => build_curved_line_path(&points, dpr),
    };

    // Draw the line
    batch.push(RenderCommand::StrokePath {
        path,
        style: create_line_style(&options.line_style, line_color, line_width),
    });

    // Draw point markers if enabled
    if options.point_markers_visible {
        if let Some(radius) = options.point_markers_radius {
            for point in &points {
                batch.push(RenderCommand::FillCircle {
                    center: *point,
                    radius,
                    color: line_color,
                });
            }
        }
    }
}

/// Build a simple line path (straight lines between points)
fn build_simple_line_path(points: &[Point]) -> Path {
    if points.is_empty() {
        return Path::new();
    }

    let mut builder = PathBuilder::new();
    builder.move_to(points[0]);
    for point in &points[1..] {
        builder.line_to(*point);
    }
    builder.build()
}

/// Build a step line path (horizontal then vertical)
fn build_step_line_path(points: &[Point]) -> Path {
    if points.is_empty() {
        return Path::new();
    }

    let mut builder = PathBuilder::new();
    builder.move_to(points[0]);

    for i in 1..points.len() {
        // Horizontal line to next X
        builder.line_to(Point::new(points[i].x, points[i - 1].y));
        // Vertical line to next Y
        builder.line_to(points[i]);
    }

    builder.build()
}

/// Build a curved line path using Catmull-Rom splines
fn build_curved_line_path(points: &[Point], _dpr: f64) -> Path {
    if points.len() < 2 {
        return Path::new();
    }

    // Convert to tuples for spline function
    let point_tuples: Vec<(f64, f64)> = points.iter().map(|p| (p.x, p.y)).collect();

    // Generate smooth curve (10 segments per control point)
    let smooth_points = catmull_rom_spline(&point_tuples, 10);

    // Build path
    let mut builder = PathBuilder::new();
    if let Some(&first) = smooth_points.first() {
        builder.move_to(Point::new(first.0, first.1));
        for &(x, y) in &smooth_points[1..] {
            builder.line_to(Point::new(x, y));
        }
    }

    builder.build()
}

// =============================================================================
// Area Series
// =============================================================================

/// Render area series with gradient fill
///
/// # Arguments
/// * `batch` - RenderBatch to push commands to
/// * `data` - Area data points
/// * `options` - Styling options for the area
/// * `bar_to_x` - Function to convert bar index to X coordinate
/// * `price_to_y` - Function to convert price to Y coordinate
/// * `chart_bottom` - Y coordinate of chart bottom (for fill)
/// * `dpr` - Device pixel ratio for crisp rendering
pub fn render_area(
    batch: &mut RenderBatch,
    data: &[AreaData],
    options: &AreaStyleOptions,
    bar_to_x: impl Fn(usize) -> f64,
    price_to_y: impl Fn(f64) -> f64,
    chart_bottom: f64,
    dpr: f64,
) {
    if data.is_empty() {
        return;
    }

    // Collect valid points
    let mut points = Vec::new();
    for (i, item) in data.iter().enumerate() {
        if item.point.value.is_nan() {
            continue;
        }
        let x = bar_to_x(i);
        let y = price_to_y(item.point.value);
        points.push(Point::new(x, y));
    }

    if points.is_empty() {
        return;
    }

    // Create fill path
    let mut builder = PathBuilder::new();

    if options.invert_filled_area {
        // Fill above line (to top)
        builder.move_to(Point::new(points[0].x, 0.0));
        for point in &points {
            builder.line_to(*point);
        }
        builder.line_to(Point::new(points[points.len() - 1].x, 0.0));
    } else {
        // Fill below line (to bottom) - standard
        builder.move_to(Point::new(points[0].x, chart_bottom));
        for point in &points {
            builder.line_to(*point);
        }
        builder.line_to(Point::new(points[points.len() - 1].x, chart_bottom));
    }

    builder.close();
    let fill_path = builder.build();

    // Create gradient fill
    let gradient = FillStyle::LinearGradient {
        start: Point::new(0.0, 0.0),
        end: Point::new(0.0, chart_bottom),
        stops: vec![
            (0.0, parse_color(&options.top_color)),
            (1.0, parse_color(&options.bottom_color)),
        ],
    };

    // Draw fill
    batch.push(RenderCommand::FillPath {
        path: fill_path,
        style: gradient,
    });

    // Draw line
    if options.line_visible {
        let line_color = parse_color(&options.line_color);
        let line_width = options.line_width as f64;

        let line_path = match options.line_type {
            LineType::Simple => build_simple_line_path(&points),
            LineType::WithSteps => build_step_line_path(&points),
            LineType::Curved => build_curved_line_path(&points, dpr),
        };

        batch.push(RenderCommand::StrokePath {
            path: line_path,
            style: create_line_style(&options.line_style, line_color, line_width),
        });
    }

    // Draw point markers if enabled
    if options.point_markers_visible {
        if let Some(radius) = options.point_markers_radius {
            let marker_color = parse_color(&options.line_color);
            for point in &points {
                batch.push(RenderCommand::FillCircle {
                    center: *point,
                    radius,
                    color: marker_color,
                });
            }
        }
    }
}

// =============================================================================
// Bar Series (OHLC bars)
// =============================================================================

/// Render bar series (OHLC bars)
///
/// # Arguments
/// * `batch` - RenderBatch to push commands to
/// * `data` - Bar data points
/// * `options` - Styling options for bars
/// * `bar_to_x` - Function to convert bar index to X coordinate
/// * `price_to_y` - Function to convert price to Y coordinate
/// * `bar_width` - Base width of each bar
/// * `dpr` - Device pixel ratio for crisp rendering
pub fn render_bars(
    batch: &mut RenderBatch,
    data: &[BarData],
    options: &BarStyleOptions,
    bar_to_x: impl Fn(usize) -> f64,
    price_to_y: impl Fn(f64) -> f64,
    bar_width: f64,
    dpr: f64,
) {
    if data.is_empty() {
        return;
    }

    let tick_width = bar_width * 0.3; // Tick extends 30% of bar width

    for (i, bar_data) in data.iter().enumerate() {
        let bar = &bar_data.bar;

        // Skip invalid bars
        if bar.open.is_nan() || bar.high.is_nan() || bar.low.is_nan() || bar.close.is_nan() {
            continue;
        }

        let x = crisp_coord(bar_to_x(i), dpr);
        let open_y = crisp_coord(price_to_y(bar.open), dpr);
        let high_y = crisp_coord(price_to_y(bar.high), dpr);
        let low_y = crisp_coord(price_to_y(bar.low), dpr);
        let close_y = crisp_coord(price_to_y(bar.close), dpr);

        let is_bullish = bar.is_bullish();

        // Determine color
        let color = if let Some(ref col) = bar_data.color {
            parse_color(col)
        } else if is_bullish {
            parse_color(&options.up_color)
        } else {
            parse_color(&options.down_color)
        };

        let line_width = if options.thin_bars { 1.0 } else { 2.0 };
        let style = LineStyle::solid(color, line_width);

        // Draw vertical line from high to low
        batch.push(RenderCommand::Line {
            from: Point::new(x, high_y),
            to: Point::new(x, low_y),
            style: style.clone(),
        });

        // Draw open tick (left)
        if options.open_visible {
            batch.push(RenderCommand::Line {
                from: Point::new(x - tick_width, open_y),
                to: Point::new(x, open_y),
                style: style.clone(),
            });
        }

        // Draw close tick (right)
        batch.push(RenderCommand::Line {
            from: Point::new(x, close_y),
            to: Point::new(x + tick_width, close_y),
            style,
        });
    }
}

// =============================================================================
// Histogram Series
// =============================================================================

/// Parameters for histogram rendering
pub struct HistogramParams<'a, F1, F2>
where
    F1: Fn(usize) -> f64,
    F2: Fn(f64) -> f64,
{
    pub data: &'a [HistogramData],
    pub options: &'a HistogramStyleOptions,
    pub bar_to_x: F1,
    pub price_to_y: F2,
    pub base_value: f64,
    pub bar_width: f64,
    pub dpr: f64,
}

/// Render histogram series
///
/// # Arguments
/// * `batch` - RenderBatch to push commands to
/// * `params` - Histogram rendering parameters
pub fn render_histogram<F1, F2>(batch: &mut RenderBatch, params: HistogramParams<'_, F1, F2>)
where
    F1: Fn(usize) -> f64,
    F2: Fn(f64) -> f64,
{
    let HistogramParams {
        data,
        options,
        bar_to_x,
        price_to_y,
        base_value,
        bar_width,
        dpr,
    } = params;

    if data.is_empty() {
        return;
    }

    let crisp_width = crisp_bar_width(bar_width * 0.8, dpr); // 80% of bar spacing
    let base_y = price_to_y(base_value);

    for (i, item) in data.iter().enumerate() {
        let value = item.point.value;

        if value.is_nan() {
            continue;
        }

        let x = bar_to_x(i);
        let value_y = price_to_y(value);

        // Determine color
        let color = if let Some(ref col) = item.color {
            parse_color(col)
        } else {
            parse_color(&options.color)
        };

        // Determine direction and dimensions
        let (top, height) = if value >= base_value {
            // Bar up (positive value)
            (value_y, (base_y - value_y).max(1.0 / dpr))
        } else {
            // Bar down (negative value)
            (base_y, (value_y - base_y).max(1.0 / dpr))
        };

        // Draw bar
        let (rect_x, rect_y, rect_w, rect_h) =
            crisp_rect(x - crisp_width / 2.0, top, crisp_width, height, dpr);

        batch.push(RenderCommand::FillRect {
            rect: Rect::new(rect_x, rect_y, rect_w, rect_h),
            color,
        });
    }
}

// =============================================================================
// Baseline Series
// =============================================================================

/// Baseline segment (above or below baseline)
struct BaselineSegment {
    points: Vec<Point>,
    is_above: bool,
}

/// Parameters for baseline rendering
pub struct BaselineParams<'a, F1, F2>
where
    F1: Fn(usize) -> f64,
    F2: Fn(f64) -> f64,
{
    pub data: &'a [BaselineData],
    pub options: &'a BaselineStyleOptions,
    pub bar_to_x: F1,
    pub price_to_y: F2,
    pub baseline_value: f64,
    pub chart_bottom: f64,
    pub dpr: f64,
}

/// Render baseline series (split fill above/below)
///
/// # Arguments
/// * `batch` - RenderBatch to push commands to
/// * `params` - Baseline rendering parameters
pub fn render_baseline<F1, F2>(batch: &mut RenderBatch, params: BaselineParams<'_, F1, F2>)
where
    F1: Fn(usize) -> f64,
    F2: Fn(f64) -> f64,
{
    let BaselineParams {
        data,
        options,
        bar_to_x,
        price_to_y,
        baseline_value,
        chart_bottom,
        dpr,
    } = params;

    if data.is_empty() {
        return;
    }

    // Collect valid points
    let mut points = Vec::new();
    for (i, item) in data.iter().enumerate() {
        if item.point.value.is_nan() {
            continue;
        }
        let x = bar_to_x(i);
        let y = price_to_y(item.point.value);
        points.push(Point::new(x, y));
    }

    if points.is_empty() {
        return;
    }

    let base_y = price_to_y(baseline_value);

    // Split into segments above/below baseline
    let segments = split_baseline_segments(&points, base_y);

    // Draw each segment
    for segment in &segments {
        if segment.is_above {
            // Top zone (above baseline)
            render_baseline_segment(
                batch,
                BaselineSegmentParams {
                    points: &segment.points,
                    base_y,
                    gradient_end_y: 0.0,
                    fill_color1: &options.top_fill_color1,
                    fill_color2: &options.top_fill_color2,
                    line_color: &options.top_line_color,
                    options,
                    dpr,
                },
            );
        } else {
            // Bottom zone (below baseline)
            render_baseline_segment(
                batch,
                BaselineSegmentParams {
                    points: &segment.points,
                    base_y,
                    gradient_end_y: chart_bottom,
                    fill_color1: &options.bottom_fill_color1,
                    fill_color2: &options.bottom_fill_color2,
                    line_color: &options.bottom_line_color,
                    options,
                    dpr,
                },
            );
        }
    }
}

/// Split points into segments above/below baseline
fn split_baseline_segments(points: &[Point], base_y: f64) -> Vec<BaselineSegment> {
    let mut segments = Vec::new();
    let mut current_segment = BaselineSegment {
        points: Vec::new(),
        is_above: false,
    };

    for i in 0..points.len() {
        let point = points[i];
        let is_above = point.y < base_y; // Y grows downward

        if current_segment.points.is_empty() {
            // Start new segment
            current_segment.is_above = is_above;
            current_segment.points.push(point);
        } else if current_segment.is_above == is_above {
            // Continue current segment
            current_segment.points.push(point);
        } else {
            // Crossing baseline
            let prev = points[i - 1];

            // Calculate intersection point
            let intersection = calculate_intersection(prev, point, base_y);
            current_segment.points.push(intersection);
            segments.push(current_segment);

            // Start new segment
            current_segment = BaselineSegment {
                points: vec![intersection, point],
                is_above,
            };
        }
    }

    if !current_segment.points.is_empty() {
        segments.push(current_segment);
    }

    segments
}

/// Calculate intersection point with horizontal baseline
fn calculate_intersection(p1: Point, p2: Point, base_y: f64) -> Point {
    if (p2.y - p1.y).abs() < 0.0001 {
        // Nearly horizontal line
        return Point::new((p1.x + p2.x) / 2.0, base_y);
    }

    // Linear interpolation
    let t = (base_y - p1.y) / (p2.y - p1.y);
    let x = p1.x + t * (p2.x - p1.x);

    Point::new(x, base_y)
}

/// Parameters for baseline segment rendering
struct BaselineSegmentParams<'a> {
    points: &'a [Point],
    base_y: f64,
    gradient_end_y: f64,
    fill_color1: &'a str,
    fill_color2: &'a str,
    line_color: &'a str,
    options: &'a BaselineStyleOptions,
    dpr: f64,
}

/// Render a single baseline segment with fill and line
fn render_baseline_segment(batch: &mut RenderBatch, params: BaselineSegmentParams<'_>) {
    let BaselineSegmentParams {
        points,
        base_y,
        gradient_end_y,
        fill_color1,
        fill_color2,
        line_color,
        options,
        dpr,
    } = params;

    if points.is_empty() {
        return;
    }

    // Create fill path
    let mut builder = PathBuilder::new();
    builder.move_to(Point::new(points[0].x, base_y));

    for point in points {
        builder.line_to(*point);
    }

    builder.line_to(Point::new(points[points.len() - 1].x, base_y));
    builder.close();
    let fill_path = builder.build();

    // Create gradient fill
    let gradient = FillStyle::LinearGradient {
        start: Point::new(0.0, base_y),
        end: Point::new(0.0, gradient_end_y),
        stops: vec![
            (0.0, parse_color(fill_color1)),
            (1.0, parse_color(fill_color2)),
        ],
    };

    // Draw fill
    batch.push(RenderCommand::FillPath {
        path: fill_path,
        style: gradient,
    });

    // Draw line
    if options.line_visible {
        let color = parse_color(line_color);
        let width = options.line_width as f64;

        let line_path = match options.line_type {
            LineType::Simple => build_simple_line_path(points),
            LineType::WithSteps => build_step_line_path(points),
            LineType::Curved => build_curved_line_path(points, dpr),
        };

        batch.push(RenderCommand::StrokePath {
            path: line_path,
            style: create_line_style(&options.line_style, color, width),
        });
    }
}

// =============================================================================
// Hollow Candlestick Series
// =============================================================================

/// Render hollow candlestick series
///
/// Hollow candles: bullish candles are outlined (hollow), bearish are filled.
/// This provides a quick visual distinction of trend direction.
///
/// # Arguments
/// * `batch` - RenderBatch to push commands to
/// * `data` - Candlestick data points
/// * `options` - Styling options for candlesticks
/// * `bar_to_x` - Function to convert bar index to X coordinate
/// * `price_to_y` - Function to convert price to Y coordinate
/// * `bar_width` - Base width of each candlestick
/// * `dpr` - Device pixel ratio for crisp rendering
pub fn render_hollow_candles(
    batch: &mut RenderBatch,
    data: &[CandlestickData],
    options: &CandlestickStyleOptions,
    bar_to_x: impl Fn(usize) -> f64,
    price_to_y: impl Fn(f64) -> f64,
    bar_width: f64,
    dpr: f64,
) {
    if data.is_empty() {
        return;
    }

    let crisp_width = crisp_bar_width(bar_width, dpr);

    for (i, candle) in data.iter().enumerate() {
        let bar = &candle.bar;

        if bar.open.is_nan() || bar.high.is_nan() || bar.low.is_nan() || bar.close.is_nan() {
            continue;
        }

        let x = bar_to_x(i);
        let open_y = price_to_y(bar.open);
        let high_y = price_to_y(bar.high);
        let low_y = price_to_y(bar.low);
        let close_y = price_to_y(bar.close);

        let is_bullish = bar.is_bullish();

        // Determine colors
        let body_color = if let Some(ref color) = candle.color {
            parse_color(color)
        } else if is_bullish {
            parse_color(&options.up_color)
        } else {
            parse_color(&options.down_color)
        };

        let wick_color = if let Some(ref color) = candle.wick_color {
            parse_color(color)
        } else if !options.wick_color.is_empty() {
            parse_color(&options.wick_color)
        } else if is_bullish {
            parse_color(&options.wick_up_color)
        } else {
            parse_color(&options.wick_down_color)
        };

        // Draw wick
        if options.wick_visible {
            let wick_x = crisp_coord(x, dpr);
            batch.push(RenderCommand::Line {
                from: Point::new(wick_x, crisp_coord(high_y, dpr)),
                to: Point::new(wick_x, crisp_coord(low_y, dpr)),
                style: LineStyle::solid(wick_color, 1.0),
            });
        }

        // Draw body
        let body_top = open_y.min(close_y);
        let body_bottom = open_y.max(close_y);
        let body_height = (body_bottom - body_top).max(1.0 / dpr);

        let (rect_x, rect_y, rect_w, rect_h) = crisp_rect(
            x - crisp_width / 2.0,
            body_top,
            crisp_width,
            body_height,
            dpr,
        );

        let rect = Rect::new(rect_x, rect_y, rect_w, rect_h);

        if is_bullish {
            // Hollow (outline only) for bullish
            batch.push(RenderCommand::StrokeRect {
                rect,
                style: LineStyle::solid(body_color, 1.0),
            });
        } else {
            // Filled for bearish
            batch.push(RenderCommand::FillRect {
                rect,
                color: body_color,
            });
        }
    }
}

// =============================================================================
// Heikin Ashi Series
// =============================================================================

/// Render Heikin Ashi candlestick series
///
/// Heikin Ashi uses averaged values to smooth out noise:
/// - HA Close = (Open + High + Low + Close) / 4
/// - HA Open = (prev HA Open + prev HA Close) / 2
/// - HA High = max(High, HA Open, HA Close)
/// - HA Low = min(Low, HA Open, HA Close)
///
/// # Arguments
/// * `batch` - RenderBatch to push commands to
/// * `data` - Candlestick data points (raw OHLC, will be converted to HA)
/// * `options` - Styling options for candlesticks
/// * `bar_to_x` - Function to convert bar index to X coordinate
/// * `price_to_y` - Function to convert price to Y coordinate
/// * `bar_width` - Base width of each candlestick
/// * `dpr` - Device pixel ratio for crisp rendering
pub fn render_heikin_ashi(
    batch: &mut RenderBatch,
    data: &[CandlestickData],
    options: &CandlestickStyleOptions,
    bar_to_x: impl Fn(usize) -> f64,
    price_to_y: impl Fn(f64) -> f64,
    bar_width: f64,
    dpr: f64,
) {
    if data.is_empty() {
        return;
    }

    let crisp_width = crisp_bar_width(bar_width, dpr);

    // Calculate Heikin Ashi values
    let mut ha_open = data[0].bar.open;
    let mut ha_close;

    for (i, candle) in data.iter().enumerate() {
        let bar = &candle.bar;

        if bar.open.is_nan() || bar.high.is_nan() || bar.low.is_nan() || bar.close.is_nan() {
            continue;
        }

        // Calculate HA values
        ha_close = (bar.open + bar.high + bar.low + bar.close) / 4.0;
        let ha_high = bar.high.max(ha_open).max(ha_close);
        let ha_low = bar.low.min(ha_open).min(ha_close);

        let x = bar_to_x(i);
        let open_y = price_to_y(ha_open);
        let high_y = price_to_y(ha_high);
        let low_y = price_to_y(ha_low);
        let close_y = price_to_y(ha_close);

        let is_bullish = ha_close >= ha_open;

        // Determine colors
        let body_color = if let Some(ref color) = candle.color {
            parse_color(color)
        } else if is_bullish {
            parse_color(&options.up_color)
        } else {
            parse_color(&options.down_color)
        };

        let wick_color = if !options.wick_color.is_empty() {
            parse_color(&options.wick_color)
        } else if is_bullish {
            parse_color(&options.wick_up_color)
        } else {
            parse_color(&options.wick_down_color)
        };

        // Draw wick
        if options.wick_visible {
            let wick_x = crisp_coord(x, dpr);
            batch.push(RenderCommand::Line {
                from: Point::new(wick_x, crisp_coord(high_y, dpr)),
                to: Point::new(wick_x, crisp_coord(low_y, dpr)),
                style: LineStyle::solid(wick_color, 1.0),
            });
        }

        // Draw body
        let body_top = open_y.min(close_y);
        let body_bottom = open_y.max(close_y);
        let body_height = (body_bottom - body_top).max(1.0 / dpr);

        let (rect_x, rect_y, rect_w, rect_h) = crisp_rect(
            x - crisp_width / 2.0,
            body_top,
            crisp_width,
            body_height,
            dpr,
        );

        batch.push(RenderCommand::FillRect {
            rect: Rect::new(rect_x, rect_y, rect_w, rect_h),
            color: body_color,
        });

        // Update HA open for next bar
        ha_open = (ha_open + ha_close) / 2.0;
    }
}

// =============================================================================
// Step Line Series
// =============================================================================

/// Render step line series (staircase chart)
///
/// Creates horizontal-then-vertical steps between points.
///
/// # Arguments
/// * `batch` - RenderBatch to push commands to
/// * `data` - Line data points
/// * `options` - Styling options for the line
/// * `bar_to_x` - Function to convert bar index to X coordinate
/// * `price_to_y` - Function to convert price to Y coordinate
/// * `dpr` - Device pixel ratio for crisp rendering
pub fn render_step_line(
    batch: &mut RenderBatch,
    data: &[LineData],
    options: &LineStyleOptions,
    bar_to_x: impl Fn(usize) -> f64,
    price_to_y: impl Fn(f64) -> f64,
    _dpr: f64,
) {
    if !options.line_visible || data.is_empty() {
        return;
    }

    // Collect valid points
    let mut points = Vec::new();
    for (i, item) in data.iter().enumerate() {
        if item.point.value.is_nan() {
            continue;
        }
        let x = bar_to_x(i);
        let y = price_to_y(item.point.value);
        points.push(Point::new(x, y));
    }

    if points.is_empty() {
        return;
    }

    let line_color = parse_color(&options.color);
    let line_width = options.line_width as f64;

    // Build step path
    let path = build_step_line_path(&points);

    batch.push(RenderCommand::StrokePath {
        path,
        style: create_line_style(&options.line_style, line_color, line_width),
    });
}

// =============================================================================
// Line with Markers Series
// =============================================================================

/// Parameters for line with markers rendering
pub struct LineWithMarkersParams<'a, F1, F2>
where
    F1: Fn(usize) -> f64,
    F2: Fn(f64) -> f64,
{
    pub data: &'a [LineData],
    pub options: &'a LineStyleOptions,
    pub bar_to_x: F1,
    pub price_to_y: F2,
    pub marker_radius: f64,
    pub dpr: f64,
}

/// Render line series with dot markers at each point
///
/// # Arguments
/// * `batch` - RenderBatch to push commands to
/// * `params` - Line with markers rendering parameters
pub fn render_line_with_markers<F1, F2>(
    batch: &mut RenderBatch,
    params: LineWithMarkersParams<'_, F1, F2>,
) where
    F1: Fn(usize) -> f64,
    F2: Fn(f64) -> f64,
{
    let LineWithMarkersParams {
        data,
        options,
        bar_to_x,
        price_to_y,
        marker_radius,
        dpr,
    } = params;

    if data.is_empty() {
        return;
    }

    // Collect valid points
    let mut points = Vec::new();
    for (i, item) in data.iter().enumerate() {
        if item.point.value.is_nan() {
            continue;
        }
        let x = bar_to_x(i);
        let y = price_to_y(item.point.value);
        points.push(Point::new(x, y));
    }

    if points.is_empty() {
        return;
    }

    let line_color = parse_color(&options.color);
    let line_width = options.line_width as f64;

    // Draw line if visible
    if options.line_visible {
        let path = match options.line_type {
            LineType::Simple => build_simple_line_path(&points),
            LineType::WithSteps => build_step_line_path(&points),
            LineType::Curved => build_curved_line_path(&points, dpr),
        };

        batch.push(RenderCommand::StrokePath {
            path,
            style: create_line_style(&options.line_style, line_color, line_width),
        });
    }

    // Always draw markers
    let radius = if marker_radius > 0.0 {
        marker_radius
    } else {
        3.0
    };
    for point in &points {
        batch.push(RenderCommand::FillCircle {
            center: *point,
            radius,
            color: line_color,
        });
    }
}

// =============================================================================
// HLC Area Series
// =============================================================================

/// Parameters for HLC area rendering
pub struct HlcAreaParams<'a, F1, F2>
where
    F1: Fn(usize) -> f64,
    F2: Fn(f64) -> f64,
{
    pub data: &'a [CandlestickData],
    pub up_color: &'a str,
    pub down_color: &'a str,
    pub bar_to_x: F1,
    pub price_to_y: F2,
}

/// Render HLC Area series (High-Low-Close with filled area)
///
/// Draws a filled area between high and low, with close line.
///
/// # Arguments
/// * `batch` - RenderBatch to push commands to
/// * `params` - HLC area rendering parameters
pub fn render_hlc_area<F1, F2>(batch: &mut RenderBatch, params: HlcAreaParams<'_, F1, F2>)
where
    F1: Fn(usize) -> f64,
    F2: Fn(f64) -> f64,
{
    let HlcAreaParams {
        data,
        up_color,
        down_color,
        bar_to_x,
        price_to_y,
    } = params;

    if data.is_empty() {
        return;
    }

    let up = parse_color(up_color);
    let down = parse_color(down_color);

    // Build high line, low line, and filled areas
    let mut high_points = Vec::new();
    let mut low_points = Vec::new();
    let mut close_points = Vec::new();

    for (i, candle) in data.iter().enumerate() {
        let bar = &candle.bar;
        if bar.high.is_nan() || bar.low.is_nan() || bar.close.is_nan() {
            continue;
        }

        let x = bar_to_x(i);
        high_points.push(Point::new(x, price_to_y(bar.high)));
        low_points.push(Point::new(x, price_to_y(bar.low)));
        close_points.push((x, price_to_y(bar.close), bar.is_bullish()));
    }

    if high_points.is_empty() {
        return;
    }

    // Draw filled area between high and low
    let mut builder = PathBuilder::new();

    // Start from first high point
    builder.move_to(high_points[0]);

    // Draw high line forward
    for point in high_points.iter().skip(1) {
        builder.line_to(*point);
    }

    // Draw low line backward
    for point in low_points.iter().rev() {
        builder.line_to(*point);
    }

    builder.close();
    let area_path = builder.build();

    // Use semi-transparent fill
    let fill_color = Color::rgba(up.r, up.g, up.b, 80);
    batch.push(RenderCommand::FillPath {
        path: area_path,
        style: FillStyle::Solid(fill_color),
    });

    // Draw close line with color based on direction
    for i in 1..close_points.len() {
        let (x1, y1, _) = close_points[i - 1];
        let (x2, y2, is_bullish) = close_points[i];

        let color = if is_bullish { up } else { down };

        batch.push(RenderCommand::Line {
            from: Point::new(x1, y1),
            to: Point::new(x2, y2),
            style: LineStyle::solid(color, 2.0),
        });
    }
}

// =============================================================================
// Columns Series
// =============================================================================

/// Render columns series (vertical bars from baseline)
///
/// Similar to histogram but typically used for volume or discrete data.
///
/// # Arguments
/// * `batch` - RenderBatch to push commands to
/// * `params` - Histogram rendering parameters (reused for columns)
pub fn render_columns<F1, F2>(batch: &mut RenderBatch, params: HistogramParams<'_, F1, F2>)
where
    F1: Fn(usize) -> f64,
    F2: Fn(f64) -> f64,
{
    // Columns are essentially the same as histogram
    // but we could add border/different styling if needed
    render_histogram(batch, params);
}

// =============================================================================
// Helper Functions
// =============================================================================

/// Parse CSS color string to Color type
fn parse_color(css: &str) -> Color {
    Color::from_css(css).unwrap_or(Color::BLACK)
}

/// Create LineStyle with dash pattern support
fn create_line_style(
    line_style: &crate::model::series::LineStyle,
    color: Color,
    width: f64,
) -> LineStyle {
    let dash_pattern = line_style.dash_pattern(width);

    if dash_pattern.is_empty() {
        LineStyle::solid(color, width)
    } else {
        // Create LineStyle with custom dash pattern
        let mut style = LineStyle::solid(color, width);
        style.dash = Some(dash_pattern);
        style
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_parse_color() {
        let color = parse_color("#26a69a");
        assert_eq!(color.r, 0x26);
        assert_eq!(color.g, 0xa6);
        assert_eq!(color.b, 0x9a);
        assert_eq!(color.a, 255);
    }

    #[test]
    fn test_intersection_calculation() {
        let p1 = Point::new(0.0, 0.0);
        let p2 = Point::new(10.0, 10.0);
        let base_y = 5.0;

        let intersection = calculate_intersection(p1, p2, base_y);
        assert_eq!(intersection.x, 5.0);
        assert_eq!(intersection.y, 5.0);
    }

    #[test]
    fn test_split_baseline_segments() {
        let points = vec![
            Point::new(0.0, 0.0), // Above (y < base_y)
            Point::new(1.0, 1.0), // Above
            Point::new(2.0, 6.0), // Below (y > base_y)
            Point::new(3.0, 7.0), // Below
        ];
        let base_y = 5.0;

        let segments = split_baseline_segments(&points, base_y);
        assert_eq!(segments.len(), 2);
        assert!(segments[0].is_above);
        assert!(!segments[1].is_above);
    }

    #[test]
    fn test_build_simple_line_path() {
        let points = vec![
            Point::new(0.0, 0.0),
            Point::new(1.0, 1.0),
            Point::new(2.0, 2.0),
        ];

        let path = build_simple_line_path(&points);
        assert!(!path.is_empty());
        assert_eq!(path.commands().len(), 3); // MoveTo + 2 LineTo
    }
}
