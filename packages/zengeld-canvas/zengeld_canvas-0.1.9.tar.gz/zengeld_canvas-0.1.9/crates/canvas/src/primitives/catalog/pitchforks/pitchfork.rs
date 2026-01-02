//! Andrew's Pitchfork primitive
//!
//! A three-point technical analysis tool consisting of a median line
//! with parallel upper and lower trendlines.

use super::super::{
    LineStyle, Primitive, PrimitiveColor, PrimitiveData, PrimitiveKind, PrimitiveMetadata,
    RenderContext, TextAlign, TextAnchor, config::FibLevelConfig, crisp,
};
use serde::{Deserialize, Serialize};

/// Pitchfork levels (multipliers from median)
pub const DEFAULT_PITCHFORK_LEVELS: &[f64] = &[-1.0, -0.5, 0.0, 0.5, 1.0];

/// Create default level configs for pitchfork
fn default_level_configs() -> Vec<FibLevelConfig> {
    DEFAULT_PITCHFORK_LEVELS
        .iter()
        .map(|&level| FibLevelConfig::new(level))
        .collect()
}

/// Deserialize level configs with backward compatibility for old `levels: Vec<f64>` format
fn deserialize_level_configs<'de, D>(deserializer: D) -> Result<Vec<FibLevelConfig>, D::Error>
where
    D: serde::Deserializer<'de>,
{
    use serde::de::{self, SeqAccess, Visitor};

    struct LevelConfigsVisitor;

    impl<'de> Visitor<'de> for LevelConfigsVisitor {
        type Value = Vec<FibLevelConfig>;

        fn expecting(&self, formatter: &mut std::fmt::Formatter) -> std::fmt::Result {
            formatter.write_str("a sequence of FibLevelConfig objects or f64 level values")
        }

        fn visit_seq<A>(self, mut seq: A) -> Result<Self::Value, A::Error>
        where
            A: SeqAccess<'de>,
        {
            let mut configs = Vec::new();

            while let Some(value) = seq.next_element::<serde_json::Value>()? {
                // Try to parse as FibLevelConfig first
                if value.is_object() {
                    let config: FibLevelConfig =
                        serde_json::from_value(value).map_err(de::Error::custom)?;
                    configs.push(config);
                } else if let Some(level) = value.as_f64() {
                    // Backward compatibility: old format was just f64 levels
                    configs.push(FibLevelConfig::new(level));
                } else {
                    return Err(de::Error::custom("expected FibLevelConfig object or f64"));
                }
            }

            Ok(configs)
        }
    }

    deserializer.deserialize_seq(LevelConfigsVisitor)
}

/// Andrew's Pitchfork
#[derive(Clone, Debug, Serialize, Deserialize)]
pub struct Pitchfork {
    /// Common primitive data
    pub data: PrimitiveData,
    /// Point 1 - the handle (starting pivot)
    pub bar1: f64,
    pub price1: f64,
    /// Point 2 - first swing (usually a high/low)
    pub bar2: f64,
    pub price2: f64,
    /// Point 3 - second swing (opposite of point 2)
    pub bar3: f64,
    pub price3: f64,
    /// Pitchfork level configurations (0 = median, 1 = upper, -1 = lower)
    /// with individual visibility, color, and style settings
    #[serde(
        default = "default_level_configs",
        deserialize_with = "deserialize_level_configs"
    )]
    pub level_configs: Vec<FibLevelConfig>,
    /// Extend lines
    #[serde(default = "default_true")]
    pub extend: bool,
    /// Show level labels
    #[serde(default = "default_true")]
    pub show_labels: bool,
}

fn default_true() -> bool {
    true
}

impl Pitchfork {
    /// Create a new pitchfork
    pub fn new(
        bar1: f64,
        price1: f64,
        bar2: f64,
        price2: f64,
        bar3: f64,
        price3: f64,
        color: &str,
    ) -> Self {
        Self {
            data: PrimitiveData {
                type_id: "pitchfork".to_string(),
                display_name: "Pitchfork".to_string(),
                color: PrimitiveColor::new(color),
                width: 1.0,
                ..Default::default()
            },
            bar1,
            price1,
            bar2,
            price2,
            bar3,
            price3,
            level_configs: default_level_configs(),
            extend: true,
            show_labels: true,
        }
    }

    /// Get visible levels as f64 values (for hit testing and rendering)
    pub fn visible_levels(&self) -> Vec<f64> {
        self.level_configs
            .iter()
            .filter(|c| c.visible)
            .map(|c| c.level)
            .collect()
    }

    /// Get the midpoint between points 2 and 3
    pub fn midpoint(&self) -> (f64, f64) {
        (
            (self.bar2 + self.bar3) / 2.0,
            (self.price2 + self.price3) / 2.0,
        )
    }

    /// Get the channel width (half distance from point 2 to point 3)
    pub fn channel_offset(&self) -> (f64, f64) {
        (
            (self.bar3 - self.bar2) / 2.0,
            (self.price3 - self.price2) / 2.0,
        )
    }

    /// Get median line direction
    pub fn median_direction(&self) -> (f64, f64) {
        let (mid_bar, mid_price) = self.midpoint();
        (mid_bar - self.bar1, mid_price - self.price1)
    }
}

impl Primitive for Pitchfork {
    fn type_id(&self) -> &'static str {
        "pitchfork"
    }

    fn display_name(&self) -> &str {
        &self.data.display_name
    }

    fn kind(&self) -> PrimitiveKind {
        PrimitiveKind::Channel
    }

    fn data(&self) -> &PrimitiveData {
        &self.data
    }

    fn data_mut(&mut self) -> &mut PrimitiveData {
        &mut self.data
    }

    fn points(&self) -> Vec<(f64, f64)> {
        vec![
            (self.bar1, self.price1),
            (self.bar2, self.price2),
            (self.bar3, self.price3),
        ]
    }

    fn set_points(&mut self, points: &[(f64, f64)]) {
        if let Some(&(bar, price)) = points.first() {
            self.bar1 = bar;
            self.price1 = price;
        }
        if let Some(&(bar, price)) = points.get(1) {
            self.bar2 = bar;
            self.price2 = price;
        }
        if let Some(&(bar, price)) = points.get(2) {
            self.bar3 = bar;
            self.price3 = price;
        }
    }

    fn translate(&mut self, bar_delta: f64, price_delta: f64) {
        self.bar1 += bar_delta;
        self.bar2 += bar_delta;
        self.bar3 += bar_delta;
        self.price1 += price_delta;
        self.price2 += price_delta;
        self.price3 += price_delta;
    }

    fn render(&self, ctx: &mut dyn RenderContext, is_selected: bool) {
        let dpr = ctx.dpr();
        let x1 = ctx.bar_to_x(self.bar1);
        let y1 = ctx.price_to_y(self.price1);
        let chart_width = ctx.chart_width();

        let (mid_bar, mid_price) = self.midpoint();
        let mid_x = ctx.bar_to_x(mid_bar);
        let mid_y = ctx.price_to_y(mid_price);

        let (offset_bar, offset_price) = self.channel_offset();
        let offset_x = ctx.bar_to_x(mid_bar + offset_bar) - mid_x;
        let offset_y = ctx.price_to_y(mid_price + offset_price) - mid_y;

        // Draw pitchfork tines at each visible level
        for config in &self.level_configs {
            if !config.visible {
                continue;
            }

            let level = config.level;
            let start_x = x1 + offset_x * level;
            let start_y = y1 + offset_y * level;
            let end_x = mid_x + offset_x * level;
            let end_y = mid_y + offset_y * level;

            // Use level-specific color or fall back to primitive color
            let stroke_color = config.color.as_ref().unwrap_or(&self.data.color.stroke);
            ctx.set_stroke_color(stroke_color);

            // Use level-specific width or fall back to primitive width
            let stroke_width = config.width.unwrap_or(self.data.width);
            ctx.set_stroke_width(stroke_width);

            // Use level-specific style or fall back to primitive style
            let line_style = match config.style.as_str() {
                "dashed" => LineStyle::Dashed,
                "dotted" => LineStyle::Dotted,
                "large_dashed" => LineStyle::LargeDashed,
                "sparse_dotted" => LineStyle::SparseDotted,
                _ => self.data.style,
            };
            match line_style {
                LineStyle::Solid => ctx.set_line_dash(&[]),
                LineStyle::Dashed => ctx.set_line_dash(&[8.0, 4.0]),
                LineStyle::Dotted => ctx.set_line_dash(&[2.0, 2.0]),
                LineStyle::LargeDashed => ctx.set_line_dash(&[12.0, 6.0]),
                LineStyle::SparseDotted => ctx.set_line_dash(&[2.0, 8.0]),
            }

            ctx.begin_path();
            ctx.move_to(crisp(start_x, dpr), crisp(start_y, dpr));

            if self.extend {
                let dx = end_x - start_x;
                let dy = end_y - start_y;
                let len = (dx * dx + dy * dy).sqrt();
                if len > 0.0 {
                    let ext = chart_width * 2.0;
                    let nx = dx / len;
                    let ny = dy / len;
                    ctx.line_to(
                        crisp(start_x + nx * ext, dpr),
                        crisp(start_y + ny * ext, dpr),
                    );
                }
            } else {
                ctx.line_to(crisp(end_x, dpr), crisp(end_y, dpr));
            }
            ctx.stroke();
        }
        ctx.set_line_dash(&[]);

        let _ = is_selected;
    }

    fn text_anchor(&self, ctx: &dyn RenderContext) -> Option<TextAnchor> {
        let text = self.data.text.as_ref()?;
        if text.content.is_empty() {
            return None;
        }

        // Position text along the median line (from point1 to midpoint of points 2 and 3)
        let x1 = ctx.bar_to_x(self.bar1);
        let y1 = ctx.price_to_y(self.price1);

        let (mid_bar, mid_price) = self.midpoint();
        let mid_x = ctx.bar_to_x(mid_bar);
        let mid_y = ctx.price_to_y(mid_price);

        // Calculate the direction vector along the median line
        let dx = mid_x - x1;
        let dy = mid_y - y1;
        let line_length = (dx * dx + dy * dy).sqrt();

        if line_length < 0.001 {
            // Fallback to point1 if line is too short
            return Some(TextAnchor::new(x1, y1, &self.data.color.stroke));
        }

        // Position text along the median line
        let t = match text.h_align {
            TextAlign::Start => 0.2,  // Near the start (point1)
            TextAlign::Center => 0.5, // Center of median line
            TextAlign::End => 0.8,    // Near the end (midpoint)
        };

        let x = x1 + dx * t;
        let y = y1 + dy * t;

        // Calculate rotation angle
        let raw_angle = dy.atan2(dx);
        let angle_flipped =
            !(-std::f64::consts::FRAC_PI_2..=std::f64::consts::FRAC_PI_2).contains(&raw_angle);
        let angle = if raw_angle > std::f64::consts::FRAC_PI_2 {
            raw_angle - std::f64::consts::PI
        } else if raw_angle < -std::f64::consts::FRAC_PI_2 {
            raw_angle + std::f64::consts::PI
        } else {
            raw_angle
        };

        // Calculate perpendicular offset for vertical alignment
        let (mut perp_x, mut perp_y) = (-dy / line_length, dx / line_length);

        if angle_flipped {
            perp_x = -perp_x;
            perp_y = -perp_y;
        }

        let offset = match text.v_align {
            TextAlign::Start => -(text.font_size / 2.0 + 5.0),
            TextAlign::Center => 0.0,
            TextAlign::End => text.font_size / 2.0 + 5.0,
        };

        let final_x = x + perp_x * offset;
        let final_y = y + perp_y * offset;

        Some(TextAnchor::with_rotation(
            final_x,
            final_y,
            &self.data.color.stroke,
            angle,
        ))
    }

    fn level_configs(&self) -> Option<Vec<FibLevelConfig>> {
        Some(self.level_configs.clone())
    }

    fn set_level_configs(&mut self, configs: Vec<FibLevelConfig>) -> bool {
        self.level_configs = configs;
        true
    }

    fn to_json(&self) -> String {
        serde_json::to_string(self).unwrap_or_default()
    }

    fn clone_box(&self) -> Box<dyn Primitive> {
        Box::new(self.clone())
    }
}

// =============================================================================
// Factory Registration
// =============================================================================

fn create_pitchfork(points: &[(f64, f64)], color: &str) -> Box<dyn Primitive> {
    let (bar1, price1) = points.first().copied().unwrap_or((0.0, 0.0));
    let (bar2, price2) = points
        .get(1)
        .copied()
        .unwrap_or((bar1 + 10.0, price1 + 10.0));
    let (bar3, price3) = points
        .get(2)
        .copied()
        .unwrap_or((bar1 + 10.0, price1 - 10.0));
    Box::new(Pitchfork::new(
        bar1, price1, bar2, price2, bar3, price3, color,
    ))
}

pub fn metadata() -> PrimitiveMetadata {
    PrimitiveMetadata {
        type_id: "pitchfork",
        display_name: "Pitchfork",
        kind: PrimitiveKind::Channel,
        factory: create_pitchfork,
        supports_text: true,
        has_levels: true,
        has_points_config: false,
    }
}
