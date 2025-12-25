#
# Pavlin Georgiev, Softel Labs
#
# This is a proprietary file and may not be copied,
# distributed, or modified without express permission
# from the owner. For licensing inquiries, please
# contact pavlin@softel.bg.
#
# 2024
#

import math
import numpy as np


def points_distance(p1, p2):
  p1 = np.array(p1)
  p2 = np.array(p2)
  return np.linalg.norm(p1 - p2)

def validate_point(p, w, h):
  x = max(p[0], 0)
  x = min(x, w)
  y = max(p[1], 0)
  y = min(y, h)
  return (x, y)

# Calc diameter point from a circle point and circle center
def diameter_point(p1, p2):
  x = 2 * p2[0] - p1[0]
  y = 2 * p2[1] - p1[1]
  return (x, y)

# Center point for a line section (with some ratio for general purpose)
def line_section_center_point(p1, p2, ratio=0.5):
  x = int(p1[0] + ratio * (p2[0] - p1[0]))
  y = int(p1[1] + ratio * (p2[1] - p1[1]))
  return (x, y)

# Line equation ax + by + c = 0 coefficients
def line_coeff(l):
  a = l[0][1] - l[1][1]
  b = l[1][0] - l[0][0]
  c = l[0][0] * l[1][1] - l[1][0] * l[0][1]
  return a, b, c

# 2 Lines intersection point (None, None) when parallel
def lines_intersection(l1, l2):
  a1, b1, c1 = line_coeff(l1)
  a2, b2, c2 = line_coeff(l2)

  d = (a1 * b2 - a2 * b1)
  if d != 0.0:
    x = (b1 * c2 - b2 * c1) / d
    y = (c1 * a2 - c2 * a1) / d
  else:
    x, y = None, None
  return x, y

# Check if p is between p1 and p2 on a line
def line_point_between(p, p1, p2):
  return (
        p[0] >= min(p1[0], p2[0]) and p[0] <= max(p1[0], p2[0])
    and p[1] >= min(p1[1], p2[1]) and p[1] <= max(p1[1], p2[1])
  )

# Check a point p is intersection for 2 line segments l1 and l2
def is_point_segments_intersection(p, l1, l2):
  return line_point_between(p, l1[0], l1[1]) and line_point_between(p, l2[0], l2[1])

# Angle from radians to degrees convertor
def angle_rad2deg(angle):
  return math.fabs(angle * 180 / math.pi)

# Angle between lines in radians
def lines_angle(l1, l2):
  v1 = (l1[0][0] - l1[1][0], l1[0][1] - l1[1][1])
  v2 = (l2[0][0] - l2[1][0], l2[0][1] - l2[1][1])
  return math.atan2(v1[0], v1[1]) - math.atan2(v2[0], v2[1])

# Angle between lines in degrees
def lines_angle_deg(l1, l2):
  return angle_rad2deg(lines_angle(l1, l2))
