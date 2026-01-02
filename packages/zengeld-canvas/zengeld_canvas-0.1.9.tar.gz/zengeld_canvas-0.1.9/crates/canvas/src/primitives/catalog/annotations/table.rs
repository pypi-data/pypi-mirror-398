//! Table primitive - data table annotation

use super::super::{
    Primitive, PrimitiveColor, PrimitiveData, PrimitiveKind, PrimitiveMetadata, RenderContext,
    crisp,
};
use serde::{Deserialize, Serialize};

#[derive(Clone, Debug, Serialize, Deserialize)]
pub struct Table {
    pub data: PrimitiveData,
    pub bar: f64,
    pub price: f64,
    pub rows: Vec<Vec<String>>,
    #[serde(default = "default_cols")]
    pub columns: u8,
    #[serde(default = "default_true")]
    pub show_header: bool,
}
fn default_cols() -> u8 {
    2
}
fn default_true() -> bool {
    true
}

impl Table {
    pub fn new(bar: f64, price: f64, color: &str) -> Self {
        Self {
            data: PrimitiveData {
                type_id: "table".to_string(),
                display_name: "Table".to_string(),
                color: PrimitiveColor::new(color),
                width: 1.0,
                ..Default::default()
            },
            bar,
            price,
            rows: vec![
                vec!["Header1".to_string(), "Header2".to_string()],
                vec!["Value1".to_string(), "Value2".to_string()],
            ],
            columns: 2,
            show_header: true,
        }
    }
}

impl Primitive for Table {
    fn type_id(&self) -> &'static str {
        "table"
    }
    fn display_name(&self) -> &str {
        &self.data.display_name
    }
    fn kind(&self) -> PrimitiveKind {
        PrimitiveKind::Annotation
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
    fn render(&self, ctx: &mut dyn RenderContext, is_selected: bool) {
        let dpr = ctx.dpr();
        let x = ctx.bar_to_x(self.bar);
        let y = ctx.price_to_y(self.price);
        let cell_w = 80.0;
        let cell_h = 24.0;
        let total_w = self.columns as f64 * cell_w;
        let total_h = self.rows.len() as f64 * cell_h;

        // Draw table background
        ctx.set_fill_color(&format!("{}E0", &self.data.color.stroke));
        ctx.fill_rect(crisp(x, dpr), crisp(y, dpr), total_w, total_h);

        // Draw header background
        if self.show_header && !self.rows.is_empty() {
            ctx.set_fill_color(&self.data.color.stroke);
            ctx.fill_rect(crisp(x, dpr), crisp(y, dpr), total_w, cell_h);
        }

        // Draw grid lines
        ctx.set_stroke_color(&self.data.color.stroke);
        ctx.set_stroke_width(1.0);

        // Horizontal lines
        for i in 0..=self.rows.len() {
            let ly = y + i as f64 * cell_h;
            ctx.begin_path();
            ctx.move_to(crisp(x, dpr), crisp(ly, dpr));
            ctx.line_to(crisp(x + total_w, dpr), crisp(ly, dpr));
            ctx.stroke();
        }

        // Vertical lines
        for i in 0..=self.columns {
            let lx = x + i as f64 * cell_w;
            ctx.begin_path();
            ctx.move_to(crisp(lx, dpr), crisp(y, dpr));
            ctx.line_to(crisp(lx, dpr), crisp(y + total_h, dpr));
            ctx.stroke();
        }

        // Draw cell text
        ctx.set_font("11px sans-serif");
        for (row_idx, row) in self.rows.iter().enumerate() {
            let is_header = row_idx == 0 && self.show_header;
            ctx.set_fill_color(if is_header { "#000000" } else { "#FFFFFF" });
            for (col_idx, cell) in row.iter().enumerate() {
                if col_idx < self.columns as usize {
                    let cx = x + col_idx as f64 * cell_w + 4.0;
                    let cy = y + row_idx as f64 * cell_h + 16.0;
                    ctx.fill_text(cell, cx, cy);
                }
            }
        }

        let _ = is_selected;
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
        type_id: "table",
        display_name: "Table",
        kind: PrimitiveKind::Annotation,
        factory: |points, color| {
            let (b, p) = points.first().copied().unwrap_or((0.0, 0.0));
            Box::new(Table::new(b, p, color))
        },
        supports_text: true,
        has_levels: false,
        has_points_config: false,
    }
}
