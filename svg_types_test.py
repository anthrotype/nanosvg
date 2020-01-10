import pytest
from svg_types import SVGPath

@pytest.mark.parametrize(
  "path, expected_result",
  [
    # path explodes to show implicit commands & becomes absolute
    (
      'm1,1 2,0 1,3',
      'M1,1 L3,1 L4,4',
    ),
    # Vertical, Horizontal movement
    (
      'm2,2 h2 v2 h-1 v-1 H8 V8',
      'M2,2 H4 V4 H3 V3 H8 V8',
    ),
    # Quadratic bezier curve
    (
      'm2,2 q1,1 2,2 Q5,5 6,6',
      'M2,2 Q3,3 4,4 Q5,5 6,6',
    ),
    # Elliptic arc
    (
      'm2,2 a1,1 0 0 0 3,3 A2,2 1 1 1 4,4',
      'M2,2 A1 1 0 0 0 5,5 A2 2 1 1 1 4,4',
    ),
    # Cubic bezier
    (
      'm2,2 c1,-1 2,4 3,3 C4 4 5 5 6 6',
      'M2,2 C3,1 4,6 5,5 C4,4 5,5 6,6',
    ),
  ]
)
def test_path_absolute(path: str, expected_result: str):
  actual = SVGPath(d=path).absolute(inplace=True).d
  print(f'A: {actual}')
  print(f'E: {expected_result}')
  assert actual == expected_result

@pytest.mark.parametrize(
  "path, move, expected_result",
  [
    # path with implicit relative lines
    (
      'm1,1 2,0 1,3',
      (2, 2),
      'M3,3 l2,0 l1,3',
    ),
    # path with implicit absolute lines
    (
      'M1,1 2,0 1,3',
      (2, 2),
      'M3,3 L4,2 L3,5',
    ),
    # Vertical, Horizontal movement
    (
      'm2,2 h2 v2 h-1 v-1 H8 V8',
      (-1, -2),
      'M1,0 h2 v2 h-1 v-1 H7 V6',
    ),
    # Quadratic bezier curve
    (
      'm2,2 q1,1 2,2 Q5,5 6,6',
      (3, 1),
      'M5,3 q1,1 2,2 Q8,6 9,7',
    ),
    # Elliptic arc
    (
      'm2,2 a1,1 0 0 0 3,3 A2,2 1 1 1 4,4',
      (1, 3),
      'M3,5 a1 1 0 0 0 3,3 A2 2 1 1 1 5,7',
    ),
    # Cubic bezier
    (
      'm2,2 c1,-1 2,4 3,3 C4 4 5 5 6 6',
      (4, 2),
      'M6,4 c1,-1 2,4 3,3 C8,6 9,7 10,8',
    ),
  ]
)
def test_path_move(path: str, move, expected_result: str):
  actual = SVGPath(d=path).move(*move, inplace=True).d
  print(f'A: {actual}')
  print(f'E: {expected_result}')
  assert actual == expected_result

@pytest.mark.parametrize(
  "path, expected_result",
  [
    # C/S
    (
      'M600,800 C625,700 725,700 750,800 S875,900 900,800',
      'M600,800 C625,700 725,700 750,800 C775,900 875,900 900,800'
    ),
    # TODO Q/T test
    # TODO chain of shorthands
  ]
)
def test_expand_shorthand(path, expected_result):
  actual = SVGPath(d=path).expand_shorthand(inplace=True).d
  print(f'A: {actual}')
  print(f'E: {expected_result}')
  assert actual == expected_result
