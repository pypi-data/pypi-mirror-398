//! Multichart Layout System
//!
//! Provides preset layouts for arranging multiple charts in a grid.
//! Supports various configurations like 1x1, 2x2, 1+3, 3x1, etc.

use serde::{Deserialize, Serialize};

/// Unique identifier for a chart cell in a layout
pub type CellId = usize;

/// Individual cell in a multichart layout
#[derive(Clone, Debug, Serialize, Deserialize)]
pub struct LayoutCell {
    /// Cell identifier (0-indexed)
    pub id: CellId,
    /// Row position (0-indexed from top)
    pub row: usize,
    /// Column position (0-indexed from left)
    pub col: usize,
    /// Row span (1 = single row)
    pub row_span: usize,
    /// Column span (1 = single column)
    pub col_span: usize,
    /// Whether this cell shows price scale
    pub show_price_scale: bool,
    /// Whether this cell shows time scale
    pub show_time_scale: bool,
}

impl LayoutCell {
    /// Create a new cell at position
    pub fn new(id: CellId, row: usize, col: usize) -> Self {
        Self {
            id,
            row,
            col,
            row_span: 1,
            col_span: 1,
            show_price_scale: true,
            show_time_scale: true,
        }
    }

    /// Create a cell with span
    pub fn with_span(id: CellId, row: usize, col: usize, row_span: usize, col_span: usize) -> Self {
        Self {
            id,
            row,
            col,
            row_span,
            col_span,
            show_price_scale: true,
            show_time_scale: true,
        }
    }

    /// Calculate cell bounds within total dimensions
    pub fn bounds(
        &self,
        total_width: f64,
        total_height: f64,
        rows: usize,
        cols: usize,
        gap: f64,
    ) -> CellBounds {
        let cell_width = (total_width - gap * (cols - 1) as f64) / cols as f64;
        let cell_height = (total_height - gap * (rows - 1) as f64) / rows as f64;

        let x = self.col as f64 * (cell_width + gap);
        let y = self.row as f64 * (cell_height + gap);
        let width = cell_width * self.col_span as f64 + gap * (self.col_span - 1) as f64;
        let height = cell_height * self.row_span as f64 + gap * (self.row_span - 1) as f64;

        CellBounds {
            x,
            y,
            width,
            height,
        }
    }
}

/// Computed bounds for a cell
#[derive(Clone, Copy, Debug)]
pub struct CellBounds {
    pub x: f64,
    pub y: f64,
    pub width: f64,
    pub height: f64,
}

impl CellBounds {
    /// Check if point is inside bounds
    pub fn contains(&self, x: f64, y: f64) -> bool {
        x >= self.x && x < self.x + self.width && y >= self.y && y < self.y + self.height
    }
}

/// Multichart layout configuration
#[derive(Clone, Debug, Serialize, Deserialize)]
pub struct MultichartLayout {
    /// Layout name/identifier
    pub name: String,
    /// Number of rows in grid
    pub rows: usize,
    /// Number of columns in grid
    pub cols: usize,
    /// Gap between cells in pixels
    pub gap: f64,
    /// Individual cells
    pub cells: Vec<LayoutCell>,
    /// Whether scales are shared between charts
    pub shared_time_scale: bool,
    /// Whether crosshair syncs across charts
    pub sync_crosshair: bool,
}

impl MultichartLayout {
    /// Create a simple grid layout (e.g., 2x2, 3x3)
    pub fn grid(rows: usize, cols: usize) -> Self {
        let mut cells = Vec::with_capacity(rows * cols);
        let mut id = 0;

        for row in 0..rows {
            for col in 0..cols {
                let mut cell = LayoutCell::new(id, row, col);
                // Only rightmost column shows price scale
                cell.show_price_scale = col == cols - 1;
                // Only bottom row shows time scale
                cell.show_time_scale = row == rows - 1;
                cells.push(cell);
                id += 1;
            }
        }

        Self {
            name: format!("{}x{}", rows, cols),
            rows,
            cols,
            gap: 1.0,
            cells,
            shared_time_scale: true,
            sync_crosshair: true,
        }
    }

    /// Single chart (1x1)
    pub fn single() -> Self {
        Self::grid(1, 1)
    }

    /// Two charts side by side (1x2)
    pub fn horizontal_split() -> Self {
        Self::grid(1, 2)
    }

    /// Two charts stacked (2x1)
    pub fn vertical_split() -> Self {
        Self::grid(2, 1)
    }

    /// Four charts (2x2)
    pub fn quad() -> Self {
        Self::grid(2, 2)
    }

    /// Three horizontal (1x3)
    pub fn triple_horizontal() -> Self {
        Self::grid(1, 3)
    }

    /// Three vertical (3x1)
    pub fn triple_vertical() -> Self {
        Self::grid(3, 1)
    }

    /// Six charts (2x3)
    pub fn six_pack() -> Self {
        Self::grid(2, 3)
    }

    /// Eight charts (2x4)
    pub fn eight() -> Self {
        Self::grid(2, 4)
    }

    /// One large + three small (1+3 layout)
    /// ```text
    /// ┌───────┬───┐
    /// │       │ 1 │
    /// │   0   ├───┤
    /// │       │ 2 │
    /// │       ├───┤
    /// │       │ 3 │
    /// └───────┴───┘
    /// ```
    pub fn one_plus_three() -> Self {
        Self {
            name: "1+3".to_string(),
            rows: 3,
            cols: 2,
            gap: 1.0,
            cells: vec![
                LayoutCell::with_span(0, 0, 0, 3, 1), // Main chart spans all rows
                LayoutCell::new(1, 0, 1),
                LayoutCell::new(2, 1, 1),
                LayoutCell::new(3, 2, 1),
            ],
            shared_time_scale: true,
            sync_crosshair: true,
        }
    }

    /// Three small + one large (3+1 layout)
    /// ```text
    /// ┌───┬───────┐
    /// │ 0 │       │
    /// ├───┤       │
    /// │ 1 │   3   │
    /// ├───┤       │
    /// │ 2 │       │
    /// └───┴───────┘
    /// ```
    pub fn three_plus_one() -> Self {
        Self {
            name: "3+1".to_string(),
            rows: 3,
            cols: 2,
            gap: 1.0,
            cells: vec![
                LayoutCell::new(0, 0, 0),
                LayoutCell::new(1, 1, 0),
                LayoutCell::new(2, 2, 0),
                LayoutCell::with_span(3, 0, 1, 3, 1), // Main chart spans all rows
            ],
            shared_time_scale: true,
            sync_crosshair: true,
        }
    }

    /// One large on top + two below (1+2 layout)
    /// ```text
    /// ┌───────────┐
    /// │     0     │
    /// ├─────┬─────┤
    /// │  1  │  2  │
    /// └─────┴─────┘
    /// ```
    pub fn one_plus_two() -> Self {
        Self {
            name: "1+2".to_string(),
            rows: 2,
            cols: 2,
            gap: 1.0,
            cells: vec![
                LayoutCell::with_span(0, 0, 0, 1, 2), // Top spans both columns
                LayoutCell::new(1, 1, 0),
                LayoutCell::new(2, 1, 1),
            ],
            shared_time_scale: true,
            sync_crosshair: true,
        }
    }

    /// Two on top + one large below (2+1 layout)
    /// ```text
    /// ┌─────┬─────┐
    /// │  0  │  1  │
    /// ├─────┴─────┤
    /// │     2     │
    /// └───────────┘
    /// ```
    pub fn two_plus_one() -> Self {
        Self {
            name: "2+1".to_string(),
            rows: 2,
            cols: 2,
            gap: 1.0,
            cells: vec![
                LayoutCell::new(0, 0, 0),
                LayoutCell::new(1, 0, 1),
                LayoutCell::with_span(2, 1, 0, 1, 2), // Bottom spans both columns
            ],
            shared_time_scale: true,
            sync_crosshair: true,
        }
    }

    /// Get all available preset layouts
    pub fn presets() -> Vec<Self> {
        vec![
            Self::single(),
            Self::horizontal_split(),
            Self::vertical_split(),
            Self::quad(),
            Self::triple_horizontal(),
            Self::triple_vertical(),
            Self::one_plus_three(),
            Self::three_plus_one(),
            Self::one_plus_two(),
            Self::two_plus_one(),
            Self::six_pack(),
            Self::eight(),
        ]
    }

    /// Get preset by name
    pub fn preset_by_name(name: &str) -> Option<Self> {
        Self::presets().into_iter().find(|p| p.name == name)
    }

    /// Number of charts in this layout
    pub fn chart_count(&self) -> usize {
        self.cells.len()
    }

    /// Calculate bounds for all cells
    pub fn calculate_bounds(
        &self,
        total_width: f64,
        total_height: f64,
    ) -> Vec<(CellId, CellBounds)> {
        self.cells
            .iter()
            .map(|cell| {
                (
                    cell.id,
                    cell.bounds(total_width, total_height, self.rows, self.cols, self.gap),
                )
            })
            .collect()
    }

    /// Find cell at position
    pub fn cell_at(&self, x: f64, y: f64, total_width: f64, total_height: f64) -> Option<CellId> {
        for cell in &self.cells {
            let bounds = cell.bounds(total_width, total_height, self.rows, self.cols, self.gap);
            if bounds.contains(x, y) {
                return Some(cell.id);
            }
        }
        None
    }

    /// Builder: set gap between cells
    pub fn with_gap(mut self, gap: f64) -> Self {
        self.gap = gap;
        self
    }

    /// Builder: enable/disable shared time scale
    pub fn with_shared_time_scale(mut self, shared: bool) -> Self {
        self.shared_time_scale = shared;
        self
    }

    /// Builder: enable/disable crosshair sync
    pub fn with_sync_crosshair(mut self, sync: bool) -> Self {
        self.sync_crosshair = sync;
        self
    }
}

impl Default for MultichartLayout {
    fn default() -> Self {
        Self::single()
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_grid_layout() {
        let layout = MultichartLayout::quad();
        assert_eq!(layout.rows, 2);
        assert_eq!(layout.cols, 2);
        assert_eq!(layout.chart_count(), 4);
    }

    #[test]
    fn test_one_plus_three() {
        let layout = MultichartLayout::one_plus_three();
        assert_eq!(layout.chart_count(), 4);
        // First cell spans 3 rows
        assert_eq!(layout.cells[0].row_span, 3);
    }

    #[test]
    fn test_cell_bounds() {
        let layout = MultichartLayout::quad();
        let bounds = layout.calculate_bounds(800.0, 600.0);
        assert_eq!(bounds.len(), 4);

        // First cell should be at (0, 0)
        assert!((bounds[0].1.x - 0.0).abs() < 0.1);
        assert!((bounds[0].1.y - 0.0).abs() < 0.1);
    }

    #[test]
    fn test_presets() {
        let presets = MultichartLayout::presets();
        assert!(presets.len() >= 10);

        // Check we can find by name
        assert!(MultichartLayout::preset_by_name("2x2").is_some());
        assert!(MultichartLayout::preset_by_name("1+3").is_some());
    }
}
