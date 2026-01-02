//! Pattern Match Event - Detected chart pattern events

use super::super::{
    Primitive, PrimitiveColor, PrimitiveData, PrimitiveKind, PrimitiveMetadata, RenderContext,
    TextAnchor, crisp,
};
use serde::{Deserialize, Serialize};

/// Type of pattern detected
#[derive(Clone, Copy, Debug, PartialEq, Eq, Serialize, Deserialize)]
#[serde(rename_all = "snake_case")]
#[derive(Default)]
pub enum PatternType {
    // Reversal patterns
    HeadAndShoulders,
    InverseHeadAndShoulders,
    DoubleTop,
    DoubleBottom,
    TripleTop,
    TripleBottom,

    // Continuation patterns
    AscendingTriangle,
    DescendingTriangle,
    SymmetricalTriangle,
    BullFlag,
    BearFlag,
    BullPennant,
    BearPennant,
    Rectangle,
    Wedge,

    // Harmonic patterns
    Gartley,
    Butterfly,
    Bat,
    Crab,
    Shark,
    Cypher,

    // Candlestick patterns (single)
    Doji,
    Hammer,
    InvertedHammer,
    ShootingStar,
    HangingMan,
    Marubozu,
    SpinningTop,

    // Candlestick patterns (multi)
    Engulfing,
    Harami,
    MorningStar,
    EveningStar,
    ThreeWhiteSoldiers,
    ThreeBlackCrows,
    Piercing,
    DarkCloudCover,
    TweezerTop,
    TweezerBottom,

    // Elliott wave
    ImpulseWave,
    CorrectiveWave,

    // Custom
    #[default]
    Custom,
}

impl PatternType {
    pub fn as_str(&self) -> &'static str {
        match self {
            Self::HeadAndShoulders => "head_shoulders",
            Self::InverseHeadAndShoulders => "inv_head_shoulders",
            Self::DoubleTop => "double_top",
            Self::DoubleBottom => "double_bottom",
            Self::TripleTop => "triple_top",
            Self::TripleBottom => "triple_bottom",
            Self::AscendingTriangle => "ascending_triangle",
            Self::DescendingTriangle => "descending_triangle",
            Self::SymmetricalTriangle => "symmetrical_triangle",
            Self::BullFlag => "bull_flag",
            Self::BearFlag => "bear_flag",
            Self::BullPennant => "bull_pennant",
            Self::BearPennant => "bear_pennant",
            Self::Rectangle => "rectangle",
            Self::Wedge => "wedge",
            Self::Gartley => "gartley",
            Self::Butterfly => "butterfly",
            Self::Bat => "bat",
            Self::Crab => "crab",
            Self::Shark => "shark",
            Self::Cypher => "cypher",
            Self::Doji => "doji",
            Self::Hammer => "hammer",
            Self::InvertedHammer => "inverted_hammer",
            Self::ShootingStar => "shooting_star",
            Self::HangingMan => "hanging_man",
            Self::Marubozu => "marubozu",
            Self::SpinningTop => "spinning_top",
            Self::Engulfing => "engulfing",
            Self::Harami => "harami",
            Self::MorningStar => "morning_star",
            Self::EveningStar => "evening_star",
            Self::ThreeWhiteSoldiers => "three_white_soldiers",
            Self::ThreeBlackCrows => "three_black_crows",
            Self::Piercing => "piercing",
            Self::DarkCloudCover => "dark_cloud_cover",
            Self::TweezerTop => "tweezer_top",
            Self::TweezerBottom => "tweezer_bottom",
            Self::ImpulseWave => "impulse_wave",
            Self::CorrectiveWave => "corrective_wave",
            Self::Custom => "custom",
        }
    }

    pub fn display_name(&self) -> &'static str {
        match self {
            Self::HeadAndShoulders => "Head & Shoulders",
            Self::InverseHeadAndShoulders => "Inverse H&S",
            Self::DoubleTop => "Double Top",
            Self::DoubleBottom => "Double Bottom",
            Self::TripleTop => "Triple Top",
            Self::TripleBottom => "Triple Bottom",
            Self::AscendingTriangle => "Ascending Triangle",
            Self::DescendingTriangle => "Descending Triangle",
            Self::SymmetricalTriangle => "Symmetrical Triangle",
            Self::BullFlag => "Bull Flag",
            Self::BearFlag => "Bear Flag",
            Self::BullPennant => "Bull Pennant",
            Self::BearPennant => "Bear Pennant",
            Self::Rectangle => "Rectangle",
            Self::Wedge => "Wedge",
            Self::Gartley => "Gartley",
            Self::Butterfly => "Butterfly",
            Self::Bat => "Bat",
            Self::Crab => "Crab",
            Self::Shark => "Shark",
            Self::Cypher => "Cypher",
            Self::Doji => "Doji",
            Self::Hammer => "Hammer",
            Self::InvertedHammer => "Inverted Hammer",
            Self::ShootingStar => "Shooting Star",
            Self::HangingMan => "Hanging Man",
            Self::Marubozu => "Marubozu",
            Self::SpinningTop => "Spinning Top",
            Self::Engulfing => "Engulfing",
            Self::Harami => "Harami",
            Self::MorningStar => "Morning Star",
            Self::EveningStar => "Evening Star",
            Self::ThreeWhiteSoldiers => "Three White Soldiers",
            Self::ThreeBlackCrows => "Three Black Crows",
            Self::Piercing => "Piercing",
            Self::DarkCloudCover => "Dark Cloud Cover",
            Self::TweezerTop => "Tweezer Top",
            Self::TweezerBottom => "Tweezer Bottom",
            Self::ImpulseWave => "Impulse Wave",
            Self::CorrectiveWave => "Corrective Wave",
            Self::Custom => "Custom Pattern",
        }
    }

    pub fn default_color(&self) -> &'static str {
        match self {
            // Bullish patterns - green
            Self::InverseHeadAndShoulders
            | Self::DoubleBottom
            | Self::TripleBottom
            | Self::AscendingTriangle
            | Self::BullFlag
            | Self::BullPennant
            | Self::Hammer
            | Self::InvertedHammer
            | Self::MorningStar
            | Self::ThreeWhiteSoldiers
            | Self::Piercing
            | Self::TweezerBottom => "#26a69a",

            // Bearish patterns - red
            Self::HeadAndShoulders
            | Self::DoubleTop
            | Self::TripleTop
            | Self::DescendingTriangle
            | Self::BearFlag
            | Self::BearPennant
            | Self::ShootingStar
            | Self::HangingMan
            | Self::EveningStar
            | Self::ThreeBlackCrows
            | Self::DarkCloudCover
            | Self::TweezerTop => "#ef5350",

            // Neutral patterns - blue/purple
            Self::SymmetricalTriangle
            | Self::Rectangle
            | Self::Wedge
            | Self::Doji
            | Self::SpinningTop
            | Self::Engulfing
            | Self::Harami => "#2196F3",

            // Harmonic patterns - purple
            Self::Gartley
            | Self::Butterfly
            | Self::Bat
            | Self::Crab
            | Self::Shark
            | Self::Cypher => "#9C27B0",

            // Elliott wave - orange
            Self::ImpulseWave | Self::CorrectiveWave => "#FF9800",

            Self::Marubozu | Self::Custom => "#787B86",
        }
    }

    pub fn is_bullish(&self) -> bool {
        matches!(
            self,
            Self::InverseHeadAndShoulders
                | Self::DoubleBottom
                | Self::TripleBottom
                | Self::AscendingTriangle
                | Self::BullFlag
                | Self::BullPennant
                | Self::Hammer
                | Self::InvertedHammer
                | Self::MorningStar
                | Self::ThreeWhiteSoldiers
                | Self::Piercing
                | Self::TweezerBottom
        )
    }

    pub fn is_bearish(&self) -> bool {
        matches!(
            self,
            Self::HeadAndShoulders
                | Self::DoubleTop
                | Self::TripleTop
                | Self::DescendingTriangle
                | Self::BearFlag
                | Self::BearPennant
                | Self::ShootingStar
                | Self::HangingMan
                | Self::EveningStar
                | Self::ThreeBlackCrows
                | Self::DarkCloudCover
                | Self::TweezerTop
        )
    }

    pub fn is_harmonic(&self) -> bool {
        matches!(
            self,
            Self::Gartley | Self::Butterfly | Self::Bat | Self::Crab | Self::Shark | Self::Cypher
        )
    }

    pub fn is_candlestick(&self) -> bool {
        matches!(
            self,
            Self::Doji
                | Self::Hammer
                | Self::InvertedHammer
                | Self::ShootingStar
                | Self::HangingMan
                | Self::Marubozu
                | Self::SpinningTop
                | Self::Engulfing
                | Self::Harami
                | Self::MorningStar
                | Self::EveningStar
                | Self::ThreeWhiteSoldiers
                | Self::ThreeBlackCrows
                | Self::Piercing
                | Self::DarkCloudCover
                | Self::TweezerTop
                | Self::TweezerBottom
        )
    }
}

/// Pattern match event primitive
#[derive(Clone, Debug, Serialize, Deserialize)]
pub struct PatternMatch {
    pub data: PrimitiveData,
    pub bar: f64,       // Detection bar
    pub price: f64,     // Detection price
    pub start_bar: f64, // Pattern start bar
    pub end_bar: f64,   // Pattern end bar
    pub pattern_type: PatternType,
    #[serde(default = "default_confidence")]
    pub confidence: f64, // 0.0 - 1.0
    #[serde(default = "default_size")]
    pub size: f64,
}

fn default_confidence() -> f64 {
    1.0
}
fn default_size() -> f64 {
    16.0
}

impl PatternMatch {
    pub fn new(bar: f64, price: f64, pattern_type: PatternType) -> Self {
        let color = pattern_type.default_color();
        Self {
            data: PrimitiveData {
                type_id: "pattern_match".to_string(),
                display_name: pattern_type.display_name().to_string(),
                color: PrimitiveColor::new(color),
                width: 2.0,
                ..Default::default()
            },
            bar,
            price,
            start_bar: bar - 20.0, // Default pattern span
            end_bar: bar,
            pattern_type,
            confidence: 1.0,
            size: default_size(),
        }
    }

    pub fn with_span(mut self, start: f64, end: f64) -> Self {
        self.start_bar = start;
        self.end_bar = end;
        self
    }

    pub fn with_confidence(mut self, conf: f64) -> Self {
        self.confidence = conf.clamp(0.0, 1.0);
        self
    }
}

impl Primitive for PatternMatch {
    fn type_id(&self) -> &'static str {
        "pattern_match"
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
        self.start_bar += bd;
        self.end_bar += bd;
    }

    fn render(&self, ctx: &mut dyn RenderContext, _is_selected: bool) {
        let dpr = ctx.dpr();
        let x = ctx.bar_to_x(self.bar);
        let y = ctx.price_to_y(self.price);
        let s = self.size;

        // Adjust alpha based on confidence
        let alpha = 0.5 + (self.confidence * 0.5);

        ctx.set_fill_color(&self.data.color.stroke);
        ctx.set_stroke_color(&self.data.color.stroke);
        ctx.set_stroke_width(self.data.width);
        ctx.set_global_alpha(alpha);

        // Draw a badge/label shape
        let badge_width = s * 1.5;
        let badge_height = s;

        // Draw as regular rect (rounded rect not available in RenderContext)
        ctx.fill_rect(
            crisp(x - badge_width / 2.0, dpr),
            crisp(y - badge_height / 2.0, dpr),
            badge_width,
            badge_height,
        );

        // Draw pattern type indicator
        ctx.set_fill_color("#FFFFFF");
        ctx.set_global_alpha(1.0);

        // Draw simple icon based on pattern type
        if self.pattern_type.is_bullish() {
            // Upward arrow in badge
            ctx.begin_path();
            ctx.move_to(crisp(x, dpr), crisp(y - 4.0, dpr));
            ctx.line_to(crisp(x - 4.0, dpr), crisp(y + 2.0, dpr));
            ctx.line_to(crisp(x + 4.0, dpr), crisp(y + 2.0, dpr));
            ctx.close_path();
            ctx.fill();
        } else if self.pattern_type.is_bearish() {
            // Downward arrow in badge
            ctx.begin_path();
            ctx.move_to(crisp(x, dpr), crisp(y + 4.0, dpr));
            ctx.line_to(crisp(x - 4.0, dpr), crisp(y - 2.0, dpr));
            ctx.line_to(crisp(x + 4.0, dpr), crisp(y - 2.0, dpr));
            ctx.close_path();
            ctx.fill();
        } else {
            // Neutral - circle
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
    }

    fn text_anchor(&self, ctx: &dyn RenderContext) -> Option<TextAnchor> {
        let text = self.data.text.as_ref()?;
        if text.content.is_empty() {
            return None;
        }

        let x = ctx.bar_to_x(self.bar);
        let y = ctx.price_to_y(self.price);
        let offset = self.size + text.font_size / 2.0;
        let y_offset = if self.pattern_type.is_bullish() {
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
        type_id: "pattern_match",
        display_name: "Pattern Match",
        kind: PrimitiveKind::Signal,
        factory: |points, color| {
            let (b, p) = points.first().copied().unwrap_or((0.0, 0.0));
            let mut event = PatternMatch::new(b, p, PatternType::Custom);
            event.data.color = PrimitiveColor::new(color);
            Box::new(event)
        },
        supports_text: true,
        has_levels: false,
        has_points_config: false,
    }
}
