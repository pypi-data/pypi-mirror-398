//! System Signals - strategy-generated markers
//!
//! SystemSignal uses Emoji primitive for rendering signal markers.
//! Signals are non-interactive (cannot be dragged/edited) and are
//! stored separately from user-created primitives.

use crate::primitives::catalog::icons::{Emoji, EmojiType};
use crate::primitives::core::{Primitive, RenderContext};
use serde::{Deserialize, Serialize};
use std::str::FromStr;

/// Signal type for strategy markers
#[derive(Clone, Copy, Debug, PartialEq, Eq, Serialize, Deserialize, Default)]
pub enum SignalType {
    /// Buy signal (bullish)
    Buy,
    /// Sell signal (bearish)
    Sell,
    /// Take profit level
    TakeProfit,
    /// Stop loss level
    StopLoss,
    /// Entry point
    Entry,
    /// Exit point
    Exit,
    /// Custom marker
    #[default]
    Custom,
}

impl SignalType {
    pub fn as_str(&self) -> &'static str {
        match self {
            Self::Buy => "buy",
            Self::Sell => "sell",
            Self::TakeProfit => "take_profit",
            Self::StopLoss => "stop_loss",
            Self::Entry => "entry",
            Self::Exit => "exit",
            Self::Custom => "custom",
        }
    }

    pub fn parse(s: &str) -> Self {
        match s {
            "buy" => Self::Buy,
            "sell" => Self::Sell,
            "take_profit" => Self::TakeProfit,
            "stop_loss" => Self::StopLoss,
            "entry" => Self::Entry,
            "exit" => Self::Exit,
            _ => Self::Custom,
        }
    }

    pub fn display_name(&self) -> &'static str {
        match self {
            Self::Buy => "Buy",
            Self::Sell => "Sell",
            Self::TakeProfit => "Take Profit",
            Self::StopLoss => "Stop Loss",
            Self::Entry => "Entry",
            Self::Exit => "Exit",
            Self::Custom => "Custom",
        }
    }

    /// Default color for this signal type
    pub fn default_color(&self) -> &'static str {
        match self {
            Self::Buy | Self::Entry => "#4CAF50", // Green
            Self::Sell | Self::Exit => "#F44336", // Red
            Self::TakeProfit => "#2196F3",        // Blue
            Self::StopLoss => "#FF9800",          // Orange
            Self::Custom => "#9C27B0",            // Purple
        }
    }

    /// Get the EmojiType for this signal type
    pub fn emoji_type(&self) -> EmojiType {
        match self {
            Self::Buy | Self::Entry => EmojiType::ArrowUp,
            Self::Sell | Self::Exit => EmojiType::ArrowDown,
            Self::TakeProfit => EmojiType::Check,
            Self::StopLoss => EmojiType::Cross,
            Self::Custom => EmojiType::Circle,
        }
    }
}

impl FromStr for SignalType {
    type Err = ();

    fn from_str(s: &str) -> Result<Self, Self::Err> {
        Ok(Self::parse(s))
    }
}

/// System Signal - a strategy-generated marker
///
/// Uses Emoji primitive internally for rendering.
/// Unlike user primitives, system signals:
/// - Cannot be dragged or resized
/// - Cannot have their shape edited
/// - Are stored in a separate collection
#[derive(Clone, Debug, Serialize, Deserialize)]
pub struct SystemSignal {
    /// Unique signal ID
    pub id: u64,
    /// Strategy tag (e.g., "momentum_v1", "scalper")
    pub strategy_tag: String,
    /// Signal type
    pub signal_type: SignalType,
    /// Optional label (e.g., "TP1", "Entry #3")
    pub label: Option<String>,
    /// Timestamp when signal was generated
    pub timestamp: i64,
    /// Inner Emoji primitive for rendering
    emoji: Emoji,
    /// Visibility flag
    pub visible: bool,
}

impl SystemSignal {
    /// Create a new system signal
    pub fn new(id: u64, strategy_tag: &str, signal_type: SignalType, bar: f64, price: f64) -> Self {
        let color = signal_type.default_color();
        let mut emoji = Emoji::new(bar, price, color);
        emoji.emoji_type = signal_type.emoji_type();
        // Smaller default size for signals
        emoji.radius_bars = 1.5;
        emoji.radius_price = 30.0;

        Self {
            id,
            strategy_tag: strategy_tag.to_string(),
            signal_type,
            label: None,
            timestamp: 0,
            emoji,
            visible: true,
        }
    }

    /// Create with custom label
    pub fn with_label(mut self, label: &str) -> Self {
        self.label = Some(label.to_string());
        self
    }

    /// Create with timestamp
    pub fn with_timestamp(mut self, ts: i64) -> Self {
        self.timestamp = ts;
        self
    }

    /// Set color (overrides default)
    pub fn set_color(&mut self, color: &str) {
        self.emoji.data.color.stroke = color.to_string();
    }

    /// Get color
    pub fn color(&self) -> &str {
        &self.emoji.data.color.stroke
    }

    /// Set size (adjusts both radius_bars and radius_price proportionally)
    pub fn set_size(&mut self, size: f64) {
        self.emoji.radius_bars = size * 0.5;
        self.emoji.radius_price = size * 10.0;
    }

    /// Get size
    pub fn size(&self) -> f64 {
        self.emoji.radius_bars * 2.0
    }

    /// Get bar position
    pub fn bar(&self) -> f64 {
        self.emoji.center_bar
    }

    /// Get price position
    pub fn price(&self) -> f64 {
        self.emoji.center_price
    }

    /// Render the signal
    pub fn render(&self, ctx: &mut dyn RenderContext) {
        if !self.visible {
            return;
        }
        // Never render as selected - system signals can't be selected
        self.emoji.render(ctx, false);
    }

    /// Serialize to JSON
    pub fn to_json(&self) -> String {
        serde_json::to_string(self).unwrap_or_default()
    }

    /// Deserialize from JSON
    pub fn from_json(json: &str) -> Option<Self> {
        serde_json::from_str(json).ok()
    }
}

/// Configuration for a strategy's signals
#[derive(Clone, Debug, Default, Serialize, Deserialize)]
pub struct StrategySignalConfig {
    /// Strategy identifier
    pub strategy_tag: String,
    /// Display name
    pub display_name: String,
    /// Is this strategy's signals visible
    pub visible: bool,
    /// Color overrides by signal type
    pub colors: std::collections::HashMap<String, String>,
    /// Size override
    pub size: Option<f64>,
}

impl StrategySignalConfig {
    pub fn new(tag: &str, name: &str) -> Self {
        Self {
            strategy_tag: tag.to_string(),
            display_name: name.to_string(),
            visible: true,
            colors: std::collections::HashMap::new(),
            size: None,
        }
    }

    /// Get color for signal type (custom or default)
    pub fn color_for(&self, signal_type: SignalType) -> &str {
        self.colors
            .get(signal_type.as_str())
            .map(|s| s.as_str())
            .unwrap_or_else(|| signal_type.default_color())
    }

    /// Set color for signal type
    pub fn set_color_for(&mut self, signal_type: SignalType, color: &str) {
        self.colors
            .insert(signal_type.as_str().to_string(), color.to_string());
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_signal_creation() {
        let signal = SystemSignal::new(1, "test_strategy", SignalType::Buy, 100.0, 50000.0);
        assert_eq!(signal.signal_type, SignalType::Buy);
        assert_eq!(signal.strategy_tag, "test_strategy");
        assert_eq!(signal.bar(), 100.0);
        assert_eq!(signal.price(), 50000.0);
    }

    #[test]
    fn test_signal_type_colors() {
        assert_eq!(SignalType::Buy.default_color(), "#4CAF50");
        assert_eq!(SignalType::Sell.default_color(), "#F44336");
    }

    #[test]
    fn test_signal_type_emoji() {
        assert_eq!(SignalType::Buy.emoji_type(), EmojiType::ArrowUp);
        assert_eq!(SignalType::Sell.emoji_type(), EmojiType::ArrowDown);
        assert_eq!(SignalType::TakeProfit.emoji_type(), EmojiType::Check);
        assert_eq!(SignalType::StopLoss.emoji_type(), EmojiType::Cross);
    }

    #[test]
    fn test_signal_serialization() {
        let signal =
            SystemSignal::new(1, "test", SignalType::TakeProfit, 100.0, 50000.0).with_label("TP1");
        let json = signal.to_json();
        let restored = SystemSignal::from_json(&json).unwrap();
        assert_eq!(restored.label, Some("TP1".to_string()));
    }
}
