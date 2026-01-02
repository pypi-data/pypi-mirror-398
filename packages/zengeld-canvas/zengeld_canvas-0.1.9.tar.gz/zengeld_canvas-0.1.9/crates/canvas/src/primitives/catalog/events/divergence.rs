//! Divergence Event - RSI/MACD/indicator divergence markers

use super::super::{
    Primitive, PrimitiveColor, PrimitiveData, PrimitiveKind, PrimitiveMetadata, RenderContext,
    TextAnchor, crisp,
};
use serde::{Deserialize, Serialize};

/// Type of divergence
#[derive(Clone, Copy, Debug, PartialEq, Eq, Serialize, Deserialize)]
#[serde(rename_all = "snake_case")]
#[derive(Default)]
pub enum DivergenceType {
    /// Regular bullish divergence (price lower low, indicator higher low)
    #[default]
    RegularBullish,
    /// Regular bearish divergence (price higher high, indicator lower high)
    RegularBearish,
    /// Hidden bullish divergence (price higher low, indicator lower low)
    HiddenBullish,
    /// Hidden bearish divergence (price lower high, indicator higher high)
    HiddenBearish,
}

impl DivergenceType {
    pub fn as_str(&self) -> &'static str {
        match self {
            Self::RegularBullish => "regular_bullish",
            Self::RegularBearish => "regular_bearish",
            Self::HiddenBullish => "hidden_bullish",
            Self::HiddenBearish => "hidden_bearish",
        }
    }

    pub fn display_name(&self) -> &'static str {
        match self {
            Self::RegularBullish => "Regular Bullish Divergence",
            Self::RegularBearish => "Regular Bearish Divergence",
            Self::HiddenBullish => "Hidden Bullish Divergence",
            Self::HiddenBearish => "Hidden Bearish Divergence",
        }
    }

    pub fn short_name(&self) -> &'static str {
        match self {
            Self::RegularBullish => "Bull Div",
            Self::RegularBearish => "Bear Div",
            Self::HiddenBullish => "Hidden Bull",
            Self::HiddenBearish => "Hidden Bear",
        }
    }

    pub fn default_color(&self) -> &'static str {
        match self {
            Self::RegularBullish | Self::HiddenBullish => "#26a69a",
            Self::RegularBearish | Self::HiddenBearish => "#ef5350",
        }
    }

    pub fn is_bullish(&self) -> bool {
        matches!(self, Self::RegularBullish | Self::HiddenBullish)
    }

    pub fn is_hidden(&self) -> bool {
        matches!(self, Self::HiddenBullish | Self::HiddenBearish)
    }
}

/// Divergence event primitive
#[derive(Clone, Debug, Serialize, Deserialize)]
pub struct Divergence {
    pub data: PrimitiveData,
    // First pivot point
    pub bar1: f64,
    pub price1: f64,
    // Second pivot point
    pub bar2: f64,
    pub price2: f64,
    // Indicator values at pivots
    pub indicator_value1: f64,
    pub indicator_value2: f64,
    pub divergence_type: DivergenceType,
    #[serde(default = "default_line_width")]
    pub line_width: f64,
    #[serde(default)]
    pub indicator_name: String,
}

fn default_line_width() -> f64 {
    2.0
}

impl Divergence {
    pub fn new(
        bar1: f64,
        price1: f64,
        bar2: f64,
        price2: f64,
        divergence_type: DivergenceType,
    ) -> Self {
        let color = divergence_type.default_color();
        Self {
            data: PrimitiveData {
                type_id: "divergence".to_string(),
                display_name: "Divergence".to_string(),
                color: PrimitiveColor::new(color),
                width: 2.0,
                ..Default::default()
            },
            bar1,
            price1,
            bar2,
            price2,
            indicator_value1: 0.0,
            indicator_value2: 0.0,
            divergence_type,
            line_width: default_line_width(),
            indicator_name: String::new(),
        }
    }

    pub fn regular_bullish(bar1: f64, price1: f64, bar2: f64, price2: f64) -> Self {
        Self::new(bar1, price1, bar2, price2, DivergenceType::RegularBullish)
    }

    pub fn regular_bearish(bar1: f64, price1: f64, bar2: f64, price2: f64) -> Self {
        Self::new(bar1, price1, bar2, price2, DivergenceType::RegularBearish)
    }

    pub fn hidden_bullish(bar1: f64, price1: f64, bar2: f64, price2: f64) -> Self {
        Self::new(bar1, price1, bar2, price2, DivergenceType::HiddenBullish)
    }

    pub fn hidden_bearish(bar1: f64, price1: f64, bar2: f64, price2: f64) -> Self {
        Self::new(bar1, price1, bar2, price2, DivergenceType::HiddenBearish)
    }

    pub fn with_indicator(mut self, name: &str) -> Self {
        self.indicator_name = name.to_string();
        self
    }

    pub fn with_indicator_values(mut self, val1: f64, val2: f64) -> Self {
        self.indicator_value1 = val1;
        self.indicator_value2 = val2;
        self
    }
}

impl Primitive for Divergence {
    fn type_id(&self) -> &'static str {
        "divergence"
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
        vec![(self.bar1, self.price1), (self.bar2, self.price2)]
    }
    fn set_points(&mut self, points: &[(f64, f64)]) {
        if let Some(&(b, p)) = points.first() {
            self.bar1 = b;
            self.price1 = p;
        }
        if let Some(&(b, p)) = points.get(1) {
            self.bar2 = b;
            self.price2 = p;
        }
    }
    fn translate(&mut self, bd: f64, pd: f64) {
        self.bar1 += bd;
        self.price1 += pd;
        self.bar2 += bd;
        self.price2 += pd;
    }

    fn render(&self, ctx: &mut dyn RenderContext, _is_selected: bool) {
        let dpr = ctx.dpr();
        let x1 = ctx.bar_to_x(self.bar1);
        let y1 = ctx.price_to_y(self.price1);
        let x2 = ctx.bar_to_x(self.bar2);
        let y2 = ctx.price_to_y(self.price2);

        ctx.set_stroke_color(&self.data.color.stroke);
        ctx.set_stroke_width(self.line_width);

        // Draw dashed line connecting the two pivots (price line)
        ctx.save();
        if self.divergence_type.is_hidden() {
            ctx.set_line_dash(&[6.0, 4.0]); // Longer dashes for hidden
        } else {
            ctx.set_line_dash(&[4.0, 2.0]);
        }
        ctx.begin_path();
        ctx.move_to(crisp(x1, dpr), crisp(y1, dpr));
        ctx.line_to(crisp(x2, dpr), crisp(y2, dpr));
        ctx.stroke();
        ctx.restore();

        // Draw circles at pivot points
        ctx.set_fill_color(&self.data.color.stroke);
        let radius = 4.0;
        ctx.begin_path();
        ctx.arc(
            crisp(x1, dpr),
            crisp(y1, dpr),
            radius,
            0.0,
            std::f64::consts::TAU,
        );
        ctx.fill();
        ctx.begin_path();
        ctx.arc(
            crisp(x2, dpr),
            crisp(y2, dpr),
            radius,
            0.0,
            std::f64::consts::TAU,
        );
        ctx.fill();

        // Draw small arrow at the end indicating direction
        let arrow_size = 8.0;
        ctx.begin_path();
        if self.divergence_type.is_bullish() {
            // Upward arrow
            ctx.move_to(crisp(x2, dpr), crisp(y2 - arrow_size - 6.0, dpr));
            ctx.line_to(crisp(x2 - arrow_size / 2.0, dpr), crisp(y2 - 6.0, dpr));
            ctx.line_to(crisp(x2 + arrow_size / 2.0, dpr), crisp(y2 - 6.0, dpr));
        } else {
            // Downward arrow
            ctx.move_to(crisp(x2, dpr), crisp(y2 + arrow_size + 6.0, dpr));
            ctx.line_to(crisp(x2 - arrow_size / 2.0, dpr), crisp(y2 + 6.0, dpr));
            ctx.line_to(crisp(x2 + arrow_size / 2.0, dpr), crisp(y2 + 6.0, dpr));
        }
        ctx.close_path();
        ctx.fill();
    }

    fn text_anchor(&self, ctx: &dyn RenderContext) -> Option<TextAnchor> {
        let text = self.data.text.as_ref()?;
        if text.content.is_empty() {
            return None;
        }

        let x = ctx.bar_to_x(self.bar2);
        let y = ctx.price_to_y(self.price2);
        let offset = 20.0 + text.font_size / 2.0;
        let y_offset = if self.divergence_type.is_bullish() {
            -offset
        } else {
            offset
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
        type_id: "divergence",
        display_name: "Divergence",
        kind: PrimitiveKind::Signal,
        factory: |points, color| {
            let (b1, p1) = points.first().copied().unwrap_or((0.0, 0.0));
            let (b2, p2) = points.get(1).copied().unwrap_or((b1 + 10.0, p1));
            let mut event = Divergence::new(b1, p1, b2, p2, DivergenceType::RegularBullish);
            event.data.color = PrimitiveColor::new(color);
            Box::new(event)
        },
        supports_text: true,
        has_levels: false,
        has_points_config: false,
    }
}
