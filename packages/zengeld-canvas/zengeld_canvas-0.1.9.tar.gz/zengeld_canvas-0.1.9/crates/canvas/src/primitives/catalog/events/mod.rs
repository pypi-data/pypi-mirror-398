//! Strategy Event Primitives
//!
//! Visual primitives for strategy events like crossovers, breakdowns,
//! divergences, pattern matches, and custom signals.
//!
//! These are non-interactive markers that represent strategy-generated events.
//! Unlike user-drawn primitives, events cannot be dragged or edited.
//!
//! # Event Types
//!
//! - **Crossover** - MA crossover, MACD line cross, etc.
//! - **Breakdown** - Level breakout/breakdown events
//! - **Divergence** - RSI/MACD divergence markers
//! - **PatternMatch** - Detected pattern (triangle, H&S, etc.)
//! - **ZoneEvent** - Supply/demand zone, order block events
//! - **VolumeEvent** - Volume spike, climax, dry-up events
//! - **TrendEvent** - Trend change, reversal, continuation
//! - **MomentumEvent** - Momentum shift, exhaustion
//! - **CustomEvent** - User-defined strategy events

mod breakdown;
mod crossover;
mod custom_event;
mod divergence;
mod momentum_event;
mod pattern_match;
mod trend_event;
mod volume_event;
mod zone_event;

pub use breakdown::{Breakdown, BreakdownType, metadata as breakdown_metadata};
pub use crossover::{Crossover, CrossoverDirection, CrossoverType, metadata as crossover_metadata};
pub use custom_event::{CustomEvent, CustomEventStyle, metadata as custom_event_metadata};
pub use divergence::{Divergence, DivergenceType, metadata as divergence_metadata};
pub use momentum_event::{MomentumEvent, MomentumEventType, metadata as momentum_event_metadata};
pub use pattern_match::{PatternMatch, PatternType, metadata as pattern_match_metadata};
pub use trend_event::{TrendEvent, TrendEventType, metadata as trend_event_metadata};
pub use volume_event::{VolumeEvent, VolumeEventType, metadata as volume_event_metadata};
pub use zone_event::{ZoneAction, ZoneEvent, ZoneType, metadata as zone_event_metadata};
