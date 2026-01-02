//! Modified Schiff Pitchfork primitive
//!
//! A variation where the handle is moved to the price level of
//! point 2/3 midpoint but keeps the original bar position.

use super::super::{
    Primitive, PrimitiveColor, PrimitiveData, PrimitiveKind, PrimitiveMetadata, RenderContext,
    config::FibLevelConfig, crisp,
};
use serde::{Deserialize, Serialize};

use super::pitchfork::DEFAULT_PITCHFORK_LEVELS;

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
                if value.is_object() {
                    let config: FibLevelConfig =
                        serde_json::from_value(value).map_err(de::Error::custom)?;
                    configs.push(config);
                } else if let Some(level) = value.as_f64() {
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

fn default_true() -> bool {
    true
}

/// Modified Schiff Pitchfork
#[derive(Clone, Debug, Serialize, Deserialize)]
pub struct ModifiedSchiff {
    /// Common primitive data
    pub data: PrimitiveData,
    /// Point 1 - the handle
    pub bar1: f64,
    pub price1: f64,
    /// Point 2 - first swing
    pub bar2: f64,
    pub price2: f64,
    /// Point 3 - second swing
    pub bar3: f64,
    pub price3: f64,
    /// Pitchfork level configurations
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

impl ModifiedSchiff {
    /// Create a new Modified Schiff pitchfork
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
                type_id: "modified_schiff".to_string(),
                display_name: "Modified Schiff".to_string(),
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

    /// Get the adjusted handle point (Modified Schiff adjustment)
    /// Keeps original bar, moves price to midpoint of P2/P3
    pub fn adjusted_handle(&self) -> (f64, f64) {
        let mid_price = (self.price2 + self.price3) / 2.0;
        (self.bar1, (self.price1 + mid_price) / 2.0)
    }

    /// Get the midpoint between points 2 and 3
    pub fn midpoint(&self) -> (f64, f64) {
        (
            (self.bar2 + self.bar3) / 2.0,
            (self.price2 + self.price3) / 2.0,
        )
    }

    /// Get the channel offset
    pub fn channel_offset(&self) -> (f64, f64) {
        (
            (self.bar3 - self.bar2) / 2.0,
            (self.price3 - self.price2) / 2.0,
        )
    }
}

impl Primitive for ModifiedSchiff {
    fn type_id(&self) -> &'static str {
        "modified_schiff"
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
        let chart_width = ctx.chart_width();

        // Modified Schiff: use adjusted handle point
        let (adj_bar, adj_price) = self.adjusted_handle();
        let adj_x = ctx.bar_to_x(adj_bar);
        let adj_y = ctx.price_to_y(adj_price);

        let (mid_bar, mid_price) = self.midpoint();
        let mid_x = ctx.bar_to_x(mid_bar);
        let mid_y = ctx.price_to_y(mid_price);

        let (offset_bar, offset_price) = self.channel_offset();
        let offset_x = ctx.bar_to_x(mid_bar + offset_bar) - mid_x;
        let offset_y = ctx.price_to_y(mid_price + offset_price) - mid_y;

        // Draw pitchfork tines from adjusted handle
        for config in &self.level_configs {
            if !config.visible {
                continue;
            }

            let level = config.level;
            let start_x = adj_x + offset_x * level;
            let start_y = adj_y + offset_y * level;
            let end_x = mid_x + offset_x * level;
            let end_y = mid_y + offset_y * level;

            // Use level-specific color, width, and style if provided
            let color = config.color.as_ref().unwrap_or(&self.data.color.stroke);
            let width = config.width.unwrap_or(self.data.width);

            ctx.set_stroke_color(color);
            ctx.set_stroke_width(width);

            // Parse line style from config string
            match config.style.as_str() {
                "solid" => ctx.set_line_dash(&[]),
                "dashed" => ctx.set_line_dash(&[8.0, 4.0]),
                "dotted" => ctx.set_line_dash(&[2.0, 2.0]),
                "large_dashed" => ctx.set_line_dash(&[12.0, 6.0]),
                "sparse_dotted" => ctx.set_line_dash(&[2.0, 8.0]),
                _ => ctx.set_line_dash(&[]),
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

fn create_modified_schiff(points: &[(f64, f64)], color: &str) -> Box<dyn Primitive> {
    let (bar1, price1) = points.first().copied().unwrap_or((0.0, 0.0));
    let (bar2, price2) = points
        .get(1)
        .copied()
        .unwrap_or((bar1 + 10.0, price1 + 10.0));
    let (bar3, price3) = points
        .get(2)
        .copied()
        .unwrap_or((bar1 + 10.0, price1 - 10.0));
    Box::new(ModifiedSchiff::new(
        bar1, price1, bar2, price2, bar3, price3, color,
    ))
}

pub fn metadata() -> PrimitiveMetadata {
    PrimitiveMetadata {
        type_id: "modified_schiff",
        display_name: "Modified Schiff",
        kind: PrimitiveKind::Channel,
        factory: create_modified_schiff,
        supports_text: true,
        has_levels: true,
        has_points_config: false,
    }
}
