//! Fibonacci primitives
//!
//! Fibonacci-based technical analysis tools including retracements,
//! extensions, channels, time zones, fans, circles, arcs, spirals, and wedges.

pub mod arcs;
pub mod channel;
pub mod circles;
pub mod fan;
pub mod retracement;
pub mod speed_resistance;
pub mod spiral;
pub mod time_zones;
pub mod trend_extension;
pub mod trend_time;
pub mod wedge;

pub use arcs::FibArcs;
pub use channel::FibChannel;
pub use circles::FibCircles;
pub use fan::FibFan;
pub use retracement::FibRetracement;
pub use speed_resistance::FibSpeedResistance;
pub use spiral::FibSpiral;
pub use time_zones::FibTimeZones;
pub use trend_extension::FibTrendExtension;
pub use trend_time::FibTrendTime;
pub use wedge::FibWedge;
