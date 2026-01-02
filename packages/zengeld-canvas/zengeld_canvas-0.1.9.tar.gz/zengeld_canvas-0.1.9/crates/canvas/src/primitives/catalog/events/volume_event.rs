//! Volume Event - Volume spikes, climax, dry-up events

use super::super::{
    Primitive, PrimitiveColor, PrimitiveData, PrimitiveKind, PrimitiveMetadata, RenderContext,
    TextAnchor, crisp,
};
use serde::{Deserialize, Serialize};

/// Type of volume event
#[derive(Clone, Copy, Debug, PartialEq, Eq, Serialize, Deserialize)]
#[serde(rename_all = "snake_case")]
#[derive(Default)]
pub enum VolumeEventType {
    /// Volume spike (unusually high volume)
    #[default]
    Spike,
    /// Climax volume (extreme volume at top/bottom)
    Climax,
    /// Dry-up (unusually low volume)
    DryUp,
    /// Volume breakout (volume confirming price breakout)
    Breakout,
    /// Volume divergence (price up, volume down or vice versa)
    Divergence,
    /// Accumulation (high volume, little price movement)
    Accumulation,
    /// Distribution (high volume at top)
    Distribution,
    /// Volume confirmation (volume supports trend)
    Confirmation,
    /// Churning (high volume, no progress)
    Churning,
    /// No demand (up bar with low volume)
    NoDemand,
    /// No supply (down bar with low volume)
    NoSupply,
    /// Stopping volume (high volume stopping a move)
    Stopping,
    /// Custom
    Custom,
}

impl VolumeEventType {
    pub fn as_str(&self) -> &'static str {
        match self {
            Self::Spike => "spike",
            Self::Climax => "climax",
            Self::DryUp => "dry_up",
            Self::Breakout => "breakout",
            Self::Divergence => "divergence",
            Self::Accumulation => "accumulation",
            Self::Distribution => "distribution",
            Self::Confirmation => "confirmation",
            Self::Churning => "churning",
            Self::NoDemand => "no_demand",
            Self::NoSupply => "no_supply",
            Self::Stopping => "stopping",
            Self::Custom => "custom",
        }
    }

    pub fn display_name(&self) -> &'static str {
        match self {
            Self::Spike => "Volume Spike",
            Self::Climax => "Climax Volume",
            Self::DryUp => "Volume Dry-Up",
            Self::Breakout => "Volume Breakout",
            Self::Divergence => "Volume Divergence",
            Self::Accumulation => "Accumulation",
            Self::Distribution => "Distribution",
            Self::Confirmation => "Volume Confirmation",
            Self::Churning => "Churning",
            Self::NoDemand => "No Demand",
            Self::NoSupply => "No Supply",
            Self::Stopping => "Stopping Volume",
            Self::Custom => "Custom",
        }
    }

    pub fn default_color(&self) -> &'static str {
        match self {
            Self::Spike | Self::Climax | Self::Breakout => "#FF9800", // Orange
            Self::DryUp | Self::NoDemand | Self::NoSupply => "#9E9E9E", // Gray
            Self::Divergence => "#E91E63",                            // Pink
            Self::Accumulation | Self::Confirmation => "#26a69a",     // Green
            Self::Distribution => "#ef5350",                          // Red
            Self::Churning | Self::Stopping => "#9C27B0",             // Purple
            Self::Custom => "#787B86",
        }
    }

    pub fn is_bullish(&self) -> bool {
        matches!(
            self,
            Self::Accumulation | Self::NoSupply | Self::Confirmation
        )
    }

    pub fn is_bearish(&self) -> bool {
        matches!(self, Self::Distribution | Self::NoDemand)
    }
}

/// Volume event primitive
#[derive(Clone, Debug, Serialize, Deserialize)]
pub struct VolumeEvent {
    pub data: PrimitiveData,
    pub bar: f64,
    pub price: f64,
    pub volume: f64,     // Actual volume value
    pub avg_volume: f64, // Average volume for comparison
    pub event_type: VolumeEventType,
    #[serde(default = "default_size")]
    pub size: f64,
}

fn default_size() -> f64 {
    14.0
}

impl VolumeEvent {
    pub fn new(bar: f64, price: f64, volume: f64, event_type: VolumeEventType) -> Self {
        let color = event_type.default_color();
        Self {
            data: PrimitiveData {
                type_id: "volume_event".to_string(),
                display_name: event_type.display_name().to_string(),
                color: PrimitiveColor::new(color),
                width: 2.0,
                ..Default::default()
            },
            bar,
            price,
            volume,
            avg_volume: 0.0,
            event_type,
            size: default_size(),
        }
    }

    pub fn spike(bar: f64, price: f64, volume: f64) -> Self {
        Self::new(bar, price, volume, VolumeEventType::Spike)
    }

    pub fn climax(bar: f64, price: f64, volume: f64) -> Self {
        Self::new(bar, price, volume, VolumeEventType::Climax)
    }

    pub fn dry_up(bar: f64, price: f64, volume: f64) -> Self {
        Self::new(bar, price, volume, VolumeEventType::DryUp)
    }

    pub fn with_avg(mut self, avg: f64) -> Self {
        self.avg_volume = avg;
        self
    }

    pub fn volume_ratio(&self) -> f64 {
        if self.avg_volume > 0.0 {
            self.volume / self.avg_volume
        } else {
            1.0
        }
    }
}

impl Primitive for VolumeEvent {
    fn type_id(&self) -> &'static str {
        "volume_event"
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

        match self.event_type {
            VolumeEventType::Spike | VolumeEventType::Climax | VolumeEventType::Breakout => {
                // Draw vertical bar chart icon
                let bar_width = s / 4.0;
                let heights = [0.5, 1.0, 0.7];
                for (i, h) in heights.iter().enumerate() {
                    let bx = x - s / 2.0 + (i as f64 * bar_width * 1.2);
                    let by = y + s / 2.0 - s * h;
                    let bh = s * h;
                    ctx.fill_rect(crisp(bx, dpr), crisp(by, dpr), bar_width, bh);
                }
            }
            VolumeEventType::DryUp | VolumeEventType::NoDemand | VolumeEventType::NoSupply => {
                // Draw small dots (low volume indicator)
                for i in 0..3 {
                    let dx = x - s / 3.0 + (i as f64 * s / 3.0);
                    ctx.begin_path();
                    ctx.arc(
                        crisp(dx, dpr),
                        crisp(y, dpr),
                        2.0,
                        0.0,
                        std::f64::consts::TAU,
                    );
                    ctx.fill();
                }
            }
            VolumeEventType::Divergence => {
                // Draw divergence lines
                ctx.begin_path();
                ctx.move_to(crisp(x - s / 2.0, dpr), crisp(y - s / 4.0, dpr));
                ctx.line_to(crisp(x + s / 2.0, dpr), crisp(y + s / 4.0, dpr));
                ctx.stroke();
                ctx.begin_path();
                ctx.move_to(crisp(x - s / 2.0, dpr), crisp(y + s / 4.0, dpr));
                ctx.line_to(crisp(x + s / 2.0, dpr), crisp(y - s / 4.0, dpr));
                ctx.stroke();
            }
            VolumeEventType::Accumulation | VolumeEventType::Distribution => {
                // Draw horizontal bars stacking
                let bar_height = s / 5.0;
                for i in 0..4 {
                    let by = y - s / 2.0 + (i as f64 * bar_height * 1.2);
                    let bw = s * (0.4 + (i as f64 * 0.2));
                    ctx.fill_rect(crisp(x - bw / 2.0, dpr), crisp(by, dpr), bw, bar_height);
                }
            }
            _ => {
                // Default: circle with V
                ctx.begin_path();
                ctx.arc(
                    crisp(x, dpr),
                    crisp(y, dpr),
                    s / 2.0,
                    0.0,
                    std::f64::consts::TAU,
                );
                ctx.stroke();

                // Draw V inside
                ctx.begin_path();
                ctx.move_to(crisp(x - s / 4.0, dpr), crisp(y - s / 4.0, dpr));
                ctx.line_to(crisp(x, dpr), crisp(y + s / 4.0, dpr));
                ctx.line_to(crisp(x + s / 4.0, dpr), crisp(y - s / 4.0, dpr));
                ctx.stroke();
            }
        }
    }

    fn text_anchor(&self, ctx: &dyn RenderContext) -> Option<TextAnchor> {
        let text = self.data.text.as_ref()?;
        if text.content.is_empty() {
            return None;
        }

        let x = ctx.bar_to_x(self.bar);
        let y = ctx.price_to_y(self.price);
        let offset = self.size + text.font_size / 2.0;
        Some(TextAnchor::new(x, y - offset, &self.data.color.stroke))
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
        type_id: "volume_event",
        display_name: "Volume Event",
        kind: PrimitiveKind::Signal,
        factory: |points, color| {
            let (b, p) = points.first().copied().unwrap_or((0.0, 0.0));
            let mut event = VolumeEvent::new(b, p, 1000.0, VolumeEventType::Spike);
            event.data.color = PrimitiveColor::new(color);
            Box::new(event)
        },
        supports_text: true,
        has_levels: false,
        has_points_config: false,
    }
}
