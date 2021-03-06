# Copyright 2020 Google LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""SVGPath <=> skia-pathops constructs to enable ops on paths."""
import functools
import pathops
from nanosvg.svg_transform import Affine2D
from nanosvg.svg_types import SVGPath, SVGShape


def _svg_arc_to_skia_arcTo(self, rx, ry, xAxisRotate, largeArc, sweep, x, y):
    # SVG 'sweep-flag' value is opposite the integer value of SkPath.arcTo 'sweep'.
    # SVG sweep-flag uses 1 for clockwise, while SkPathDirection::kCW cast to
    # int is zero, thus we need to negate it.
    self.arcTo(rx, ry, xAxisRotate, largeArc, not sweep, x, y)


# Absolutes coords assumed
# A should never occur because we convert arcs to cubics
# S,T should never occur because we eliminate shorthand
_SVG_CMD_TO_SKIA_FN = {
    "M": pathops.Path.moveTo,
    "L": pathops.Path.lineTo,
    "Q": pathops.Path.quadTo,
    "Z": pathops.Path.close,
    "C": pathops.Path.cubicTo,
    "A": _svg_arc_to_skia_arcTo,
}

_SVG_TO_SKIA_LINE_CAP = {
    "butt": pathops.LineCap.BUTT_CAP,
    "round": pathops.LineCap.ROUND_CAP,
    "square": pathops.LineCap.SQUARE_CAP,
}

_SVG_TO_SKIA_LINE_JOIN = {
    "miter": pathops.LineJoin.MITER_JOIN,
    "round": pathops.LineJoin.ROUND_JOIN,
    "bevel": pathops.LineJoin.BEVEL_JOIN,
    # No arcs or miter-clip
}


def _simple_skia_to_svg(svg_cmd, svg_path, points):
    # pathops.Path gives us sequences of points, flatten 'em
    cmd_args = tuple(c for pt in points for c in pt)
    svg_path._add_cmd(svg_cmd, *cmd_args)


def _qcurveto_to_svg(svg_path, points):
    for (control_pt, end_pt) in pathops.decompose_quadratic_segment(points):
        svg_path._add_cmd("Q", *control_pt, *end_pt)


_SKIA_CMD_TO_SVG_CMD = {
    # simple conversions
    "moveTo": functools.partial(_simple_skia_to_svg, "M"),
    "lineTo": functools.partial(_simple_skia_to_svg, "L"),
    "quadTo": functools.partial(_simple_skia_to_svg, "Q"),
    "curveTo": functools.partial(_simple_skia_to_svg, "C"),
    "closePath": functools.partial(_simple_skia_to_svg, "Z"),
    # more interesting conversions
    "qCurveTo": _qcurveto_to_svg,
    # nop
    "endPath": lambda *_: None,
}


def skia_path(shape: SVGShape, tolerance: float):
    path = (
        shape.as_path(tolerance)
        .explicit_lines()  # hHvV => lL
        .expand_shorthand(inplace=True)
        .absolute(inplace=True)
    )

    sk_path = pathops.Path()
    for cmd, args in path:
        if cmd not in _SVG_CMD_TO_SKIA_FN:
            raise ValueError(f'No mapping to Skia for "{cmd} {args}"')
        _SVG_CMD_TO_SKIA_FN[cmd](sk_path, *args)

    sk_path.convertConicsToQuads(tolerance)
    return sk_path


def svg_path(skia_path: pathops.Path) -> SVGPath:
    svg_path = SVGPath()
    for cmd, points in skia_path.segments:
        if cmd not in _SKIA_CMD_TO_SVG_CMD:
            raise ValueError(f'No mapping to svg for "{cmd} {points}"')
        _SKIA_CMD_TO_SVG_CMD[cmd](svg_path, points)
    return svg_path


def _do_pathop(tolerance, op, svg_shapes) -> SVGShape:
    tolerance = float(tolerance)
    if not svg_shapes:
        return SVGPath()

    sk_path = skia_path(svg_shapes[0], tolerance)
    for svg_shape in svg_shapes[1:]:
        sk_path2 = skia_path(svg_shape, tolerance)
        sk_path = pathops.op(sk_path, sk_path2, op)
    return svg_path(sk_path)


def union(tolerance, *svg_shapes) -> SVGShape:
    return _do_pathop(tolerance, pathops.PathOp.UNION, svg_shapes)


def intersection(tolerance, *svg_shapes) -> SVGShape:
    return _do_pathop(tolerance, pathops.PathOp.INTERSECTION, svg_shapes)


def transform(svg_shape: SVGShape, affine: Affine2D, tolerance: float) -> SVGShape:
    sk_path = skia_path(svg_shape, tolerance).transform(*affine)
    return svg_path(sk_path)


def stroke(shape: SVGShape, tolerance: float) -> SVGShape:
    """Create a path that is shape with it's stroke applied."""
    cap = _SVG_TO_SKIA_LINE_CAP.get(shape.stroke_linecap, None)
    if cap is None:
        raise ValueError(f"Unsupported cap {shape.stroke_linecap}")
    join = _SVG_TO_SKIA_LINE_JOIN.get(shape.stroke_linejoin, None)
    if join is None:
        raise ValueError(f"Unsupported join {shape.stroke_linejoin}")
    sk_path = skia_path(shape, tolerance)
    sk_path.stroke(shape.stroke_width, cap, join, shape.stroke_miterlimit)
    return svg_path(sk_path)


def bounding_box(shape: SVGShape, tolerance: float):
    return skia_path(shape, tolerance).bounds
