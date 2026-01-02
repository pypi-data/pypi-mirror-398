//! Indicator and Signal Rendering
//!
//! High-level rendering functions for indicators, signals, and strategies.
//! Indicators are rendered based on their VectorStyle (line, area, histogram, etc.)

use super::super::engine::{
    Color, FillStyle, LineStyle, Point, Rect, RenderBatch, RenderCommand, TextStyle,
    crisp_bar_width, crisp_coord, crisp_rect,
};
use crate::model::indicators::{
    ArrowDirection, Indicator, IndicatorLevel, IndicatorVector, Signal, SignalVisual, Strategy,
    VectorStyle,
};

// =============================================================================
// Color Parsing
// =============================================================================

fn parse_color(color: &str) -> Color {
    Color::from_hex(color).unwrap_or(Color::rgb(128, 128, 128))
}

fn parse_color_with_alpha(color: &str, alpha: f64) -> Color {
    let mut c = Color::from_hex(color).unwrap_or(Color::rgb(128, 128, 128));
    c.a = (alpha * 255.0) as u8;
    c
}

// =============================================================================
// Indicator Rendering
// =============================================================================

/// Render an indicator with all its vectors
///
/// Each vector is rendered according to its VectorStyle (Line, Area, Histogram, etc.)
///
/// # Arguments
/// * `batch` - RenderBatch to push commands to
/// * `indicator` - The indicator to render
/// * `bar_to_x` - Function to convert bar index to X coordinate
/// * `price_to_y` - Function to convert indicator value to Y coordinate (already scaled for sub-pane if needed)
/// * `bar_width` - Width of each bar
/// * `dpr` - Device pixel ratio
/// * `visible_range` - Optional (start, end) bar range for culling
pub fn render_indicator(
    batch: &mut RenderBatch,
    indicator: &Indicator,
    bar_to_x: impl Fn(usize) -> f64 + Copy,
    price_to_y: impl Fn(f64) -> f64 + Copy,
    bar_width: f64,
    dpr: f64,
    visible_range: Option<(usize, usize)>,
) {
    if !indicator.visible || indicator.is_empty() {
        return;
    }

    // Render reference levels first (behind the data)
    render_indicator_levels(
        batch,
        &indicator.levels,
        bar_to_x,
        price_to_y,
        dpr,
        visible_range,
    );

    // Render each vector
    for (i, vector) in indicator.vectors.iter().enumerate() {
        render_indicator_vector(
            batch,
            RenderIndicatorVectorParams {
                indicator,
                vector,
                vector_index: i,
                bar_to_x,
                price_to_y,
                bar_width,
                dpr,
                visible_range,
            },
        );
    }
}

/// Render reference levels (horizontal lines like overbought/oversold)
fn render_indicator_levels(
    batch: &mut RenderBatch,
    levels: &[IndicatorLevel],
    bar_to_x: impl Fn(usize) -> f64,
    price_to_y: impl Fn(f64) -> f64,
    dpr: f64,
    visible_range: Option<(usize, usize)>,
) {
    for level in levels {
        let y = crisp_coord(price_to_y(level.value), dpr);
        let color = parse_color(&level.color);

        // Get X range
        let (x_start, x_end) = if let Some((start, end)) = visible_range {
            (bar_to_x(start), bar_to_x(end))
        } else {
            (0.0, 10000.0) // Large default
        };

        let dash = match level.style.as_str() {
            "dotted" => Some(vec![2.0, 2.0]),
            "dashed" => Some(vec![6.0, 4.0]),
            _ => None,
        };

        batch.push(RenderCommand::Line {
            from: Point::new(x_start, y),
            to: Point::new(x_end, y),
            style: LineStyle {
                color,
                width: level.width,
                dash,
                ..Default::default()
            },
        });
    }
}

/// Render a single indicator vector
fn render_indicator_vector<F1, F2>(
    batch: &mut RenderBatch,
    params: RenderIndicatorVectorParams<'_, F1, F2>,
) where
    F1: Fn(usize) -> f64 + Copy,
    F2: Fn(f64) -> f64 + Copy,
{
    let RenderIndicatorVectorParams {
        indicator,
        vector,
        vector_index,
        bar_to_x,
        price_to_y,
        bar_width,
        dpr,
        visible_range,
    } = params;

    if vector.values.is_empty() {
        return;
    }

    let (start, end) = visible_range.unwrap_or((0, vector.values.len()));
    let start = start.saturating_sub(1).min(vector.values.len());
    let end = (end + 1).min(vector.values.len());

    match &vector.style {
        VectorStyle::Line {
            color,
            width,
            dashed,
        } => {
            render_vector_line(
                batch,
                VectorLineParams {
                    values: &vector.values,
                    color,
                    width: *width,
                    dashed: *dashed,
                    bar_to_x,
                    price_to_y,
                    dpr,
                    start,
                    end,
                },
            );
        }
        VectorStyle::Area {
            color,
            fill_alpha,
            line_width,
        } => {
            render_vector_area(
                batch,
                VectorAreaParams {
                    values: &vector.values,
                    color,
                    fill_alpha: *fill_alpha,
                    line_width: *line_width,
                    bar_to_x,
                    price_to_y,
                    dpr,
                    start,
                    end,
                },
            );
        }
        VectorStyle::Histogram {
            up_color,
            down_color,
            bar_width_ratio,
        } => {
            render_vector_histogram(
                batch,
                VectorHistogramParams {
                    values: &vector.values,
                    up_color,
                    down_color,
                    bar_width_ratio: *bar_width_ratio,
                    bar_to_x,
                    price_to_y,
                    bar_width,
                    dpr,
                    start,
                    end,
                },
            );
        }
        VectorStyle::Dots {
            color,
            radius,
            filled,
        } => {
            render_vector_dots(
                batch,
                VectorDotsParams {
                    values: &vector.values,
                    color,
                    radius: *radius,
                    filled: *filled,
                    bar_to_x,
                    price_to_y,
                    dpr,
                    start,
                    end,
                },
            );
        }
        VectorStyle::Step { color, width } => {
            render_vector_step(
                batch,
                VectorStepParams {
                    values: &vector.values,
                    color,
                    width: *width,
                    bar_to_x,
                    price_to_y,
                    dpr,
                    start,
                    end,
                },
            );
        }
        VectorStyle::Cloud {
            color_above,
            color_below,
            fill_alpha,
            fill_to_vector,
        } => {
            // Cloud fills between this vector and another
            if let Some(other_vector) = indicator.vectors.get(*fill_to_vector) {
                render_vector_cloud(
                    batch,
                    VectorCloudParams {
                        values1: &vector.values,
                        values2: &other_vector.values,
                        color_above,
                        color_below,
                        fill_alpha: *fill_alpha,
                        bar_to_x,
                        price_to_y,
                        dpr,
                        start,
                        end,
                    },
                );
            }
        }
        VectorStyle::Hidden => {
            // Don't render
        }
    }
    let _ = vector_index; // Suppress unused warning
}

// =============================================================================
// Vector Style Renderers - Parameter Structs
// =============================================================================

/// Parameters for render_indicator_vector
struct RenderIndicatorVectorParams<'a, F1, F2>
where
    F1: Fn(usize) -> f64 + Copy,
    F2: Fn(f64) -> f64 + Copy,
{
    indicator: &'a Indicator,
    vector: &'a IndicatorVector,
    vector_index: usize,
    bar_to_x: F1,
    price_to_y: F2,
    bar_width: f64,
    dpr: f64,
    visible_range: Option<(usize, usize)>,
}

/// Parameters for vector line rendering
struct VectorLineParams<'a, F1, F2>
where
    F1: Fn(usize) -> f64,
    F2: Fn(f64) -> f64,
{
    values: &'a [f64],
    color: &'a str,
    width: f64,
    dashed: bool,
    bar_to_x: F1,
    price_to_y: F2,
    dpr: f64,
    start: usize,
    end: usize,
}

/// Parameters for vector area rendering
struct VectorAreaParams<'a, F1, F2>
where
    F1: Fn(usize) -> f64,
    F2: Fn(f64) -> f64,
{
    values: &'a [f64],
    color: &'a str,
    fill_alpha: f64,
    line_width: f64,
    bar_to_x: F1,
    price_to_y: F2,
    dpr: f64,
    start: usize,
    end: usize,
}

/// Parameters for vector histogram rendering
struct VectorHistogramParams<'a, F1, F2>
where
    F1: Fn(usize) -> f64,
    F2: Fn(f64) -> f64,
{
    values: &'a [f64],
    up_color: &'a str,
    down_color: &'a str,
    bar_width_ratio: f64,
    bar_to_x: F1,
    price_to_y: F2,
    bar_width: f64,
    dpr: f64,
    start: usize,
    end: usize,
}

/// Parameters for vector dots rendering
struct VectorDotsParams<'a, F1, F2>
where
    F1: Fn(usize) -> f64,
    F2: Fn(f64) -> f64,
{
    values: &'a [f64],
    color: &'a str,
    radius: f64,
    filled: bool,
    bar_to_x: F1,
    price_to_y: F2,
    dpr: f64,
    start: usize,
    end: usize,
}

/// Parameters for vector step rendering
struct VectorStepParams<'a, F1, F2>
where
    F1: Fn(usize) -> f64,
    F2: Fn(f64) -> f64,
{
    values: &'a [f64],
    color: &'a str,
    width: f64,
    bar_to_x: F1,
    price_to_y: F2,
    dpr: f64,
    start: usize,
    end: usize,
}

/// Parameters for vector cloud rendering
struct VectorCloudParams<'a, F1, F2>
where
    F1: Fn(usize) -> f64,
    F2: Fn(f64) -> f64,
{
    values1: &'a [f64],
    values2: &'a [f64],
    color_above: &'a str,
    color_below: &'a str,
    fill_alpha: f64,
    bar_to_x: F1,
    price_to_y: F2,
    dpr: f64,
    start: usize,
    end: usize,
}

/// Parameters for cloud segment rendering
struct CloudSegmentParams<'a, F1, F2>
where
    F1: Fn(usize) -> f64,
    F2: Fn(f64) -> f64,
{
    values1: &'a [f64],
    values2: &'a [f64],
    color_above: &'a str,
    color_below: &'a str,
    fill_alpha: f64,
    bar_to_x: &'a F1,
    price_to_y: &'a F2,
    dpr: f64,
    start: usize,
    end: usize,
}

// =============================================================================
// Vector Style Renderers - Implementation
// =============================================================================

fn render_vector_line<F1, F2>(batch: &mut RenderBatch, params: VectorLineParams<'_, F1, F2>)
where
    F1: Fn(usize) -> f64,
    F2: Fn(f64) -> f64,
{
    let VectorLineParams {
        values,
        color,
        width,
        dashed,
        bar_to_x,
        price_to_y,
        dpr,
        start,
        end,
    } = params;

    let mut points = Vec::new();

    for (idx, &value) in values[start..end].iter().enumerate() {
        let i = start + idx;
        if value.is_nan() || value.is_infinite() {
            // Break line on invalid values - render what we have
            if points.len() >= 2 {
                let dash = if dashed { Some(vec![6.0, 4.0]) } else { None };
                batch.push(RenderCommand::Polyline {
                    points: std::mem::take(&mut points),
                    style: LineStyle {
                        color: parse_color(color),
                        width,
                        dash,
                        ..Default::default()
                    },
                });
            }
            points.clear();
            continue;
        }

        let x = crisp_coord(bar_to_x(i), dpr);
        let y = crisp_coord(price_to_y(value), dpr);
        points.push(Point::new(x, y));
    }

    // Render remaining points
    if points.len() >= 2 {
        let dash = if dashed { Some(vec![6.0, 4.0]) } else { None };
        batch.push(RenderCommand::Polyline {
            points,
            style: LineStyle {
                color: parse_color(color),
                width,
                dash,
                ..Default::default()
            },
        });
    }
}

fn render_vector_area<F1, F2>(batch: &mut RenderBatch, params: VectorAreaParams<'_, F1, F2>)
where
    F1: Fn(usize) -> f64,
    F2: Fn(f64) -> f64,
{
    let VectorAreaParams {
        values,
        color,
        fill_alpha,
        line_width,
        bar_to_x,
        price_to_y,
        dpr,
        start,
        end,
    } = params;

    let mut line_points = Vec::new();
    let mut first_x = 0.0;
    let mut last_x = 0.0;
    let baseline_y = price_to_y(0.0); // Area fills down to zero
    let mut started = false;

    for (idx, &value) in values[start..end].iter().enumerate() {
        let i = start + idx;
        if value.is_nan() || value.is_infinite() {
            continue;
        }

        let x = crisp_coord(bar_to_x(i), dpr);
        let y = crisp_coord(price_to_y(value), dpr);

        if !started {
            first_x = x;
            started = true;
        }
        line_points.push(Point::new(x, y));
        last_x = x;
    }

    if line_points.len() >= 2 {
        // Build area polygon
        let mut area_points = Vec::with_capacity(line_points.len() + 2);
        area_points.push(Point::new(first_x, baseline_y));
        area_points.extend(line_points.iter().copied());
        area_points.push(Point::new(last_x, baseline_y));

        // Fill area
        batch.push(RenderCommand::FillPolygon {
            points: area_points,
            style: FillStyle::Solid(parse_color_with_alpha(color, fill_alpha)),
        });

        // Stroke line
        if line_width > 0.0 {
            batch.push(RenderCommand::Polyline {
                points: line_points,
                style: LineStyle {
                    color: parse_color(color),
                    width: line_width,
                    ..Default::default()
                },
            });
        }
    }
}

fn render_vector_histogram<F1, F2>(
    batch: &mut RenderBatch,
    params: VectorHistogramParams<'_, F1, F2>,
) where
    F1: Fn(usize) -> f64,
    F2: Fn(f64) -> f64,
{
    let VectorHistogramParams {
        values,
        up_color,
        down_color,
        bar_width_ratio,
        bar_to_x,
        price_to_y,
        bar_width,
        dpr,
        start,
        end,
    } = params;

    let crisp_width = crisp_bar_width(bar_width * bar_width_ratio, dpr);
    let zero_y = crisp_coord(price_to_y(0.0), dpr);

    for (idx, &value) in values[start..end].iter().enumerate() {
        let i = start + idx;
        if value.is_nan() || value.is_infinite() {
            continue;
        }

        let x = bar_to_x(i);
        let y = price_to_y(value);

        let (rx, ry, rw, rh) = crisp_rect(
            x - crisp_width / 2.0,
            y.min(zero_y),
            crisp_width,
            (y - zero_y).abs().max(1.0),
            dpr,
        );

        let color = if value >= 0.0 {
            parse_color(up_color)
        } else {
            parse_color(down_color)
        };

        batch.push(RenderCommand::FillRect {
            rect: Rect::new(rx, ry, rw, rh),
            color,
        });
    }
}

fn render_vector_dots<F1, F2>(batch: &mut RenderBatch, params: VectorDotsParams<'_, F1, F2>)
where
    F1: Fn(usize) -> f64,
    F2: Fn(f64) -> f64,
{
    let VectorDotsParams {
        values,
        color,
        radius,
        filled,
        bar_to_x,
        price_to_y,
        dpr,
        start,
        end,
    } = params;

    let color = parse_color(color);

    for (idx, &value) in values[start..end].iter().enumerate() {
        let i = start + idx;
        if value.is_nan() || value.is_infinite() {
            continue;
        }

        let x = crisp_coord(bar_to_x(i), dpr);
        let y = crisp_coord(price_to_y(value), dpr);

        if filled {
            batch.push(RenderCommand::FillCircle {
                center: Point::new(x, y),
                radius,
                color,
            });
        } else {
            batch.push(RenderCommand::StrokeCircle {
                center: Point::new(x, y),
                radius,
                style: LineStyle {
                    color,
                    width: 1.0,
                    ..Default::default()
                },
            });
        }
    }
}

fn render_vector_step<F1, F2>(batch: &mut RenderBatch, params: VectorStepParams<'_, F1, F2>)
where
    F1: Fn(usize) -> f64,
    F2: Fn(f64) -> f64,
{
    let VectorStepParams {
        values,
        color,
        width,
        bar_to_x,
        price_to_y,
        dpr,
        start,
        end,
    } = params;

    let mut points = Vec::new();
    let mut prev_y = 0.0;
    let mut started = false;

    for (idx, &value) in values[start..end].iter().enumerate() {
        let i = start + idx;
        if value.is_nan() || value.is_infinite() {
            // Break on invalid values
            if points.len() >= 2 {
                batch.push(RenderCommand::Polyline {
                    points: std::mem::take(&mut points),
                    style: LineStyle {
                        color: parse_color(color),
                        width,
                        ..Default::default()
                    },
                });
            }
            points.clear();
            started = false;
            continue;
        }

        let x = crisp_coord(bar_to_x(i), dpr);
        let y = crisp_coord(price_to_y(value), dpr);

        if !started {
            points.push(Point::new(x, y));
            started = true;
        } else {
            // Step: horizontal then vertical
            points.push(Point::new(x, prev_y));
            points.push(Point::new(x, y));
        }
        prev_y = y;
    }

    if points.len() >= 2 {
        batch.push(RenderCommand::Polyline {
            points,
            style: LineStyle {
                color: parse_color(color),
                width,
                ..Default::default()
            },
        });
    }
}

fn render_vector_cloud<F1, F2>(batch: &mut RenderBatch, params: VectorCloudParams<'_, F1, F2>)
where
    F1: Fn(usize) -> f64,
    F2: Fn(f64) -> f64,
{
    let VectorCloudParams {
        values1,
        values2,
        color_above,
        color_below,
        fill_alpha,
        bar_to_x,
        price_to_y,
        dpr,
        start,
        end,
    } = params;

    // Cloud requires both vectors to have same length
    let len = values1.len().min(values2.len());
    if len == 0 {
        return;
    }

    let end = end.min(len);

    // Build segments where both values are valid
    let mut segment_start = None;

    for i in start..=end {
        let valid = if i < end {
            let v1 = values1[i];
            let v2 = values2[i];
            !v1.is_nan() && !v1.is_infinite() && !v2.is_nan() && !v2.is_infinite()
        } else {
            false
        };

        if valid {
            if segment_start.is_none() {
                segment_start = Some(i);
            }
        } else if let Some(seg_start) = segment_start {
            // Render this segment
            render_cloud_segment(
                batch,
                CloudSegmentParams {
                    values1,
                    values2,
                    color_above,
                    color_below,
                    fill_alpha,
                    bar_to_x: &bar_to_x,
                    price_to_y: &price_to_y,
                    dpr,
                    start: seg_start,
                    end: i,
                },
            );
            segment_start = None;
        }
    }
}

fn render_cloud_segment<F1, F2>(batch: &mut RenderBatch, params: CloudSegmentParams<'_, F1, F2>)
where
    F1: Fn(usize) -> f64,
    F2: Fn(f64) -> f64,
{
    let CloudSegmentParams {
        values1,
        values2,
        color_above,
        color_below,
        fill_alpha,
        bar_to_x,
        price_to_y,
        dpr,
        start,
        end,
    } = params;

    if end <= start {
        return;
    }

    // Build polygon: forward path (values1) + backward path (values2, reversed)
    let mut points = Vec::with_capacity((end - start) * 2);

    for (idx, &v1) in values1[start..end].iter().enumerate() {
        let i = start + idx;
        let x = crisp_coord(bar_to_x(i), dpr);
        let y = crisp_coord(price_to_y(v1), dpr);
        points.push(Point::new(x, y));
    }

    for i in (start..end).rev() {
        let x = crisp_coord(bar_to_x(i), dpr);
        let y = crisp_coord(price_to_y(values2[i]), dpr);
        points.push(Point::new(x, y));
    }

    // Determine if above or below (check first point)
    let is_above = values1[start] > values2[start];
    let color = if is_above { color_above } else { color_below };

    batch.push(RenderCommand::FillPolygon {
        points,
        style: FillStyle::Solid(parse_color_with_alpha(color, fill_alpha)),
    });
}

// =============================================================================
// Signal Rendering
// =============================================================================

/// Render signals on the chart
///
/// # Arguments
/// * `batch` - RenderBatch to push commands to
/// * `signals` - The signals to render
/// * `bar_to_x` - Function to convert bar index to X coordinate
/// * `price_to_y` - Function to convert price to Y coordinate
/// * `dpr` - Device pixel ratio
pub fn render_signals(
    batch: &mut RenderBatch,
    signals: &[Signal],
    bar_to_x: impl Fn(f64) -> f64 + Copy,
    price_to_y: impl Fn(f64) -> f64 + Copy,
    dpr: f64,
) {
    for signal in signals {
        if !signal.visible {
            continue;
        }

        let x = crisp_coord(bar_to_x(signal.bar), dpr);
        let y = crisp_coord(price_to_y(signal.price), dpr);

        render_signal_visual(batch, &signal.visual, x, y, dpr);
    }
}

fn render_signal_visual(batch: &mut RenderBatch, visual: &SignalVisual, x: f64, y: f64, dpr: f64) {
    match visual {
        SignalVisual::Arrow {
            direction,
            color,
            size,
        } => {
            render_arrow(batch, x, y, direction, color, *size, dpr);
        }
        SignalVisual::Dot { color, radius } => {
            render_dot(batch, x, y, color, *radius, dpr);
        }
        SignalVisual::Label {
            text,
            color,
            background,
        } => {
            render_label(batch, x, y, text, color, background.as_deref(), dpr);
        }
        SignalVisual::Flag { color, label } => {
            render_flag(batch, x, y, color, label.as_deref(), dpr);
        }
        SignalVisual::Emoji { emoji, size } => {
            render_emoji(batch, x, y, emoji, *size, dpr);
        }
        SignalVisual::Primitive { .. } => {
            // Primitives are rendered separately through the primitive system
        }
    }
}

fn render_arrow(
    batch: &mut RenderBatch,
    x: f64,
    y: f64,
    direction: &ArrowDirection,
    color: &str,
    size: f64,
    _dpr: f64,
) {
    let color = parse_color(color);
    let half = size / 2.0;

    let points = match direction {
        ArrowDirection::Up => vec![
            Point::new(x, y - half),
            Point::new(x - half * 0.7, y + half * 0.5),
            Point::new(x + half * 0.7, y + half * 0.5),
        ],
        ArrowDirection::Down => vec![
            Point::new(x, y + half),
            Point::new(x - half * 0.7, y - half * 0.5),
            Point::new(x + half * 0.7, y - half * 0.5),
        ],
        ArrowDirection::Left => vec![
            Point::new(x - half, y),
            Point::new(x + half * 0.5, y - half * 0.7),
            Point::new(x + half * 0.5, y + half * 0.7),
        ],
        ArrowDirection::Right => vec![
            Point::new(x + half, y),
            Point::new(x - half * 0.5, y - half * 0.7),
            Point::new(x - half * 0.5, y + half * 0.7),
        ],
    };

    batch.push(RenderCommand::FillPolygon {
        points,
        style: FillStyle::Solid(color),
    });
}

fn render_dot(batch: &mut RenderBatch, x: f64, y: f64, color: &str, radius: f64, _dpr: f64) {
    batch.push(RenderCommand::FillCircle {
        center: Point::new(x, y),
        radius,
        color: parse_color(color),
    });
}

fn render_label(
    batch: &mut RenderBatch,
    x: f64,
    y: f64,
    text: &str,
    color: &str,
    background: Option<&str>,
    _dpr: f64,
) {
    let text_width = (text.len() as f64 * 7.0) + 8.0;
    let text_height = 16.0;

    // Background
    if let Some(bg) = background {
        batch.push(RenderCommand::FillRect {
            rect: Rect::new(
                x - text_width / 2.0,
                y - text_height / 2.0,
                text_width,
                text_height,
            ),
            color: parse_color(bg),
        });
    }

    // Text
    batch.push(RenderCommand::Text {
        text: text.to_string(),
        pos: Point::new(x, y),
        style: TextStyle {
            font_size: 12.0,
            color: parse_color(color),
            ..Default::default()
        },
    });
}

fn render_flag(
    batch: &mut RenderBatch,
    x: f64,
    y: f64,
    color: &str,
    label: Option<&str>,
    _dpr: f64,
) {
    let color = parse_color(color);
    let flag_height = 16.0;
    let flag_width = 12.0;
    let pole_height = 24.0;

    // Pole
    batch.push(RenderCommand::Line {
        from: Point::new(x, y),
        to: Point::new(x, y - pole_height),
        style: LineStyle {
            color,
            width: 1.5,
            ..Default::default()
        },
    });

    // Flag
    batch.push(RenderCommand::FillPolygon {
        points: vec![
            Point::new(x, y - pole_height),
            Point::new(x + flag_width, y - pole_height + flag_height / 2.0),
            Point::new(x, y - pole_height + flag_height),
        ],
        style: FillStyle::Solid(color),
    });

    // Label
    if let Some(text) = label {
        batch.push(RenderCommand::Text {
            text: text.to_string(),
            pos: Point::new(x + flag_width + 4.0, y - pole_height + flag_height / 2.0),
            style: TextStyle {
                font_size: 10.0,
                color,
                ..Default::default()
            },
        });
    }
}

fn render_emoji(batch: &mut RenderBatch, x: f64, y: f64, emoji: &str, size: f64, _dpr: f64) {
    batch.push(RenderCommand::Text {
        text: emoji.to_string(),
        pos: Point::new(x, y),
        style: TextStyle {
            font_size: size,
            ..Default::default()
        },
    });
}

// =============================================================================
// Strategy Rendering
// =============================================================================

/// Parameters for strategy rendering
pub struct StrategyParams<'a, F1, F2, F3>
where
    F1: Fn(usize) -> f64 + Copy,
    F2: Fn(f64) -> f64 + Copy,
    F3: Fn(f64) -> f64 + Copy,
{
    pub strategy: &'a Strategy,
    pub bar_to_x: F1,
    pub bar_to_x_float: F2,
    pub price_to_y: F3,
    pub bar_width: f64,
    pub dpr: f64,
    pub visible_range: Option<(usize, usize)>,
}

/// Render a complete strategy (indicators + signals)
///
/// This is a convenience function that renders all components of a strategy.
pub fn render_strategy<F1, F2, F3>(batch: &mut RenderBatch, params: StrategyParams<'_, F1, F2, F3>)
where
    F1: Fn(usize) -> f64 + Copy,
    F2: Fn(f64) -> f64 + Copy,
    F3: Fn(f64) -> f64 + Copy,
{
    let StrategyParams {
        strategy,
        bar_to_x,
        bar_to_x_float,
        price_to_y,
        bar_width,
        dpr,
        visible_range,
    } = params;

    if !strategy.visible {
        return;
    }

    // Render indicators
    for indicator in &strategy.indicators {
        render_indicator(
            batch,
            indicator,
            bar_to_x,
            price_to_y,
            bar_width,
            dpr,
            visible_range,
        );
    }

    // Render signals
    render_signals(batch, &strategy.signals, bar_to_x_float, price_to_y, dpr);

    // Note: Strategy primitives (trend lines, fibs, etc.) are rendered
    // separately through the primitive system, not here
}

// =============================================================================
// Tests
// =============================================================================

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_parse_color() {
        let c = parse_color("#FF0000");
        assert_eq!(c.r, 255);
        assert_eq!(c.g, 0);
        assert_eq!(c.b, 0);
    }

    #[test]
    fn test_parse_color_with_alpha() {
        let c = parse_color_with_alpha("#00FF00", 0.5);
        assert_eq!(c.g, 255);
        assert_eq!(c.a, 127);
    }
}
