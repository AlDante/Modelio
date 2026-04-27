#!/usr/bin/env python3
from __future__ import annotations

import argparse
import os
from pathlib import Path
import subprocess
import sys
import tempfile


JAVA_SOURCE = """
import java.lang.reflect.Field;
import org.eclipse.draw2d.ColorConstants;
import org.eclipse.draw2d.IFigure;
import org.eclipse.draw2d.RectangleFigure;
import org.eclipse.draw2d.SWTGraphics;
import org.eclipse.draw2d.geometry.Rectangle;
import org.eclipse.gef.editparts.FreeformGraphicalRootEditPart;
import org.modelio.diagram.elements.common.root.ScalableFreeformRootEditPart2;
import org.modelio.diagram.elements.common.abstractdiagram.AbstractDiagramFigure;
import org.modelio.diagram.elements.core.figures.freeform.FreeformLayeredPane2;
import org.modelio.diagram.elements.core.figures.freeform.ScalableFreeformLayeredPane2;
import org.eclipse.swt.graphics.GC;
import org.eclipse.swt.graphics.Image;
import org.eclipse.swt.graphics.ImageData;
import org.eclipse.swt.graphics.RGB;
import org.eclipse.swt.widgets.Display;

public class DiagramEditorSmokeCheck {
    private static final class ExposedRootEditPart extends ScalableFreeformRootEditPart2 {
        IFigure exposeCreateFigure() {
            return super.createFigure();
        }
    }

    private static RGB renderElementAtScale(Display display, double scale) {
        Image image = new Image(display, 200, 200);
        try {
            GC gc = new GC(image);
            try {
                SWTGraphics graphics = new SWTGraphics(gc);
                try {
                    ScalableFreeformLayeredPane2 pane = new ScalableFreeformLayeredPane2();
                    pane.setBounds(new Rectangle(0, 0, 200, 200));
                    pane.setScale(scale);

                    AbstractDiagramFigure diagram = new AbstractDiagramFigure();
                    diagram.setBounds(new Rectangle(0, 0, 200, 200));

                    RectangleFigure rect = new RectangleFigure();
                    rect.setBackgroundColor(ColorConstants.red);
                    rect.setForegroundColor(ColorConstants.red);
                    rect.setOpaque(true);
                    rect.setBounds(new Rectangle(20, 20, 60, 40));
                    diagram.add(rect);

                    pane.add(diagram);
                    pane.validate();
                    pane.paint(graphics);
                } finally {
                    graphics.dispose();
                }
            } finally {
                gc.dispose();
            }

            ImageData data = image.getImageData();
            return data.palette.getRGB(data.getPixel(30, 30));
        } finally {
            image.dispose();
        }
    }

    public static void main(String[] args) throws Exception {
        Display display = new Display();
        try {
        Field innerLayersField = FreeformGraphicalRootEditPart.class.getDeclaredField("innerLayers");
        if (!innerLayersField.getType().isAssignableFrom(FreeformLayeredPane2.class)) {
            throw new AssertionError(
                "FreeformGraphicalRootEditPart.innerLayers expects "
                    + innerLayersField.getType().getName()
                    + " but FreeformLayeredPane2 is "
                    + FreeformLayeredPane2.class.getName());
        }

        ExposedRootEditPart part = new ExposedRootEditPart();
        IFigure figure = part.exposeCreateFigure();
        if (figure == null) {
            throw new AssertionError("createFigure() returned null");
        }

        innerLayersField.setAccessible(true);
        Object innerLayers = innerLayersField.get(part);
        innerLayersField.setAccessible(false);

        if (!(innerLayers instanceof FreeformLayeredPane2)) {
            throw new AssertionError(
                "innerLayers was initialised with "
                    + (innerLayers == null ? "null" : innerLayers.getClass().getName())
                    + " instead of "
                    + FreeformLayeredPane2.class.getName());
        }

        RGB scale1 = renderElementAtScale(display, 1.0);
        if (!scale1.equals(new RGB(255, 0, 0))) {
            throw new AssertionError("ScalableFreeformLayeredPane2 failed to render a diagram element at scale 1.0: " + scale1);
        }

        RGB scale2 = renderElementAtScale(display, 2.0);
        if (!scale2.equals(new RGB(255, 0, 0))) {
            throw new AssertionError("ScalableFreeformLayeredPane2 failed to render a diagram element at scale 2.0: " + scale2);
        }

        System.out.println("Diagram editor smoke check passed.");
        } finally {
            display.dispose();
        }
    }
}
""".lstrip()


def build_argument_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Run a component-level smoke test for Modelio diagram editor compatibility on macOS aarch64."
    )
    parser.add_argument(
        "--app",
        type=Path,
        required=True,
        help="Path to the built Modelio.app bundle to test."
    )
    return parser



def resolve_java() -> str:
    java_home = os.environ.get("JAVA_HOME")
    if java_home:
        candidate = Path(java_home) / "bin" / "java"
        if candidate.exists():
            return str(candidate)
    return "java"



def run_smoke_test(app_bundle: Path) -> int:
    plugins_dir = app_bundle / "Contents" / "Eclipse" / "plugins"
    if not plugins_dir.is_dir():
        print(f"Skipping diagram editor smoke test because plugins directory is missing: {plugins_dir}")
        return 0

    java_executable = resolve_java()
    classpath = str(plugins_dir / "*")

    with tempfile.TemporaryDirectory(prefix="modelio-diagram-smoke-") as tmp_dir_name:
        tmp_dir = Path(tmp_dir_name)
        java_file = tmp_dir / "DiagramEditorSmokeCheck.java"
        java_file.write_text(JAVA_SOURCE, encoding="utf-8")

        result = subprocess.run(
            [
                java_executable,
                "-XstartOnFirstThread",
                "-classpath",
                classpath,
                str(java_file),
            ],
            capture_output=True,
            text=True,
            check=False,
        )

    if result.stdout:
        print(result.stdout, end="")
    if result.returncode != 0:
        if result.stderr:
            print(result.stderr, end="", file=sys.stderr)
        return result.returncode
    return 0



def main() -> int:
    args = build_argument_parser().parse_args()
    return run_smoke_test(args.app)


if __name__ == "__main__":
    raise SystemExit(main())

