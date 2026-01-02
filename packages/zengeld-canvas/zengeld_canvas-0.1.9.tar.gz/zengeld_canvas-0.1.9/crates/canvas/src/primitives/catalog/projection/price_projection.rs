//! Price Projection - project price movement

use super::super::{
    LineStyle, Primitive, PrimitiveColor, PrimitiveData, PrimitiveKind, PrimitiveMetadata,
    RenderContext, crisp,
};
use serde::{Deserialize, Serialize};

#[derive(Clone, Debug, Serialize, Deserialize)]
pub struct PriceProjection {
    pub data: PrimitiveData,
    pub bar1: f64,
    pub price1: f64, // Source start
    pub bar2: f64,
    pub price2: f64, // Source end
    pub bar3: f64,
    pub price3: f64, // Projection point
    #[serde(default = "default_true")]
    pub show_percentage: bool,
}
fn default_true() -> bool {
    true
}

impl PriceProjection {
    pub fn new(
        bar1: f64,
        price1: f64,
        bar2: f64,
        price2: f64,
        bar3: f64,
        price3: f64,
        color: &str,
    ) -> Self {
        Self {
            data: PrimitiveData {
                type_id: "price_projection".to_string(),
                display_name: "Price Projection".to_string(),
                color: PrimitiveColor::new(color),
                width: 2.0,
                ..Default::default()
            },
            bar1,
            price1,
            bar2,
            price2,
            bar3,
            price3,
            show_percentage: true,
        }
    }
}

impl Primitive for PriceProjection {
    fn type_id(&self) -> &'static str {
        "price_projection"
    }
    fn display_name(&self) -> &str {
        &self.data.display_name
    }
    fn kind(&self) -> PrimitiveKind {
        PrimitiveKind::Trading
    }
    fn data(&self) -> &PrimitiveData {
        &self.data
    }
    fn data_mut(&mut self) -> &mut PrimitiveData {
        &mut self.data
    }
    fn points(&self) -> Vec<(f64, f64)> {
        vec![
            (self.bar1, self.price1),
            (self.bar2, self.price2),
            (self.bar3, self.price3),
        ]
    }
    fn set_points(&mut self, pts: &[(f64, f64)]) {
        if let Some(&(b, p)) = pts.first() {
            self.bar1 = b;
            self.price1 = p;
        }
        if let Some(&(b, p)) = pts.get(1) {
            self.bar2 = b;
            self.price2 = p;
        }
        if let Some(&(b, p)) = pts.get(2) {
            self.bar3 = b;
            self.price3 = p;
        }
    }
    fn translate(&mut self, bd: f64, pd: f64) {
        self.bar1 += bd;
        self.bar2 += bd;
        self.bar3 += bd;
        self.price1 += pd;
        self.price2 += pd;
        self.price3 += pd;
    }

    fn render(&self, ctx: &mut dyn RenderContext, _is_selected: bool) {
        let dpr = ctx.dpr();
        let x1 = ctx.bar_to_x(self.bar1);
        let y1 = ctx.price_to_y(self.price1);
        let x2 = ctx.bar_to_x(self.bar2);
        let y2 = ctx.price_to_y(self.price2);
        let x3 = ctx.bar_to_x(self.bar3);
        let y3 = ctx.price_to_y(self.price3);

        // Calculate the price movement to project
        let price_delta = self.price2 - self.price1;
        let projected_price = self.price3 + price_delta;
        let y4 = ctx.price_to_y(projected_price);

        // Set stroke style
        ctx.set_stroke_color(&self.data.color.stroke);
        ctx.set_stroke_width(self.data.width);

        // Set line dash based on style
        match self.data.style {
            LineStyle::Solid => ctx.set_line_dash(&[]),
            LineStyle::Dashed => ctx.set_line_dash(&[8.0, 4.0]),
            LineStyle::Dotted => ctx.set_line_dash(&[2.0, 2.0]),
            LineStyle::LargeDashed => ctx.set_line_dash(&[12.0, 6.0]),
            LineStyle::SparseDotted => ctx.set_line_dash(&[2.0, 8.0]),
        }

        // Draw source measurement line (point 1 to point 2)
        ctx.begin_path();
        ctx.move_to(crisp(x1, dpr), crisp(y1, dpr));
        ctx.line_to(crisp(x2, dpr), crisp(y2, dpr));
        ctx.stroke();

        // Draw projection line (point 3 to projected point)
        ctx.set_line_dash(&[4.0, 4.0]); // Dashed for projection
        ctx.begin_path();
        ctx.move_to(crisp(x3, dpr), crisp(y3, dpr));
        ctx.line_to(crisp(x3, dpr), crisp(y4, dpr));
        ctx.stroke();

        // Draw horizontal levels
        ctx.set_line_dash(&[]);
        ctx.set_stroke_width(1.0);

        // Source start level
        ctx.begin_path();
        ctx.move_to(crisp(x1, dpr), crisp(y1, dpr));
        ctx.line_to(crisp(x2, dpr), crisp(y1, dpr));
        ctx.stroke();

        // Source end level
        ctx.begin_path();
        ctx.move_to(crisp(x1, dpr), crisp(y2, dpr));
        ctx.line_to(crisp(x2, dpr), crisp(y2, dpr));
        ctx.stroke();

        // Projection start level
        ctx.begin_path();
        ctx.move_to(crisp(x3, dpr), crisp(y3, dpr));
        ctx.line_to(crisp(x3 + 50.0, dpr), crisp(y3, dpr));
        ctx.stroke();

        // Projection end level
        ctx.begin_path();
        ctx.move_to(crisp(x3, dpr), crisp(y4, dpr));
        ctx.line_to(crisp(x3 + 50.0, dpr), crisp(y4, dpr));
        ctx.stroke();

        // Reset line dash
        ctx.set_line_dash(&[]);
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
        type_id: "price_projection",
        display_name: "Price Projection",
        kind: PrimitiveKind::Trading,
        factory: |points, color| {
            let (b1, p1) = points.first().copied().unwrap_or((0.0, 100.0));
            let (b2, p2) = points.get(1).copied().unwrap_or((b1 + 10.0, p1 + 5.0));
            let (b3, p3) = points.get(2).copied().unwrap_or((b2 + 10.0, p2 + 5.0));
            Box::new(PriceProjection::new(b1, p1, b2, p2, b3, p3, color))
        },
        supports_text: true,
        has_levels: false,
        has_points_config: false,
    }
}
