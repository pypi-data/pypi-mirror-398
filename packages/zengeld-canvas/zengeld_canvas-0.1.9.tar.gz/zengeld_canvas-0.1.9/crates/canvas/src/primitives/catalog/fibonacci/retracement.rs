//! Fibonacci Retracement primitive
//!
//! Shows horizontal levels at Fibonacci ratios between two price points.
//! Standard levels: 0%, 23.6%, 38.2%, 50%, 61.8%, 78.6%, 100%

use super::super::{
    LineStyle, Primitive, PrimitiveColor, PrimitiveData, PrimitiveKind, PrimitiveMetadata,
    RenderContext, TextAlign, TextAnchor, config::FibLevelConfig, crisp,
};
use serde::{Deserialize, Serialize};

/// Standard Fibonacci retracement levels
pub const DEFAULT_LEVELS: &[f64] = &[0.0, 0.236, 0.382, 0.5, 0.618, 0.786, 1.0];

/// Extended Fibonacci levels (including extensions)
pub const EXTENDED_LEVELS: &[f64] = &[
    0.0, 0.236, 0.382, 0.5, 0.618, 0.786, 1.0, 1.272, 1.618, 2.0, 2.618,
];

/// Create default level configurations
pub fn default_level_configs() -> Vec<FibLevelConfig> {
    DEFAULT_LEVELS
        .iter()
        .map(|&level| FibLevelConfig::new(level))
        .collect()
}

/// Create extended level configurations (with extensions)
pub fn extended_level_configs() -> Vec<FibLevelConfig> {
    EXTENDED_LEVELS
        .iter()
        .map(|&level| FibLevelConfig::new(level))
        .collect()
}

/// Create level configurations with fills between zones
/// Uses professional coloring: different colors for different zones
pub fn filled_level_configs() -> Vec<FibLevelConfig> {
    vec![
        FibLevelConfig::with_fill(0.0, Some("#787b86".to_string()), 0.08),
        FibLevelConfig::with_fill(0.236, Some("#f7525f".to_string()), 0.08),
        FibLevelConfig::with_fill(0.382, Some("#22ab94".to_string()), 0.08),
        FibLevelConfig::with_fill(0.5, Some("#2962ff".to_string()), 0.08),
        FibLevelConfig::with_fill(0.618, Some("#ff9800".to_string()), 0.08),
        FibLevelConfig::with_fill(0.786, Some("#9c27b0".to_string()), 0.08),
        FibLevelConfig::new(1.0), // No fill for last level
    ]
}

/// Fibonacci Retracement - horizontal levels at Fib ratios
#[derive(Clone, Debug, Serialize, Deserialize)]
pub struct FibRetracement {
    /// Common primitive data
    pub data: PrimitiveData,
    /// Start bar (point 1)
    pub bar1: f64,
    /// Start price (point 1 - usually swing high or low)
    pub price1: f64,
    /// End bar (point 2)
    pub bar2: f64,
    /// End price (point 2 - usually swing low or high)
    pub price2: f64,
    /// Fibonacci level configurations (with individual colors/widths)
    #[serde(
        default = "default_level_configs",
        deserialize_with = "deserialize_level_configs"
    )]
    pub level_configs: Vec<FibLevelConfig>,
    /// Show price labels
    #[serde(default = "default_true")]
    pub show_prices: bool,
    /// Show percentage labels
    #[serde(default = "default_true")]
    pub show_percentages: bool,
    /// Extend lines to left
    #[serde(default)]
    pub extend_left: bool,
    /// Extend lines to right
    #[serde(default = "default_true")]
    pub extend_right: bool,
    /// Fill between levels
    #[serde(default)]
    pub show_fill: bool,
    /// Fill opacity (0.0 to 1.0)
    #[serde(default = "default_fill_opacity")]
    pub fill_opacity: f64,
}

fn default_true() -> bool {
    true
}
fn default_fill_opacity() -> f64 {
    0.1
}

/// Backward compatibility: deserialize old `levels: Vec<f64>` format
fn deserialize_level_configs<'de, D>(deserializer: D) -> Result<Vec<FibLevelConfig>, D::Error>
where
    D: serde::Deserializer<'de>,
{
    #[derive(Deserialize)]
    #[serde(untagged)]
    enum LevelFormat {
        Configs(Vec<FibLevelConfig>),
        Levels(Vec<f64>),
    }

    match LevelFormat::deserialize(deserializer)? {
        LevelFormat::Configs(configs) => Ok(configs),
        LevelFormat::Levels(levels) => {
            // Convert old format to new format
            Ok(levels
                .iter()
                .map(|&level| FibLevelConfig::new(level))
                .collect())
        }
    }
}

impl FibRetracement {
    /// Create a new Fibonacci retracement
    pub fn new(bar1: f64, price1: f64, bar2: f64, price2: f64, color: &str) -> Self {
        Self {
            data: PrimitiveData {
                type_id: "fib_retracement".to_string(),
                display_name: "Fib Retracement".to_string(),
                color: PrimitiveColor::new(color),
                width: 1.0,
                ..Default::default()
            },
            bar1,
            price1,
            bar2,
            price2,
            level_configs: default_level_configs(),
            show_prices: true,
            show_percentages: true,
            extend_left: false,
            extend_right: true,
            show_fill: false,
            fill_opacity: 0.1,
        }
    }

    /// Get the price at a given Fibonacci level
    pub fn price_at_level(&self, level: f64) -> f64 {
        self.price1 + (self.price2 - self.price1) * level
    }

    /// Get all level prices (only visible levels)
    pub fn level_prices(&self) -> Vec<(f64, f64)> {
        self.level_configs
            .iter()
            .filter(|cfg| cfg.visible)
            .map(|cfg| (cfg.level, self.price_at_level(cfg.level)))
            .collect()
    }
}

impl Primitive for FibRetracement {
    fn type_id(&self) -> &'static str {
        "fib_retracement"
    }

    fn display_name(&self) -> &str {
        &self.data.display_name
    }

    fn kind(&self) -> PrimitiveKind {
        PrimitiveKind::Fibonacci
    }

    fn data(&self) -> &PrimitiveData {
        &self.data
    }

    fn data_mut(&mut self) -> &mut PrimitiveData {
        &mut self.data
    }

    fn points(&self) -> Vec<(f64, f64)> {
        vec![(self.bar1, self.price1), (self.bar2, self.price2)]
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
    }

    fn translate(&mut self, bar_delta: f64, price_delta: f64) {
        self.bar1 += bar_delta;
        self.bar2 += bar_delta;
        self.price1 += price_delta;
        self.price2 += price_delta;
    }

    fn render(&self, ctx: &mut dyn RenderContext, is_selected: bool) {
        let dpr = ctx.dpr();
        let x1 = ctx.bar_to_x(self.bar1);
        let x2 = ctx.bar_to_x(self.bar2);
        let chart_width = ctx.chart_width();

        let left_x = if self.extend_left { 0.0 } else { x1.min(x2) };
        let right_x = if self.extend_right {
            chart_width
        } else {
            x1.max(x2)
        };

        // Collect visible levels sorted by level value for fill rendering
        let mut visible_levels: Vec<(usize, f64, f64)> = self
            .level_configs
            .iter()
            .enumerate()
            .filter(|(_, cfg)| cfg.visible)
            .map(|(idx, cfg)| {
                let y = ctx.price_to_y(self.price_at_level(cfg.level));
                (idx, cfg.level, y)
            })
            .collect();
        visible_levels.sort_by(|a, b| a.1.partial_cmp(&b.1).unwrap_or(std::cmp::Ordering::Equal));

        // Draw fills between adjacent visible levels (before lines so lines are on top)
        for i in 0..visible_levels.len().saturating_sub(1) {
            let (idx, _, y_top) = visible_levels[i];
            let (_, _, y_bottom) = visible_levels[i + 1];

            let cfg = &self.level_configs[idx];
            if cfg.fill_enabled {
                // Use fill_color or fall back to line color
                let fill_color = cfg
                    .fill_color
                    .as_deref()
                    .or(cfg.color.as_deref())
                    .unwrap_or(&self.data.color.stroke);

                // Apply fill with opacity
                ctx.set_fill_color_alpha(fill_color, cfg.fill_opacity);
                ctx.begin_path();
                ctx.move_to(left_x, y_top);
                ctx.line_to(right_x, y_top);
                ctx.line_to(right_x, y_bottom);
                ctx.line_to(left_x, y_bottom);
                ctx.close_path();
                ctx.fill();
                ctx.reset_alpha();
            }
        }

        // Draw each level line with individual colors/widths
        for cfg in &self.level_configs {
            if !cfg.visible {
                continue;
            }

            let level_price = self.price_at_level(cfg.level);
            let y = ctx.price_to_y(level_price);

            // Use level-specific color or fall back to main color
            let color = cfg.color.as_deref().unwrap_or(&self.data.color.stroke);
            ctx.set_stroke_color(color);

            // Use level-specific width or fall back to main width
            let width = cfg.width.unwrap_or(self.data.width);
            ctx.set_stroke_width(width);

            // Parse style from string
            let line_style = match cfg.style.as_str() {
                "dashed" => LineStyle::Dashed,
                "dotted" => LineStyle::Dotted,
                "large_dashed" => LineStyle::LargeDashed,
                "sparse_dotted" => LineStyle::SparseDotted,
                _ => LineStyle::Solid,
            };

            match line_style {
                LineStyle::Solid => ctx.set_line_dash(&[]),
                LineStyle::Dashed => ctx.set_line_dash(&[8.0, 4.0]),
                LineStyle::Dotted => ctx.set_line_dash(&[2.0, 2.0]),
                LineStyle::LargeDashed => ctx.set_line_dash(&[12.0, 6.0]),
                LineStyle::SparseDotted => ctx.set_line_dash(&[2.0, 8.0]),
            }

            ctx.begin_path();
            ctx.move_to(crisp(left_x, dpr), crisp(y, dpr));
            ctx.line_to(crisp(right_x, dpr), crisp(y, dpr));
            ctx.stroke();
        }
        ctx.set_line_dash(&[]);

        // Draw connecting line from point 1 to point 2
        let y1 = ctx.price_to_y(self.price1);
        let y2 = ctx.price_to_y(self.price2);
        ctx.set_line_dash(&[4.0, 4.0]);
        ctx.begin_path();
        ctx.move_to(crisp(x1, dpr), crisp(y1, dpr));
        ctx.line_to(crisp(x2, dpr), crisp(y2, dpr));
        ctx.stroke();
        ctx.set_line_dash(&[]);

        let _ = is_selected;
    }

    fn text_anchor(&self, ctx: &dyn RenderContext) -> Option<TextAnchor> {
        // Only render if text is set and has content
        let text = self.data.text.as_ref()?;
        if text.content.is_empty() {
            return None;
        }

        // Get screen coordinates
        let x1 = ctx.bar_to_x(self.bar1);
        let y1 = ctx.price_to_y(self.price1);
        let x2 = ctx.bar_to_x(self.bar2);
        let y2 = ctx.price_to_y(self.price2);

        // Determine top/bottom Y (in screen coords, smaller y = top)
        let (top_y, bottom_y) = if y1 < y2 { (y1, y2) } else { (y2, y1) };

        // Determine left/right X
        let (left_x, right_x) = if x1 < x2 { (x1, x2) } else { (x2, x1) };

        // Calculate center
        let center_x = (x1 + x2) / 2.0;
        let center_y = (y1 + y2) / 2.0;

        // Calculate text position based on alignment
        // v_align: Start = above top line, Center = center, End = below bottom line
        // h_align: Start = left, Center = center, End = right

        let text_offset = 8.0; // pixels offset from fib box

        let x = match text.h_align {
            TextAlign::Start => left_x,
            TextAlign::Center => center_x,
            TextAlign::End => right_x,
        };

        let y = match text.v_align {
            TextAlign::Start => top_y - text_offset, // above top line
            TextAlign::Center => center_y,           // center of fib
            TextAlign::End => bottom_y + text_offset + text.font_size, // below bottom line
        };

        Some(TextAnchor::new(x, y, &self.data.color.stroke))
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

// Note: Configurable is now implemented via blanket impl in config.rs
// This provides base configuration (color, width, style, coordinates) automatically.
// Custom properties (show_prices, extend_left, etc.) could be added via a
// separate trait or by extending the base properties in the future.

// =============================================================================
// Factory Registration
// =============================================================================

fn create_fib_retracement(points: &[(f64, f64)], color: &str) -> Box<dyn Primitive> {
    let (bar1, price1) = points.first().copied().unwrap_or((0.0, 0.0));
    let (bar2, price2) = points.get(1).copied().unwrap_or((bar1 + 10.0, price1));
    Box::new(FibRetracement::new(bar1, price1, bar2, price2, color))
}

pub fn metadata() -> PrimitiveMetadata {
    PrimitiveMetadata {
        type_id: "fib_retracement",
        display_name: "Fib Retracement",
        kind: PrimitiveKind::Fibonacci,
        factory: create_fib_retracement,
        supports_text: true,
        has_levels: true,
        has_points_config: false,
    }
}
