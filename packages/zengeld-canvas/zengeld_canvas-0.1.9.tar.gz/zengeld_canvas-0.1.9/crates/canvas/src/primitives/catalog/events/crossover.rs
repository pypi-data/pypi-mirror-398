//! Crossover Event - MA crossover, MACD line cross, etc.

use super::super::{
    Primitive, PrimitiveColor, PrimitiveData, PrimitiveKind, PrimitiveMetadata, RenderContext,
    TextAlign, TextAnchor, crisp,
};
use serde::{Deserialize, Serialize};

/// Type of crossover
#[derive(Clone, Copy, Debug, PartialEq, Eq, Serialize, Deserialize)]
#[serde(rename_all = "snake_case")]
#[derive(Default)]
pub enum CrossoverType {
    /// Moving average crossover (e.g., 10/20 MA)
    #[default]
    MovingAverage,
    /// MACD line crossing signal line
    Macd,
    /// Stochastic %K/%D crossover
    Stochastic,
    /// Price crossing a level (MA, support, etc.)
    PriceLevel,
    /// RSI crossing overbought/oversold level
    RsiLevel,
    /// Zero line crossover (MACD, momentum)
    ZeroLine,
    /// Custom crossover type
    Custom,
}

impl CrossoverType {
    pub fn as_str(&self) -> &'static str {
        match self {
            Self::MovingAverage => "ma_cross",
            Self::Macd => "macd_cross",
            Self::Stochastic => "stoch_cross",
            Self::PriceLevel => "price_level",
            Self::RsiLevel => "rsi_level",
            Self::ZeroLine => "zero_line",
            Self::Custom => "custom",
        }
    }

    pub fn display_name(&self) -> &'static str {
        match self {
            Self::MovingAverage => "MA Crossover",
            Self::Macd => "MACD Crossover",
            Self::Stochastic => "Stochastic Crossover",
            Self::PriceLevel => "Price Level Cross",
            Self::RsiLevel => "RSI Level Cross",
            Self::ZeroLine => "Zero Line Cross",
            Self::Custom => "Custom Crossover",
        }
    }
}

/// Direction of crossover
#[derive(Clone, Copy, Debug, PartialEq, Eq, Serialize, Deserialize)]
#[serde(rename_all = "snake_case")]
#[derive(Default)]
pub enum CrossoverDirection {
    /// Bullish crossover (fast crosses above slow)
    #[default]
    Bullish,
    /// Bearish crossover (fast crosses below slow)
    Bearish,
}

impl CrossoverDirection {
    pub fn default_color(&self) -> &'static str {
        match self {
            Self::Bullish => "#26a69a",
            Self::Bearish => "#ef5350",
        }
    }
}

/// Crossover event primitive
#[derive(Clone, Debug, Serialize, Deserialize)]
pub struct Crossover {
    pub data: PrimitiveData,
    pub bar: f64,
    pub price: f64,
    pub crossover_type: CrossoverType,
    pub direction: CrossoverDirection,
    #[serde(default = "default_size")]
    pub size: f64,
    #[serde(default)]
    pub indicator_name: String,
}

fn default_size() -> f64 {
    16.0
}

impl Crossover {
    pub fn new(
        bar: f64,
        price: f64,
        crossover_type: CrossoverType,
        direction: CrossoverDirection,
    ) -> Self {
        let color = direction.default_color();
        Self {
            data: PrimitiveData {
                type_id: "crossover".to_string(),
                display_name: "Crossover".to_string(),
                color: PrimitiveColor::new(color),
                width: 2.0,
                ..Default::default()
            },
            bar,
            price,
            crossover_type,
            direction,
            size: default_size(),
            indicator_name: String::new(),
        }
    }

    pub fn ma_cross(bar: f64, price: f64, direction: CrossoverDirection) -> Self {
        Self::new(bar, price, CrossoverType::MovingAverage, direction)
    }

    pub fn macd_cross(bar: f64, price: f64, direction: CrossoverDirection) -> Self {
        Self::new(bar, price, CrossoverType::Macd, direction)
    }

    pub fn with_indicator(mut self, name: &str) -> Self {
        self.indicator_name = name.to_string();
        self
    }
}

impl Primitive for Crossover {
    fn type_id(&self) -> &'static str {
        "crossover"
    }
    fn display_name(&self) -> &str {
        &self.data.display_name
    }
    fn kind(&self) -> PrimitiveKind {
        PrimitiveKind::Signal
    }
    fn data(&self) -> &PrimitiveData {
        &self.data
    }
    fn data_mut(&mut self) -> &mut PrimitiveData {
        &mut self.data
    }
    fn points(&self) -> Vec<(f64, f64)> {
        vec![(self.bar, self.price)]
    }
    fn set_points(&mut self, points: &[(f64, f64)]) {
        if let Some(&(b, p)) = points.first() {
            self.bar = b;
            self.price = p;
        }
    }
    fn translate(&mut self, bd: f64, pd: f64) {
        self.bar += bd;
        self.price += pd;
    }

    fn render(&self, ctx: &mut dyn RenderContext, _is_selected: bool) {
        let dpr = ctx.dpr();
        let x = ctx.bar_to_x(self.bar);
        let y = ctx.price_to_y(self.price);
        let s = self.size;

        ctx.set_fill_color(&self.data.color.stroke);
        ctx.set_stroke_color(&self.data.color.stroke);
        ctx.set_stroke_width(self.data.width);

        // Draw X mark for crossover
        ctx.begin_path();
        let offset = s / 2.0;
        ctx.move_to(crisp(x - offset, dpr), crisp(y - offset, dpr));
        ctx.line_to(crisp(x + offset, dpr), crisp(y + offset, dpr));
        ctx.move_to(crisp(x + offset, dpr), crisp(y - offset, dpr));
        ctx.line_to(crisp(x - offset, dpr), crisp(y + offset, dpr));
        ctx.stroke();

        // Draw small circle at center
        ctx.begin_path();
        ctx.arc(
            crisp(x, dpr),
            crisp(y, dpr),
            3.0,
            0.0,
            std::f64::consts::TAU,
        );
        ctx.fill();
    }

    fn text_anchor(&self, ctx: &dyn RenderContext) -> Option<TextAnchor> {
        let text = self.data.text.as_ref()?;
        if text.content.is_empty() {
            return None;
        }

        let x = ctx.bar_to_x(self.bar);
        let y = ctx.price_to_y(self.price);
        let offset = self.size + text.font_size / 2.0;
        let y_offset = match text.v_align {
            TextAlign::Start => -offset,
            TextAlign::Center => 0.0,
            TextAlign::End => offset,
        };
        Some(TextAnchor::new(x, y + y_offset, &self.data.color.stroke))
    }

    fn to_json(&self) -> String {
        serde_json::to_string(self).unwrap_or_default()
    }
    fn clone_box(&self) -> Box<dyn Primitive> {
        Box::new(self.clone())
    }
}

pub fn metadata() -> PrimitiveMetadata {
    PrimitiveMetadata {
        type_id: "crossover",
        display_name: "Crossover",
        kind: PrimitiveKind::Signal,
        factory: |points, color| {
            let (b, p) = points.first().copied().unwrap_or((0.0, 0.0));
            let mut event = Crossover::new(
                b,
                p,
                CrossoverType::MovingAverage,
                CrossoverDirection::Bullish,
            );
            event.data.color = PrimitiveColor::new(color);
            Box::new(event)
        },
        supports_text: true,
        has_levels: false,
        has_points_config: false,
    }
}
