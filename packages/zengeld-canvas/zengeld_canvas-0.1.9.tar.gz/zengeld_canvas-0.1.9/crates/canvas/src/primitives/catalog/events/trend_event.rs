//! Trend Event - Trend changes, reversals, continuations

use super::super::{
    Primitive, PrimitiveColor, PrimitiveData, PrimitiveKind, PrimitiveMetadata, RenderContext,
    TextAnchor, crisp,
};
use serde::{Deserialize, Serialize};

/// Type of trend event
#[derive(Clone, Copy, Debug, PartialEq, Eq, Serialize, Deserialize)]
#[serde(rename_all = "snake_case")]
#[derive(Default)]
pub enum TrendEventType {
    /// Trend start (new trend beginning)
    TrendStart,
    /// Trend end (trend termination)
    TrendEnd,
    /// Trend reversal (direction change)
    #[default]
    Reversal,
    /// Trend continuation (pullback complete, trend resuming)
    Continuation,
    /// Higher high (uptrend confirmation)
    HigherHigh,
    /// Higher low (uptrend confirmation)
    HigherLow,
    /// Lower high (downtrend confirmation)
    LowerHigh,
    /// Lower low (downtrend confirmation)
    LowerLow,
    /// Swing high (local maximum)
    SwingHigh,
    /// Swing low (local minimum)
    SwingLow,
    /// Change of character (trend structure break)
    CHoCH,
    /// Break of structure (trend confirmation)
    BoS,
    /// Pullback start
    PullbackStart,
    /// Pullback end
    PullbackEnd,
    /// Ranging/sideways market
    Ranging,
    /// Custom
    Custom,
}

impl TrendEventType {
    pub fn as_str(&self) -> &'static str {
        match self {
            Self::TrendStart => "trend_start",
            Self::TrendEnd => "trend_end",
            Self::Reversal => "reversal",
            Self::Continuation => "continuation",
            Self::HigherHigh => "hh",
            Self::HigherLow => "hl",
            Self::LowerHigh => "lh",
            Self::LowerLow => "ll",
            Self::SwingHigh => "swing_high",
            Self::SwingLow => "swing_low",
            Self::CHoCH => "choch",
            Self::BoS => "bos",
            Self::PullbackStart => "pullback_start",
            Self::PullbackEnd => "pullback_end",
            Self::Ranging => "ranging",
            Self::Custom => "custom",
        }
    }

    pub fn display_name(&self) -> &'static str {
        match self {
            Self::TrendStart => "Trend Start",
            Self::TrendEnd => "Trend End",
            Self::Reversal => "Reversal",
            Self::Continuation => "Continuation",
            Self::HigherHigh => "Higher High",
            Self::HigherLow => "Higher Low",
            Self::LowerHigh => "Lower High",
            Self::LowerLow => "Lower Low",
            Self::SwingHigh => "Swing High",
            Self::SwingLow => "Swing Low",
            Self::CHoCH => "CHoCH",
            Self::BoS => "Break of Structure",
            Self::PullbackStart => "Pullback Start",
            Self::PullbackEnd => "Pullback End",
            Self::Ranging => "Ranging",
            Self::Custom => "Custom",
        }
    }

    pub fn short_label(&self) -> &'static str {
        match self {
            Self::TrendStart => "TS",
            Self::TrendEnd => "TE",
            Self::Reversal => "REV",
            Self::Continuation => "CONT",
            Self::HigherHigh => "HH",
            Self::HigherLow => "HL",
            Self::LowerHigh => "LH",
            Self::LowerLow => "LL",
            Self::SwingHigh => "SH",
            Self::SwingLow => "SL",
            Self::CHoCH => "CHoCH",
            Self::BoS => "BoS",
            Self::PullbackStart => "PB",
            Self::PullbackEnd => "PBE",
            Self::Ranging => "RNG",
            Self::Custom => "?",
        }
    }

    pub fn default_color(&self) -> &'static str {
        match self {
            // Bullish events - green
            Self::HigherHigh | Self::HigherLow | Self::SwingLow | Self::TrendStart => "#26a69a",

            // Bearish events - red
            Self::LowerHigh | Self::LowerLow | Self::SwingHigh | Self::TrendEnd => "#ef5350",

            // Neutral/structure events - blue/purple
            Self::Reversal | Self::CHoCH => "#9C27B0",
            Self::Continuation | Self::BoS => "#2196F3",
            Self::PullbackStart | Self::PullbackEnd => "#FF9800",
            Self::Ranging => "#787B86",
            Self::Custom => "#787B86",
        }
    }

    pub fn is_bullish(&self) -> bool {
        matches!(self, Self::HigherHigh | Self::HigherLow | Self::SwingLow)
    }

    pub fn is_bearish(&self) -> bool {
        matches!(self, Self::LowerHigh | Self::LowerLow | Self::SwingHigh)
    }

    pub fn is_swing(&self) -> bool {
        matches!(
            self,
            Self::SwingHigh
                | Self::SwingLow
                | Self::HigherHigh
                | Self::HigherLow
                | Self::LowerHigh
                | Self::LowerLow
        )
    }
}

/// Trend event primitive
#[derive(Clone, Debug, Serialize, Deserialize)]
pub struct TrendEvent {
    pub data: PrimitiveData,
    pub bar: f64,
    pub price: f64,
    pub event_type: TrendEventType,
    #[serde(default = "default_size")]
    pub size: f64,
    #[serde(default)]
    pub is_bullish_context: bool, // Overall trend context
}

fn default_size() -> f64 {
    14.0
}

impl TrendEvent {
    pub fn new(bar: f64, price: f64, event_type: TrendEventType) -> Self {
        let color = event_type.default_color();
        Self {
            data: PrimitiveData {
                type_id: "trend_event".to_string(),
                display_name: event_type.display_name().to_string(),
                color: PrimitiveColor::new(color),
                width: 2.0,
                ..Default::default()
            },
            bar,
            price,
            event_type,
            size: default_size(),
            is_bullish_context: true,
        }
    }

    pub fn reversal(bar: f64, price: f64) -> Self {
        Self::new(bar, price, TrendEventType::Reversal)
    }

    pub fn continuation(bar: f64, price: f64) -> Self {
        Self::new(bar, price, TrendEventType::Continuation)
    }

    pub fn higher_high(bar: f64, price: f64) -> Self {
        Self::new(bar, price, TrendEventType::HigherHigh)
    }

    pub fn higher_low(bar: f64, price: f64) -> Self {
        Self::new(bar, price, TrendEventType::HigherLow)
    }

    pub fn lower_high(bar: f64, price: f64) -> Self {
        Self::new(bar, price, TrendEventType::LowerHigh)
    }

    pub fn lower_low(bar: f64, price: f64) -> Self {
        Self::new(bar, price, TrendEventType::LowerLow)
    }

    pub fn swing_high(bar: f64, price: f64) -> Self {
        Self::new(bar, price, TrendEventType::SwingHigh)
    }

    pub fn swing_low(bar: f64, price: f64) -> Self {
        Self::new(bar, price, TrendEventType::SwingLow)
    }

    pub fn choch(bar: f64, price: f64) -> Self {
        Self::new(bar, price, TrendEventType::CHoCH)
    }

    pub fn bos(bar: f64, price: f64) -> Self {
        Self::new(bar, price, TrendEventType::BoS)
    }

    pub fn with_context(mut self, bullish: bool) -> Self {
        self.is_bullish_context = bullish;
        self
    }
}

impl Primitive for TrendEvent {
    fn type_id(&self) -> &'static str {
        "trend_event"
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

        if self.event_type.is_swing() {
            // Draw swing point marker
            let is_high = matches!(
                self.event_type,
                TrendEventType::SwingHigh | TrendEventType::HigherHigh | TrendEventType::LowerHigh
            );

            // Small horizontal line at price level
            ctx.begin_path();
            ctx.move_to(crisp(x - s / 2.0, dpr), crisp(y, dpr));
            ctx.line_to(crisp(x + s / 2.0, dpr), crisp(y, dpr));
            ctx.stroke();

            // Small vertical tick
            ctx.begin_path();
            if is_high {
                ctx.move_to(crisp(x, dpr), crisp(y, dpr));
                ctx.line_to(crisp(x, dpr), crisp(y - s / 2.0, dpr));
            } else {
                ctx.move_to(crisp(x, dpr), crisp(y, dpr));
                ctx.line_to(crisp(x, dpr), crisp(y + s / 2.0, dpr));
            }
            ctx.stroke();

            // Draw label
            ctx.set_font("9px sans-serif");
            ctx.set_fill_color(&self.data.color.stroke);
            let label = self.event_type.short_label();
            let label_y = if is_high {
                y - s / 2.0 - 4.0
            } else {
                y + s / 2.0 + 10.0
            };
            ctx.fill_text(label, x - (label.len() as f64 * 3.0), label_y);
        } else if matches!(self.event_type, TrendEventType::CHoCH | TrendEventType::BoS) {
            // Draw structure break marker
            ctx.begin_path();
            ctx.move_to(crisp(x - s / 2.0, dpr), crisp(y, dpr));
            ctx.line_to(crisp(x + s / 2.0, dpr), crisp(y, dpr));
            ctx.stroke();

            // Draw label badge
            let label = self.event_type.short_label();
            let badge_width = (label.len() as f64 * 6.0) + 8.0;
            let badge_height = 14.0;
            let badge_y = y - badge_height - 4.0;

            ctx.fill_rect(
                crisp(x - badge_width / 2.0, dpr),
                crisp(badge_y, dpr),
                badge_width,
                badge_height,
            );

            ctx.set_fill_color("#FFFFFF");
            ctx.set_font("10px sans-serif");
            ctx.fill_text(label, x - (label.len() as f64 * 2.5), badge_y + 10.0);
        } else if matches!(self.event_type, TrendEventType::Reversal) {
            // Draw curved arrow for reversal
            ctx.begin_path();
            let arc_start = if self.is_bullish_context {
                std::f64::consts::PI
            } else {
                0.0
            };
            let arc_end = arc_start + std::f64::consts::PI;
            ctx.arc(crisp(x, dpr), crisp(y, dpr), s / 2.0, arc_start, arc_end);
            ctx.stroke();

            // Arrow head
            let arrow_x = if self.is_bullish_context {
                x + s / 2.0
            } else {
                x - s / 2.0
            };
            ctx.begin_path();
            ctx.move_to(crisp(arrow_x, dpr), crisp(y, dpr));
            if self.is_bullish_context {
                ctx.line_to(crisp(arrow_x - 4.0, dpr), crisp(y - 4.0, dpr));
                ctx.line_to(crisp(arrow_x - 4.0, dpr), crisp(y + 4.0, dpr));
            } else {
                ctx.line_to(crisp(arrow_x + 4.0, dpr), crisp(y - 4.0, dpr));
                ctx.line_to(crisp(arrow_x + 4.0, dpr), crisp(y + 4.0, dpr));
            }
            ctx.close_path();
            ctx.fill();
        } else {
            // Default: diamond shape
            ctx.begin_path();
            ctx.move_to(crisp(x, dpr), crisp(y - s / 2.0, dpr)); // top
            ctx.line_to(crisp(x + s / 2.0, dpr), crisp(y, dpr)); // right
            ctx.line_to(crisp(x, dpr), crisp(y + s / 2.0, dpr)); // bottom
            ctx.line_to(crisp(x - s / 2.0, dpr), crisp(y, dpr)); // left
            ctx.close_path();
            ctx.fill();
        }
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
        type_id: "trend_event",
        display_name: "Trend Event",
        kind: PrimitiveKind::Signal,
        factory: |points, color| {
            let (b, p) = points.first().copied().unwrap_or((0.0, 0.0));
            let mut event = TrendEvent::new(b, p, TrendEventType::Reversal);
            event.data.color = PrimitiveColor::new(color);
            Box::new(event)
        },
        supports_text: true,
        has_levels: false,
        has_points_config: false,
    }
}
