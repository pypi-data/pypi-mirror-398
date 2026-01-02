//! Zone Event - Supply/demand zones, order blocks, liquidity events

use super::super::{
    Primitive, PrimitiveColor, PrimitiveData, PrimitiveKind, PrimitiveMetadata, RenderContext,
    TextAnchor, crisp_rect,
};
use serde::{Deserialize, Serialize};

/// Type of zone
#[derive(Clone, Copy, Debug, PartialEq, Eq, Serialize, Deserialize)]
#[serde(rename_all = "snake_case")]
#[derive(Default)]
pub enum ZoneType {
    /// Supply zone (potential selling pressure)
    #[default]
    Supply,
    /// Demand zone (potential buying pressure)
    Demand,
    /// Order block (institutional footprint)
    OrderBlock,
    /// Fair value gap / imbalance
    FairValueGap,
    /// Liquidity pool (stop loss cluster)
    LiquidityPool,
    /// Breaker block
    BreakerBlock,
    /// Mitigation block
    MitigationBlock,
    /// Volume point of control
    VolumePoC,
    /// Volume value area high
    VolumeVAH,
    /// Volume value area low
    VolumeVAL,
    /// Custom zone
    Custom,
}

impl ZoneType {
    pub fn as_str(&self) -> &'static str {
        match self {
            Self::Supply => "supply",
            Self::Demand => "demand",
            Self::OrderBlock => "order_block",
            Self::FairValueGap => "fvg",
            Self::LiquidityPool => "liquidity",
            Self::BreakerBlock => "breaker",
            Self::MitigationBlock => "mitigation",
            Self::VolumePoC => "vpoc",
            Self::VolumeVAH => "vah",
            Self::VolumeVAL => "val",
            Self::Custom => "custom",
        }
    }

    pub fn display_name(&self) -> &'static str {
        match self {
            Self::Supply => "Supply Zone",
            Self::Demand => "Demand Zone",
            Self::OrderBlock => "Order Block",
            Self::FairValueGap => "Fair Value Gap",
            Self::LiquidityPool => "Liquidity Pool",
            Self::BreakerBlock => "Breaker Block",
            Self::MitigationBlock => "Mitigation Block",
            Self::VolumePoC => "Volume PoC",
            Self::VolumeVAH => "Value Area High",
            Self::VolumeVAL => "Value Area Low",
            Self::Custom => "Custom Zone",
        }
    }

    pub fn default_color(&self) -> &'static str {
        match self {
            Self::Supply | Self::VolumeVAH => "#ef535040", // Red transparent
            Self::Demand | Self::VolumeVAL => "#26a69a40", // Green transparent
            Self::OrderBlock => "#9C27B040",               // Purple
            Self::FairValueGap => "#2196F340",             // Blue
            Self::LiquidityPool => "#FF980040",            // Orange
            Self::BreakerBlock => "#E91E6340",             // Pink
            Self::MitigationBlock => "#00BCD440",          // Cyan
            Self::VolumePoC => "#FFC10740",                // Amber
            Self::Custom => "#787B8640",                   // Gray
        }
    }

    pub fn is_bullish(&self) -> bool {
        matches!(self, Self::Demand | Self::VolumeVAL)
    }

    pub fn is_bearish(&self) -> bool {
        matches!(self, Self::Supply | Self::VolumeVAH)
    }
}

/// Action that occurred at zone
#[derive(Clone, Copy, Debug, PartialEq, Eq, Serialize, Deserialize)]
#[serde(rename_all = "snake_case")]
#[derive(Default)]
pub enum ZoneAction {
    /// Zone was created/formed
    Created,
    /// Zone was tested (price touched)
    Tested,
    /// Zone was broken through
    Broken,
    /// Zone was mitigated (filled)
    Mitigated,
    /// Zone is still valid/active
    #[default]
    Active,
}

/// Zone event primitive
#[derive(Clone, Debug, Serialize, Deserialize)]
pub struct ZoneEvent {
    pub data: PrimitiveData,
    pub bar1: f64, // Zone start bar
    pub bar2: f64, // Zone end bar (extends right)
    pub price_high: f64,
    pub price_low: f64,
    pub zone_type: ZoneType,
    pub action: ZoneAction,
    #[serde(default)]
    pub strength: f64, // 0.0 - 1.0, how strong the zone is
    #[serde(default)]
    pub test_count: u32, // Times zone was tested
}

impl ZoneEvent {
    pub fn new(bar1: f64, bar2: f64, price_high: f64, price_low: f64, zone_type: ZoneType) -> Self {
        let color = zone_type.default_color();
        Self {
            data: PrimitiveData {
                type_id: "zone_event".to_string(),
                display_name: zone_type.display_name().to_string(),
                color: PrimitiveColor::new(color),
                width: 1.0,
                ..Default::default()
            },
            bar1,
            bar2,
            price_high,
            price_low,
            zone_type,
            action: ZoneAction::Active,
            strength: 1.0,
            test_count: 0,
        }
    }

    pub fn supply(bar1: f64, bar2: f64, high: f64, low: f64) -> Self {
        Self::new(bar1, bar2, high, low, ZoneType::Supply)
    }

    pub fn demand(bar1: f64, bar2: f64, high: f64, low: f64) -> Self {
        Self::new(bar1, bar2, high, low, ZoneType::Demand)
    }

    pub fn order_block(bar1: f64, bar2: f64, high: f64, low: f64) -> Self {
        Self::new(bar1, bar2, high, low, ZoneType::OrderBlock)
    }

    pub fn fvg(bar1: f64, bar2: f64, high: f64, low: f64) -> Self {
        Self::new(bar1, bar2, high, low, ZoneType::FairValueGap)
    }

    pub fn with_action(mut self, action: ZoneAction) -> Self {
        self.action = action;
        self
    }

    pub fn with_strength(mut self, strength: f64) -> Self {
        self.strength = strength.clamp(0.0, 1.0);
        self
    }

    pub fn with_tests(mut self, count: u32) -> Self {
        self.test_count = count;
        self
    }
}

impl Primitive for ZoneEvent {
    fn type_id(&self) -> &'static str {
        "zone_event"
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
        vec![(self.bar1, self.price_high), (self.bar2, self.price_low)]
    }
    fn set_points(&mut self, points: &[(f64, f64)]) {
        if let Some(&(b, p)) = points.first() {
            self.bar1 = b;
            self.price_high = p;
        }
        if let Some(&(b, p)) = points.get(1) {
            self.bar2 = b;
            self.price_low = p;
        }
    }
    fn translate(&mut self, bd: f64, pd: f64) {
        self.bar1 += bd;
        self.bar2 += bd;
        self.price_high += pd;
        self.price_low += pd;
    }

    fn render(&self, ctx: &mut dyn RenderContext, _is_selected: bool) {
        let dpr = ctx.dpr();
        let x1 = ctx.bar_to_x(self.bar1);
        let x2 = ctx.bar_to_x(self.bar2);
        let y_high = ctx.price_to_y(self.price_high);
        let y_low = ctx.price_to_y(self.price_low);

        let (rx, ry, rw, rh) = crisp_rect(x1, y_high, x2 - x1, y_low - y_high, dpr);

        // Adjust alpha based on strength and action
        let base_alpha = match self.action {
            ZoneAction::Broken | ZoneAction::Mitigated => 0.2,
            ZoneAction::Tested => 0.5,
            _ => 0.6,
        };
        let alpha = base_alpha * self.strength;

        ctx.set_global_alpha(alpha);
        ctx.set_fill_color(&self.data.color.stroke);
        ctx.fill_rect(rx, ry, rw, rh);

        // Draw border
        ctx.set_global_alpha(alpha + 0.3);
        ctx.set_stroke_color(&self.data.color.stroke);
        ctx.set_stroke_width(self.data.width);

        // Different border style based on zone status
        if self.action == ZoneAction::Broken || self.action == ZoneAction::Mitigated {
            ctx.save();
            ctx.set_line_dash(&[4.0, 4.0]);
            ctx.stroke_rect(rx, ry, rw, rh);
            ctx.restore();
        } else {
            ctx.stroke_rect(rx, ry, rw, rh);
        }

        ctx.set_global_alpha(1.0);

        // Draw test count indicator if tested
        if self.test_count > 0 {
            let indicator_x = rx + rw - 12.0;
            let indicator_y = ry + 12.0;
            ctx.set_fill_color(&self.data.color.stroke);
            ctx.begin_path();
            ctx.arc(indicator_x, indicator_y, 8.0, 0.0, std::f64::consts::TAU);
            ctx.fill();

            ctx.set_fill_color("#FFFFFF");
            ctx.set_font("10px sans-serif");
            ctx.fill_text(
                &self.test_count.to_string(),
                indicator_x - 3.0,
                indicator_y + 3.0,
            );
        }
    }

    fn text_anchor(&self, ctx: &dyn RenderContext) -> Option<TextAnchor> {
        let text = self.data.text.as_ref()?;
        if text.content.is_empty() {
            return None;
        }

        let x = ctx.bar_to_x(self.bar1);
        let y = ctx.price_to_y((self.price_high + self.price_low) / 2.0);
        Some(TextAnchor::new(x + 5.0, y, &self.data.color.stroke))
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
        type_id: "zone_event",
        display_name: "Zone Event",
        kind: PrimitiveKind::Signal,
        factory: |points, color| {
            let (b1, p1) = points.first().copied().unwrap_or((0.0, 100.0));
            let (b2, p2) = points.get(1).copied().unwrap_or((b1 + 10.0, p1 - 10.0));
            let mut event = ZoneEvent::new(b1, b2, p1, p2, ZoneType::Supply);
            event.data.color = PrimitiveColor::new(color);
            Box::new(event)
        },
        supports_text: true,
        has_levels: false,
        has_points_config: false,
    }
}
