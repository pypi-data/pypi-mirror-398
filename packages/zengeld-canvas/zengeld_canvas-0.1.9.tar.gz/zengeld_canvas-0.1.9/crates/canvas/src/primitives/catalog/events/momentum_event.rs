//! Momentum Event - Momentum shifts, exhaustion, acceleration

use super::super::{
    Primitive, PrimitiveColor, PrimitiveData, PrimitiveKind, PrimitiveMetadata, RenderContext,
    TextAnchor, crisp,
};
use serde::{Deserialize, Serialize};

/// Type of momentum event
#[derive(Clone, Copy, Debug, PartialEq, Eq, Serialize, Deserialize)]
#[serde(rename_all = "snake_case")]
#[derive(Default)]
pub enum MomentumEventType {
    /// Momentum acceleration (trend strengthening)
    Acceleration,
    /// Momentum deceleration (trend weakening)
    Deceleration,
    /// Momentum exhaustion (trend about to end)
    Exhaustion,
    /// Momentum shift (change in momentum direction)
    #[default]
    Shift,
    /// Oversold condition
    Oversold,
    /// Overbought condition
    Overbought,
    /// RSI divergence signal
    RsiDivergence,
    /// MACD divergence signal
    MacdDivergence,
    /// Momentum building
    Building,
    /// Momentum fading
    Fading,
    /// Extreme reading (indicator at extreme)
    Extreme,
    /// Neutral/reset
    Neutral,
    /// Custom
    Custom,
}

impl MomentumEventType {
    pub fn as_str(&self) -> &'static str {
        match self {
            Self::Acceleration => "acceleration",
            Self::Deceleration => "deceleration",
            Self::Exhaustion => "exhaustion",
            Self::Shift => "shift",
            Self::Oversold => "oversold",
            Self::Overbought => "overbought",
            Self::RsiDivergence => "rsi_div",
            Self::MacdDivergence => "macd_div",
            Self::Building => "building",
            Self::Fading => "fading",
            Self::Extreme => "extreme",
            Self::Neutral => "neutral",
            Self::Custom => "custom",
        }
    }

    pub fn display_name(&self) -> &'static str {
        match self {
            Self::Acceleration => "Momentum Acceleration",
            Self::Deceleration => "Momentum Deceleration",
            Self::Exhaustion => "Momentum Exhaustion",
            Self::Shift => "Momentum Shift",
            Self::Oversold => "Oversold",
            Self::Overbought => "Overbought",
            Self::RsiDivergence => "RSI Divergence",
            Self::MacdDivergence => "MACD Divergence",
            Self::Building => "Momentum Building",
            Self::Fading => "Momentum Fading",
            Self::Extreme => "Extreme Reading",
            Self::Neutral => "Neutral",
            Self::Custom => "Custom",
        }
    }

    pub fn default_color(&self) -> &'static str {
        match self {
            Self::Acceleration | Self::Building => "#26a69a", // Green
            Self::Deceleration | Self::Fading => "#FF9800",   // Orange
            Self::Exhaustion => "#ef5350",                    // Red
            Self::Shift => "#9C27B0",                         // Purple
            Self::Oversold => "#26a69a",                      // Green (bullish signal)
            Self::Overbought => "#ef5350",                    // Red (bearish signal)
            Self::RsiDivergence | Self::MacdDivergence => "#E91E63", // Pink
            Self::Extreme => "#F44336",                       // Deep red
            Self::Neutral => "#787B86",                       // Gray
            Self::Custom => "#787B86",
        }
    }

    pub fn is_bullish(&self) -> bool {
        matches!(self, Self::Acceleration | Self::Building | Self::Oversold)
    }

    pub fn is_bearish(&self) -> bool {
        matches!(
            self,
            Self::Deceleration | Self::Fading | Self::Overbought | Self::Exhaustion
        )
    }
}

/// Momentum event primitive
#[derive(Clone, Debug, Serialize, Deserialize)]
pub struct MomentumEvent {
    pub data: PrimitiveData,
    pub bar: f64,
    pub price: f64,
    pub event_type: MomentumEventType,
    #[serde(default = "default_size")]
    pub size: f64,
    #[serde(default)]
    pub indicator_value: f64, // Optional indicator value
    #[serde(default)]
    pub indicator_name: String, // Which indicator triggered this
    #[serde(default)]
    pub strength: f64, // 0.0 - 1.0, how strong the signal
}

fn default_size() -> f64 {
    14.0
}

impl MomentumEvent {
    pub fn new(bar: f64, price: f64, event_type: MomentumEventType) -> Self {
        let color = event_type.default_color();
        Self {
            data: PrimitiveData {
                type_id: "momentum_event".to_string(),
                display_name: event_type.display_name().to_string(),
                color: PrimitiveColor::new(color),
                width: 2.0,
                ..Default::default()
            },
            bar,
            price,
            event_type,
            size: default_size(),
            indicator_value: 0.0,
            indicator_name: String::new(),
            strength: 1.0,
        }
    }

    pub fn oversold(bar: f64, price: f64) -> Self {
        Self::new(bar, price, MomentumEventType::Oversold)
    }

    pub fn overbought(bar: f64, price: f64) -> Self {
        Self::new(bar, price, MomentumEventType::Overbought)
    }

    pub fn exhaustion(bar: f64, price: f64) -> Self {
        Self::new(bar, price, MomentumEventType::Exhaustion)
    }

    pub fn acceleration(bar: f64, price: f64) -> Self {
        Self::new(bar, price, MomentumEventType::Acceleration)
    }

    pub fn with_indicator(mut self, name: &str, value: f64) -> Self {
        self.indicator_name = name.to_string();
        self.indicator_value = value;
        self
    }

    pub fn with_strength(mut self, strength: f64) -> Self {
        self.strength = strength.clamp(0.0, 1.0);
        self
    }
}

impl Primitive for MomentumEvent {
    fn type_id(&self) -> &'static str {
        "momentum_event"
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

        ctx.set_global_alpha(0.5 + self.strength * 0.5);
        ctx.set_fill_color(&self.data.color.stroke);
        ctx.set_stroke_color(&self.data.color.stroke);
        ctx.set_stroke_width(self.data.width);

        match self.event_type {
            MomentumEventType::Oversold | MomentumEventType::Overbought => {
                // Draw horizontal zone indicator
                let zone_height = s / 3.0;
                ctx.set_global_alpha(0.3);
                ctx.fill_rect(
                    crisp(x - s, dpr),
                    crisp(y - zone_height / 2.0, dpr),
                    s * 2.0,
                    zone_height,
                );
                ctx.set_global_alpha(1.0);

                // Draw arrow
                ctx.begin_path();
                if self.event_type == MomentumEventType::Oversold {
                    ctx.move_to(crisp(x, dpr), crisp(y - s / 2.0, dpr));
                    ctx.line_to(crisp(x - s / 3.0, dpr), crisp(y, dpr));
                    ctx.line_to(crisp(x + s / 3.0, dpr), crisp(y, dpr));
                } else {
                    ctx.move_to(crisp(x, dpr), crisp(y + s / 2.0, dpr));
                    ctx.line_to(crisp(x - s / 3.0, dpr), crisp(y, dpr));
                    ctx.line_to(crisp(x + s / 3.0, dpr), crisp(y, dpr));
                }
                ctx.close_path();
                ctx.fill();
            }
            MomentumEventType::Acceleration | MomentumEventType::Building => {
                // Draw double arrow (increasing)
                ctx.begin_path();
                ctx.move_to(crisp(x, dpr), crisp(y - s / 2.0, dpr));
                ctx.line_to(crisp(x - s / 3.0, dpr), crisp(y - s / 6.0, dpr));
                ctx.line_to(crisp(x + s / 3.0, dpr), crisp(y - s / 6.0, dpr));
                ctx.close_path();
                ctx.fill();

                ctx.begin_path();
                ctx.move_to(crisp(x, dpr), crisp(y + s / 6.0, dpr));
                ctx.line_to(crisp(x - s / 3.0, dpr), crisp(y + s / 2.0, dpr));
                ctx.line_to(crisp(x + s / 3.0, dpr), crisp(y + s / 2.0, dpr));
                ctx.close_path();
                ctx.fill();
            }
            MomentumEventType::Deceleration | MomentumEventType::Fading => {
                // Draw shrinking bars
                let bar_width = s / 6.0;
                let heights = [1.0, 0.7, 0.4];
                for (i, h) in heights.iter().enumerate() {
                    let bx = x - s / 2.0 + (i as f64 * (bar_width + 2.0));
                    let bh = s * h * 0.8;
                    ctx.fill_rect(crisp(bx, dpr), crisp(y - bh / 2.0, dpr), bar_width, bh);
                }
            }
            MomentumEventType::Exhaustion => {
                // Draw X mark (exhausted)
                ctx.begin_path();
                ctx.move_to(crisp(x - s / 2.0, dpr), crisp(y - s / 2.0, dpr));
                ctx.line_to(crisp(x + s / 2.0, dpr), crisp(y + s / 2.0, dpr));
                ctx.move_to(crisp(x + s / 2.0, dpr), crisp(y - s / 2.0, dpr));
                ctx.line_to(crisp(x - s / 2.0, dpr), crisp(y + s / 2.0, dpr));
                ctx.stroke();

                // Circle around it
                ctx.begin_path();
                ctx.arc(
                    crisp(x, dpr),
                    crisp(y, dpr),
                    s / 1.5,
                    0.0,
                    std::f64::consts::TAU,
                );
                ctx.stroke();
            }
            MomentumEventType::Shift => {
                // Draw wave/sine curve
                ctx.begin_path();
                ctx.move_to(crisp(x - s / 2.0, dpr), crisp(y, dpr));
                ctx.bezier_curve_to(
                    crisp(x - s / 4.0, dpr),
                    crisp(y - s / 3.0, dpr),
                    crisp(x + s / 4.0, dpr),
                    crisp(y + s / 3.0, dpr),
                    crisp(x + s / 2.0, dpr),
                    crisp(y, dpr),
                );
                ctx.stroke();
            }
            _ => {
                // Default: circle with M
                ctx.begin_path();
                ctx.arc(
                    crisp(x, dpr),
                    crisp(y, dpr),
                    s / 2.0,
                    0.0,
                    std::f64::consts::TAU,
                );
                ctx.stroke();

                ctx.set_font("10px sans-serif");
                ctx.set_fill_color(&self.data.color.stroke);
                ctx.fill_text("M", x - 4.0, y + 4.0);
            }
        }

        ctx.set_global_alpha(1.0);
    }

    fn text_anchor(&self, ctx: &dyn RenderContext) -> Option<TextAnchor> {
        let text = self.data.text.as_ref()?;
        if text.content.is_empty() {
            return None;
        }

        let x = ctx.bar_to_x(self.bar);
        let y = ctx.price_to_y(self.price);
        let offset = self.size + text.font_size;
        let y_offset = if self.event_type.is_bullish() {
            offset
        } else {
            -offset
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
        type_id: "momentum_event",
        display_name: "Momentum Event",
        kind: PrimitiveKind::Signal,
        factory: |points, color| {
            let (b, p) = points.first().copied().unwrap_or((0.0, 0.0));
            let mut event = MomentumEvent::new(b, p, MomentumEventType::Shift);
            event.data.color = PrimitiveColor::new(color);
            Box::new(event)
        },
        supports_text: true,
        has_levels: false,
        has_points_config: false,
    }
}
