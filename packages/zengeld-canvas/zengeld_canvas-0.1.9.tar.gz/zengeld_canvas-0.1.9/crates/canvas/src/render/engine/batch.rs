//! Render batch - grouped commands with optimizations
//!
//! RenderBatch collects commands for efficient batch rendering,
//! tracks bounding boxes for culling, and provides layer management.

use super::commands::RenderCommand;
use super::types::Rect;
use serde::{Deserialize, Serialize};

/// A batch of render commands with metadata for optimization
#[derive(Clone, Debug, Default, Serialize, Deserialize)]
pub struct RenderBatch {
    /// Commands in submission order
    commands: Vec<RenderCommand>,

    /// Incrementally tracked bounding box
    #[serde(skip)]
    bounds: IncrementalBounds,

    /// Layer depth for z-ordering
    pub layer: u32,

    /// Optional name for debugging
    #[serde(skip_serializing_if = "Option::is_none")]
    pub name: Option<String>,
}

/// Incrementally tracked bounding box
/// Avoids O(n) recalculation on every bounds() call
#[derive(Clone, Copy, Debug)]
struct IncrementalBounds {
    min_x: f64,
    min_y: f64,
    max_x: f64,
    max_y: f64,
    has_content: bool,
}

impl Default for IncrementalBounds {
    fn default() -> Self {
        Self::new()
    }
}

impl IncrementalBounds {
    #[inline]
    fn new() -> Self {
        Self {
            min_x: f64::INFINITY,
            min_y: f64::INFINITY,
            max_x: f64::NEG_INFINITY,
            max_y: f64::NEG_INFINITY,
            has_content: false,
        }
    }

    /// Expand bounds to include a rectangle
    #[inline]
    fn expand(&mut self, rect: &Rect) {
        self.min_x = self.min_x.min(rect.x);
        self.min_y = self.min_y.min(rect.y);
        self.max_x = self.max_x.max(rect.right());
        self.max_y = self.max_y.max(rect.bottom());
        self.has_content = true;
    }

    /// Get the computed bounds
    #[inline]
    fn get(&self) -> Option<Rect> {
        if self.has_content {
            Some(Rect::new(
                self.min_x,
                self.min_y,
                self.max_x - self.min_x,
                self.max_y - self.min_y,
            ))
        } else {
            None
        }
    }

    /// Reset for reuse
    #[inline]
    fn reset(&mut self) {
        *self = Self::new();
    }
}

impl RenderBatch {
    /// Create a new empty batch
    #[inline]
    pub fn new() -> Self {
        Self::default()
    }

    /// Create a batch with pre-allocated capacity
    #[inline]
    pub fn with_capacity(capacity: usize) -> Self {
        Self {
            commands: Vec::with_capacity(capacity),
            bounds: IncrementalBounds::new(),
            layer: 0,
            name: None,
        }
    }

    /// Create a named batch for debugging
    #[inline]
    pub fn named(name: impl Into<String>) -> Self {
        Self {
            commands: Vec::new(),
            bounds: IncrementalBounds::new(),
            layer: 0,
            name: Some(name.into()),
        }
    }

    /// Add a single command (O(1) bounds update)
    #[inline]
    pub fn push(&mut self, cmd: RenderCommand) {
        // Incrementally update bounds
        if let Some(rect) = cmd.bounds() {
            self.bounds.expand(&rect);
        }
        self.commands.push(cmd);
    }

    /// Add multiple commands
    #[inline]
    pub fn extend(&mut self, cmds: impl IntoIterator<Item = RenderCommand>) {
        for cmd in cmds {
            self.push(cmd);
        }
    }

    /// Get command count
    #[inline]
    pub fn len(&self) -> usize {
        self.commands.len()
    }

    /// Check if empty
    #[inline]
    pub fn is_empty(&self) -> bool {
        self.commands.is_empty()
    }

    /// Clear all commands
    #[inline]
    pub fn clear(&mut self) {
        self.commands.clear();
        self.bounds.reset();
    }

    /// Get commands slice
    #[inline]
    pub fn commands(&self) -> &[RenderCommand] {
        &self.commands
    }

    /// Take ownership of commands
    #[inline]
    pub fn into_commands(self) -> Vec<RenderCommand> {
        self.commands
    }

    /// Iterate over commands
    #[inline]
    pub fn iter(&self) -> impl Iterator<Item = &RenderCommand> {
        self.commands.iter()
    }

    /// Get bounding box of all commands (O(1) - incrementally tracked)
    #[inline]
    pub fn bounds(&self) -> Option<Rect> {
        self.bounds.get()
    }

    /// Check if batch intersects viewport (for culling)
    #[inline]
    pub fn intersects_viewport(&self, viewport: &Rect) -> bool {
        match self.bounds() {
            Some(bounds) => bounds.intersects(viewport),
            None => true, // State-only commands always "intersect"
        }
    }

    /// Filter commands that intersect a viewport
    pub fn cull(&self, viewport: &Rect) -> RenderBatch {
        let mut result = RenderBatch::with_capacity(self.commands.len());
        result.layer = self.layer;
        result.name = self.name.clone();

        for cmd in &self.commands {
            // Always include state commands
            if cmd.is_state_command() {
                result.push(cmd.clone());
                continue;
            }

            // Include if intersects viewport or has no bounds
            if let Some(bounds) = cmd.bounds() {
                if bounds.intersects(viewport) {
                    result.push(cmd.clone());
                }
            } else {
                result.push(cmd.clone());
            }
        }

        result
    }
}

// =============================================================================
// RenderQueue - ordered collection of batches
// =============================================================================

/// Queue of render batches in layer order
#[derive(Clone, Debug, Default)]
pub struct RenderQueue {
    batches: Vec<RenderBatch>,
    sorted: bool,
}

impl RenderQueue {
    /// Create a new empty queue
    #[inline]
    pub fn new() -> Self {
        Self::default()
    }

    /// Add a batch to the queue
    #[inline]
    pub fn push(&mut self, batch: RenderBatch) {
        self.sorted = false;
        self.batches.push(batch);
    }

    /// Add a single command as a new batch
    #[inline]
    pub fn push_command(&mut self, cmd: RenderCommand, layer: u32) {
        let mut batch = RenderBatch::new();
        batch.layer = layer;
        batch.push(cmd);
        self.push(batch);
    }

    /// Sort batches by layer (call before rendering)
    pub fn sort_by_layer(&mut self) {
        if !self.sorted {
            self.batches.sort_by_key(|b| b.layer);
            self.sorted = true;
        }
    }

    /// Get batches in layer order
    pub fn batches(&mut self) -> &[RenderBatch] {
        self.sort_by_layer();
        &self.batches
    }

    /// Clear all batches
    #[inline]
    pub fn clear(&mut self) {
        self.batches.clear();
        self.sorted = true;
    }

    /// Get total command count across all batches
    pub fn total_commands(&self) -> usize {
        self.batches.iter().map(|b| b.len()).sum()
    }

    /// Flatten all batches into a single command list
    pub fn flatten(&mut self) -> Vec<RenderCommand> {
        self.sort_by_layer();
        self.batches
            .iter()
            .flat_map(|b| b.commands().iter().cloned())
            .collect()
    }
}

// =============================================================================
// Layer constants for consistent z-ordering
// =============================================================================

/// Standard rendering layers
pub mod layers {
    /// Background (grid, watermarks)
    pub const BACKGROUND: u32 = 0;

    /// Main chart content (candles, series)
    pub const CHART: u32 = 100;

    /// Annotations and drawings
    pub const ANNOTATIONS: u32 = 200;

    /// Drawing primitives
    pub const PRIMITIVES: u32 = 300;

    /// Overlays (indicators, tools)
    pub const OVERLAYS: u32 = 400;

    /// UI elements (scales, crosshair)
    pub const UI: u32 = 500;

    /// Top-most (tooltips, popups)
    pub const TOP: u32 = 1000;
}

#[cfg(test)]
mod tests {
    use super::super::commands::RenderCommand;
    use super::super::types::Color;
    use super::*;

    #[test]
    fn test_batch_push() {
        let mut batch = RenderBatch::new();
        batch.push(RenderCommand::FillRect {
            rect: Rect::new(0.0, 0.0, 100.0, 100.0),
            color: Color::WHITE,
        });
        assert_eq!(batch.len(), 1);
    }

    #[test]
    fn test_batch_bounds() {
        let mut batch = RenderBatch::new();
        batch.push(RenderCommand::FillRect {
            rect: Rect::new(10.0, 10.0, 50.0, 50.0),
            color: Color::WHITE,
        });
        batch.push(RenderCommand::FillRect {
            rect: Rect::new(100.0, 100.0, 50.0, 50.0),
            color: Color::WHITE,
        });

        let bounds = batch.bounds().unwrap();
        assert_eq!(bounds.x, 10.0);
        assert_eq!(bounds.y, 10.0);
        assert_eq!(bounds.width, 140.0);
        assert_eq!(bounds.height, 140.0);
    }

    #[test]
    fn test_queue_layer_sorting() {
        let mut queue = RenderQueue::new();

        let mut b1 = RenderBatch::named("ui");
        b1.layer = layers::UI;

        let mut b2 = RenderBatch::named("chart");
        b2.layer = layers::CHART;

        let mut b3 = RenderBatch::named("bg");
        b3.layer = layers::BACKGROUND;

        queue.push(b1);
        queue.push(b2);
        queue.push(b3);

        let batches = queue.batches();
        assert_eq!(batches[0].name.as_deref(), Some("bg"));
        assert_eq!(batches[1].name.as_deref(), Some("chart"));
        assert_eq!(batches[2].name.as_deref(), Some("ui"));
    }
}
