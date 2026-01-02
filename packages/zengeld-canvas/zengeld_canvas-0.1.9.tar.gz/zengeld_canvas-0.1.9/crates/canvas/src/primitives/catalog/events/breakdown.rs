//! Breakdown/Breakout Event - Level breakout or breakdown events

use super::super::{
    Primitive, PrimitiveColor, PrimitiveData, PrimitiveKind, PrimitiveMetadata, RenderContext,
    TextAlign, TextAnchor, crisp,
};
use serde::{Deserialize, Serialize};

/// Type of breakdown/breakout
#[derive(Clone, Copy, Debug, PartialEq, Eq, Serialize, Deserialize)]
#[serde(rename_all = "snake_case")]
#[derive(Default)]
pub enum BreakdownType {
    /// Support level breakdown
    #[default]
    SupportBreak,
    /// Resistance level breakout
    ResistanceBreak,
    /// Trend line break
    TrendLineBreak,
    /// Channel breakout
    ChannelBreak,
    /// Range breakout
    RangeBreak,
    /// Moving average break
    MaBreak,
    /// Previous high/low break
    SwingBreak,
    /// Consolidation breakout
    ConsolidationBreak,
    /// Custom break type
    Custom,
}

impl BreakdownType {
    pub fn as_str(&self) -> &'static str {
        match self {
            Self::SupportBreak => "support_break",
            Self::ResistanceBreak => "resistance_break",
            Self::TrendLineBreak => "trend_line_break",
            Self::ChannelBreak => "channel_break",
            Self::RangeBreak => "range_break",
            Self::MaBreak => "ma_break",
            Self::SwingBreak => "swing_break",
            Self::ConsolidationBreak => "consolidation_break",
            Self::Custom => "custom",
        }
    }

    pub fn display_name(&self) -> &'static str {
        match self {
            Self::SupportBreak => "Support Breakdown",
            Self::ResistanceBreak => "Resistance Breakout",
            Self::TrendLineBreak => "Trend Line Break",
            Self::ChannelBreak => "Channel Breakout",
            Self::RangeBreak => "Range Breakout",
            Self::MaBreak => "MA Break",
            Self::SwingBreak => "Swing Break",
            Self::ConsolidationBreak => "Consolidation Breakout",
            Self::Custom => "Custom Break",
        }
    }

    pub fn default_color(&self) -> &'static str {
        match self {
            Self::SupportBreak => "#ef5350",       // Red - bearish
            Self::ResistanceBreak => "#26a69a",    // Green - bullish
            Self::TrendLineBreak => "#FF9800",     // Orange
            Self::ChannelBreak => "#2196F3",       // Blue
            Self::RangeBreak => "#9C27B0",         // Purple
            Self::MaBreak => "#00BCD4",            // Cyan
            Self::SwingBreak => "#E91E63",         // Pink
            Self::ConsolidationBreak => "#8BC34A", // Light green
            Self::Custom => "#787B86",             // Gray
        }
    }

    pub fn is_bullish(&self) -> bool {
        matches!(
            self,
            Self::ResistanceBreak | Self::RangeBreak | Self::ConsolidationBreak
        )
    }
}

/// Breakdown event primitive
#[derive(Clone, Debug, Serialize, Deserialize)]
pub struct Breakdown {
    pub data: PrimitiveData,
    pub bar: f64,
    pub price: f64,
    pub level_price: f64, // The level that was broken
    pub breakdown_type: BreakdownType,
    #[serde(default = "default_size")]
    pub size: f64,
    #[serde(default)]
    pub level_name: String,
}

fn default_size() -> f64 {
    16.0
}

impl Breakdown {
    pub fn new(bar: f64, price: f64, level_price: f64, breakdown_type: BreakdownType) -> Self {
        let color = breakdown_type.default_color();
        Self {
            data: PrimitiveData {
                type_id: "breakdown".to_string(),
                display_name: "Breakdown".to_string(),
                color: PrimitiveColor::new(color),
                width: 2.0,
                ..Default::default()
            },
            bar,
            price,
            level_price,
            breakdown_type,
            size: default_size(),
            level_name: String::new(),
        }
    }

    pub fn support_break(bar: f64, price: f64, level: f64) -> Self {
        Self::new(bar, price, level, BreakdownType::SupportBreak)
    }

    pub fn resistance_break(bar: f64, price: f64, level: f64) -> Self {
        Self::new(bar, price, level, BreakdownType::ResistanceBreak)
    }

    pub fn with_level_name(mut self, name: &str) -> Self {
        self.level_name = name.to_string();
        self
    }
}

impl Primitive for Breakdown {
    fn type_id(&self) -> &'static str {
        "breakdown"
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
        let level_y = ctx.price_to_y(self.level_price);
        let s = self.size;

        ctx.set_stroke_color(&self.data.color.stroke);
        ctx.set_stroke_width(self.data.width);

        // Draw horizontal dashed line at level
        ctx.save();
        ctx.set_line_dash(&[4.0, 4.0]);
        ctx.begin_path();
        ctx.move_to(crisp(x - s * 2.0, dpr), crisp(level_y, dpr));
        ctx.line_to(crisp(x + s * 2.0, dpr), crisp(level_y, dpr));
        ctx.stroke();
        ctx.restore();

        // Draw arrow showing direction of break
        ctx.set_fill_color(&self.data.color.stroke);
        ctx.begin_path();
        let is_up = self.price > self.level_price;
        if is_up {
            // Upward arrow (breakout)
            ctx.move_to(crisp(x, dpr), crisp(y - s / 2.0, dpr)); // top
            ctx.line_to(crisp(x - s / 3.0, dpr), crisp(y, dpr)); // left
            ctx.line_to(crisp(x + s / 3.0, dpr), crisp(y, dpr)); // right
        } else {
            // Downward arrow (breakdown)
            ctx.move_to(crisp(x, dpr), crisp(y + s / 2.0, dpr)); // bottom
            ctx.line_to(crisp(x - s / 3.0, dpr), crisp(y, dpr)); // left
            ctx.line_to(crisp(x + s / 3.0, dpr), crisp(y, dpr)); // right
        }
        ctx.close_path();
        ctx.fill();

        // Vertical line connecting level to price
        ctx.set_line_dash(&[]);
        ctx.begin_path();
        ctx.move_to(crisp(x, dpr), crisp(level_y, dpr));
        ctx.line_to(crisp(x, dpr), crisp(y, dpr));
        ctx.stroke();
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
        type_id: "breakdown",
        display_name: "Breakdown",
        kind: PrimitiveKind::Signal,
        factory: |points, color| {
            let (b, p) = points.first().copied().unwrap_or((0.0, 0.0));
            let mut event = Breakdown::new(b, p, p, BreakdownType::SupportBreak);
            event.data.color = PrimitiveColor::new(color);
            Box::new(event)
        },
        supports_text: true,
        has_levels: false,
        has_points_config: false,
    }
}
