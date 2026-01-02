//! Elliott Triple Combination - WXYXZ pattern

use super::super::{
    LineStyle, Primitive, PrimitiveColor, PrimitiveData, PrimitiveKind, PrimitiveMetadata,
    RenderContext, crisp,
};
use serde::{Deserialize, Serialize};

#[derive(Clone, Debug, Serialize, Deserialize)]
pub struct ElliottTripleCombo {
    pub data: PrimitiveData,
    pub points: Vec<(f64, f64)>, // Variable number of points
    #[serde(default = "default_true")]
    pub show_labels: bool,
}
fn default_true() -> bool {
    true
}

impl ElliottTripleCombo {
    pub fn new(points: Vec<(f64, f64)>, color: &str) -> Self {
        Self {
            data: PrimitiveData {
                type_id: "elliott_triple_combo".to_string(),
                display_name: "Elliott Triple Combo".to_string(),
                color: PrimitiveColor::new(color),
                width: 2.0,
                ..Default::default()
            },
            points,
            show_labels: true,
        }
    }
}

impl Primitive for ElliottTripleCombo {
    fn type_id(&self) -> &'static str {
        "elliott_triple_combo"
    }
    fn display_name(&self) -> &str {
        &self.data.display_name
    }
    fn kind(&self) -> PrimitiveKind {
        PrimitiveKind::Pattern
    }
    fn data(&self) -> &PrimitiveData {
        &self.data
    }
    fn data_mut(&mut self) -> &mut PrimitiveData {
        &mut self.data
    }
    fn points(&self) -> Vec<(f64, f64)> {
        self.points.clone()
    }
    fn set_points(&mut self, pts: &[(f64, f64)]) {
        self.points = pts.to_vec();
    }
    fn translate(&mut self, bd: f64, pd: f64) {
        for p in &mut self.points {
            p.0 += bd;
            p.1 += pd;
        }
    }
    fn render(&self, ctx: &mut dyn RenderContext, _is_selected: bool) {
        if self.points.is_empty() {
            return;
        }
        let dpr = ctx.dpr();
        let screen: Vec<_> = self
            .points
            .iter()
            .map(|(b, p)| (ctx.bar_to_x(*b), ctx.price_to_y(*p)))
            .collect();

        ctx.set_stroke_color(&self.data.color.stroke);
        ctx.set_stroke_width(self.data.width);
        match self.data.style {
            LineStyle::Solid => ctx.set_line_dash(&[]),
            LineStyle::Dashed => ctx.set_line_dash(&[8.0, 4.0]),
            LineStyle::Dotted => ctx.set_line_dash(&[2.0, 2.0]),
            LineStyle::LargeDashed => ctx.set_line_dash(&[12.0, 6.0]),
            LineStyle::SparseDotted => ctx.set_line_dash(&[2.0, 8.0]),
        }

        // Draw connecting lines
        ctx.begin_path();
        ctx.move_to(crisp(screen[0].0, dpr), crisp(screen[0].1, dpr));
        for (x, y) in screen.iter().skip(1) {
            ctx.line_to(crisp(*x, dpr), crisp(*y, dpr));
        }
        ctx.stroke();
        ctx.set_line_dash(&[]);

        // Draw labels (WXYXZ pattern)
        if self.show_labels {
            ctx.set_fill_color(&self.data.color.stroke);
            ctx.set_font("12px sans-serif");
            let labels = ["W", "", "", "X", "Y", "", "X2", "Z", ""];
            for (i, (x, y)) in screen.iter().enumerate() {
                if i < labels.len() && !labels[i].is_empty() {
                    let offset = if i > 0 && *y < screen[i - 1].1 {
                        -15.0
                    } else {
                        15.0
                    };
                    ctx.fill_text(labels[i], *x - 5.0, *y + offset);
                }
            }
        }
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
        type_id: "elliott_triple_combo",
        display_name: "Elliott Triple Combo",
        kind: PrimitiveKind::Pattern,
        factory: |points, color| Box::new(ElliottTripleCombo::new(points.to_vec(), color)),
        supports_text: true,
        has_levels: false,
        has_points_config: true,
    }
}
