from __future__ import annotations
from typing import Iterable, Optional, Tuple, Sequence
import numpy as np

Number4 = Tuple[float, float, float, float]
Size = Tuple[int, int]


class Box: #Box only
    """
    Canonical storage:
      - Absolute:   _a = (cx, cy, w, h)
      - Normalized: _n = (cxn, cyn, wn, hn)  in [0..1] w.r.t. .size

    Base forms (mutually exclusive at construction): xywh, xyxy, xywhn, xyxyn

    Convenience:
      - Absolute:   xy, wh, anchors x1y1, x1y2, x2y1, x2y2, x1y, x2y, xy1, xy2
      - Normalized: xyn, whn, anchors x1y1n, x1y2n, x2y1n, x2y2n, x1yn, x2yn, xy1n, xy2n
      - Anchor+size (read/write):
          Absolute:   x1y1wh, x1y2wh, x2y1wh, x2y2wh, x1ywh, x2ywh, xy1wh, xy2wh
          Normalized: x1y1whn, x1y2whn, x2y1whn, x2y2whn, x1ywhn, x2ywhn, xy1whn, xy2whn
    """

    __slots__ = ("_mode", "_a", "_n", "_size")

    _KW_ORDER = (
        "size",
        "xywhn", "xyxyn", "xywh", "xyxy",
        "xy", "wh", "xyn", "whn",
        "x1y1n", "x1y2n", "x2y1n", "x2y2n", "x1yn", "x2yn", "xy1n", "xy2n",
        "x1y1", "x1y2", "x2y1", "x2y2", "x1y", "x2y", "xy1", "xy2",
        "x1y1whn", "x1y2whn", "x2y1whn", "x2y2whn",
        "x1ywhn", "x2ywhn", "xy1whn", "xy2whn",
        "x1y1wh", "x1y2wh", "x2y1wh", "x2y2wh",
        "x1ywh", "x2ywh", "xy1wh", "xy2wh",
    )
    _BASE_FORMS = ("xywhn", "xyxyn", "xywh", "xyxy")

    # --------------------- init ---------------------
    def __init__(
            self,
            *,
            xywhn: Optional[Iterable[float]] = None,
            xyxyn: Optional[Iterable[float]] = None,
            xywh: Optional[Iterable[float]] = None,
            xyxy: Optional[Iterable[float]] = None,
            size: Optional[Size] = None,
            **kw
    ):
        self._mode: Optional[str] = None  # "a" or "n"
        self._a: Optional[Number4] = None
        self._n: Optional[Number4] = None
        self._size: Optional[Size] = None

        if size is not None: kw.setdefault("size", size)
        if xywhn is not None: kw.setdefault("xywhn", xywhn)
        if xyxyn is not None: kw.setdefault("xyxyn", xyxyn)
        if xywh is not None: kw.setdefault("xywh", xywh)
        if xyxy is not None: kw.setdefault("xyxy", xyxy)

        self._apply_kwargs(**kw)

    # --------------------- utils ---------------------
    @staticmethod
    def _np2(vals: Sequence[float]) -> np.ndarray:
        return np.array(vals, dtype=float)

    @staticmethod
    def _np4(vals: Sequence[float]) -> np.ndarray:
        return np.array(vals, dtype=float)

    def _need_size(self):
        if self._size is None:
            raise ValueError("Image size is required (set .size = (W, H)).")

    def _apply_kwargs(self, **kw):
        if not kw:
            return
        allowed = set(self._KW_ORDER)
        unknown = [k for k in kw if k not in allowed]
        if unknown:
            raise TypeError(f"Unknown init keyword(s): {unknown}. Allowed: {sorted(allowed)}")

        base_in_kw = [k for k in self._BASE_FORMS if k in kw and kw[k] is not None]
        if len(base_in_kw) > 1:
            raise ValueError(f"Provide at most one base form, got {base_in_kw}.")

        for k in self._KW_ORDER:
            if k in kw and kw[k] is not None:
                setattr(self, k, kw[k])

    # small helpers
    def _abs_xywh(self) -> Tuple[float, float, float, float]:
        cx, cy, w, h = self.xywh
        return float(cx), float(cy), float(w), float(h)

    def _abs_wh(self) -> Tuple[float, float]:
        _, _, w, h = self._abs_xywh()
        return w, h

    def _abs_corners(self) -> Tuple[float, float, float, float]:
        cx, cy, w, h = self._abs_xywh()
        return cx - w * 0.5, cy - h * 0.5, cx + w * 0.5, cy + h * 0.5

    # --------------------- size ---------------------
    @property
    def size(self) -> Optional[Size]:
        return self._size

    @size.setter
    def size(self, wh: Size):
        W, H = wh
        if not (W > 0 and H > 0):
            raise ValueError("size must be positive integers (W, H).")
        self._size = (int(W), int(H))

    def set_size(self, wh: Size) -> "Box":
        self.size = wh
        return self

    # --------------------- base forms ---------------------
    @property
    def xywh(self) -> np.ndarray:
        if self._mode == "a":
            return self._np4(self._a)  # type: ignore[arg-type]
        if self._mode == "n":
            self._need_size()
            W, H = self._size  # type: ignore[assignment]
            cxn, cyn, wn, hn = self._n  # type: ignore[misc]
            return self._np4((cxn * W, cyn * H, wn * W, hn * H))
        raise ValueError("Box is empty; set a format first.")

    @xywh.setter
    def xywh(self, vals: Iterable[float]):
        cx, cy, w, h = map(float, vals)
        self._a = (cx, cy, w, h)
        self._mode = "a"

    @property
    def xywhn(self) -> np.ndarray:
        if self._mode == "n":
            return self._np4(self._n)  # type: ignore[arg-type]
        if self._mode == "a":
            self._need_size()
            W, H = self._size  # type: ignore[assignment]
            cx, cy, w, h = self._a  # type: ignore[misc]
            return self._np4((cx / W, cy / H, w / W, h / H))
        raise ValueError("Box is empty; set a format first.")

    @xywhn.setter
    def xywhn(self, vals: Iterable[float]):
        cxn, cyn, wn, hn = map(float, vals)
        self._n = (cxn, cyn, wn, hn)
        self._mode = "n"

    @property
    def xyxy(self) -> np.ndarray:
        cx, cy, w, h = self.xywh
        return self._np4((cx - w * 0.5, cy - h * 0.5, cx + w * 0.5, cy + h * 0.5))

    @xyxy.setter
    def xyxy(self, vals: Iterable[float]):
        x1, y1, x2, y2 = map(float, vals)
        self.xywh = ((x1 + x2) * 0.5, (y1 + y2) * 0.5, (x2 - x1), (y2 - y1))

    @property
    def xyxyn(self) -> np.ndarray:
        cxn, cyn, wn, hn = self.xywhn
        return self._np4((cxn - wn * 0.5, cyn - hn * 0.5, cxn + wn * 0.5, cyn + hn * 0.5))

    @xyxyn.setter
    def xyxyn(self, vals: Iterable[float]):
        x1n, y1n, x2n, y2n = map(float, vals)
        self.xywhn = ((x1n + x2n) * 0.5, (y1n + y2n) * 0.5, (x2n - x1n), (y2n - y1n))

    # --------------------- simple components ---------------------
    @property
    def xy(self) -> np.ndarray:
        cx, cy, _, _ = self.xywh
        return self._np2((cx, cy))

    @xy.setter
    def xy(self, vals: Iterable[float]):
        x, y = map(float, vals)
        if self._mode == "a":
            cx, cy, w, h = self._a  # type: ignore[misc]
            self._a = (x, y, w, h)
        elif self._mode == "n":
            self._need_size()
            W, H = self._size  # type: ignore[assignment]
            cxn, cyn, wn, hn = self._n  # type: ignore[misc]
            self._n = (x / W, y / H, wn, hn)
        else:
            self._a = (x, y, 0.0, 0.0)
            self._mode = "a"

    @property
    def wh(self) -> np.ndarray:
        _, _, w, h = self.xywh
        return self._np2((w, h))

    @wh.setter
    def wh(self, vals: Iterable[float]):
        w, h = map(float, vals)
        if self._mode == "a":
            cx, cy, _, _ = self._a  # type: ignore[misc]
            self._a = (cx, cy, w, h)
        elif self._mode == "n":
            self._need_size()
            W, H = self._size  # type: ignore[assignment]
            cxn, cyn, _, _ = self._n  # type: ignore[misc]
            self._n = (cxn, cyn, w / W, h / H)
        else:
            self._a = (0.0, 0.0, w, h)
            self._mode = "a"

    @property
    def xyn(self) -> np.ndarray:
        if self._mode == "n":
            cxn, cyn, _, _ = self._n  # type: ignore[misc]
            return self._np2((cxn, cyn))
        if self._mode == "a":
            self._need_size()
            W, H = self._size  # type: ignore[assignment]
            cx, cy, _, _ = self._a  # type: ignore[misc]
            return self._np2((cx / W, cy / H))
        raise ValueError("Box is empty; set a format first.")

    @xyn.setter
    def xyn(self, vals: Iterable[float]):
        cxn, cyn = map(float, vals)
        if self._mode == "n":
            _, _, wn, hn = self._n  # type: ignore[misc]
            self._n = (cxn, cyn, wn, hn)
        elif self._mode == "a":
            self._need_size()
            W, H = self._size  # type: ignore[assignment]
            cx, cy, w, h = self._a  # type: ignore[misc]
            self._a = (cxn * W, cyn * H, w, h)
        else:
            self._n = (cxn, cyn, 0.0, 0.0)
            self._mode = "n"

    @property
    def whn(self) -> np.ndarray:
        if self._mode == "n":
            _, _, wn, hn = self._n  # type: ignore[misc]
            return self._np2((wn, hn))
        if self._mode == "a":
            self._need_size()
            W, H = self._size  # type: ignore[assignment]
            _, _, w, h = self._a  # type: ignore[misc]
            return self._np2((w / W, h / H))
        raise ValueError("Box is empty; set a format first.")

    @whn.setter
    def whn(self, vals: Iterable[float]):
        wn, hn = map(float, vals)
        if self._mode == "n":
            cxn, cyn, _, _ = self._n  # type: ignore[misc]
            self._n = (cxn, cyn, wn, hn)
        elif self._mode == "a":
            self._need_size()
            W, H = self._size  # type: ignore[assignment]
            cx, cy, _, _ = self._a  # type: ignore[misc]
            self._a = (cx, cy, wn * W, hn * H)
        else:
            raise ValueError("Box is empty; cannot set whn.")

    # --------------------- anchor points (get/set) ---------------------
    # getters
    def _get_anchor_abs(self, name: str) -> np.ndarray:
        x1, y1, x2, y2 = self._abs_corners()
        cx, cy, _, _ = self._abs_xywh()
        if name == "x1y1":
            return self._np2((x1, y1))
        elif name == "x1y2":
            return self._np2((x1, y2))
        elif name == "x2y1":
            return self._np2((x2, y1))
        elif name == "x2y2":
            return self._np2((x2, y2))
        elif name == "x1y":
            return self._np2((x1, cy))
        elif name == "x2y":
            return self._np2((x2, cy))
        elif name == "xy1":
            return self._np2((cx, y1))
        elif name == "xy2":
            return self._np2((cx, y2))
        else:
            raise ValueError(name)

    def _get_anchor_norm(self, name: str) -> np.ndarray:
        # Compute directly in normalized mode (no size needed)
        if self._mode == "n":
            cxn, cyn, wn, hn = self._n  # type: ignore[misc]
            half_w, half_h = wn * 0.5, hn * 0.5
            if name == "x1y1":
                return self._np2((cxn - half_w, cyn - half_h))
            elif name == "x1y2":
                return self._np2((cxn - half_w, cyn + half_h))
            elif name == "x2y1":
                return self._np2((cxn + half_w, cyn - half_h))
            elif name == "x2y2":
                return self._np2((cxn + half_w, cyn + half_h))
            elif name == "x1y":
                return self._np2((cxn - half_w, cyn))
            elif name == "x2y":
                return self._np2((cxn + half_w, cyn))
            elif name == "xy1":
                return self._np2((cxn, cyn - half_h))
            elif name == "xy2":
                return self._np2((cxn, cyn + half_h))
            else:
                raise ValueError(name)

        # Convert absolute → normalized
        self._need_size()
        W, H = self._size  # type: ignore[assignment]
        a = self._get_anchor_abs(name)
        return self._np2((a[0] / W, a[1] / H))

    # setters (move box keeping w/h)
    def _set_anchor_abs(self, name: str, p: Iterable[float]):
        x, y = map(float, p)
        w, h = self._abs_wh()
        if name == "x1y1":
            cx, cy = x + w * 0.5, y + h * 0.5
        elif name == "x1y2":
            cx, cy = x + w * 0.5, y - h * 0.5
        elif name == "x2y1":
            cx, cy = x - w * 0.5, y + h * 0.5
        elif name == "x2y2":
            cx, cy = x - w * 0.5, y - h * 0.5
        elif name == "x1y":
            cx, cy = x + w * 0.5, y
        elif name == "x2y":
            cx, cy = x - w * 0.5, y
        elif name == "xy1":
            cx, cy = x, y + h * 0.5
        elif name == "xy2":
            cx, cy = x, y - h * 0.5
        else:
            raise ValueError(name)
        self.xy = (cx, cy)

    def _set_anchor_norm(self, name: str, pn: Iterable[float]):
        xn, yn = map(float, pn)
        # Direct update in normalized mode (no size needed)
        if self._mode == "n":
            cxn, cyn, wn, hn = self._n  # type: ignore[misc]
            half_w, half_h = wn * 0.5, hn * 0.5
            if name == "x1y1":
                cxn2, cyn2 = xn + half_w, yn + half_h
            elif name == "x1y2":
                cxn2, cyn2 = xn + half_w, yn - half_h
            elif name == "x2y1":
                cxn2, cyn2 = xn - half_w, yn + half_h
            elif name == "x2y2":
                cxn2, cyn2 = xn - half_w, yn - half_h
            elif name == "x1y":
                cxn2, cyn2 = xn + half_w, yn
            elif name == "x2y":
                cxn2, cyn2 = xn - half_w, yn
            elif name == "xy1":
                cxn2, cyn2 = xn, yn + half_h
            elif name == "xy2":
                cxn2, cyn2 = xn, yn - half_h
            else:
                raise ValueError(name)
            self._n = (cxn2, cyn2, wn, hn)
            return

        # Otherwise convert normalized anchor → absolute using size
        self._need_size()
        W, H = self._size  # type: ignore[assignment]
        self._set_anchor_abs(name, (xn * W, yn * H))

    # absolute anchor properties
    @property
    def x1y1(self) -> np.ndarray:
        return self._get_anchor_abs("x1y1")

    @x1y1.setter
    def x1y1(self, p):
        self._set_anchor_abs("x1y1", p)

    @property
    def x1y2(self) -> np.ndarray:
        return self._get_anchor_abs("x1y2")

    @x1y2.setter
    def x1y2(self, p):
        self._set_anchor_abs("x1y2", p)

    @property
    def x2y1(self) -> np.ndarray:
        return self._get_anchor_abs("x2y1")

    @x2y1.setter
    def x2y1(self, p):
        self._set_anchor_abs("x2y1", p)

    @property
    def x2y2(self) -> np.ndarray:
        return self._get_anchor_abs("x2y2")

    @x2y2.setter
    def x2y2(self, p):
        self._set_anchor_abs("x2y2", p)

    @property
    def x1y(self) -> np.ndarray:
        return self._get_anchor_abs("x1y")

    @x1y.setter
    def x1y(self, p):
        self._set_anchor_abs("x1y", p)

    @property
    def x2y(self) -> np.ndarray:
        return self._get_anchor_abs("x2y")

    @x2y.setter
    def x2y(self, p):
        self._set_anchor_abs("x2y", p)

    @property
    def xy1(self) -> np.ndarray:
        return self._get_anchor_abs("xy1")

    @xy1.setter
    def xy1(self, p):
        self._set_anchor_abs("xy1", p)

    @property
    def xy2(self) -> np.ndarray:
        return self._get_anchor_abs("xy2")

    @xy2.setter
    def xy2(self, p):
        self._set_anchor_abs("xy2", p)

    # normalized anchor properties
    @property
    def x1y1n(self) -> np.ndarray:
        return self._get_anchor_norm("x1y1")

    @x1y1n.setter
    def x1y1n(self, pn):
        self._set_anchor_norm("x1y1", pn)

    @property
    def x1y2n(self) -> np.ndarray:
        return self._get_anchor_norm("x1y2")

    @x1y2n.setter
    def x1y2n(self, pn):
        self._set_anchor_norm("x1y2", pn)

    @property
    def x2y1n(self) -> np.ndarray:
        return self._get_anchor_norm("x2y1")

    @x2y1n.setter
    def x2y1n(self, pn):
        self._set_anchor_norm("x2y1", pn)

    @property
    def x2y2n(self) -> np.ndarray:
        return self._get_anchor_norm("x2y2")

    @x2y2n.setter
    def x2y2n(self, pn):
        self._set_anchor_norm("x2y2", pn)

    @property
    def x1yn(self) -> np.ndarray:
        return self._get_anchor_norm("x1y")

    @x1yn.setter
    def x1yn(self, pn):
        self._set_anchor_norm("x1y", pn)

    @property
    def x2yn(self) -> np.ndarray:
        return self._get_anchor_norm("x2y")

    @x2yn.setter
    def x2yn(self, pn):
        self._set_anchor_norm("x2y", pn)

    @property
    def xy1n(self) -> np.ndarray:
        return self._get_anchor_norm("xy1")

    @xy1n.setter
    def xy1n(self, pn):
        self._set_anchor_norm("xy1", pn)

    @property
    def xy2n(self) -> np.ndarray:
        return self._get_anchor_norm("xy2")

    @xy2n.setter
    def xy2n(self, pn):
        self._set_anchor_norm("xy2", pn)

    # --------------------- anchor + size (read/write) ---------------------
    @staticmethod
    def _unpack2(v: Iterable[float]) -> Tuple[float, float]:
        a, b = v
        return float(a), float(b)

    # absolute anchors + absolute wh
    @property
    def x1y1wh(self):
        x1, y1, x2, y2 = self._abs_corners()
        w, h = self._abs_wh()
        return self._np4((x1, y1, w, h))

    @x1y1wh.setter
    def x1y1wh(self, vals):
        (x1, y1), (w, h) = map(self._unpack2, vals)
        self.xywh = (x1 + w * 0.5, y1 + h * 0.5, w, h)

    @property
    def x1y2wh(self):
        x1, y1, x2, y2 = self._abs_corners()
        w, h = self._abs_wh()
        return self._np4((x1, y2, w, h))

    @x1y2wh.setter
    def x1y2wh(self, vals):
        (x1, y2), (w, h) = map(self._unpack2, vals)
        self.xywh = (x1 + w * 0.5, y2 - h * 0.5, w, h)

    @property
    def x2y1wh(self):
        x1, y1, x2, y2 = self._abs_corners()
        w, h = self._abs_wh()
        return self._np4((x2, y1, w, h))

    @x2y1wh.setter
    def x2y1wh(self, vals):
        (x2, y1), (w, h) = map(self._unpack2, vals)
        self.xywh = (x2 - w * 0.5, y1 + h * 0.5, w, h)

    @property
    def x2y2wh(self):
        x1, y1, x2, y2 = self._abs_corners()
        w, h = self._abs_wh()
        return self._np4((x2, y2, w, h))

    @x2y2wh.setter
    def x2y2wh(self, vals):
        (x2, y2), (w, h) = map(self._unpack2, vals)
        self.xywh = (x2 - w * 0.5, y2 - h * 0.5, w, h)

    @property
    def x1ywh(self):
        x1, y1, x2, y2 = self._abs_corners()
        w, h = self._abs_wh()
        _, cy, _, _ = self._abs_xywh()
        return self._np4((x1, cy, w, h))

    @x1ywh.setter
    def x1ywh(self, vals):
        (x1, y), (w, h) = map(self._unpack2, vals)
        self.xywh = (x1 + w * 0.5, y, w, h)

    @property
    def x2ywh(self):
        x1, y1, x2, y2 = self._abs_corners()
        w, h = self._abs_wh()
        _, cy, _, _ = self._abs_xywh()
        return self._np4((x2, cy, w, h))

    @x2ywh.setter
    def x2ywh(self, vals):
        (x2, y), (w, h) = map(self._unpack2, vals)
        self.xywh = (x2 - w * 0.5, y, w, h)

    @property
    def xy1wh(self):
        x1, y1, x2, y2 = self._abs_corners()
        w, h = self._abs_wh()
        cx, _, _, _ = self._abs_xywh()
        return self._np4((cx, y1, w, h))

    @xy1wh.setter
    def xy1wh(self, vals):
        (x, y1), (w, h) = map(self._unpack2, vals)
        self.xywh = (x, y1 + h * 0.5, w, h)

    @property
    def xy2wh(self):
        x1, y1, x2, y2 = self._abs_corners()
        w, h = self._abs_wh()
        cx, _, _, _ = self._abs_xywh()
        return self._np4((cx, y2, w, h))

    @xy2wh.setter
    def xy2wh(self, vals):
        (x, y2), (w, h) = map(self._unpack2, vals)
        self.xywh = (x, y2 - h * 0.5, w, h)

    # normalized anchor + normalized wh
    def _anchor_norm_get_pair(self, name: str):
        if self._mode == "n":
            cxn, cyn, wn, hn = self._n  # type: ignore[misc]
            half_w, half_h = wn * 0.5, hn * 0.5
            if name == "x1y1":
                xn, yn = cxn - half_w, cyn - half_h
            elif name == "x1y2":
                xn, yn = cxn - half_w, cyn + half_h
            elif name == "x2y1":
                xn, yn = cxn + half_w, cyn - half_h
            elif name == "x2y2":
                xn, yn = cxn + half_w, cyn + half_h
            elif name == "x1y":
                xn, yn = cxn - half_w, cyn
            elif name == "x2y":
                xn, yn = cxn + half_w, cyn
            elif name == "xy1":
                xn, yn = cxn, cyn - half_h
            elif name == "xy2":
                xn, yn = cxn, cyn + half_h
            else:
                raise ValueError(name)
            return self._np4((xn, yn, wn, hn))

        self._need_size()
        xn, yn = self._get_anchor_norm(name)
        wn, hn = self.whn
        return self._np4((float(xn), float(yn), float(wn), float(hn)))

    @property
    def x1y1whn(self):
        return self._anchor_norm_get_pair("x1y1")

    @x1y1whn.setter
    def x1y1whn(self, vals):
        (x1n, y1n), (wn, hn) = map(self._unpack2, vals)
        self._set_anchor_norm("x1y1", (x1n, y1n))
        self.whn = (wn, hn)

    @property
    def x1y2whn(self):
        return self._anchor_norm_get_pair("x1y2")

    @x1y2whn.setter
    def x1y2whn(self, vals):
        (x1n, y2n), (wn, hn) = map(self._unpack2, vals)
        self._set_anchor_norm("x1y2", (x1n, y2n))
        self.whn = (wn, hn)

    @property
    def x2y1whn(self):
        return self._anchor_norm_get_pair("x2y1")

    @x2y1whn.setter
    def x2y1whn(self, vals):
        (x2n, y1n), (wn, hn) = map(self._unpack2, vals)
        self._set_anchor_norm("x2y1", (x2n, y1n))
        self.whn = (wn, hn)

    @property
    def x2y2whn(self):
        return self._anchor_norm_get_pair("x2y2")

    @x2y2whn.setter
    def x2y2whn(self, vals):
        (x2n, y2n), (wn, hn) = map(self._unpack2, vals)
        self._set_anchor_norm("x2y2", (x2n, y2n))
        self.whn = (wn, hn)

    @property
    def x1ywhn(self):
        return self._anchor_norm_get_pair("x1y")

    @x1ywhn.setter
    def x1ywhn(self, vals):
        (x1n, yn), (wn, hn) = map(self._unpack2, vals)
        self._set_anchor_norm("x1y", (x1n, yn))
        self.whn = (wn, hn)

    @property
    def x2ywhn(self):
        return self._anchor_norm_get_pair("x2y")

    @x2ywhn.setter
    def x2ywhn(self, vals):
        (x2n, yn), (wn, hn) = map(self._unpack2, vals)
        self._set_anchor_norm("x2y", (x2n, yn))
        self.whn = (wn, hn)

    @property
    def xy1whn(self):
        return self._anchor_norm_get_pair("xy1")

    @xy1whn.setter
    def xy1whn(self, vals):
        (xn, y1n), (wn, hn) = map(self._unpack2, vals)
        self._set_anchor_norm("xy1", (xn, y1n))
        self.whn = (wn, hn)

    @property
    def xy2whn(self):
        return self._anchor_norm_get_pair("xy2")

    @xy2whn.setter
    def xy2whn(self, vals):
        (xn, y2n), (wn, hn) = map(self._unpack2, vals)
        self._set_anchor_norm("xy2", (xn, y2n))
        self.whn = (wn, hn)

    # --------------------- ops & stats ---------------------
    def move(self, dx: float, dy: float) -> "Box":
        if self._mode == "a":
            cx, cy, w, h = self._a  # type: ignore[misc]
            self._a = (cx + float(dx), cy + float(dy), w, h)
        elif self._mode == "n":
            self._need_size()
            W, H = self._size  # type: ignore[assignment]
            cxn, cyn, wn, hn = self._n  # type: ignore[misc]
            self._n = (cxn + dx / W, cyn + dy / H, wn, hn)
        else:
            raise ValueError("Box is empty; cannot move.")
        return self

    def scale(self, fx: float, fy: Optional[float] = None) -> "Box":
        if fy is None:
            fy = fx
        fx = float(fx)
        fy = float(fy)
        if self._mode == "a":
            cx, cy, w, h = self._a  # type: ignore[misc]
            self._a = (cx, cy, w * fx, h * fy)
        elif self._mode == "n":
            cxn, cyn, wn, hn = self._n  # type: ignore[misc]
            self._n = (cxn, cyn, wn * fx, hn * fy)
        else:
            raise ValueError("Box is empty; cannot scale.")
        return self

    # ---------- extras ----------
    def iou(self, other: "Box") -> float:
        """Intersection-over-Union in absolute pixels."""
        x1a, y1a, x2a, y2a = self.xyxy
        x1b, y1b, x2b, y2b = other.xyxy
        xi1 = max(x1a, x1b)
        yi1 = max(y1a, y1b)
        xi2 = min(x2a, x2b)
        yi2 = min(y2a, y2b)
        inter_w = max(0.0, float(xi2 - xi1))
        inter_h = max(0.0, float(yi2 - yi1))
        inter = inter_w * inter_h
        area_a = float((x2a - x1a) * (y2a - y1a))
        area_b = float((x2b - x1b) * (y2b - y1b))
        union = area_a + area_b - inter
        return 0.0 if union <= 0 else inter / union

    def clip(self) -> "Box":
        """
        Clip the box to image bounds.
        - absolute mode requires .size
        - normalized mode clamps to [0,1]
        """
        if self._mode == "a":
            self._need_size()
            W, H = self._size  # type: ignore[assignment]
            x1, y1, x2, y2 = self.xyxy
            x1 = float(min(max(x1, 0.0), W))
            x2 = float(min(max(x2, 0.0), W))
            y1 = float(min(max(y1, 0.0), H))
            y2 = float(min(max(y2, 0.0), H))
            self.xyxy = (x1, y1, x2, y2)
        elif self._mode == "n":
            cxn, cyn, wn, hn = self._n  # type: ignore[misc]
            cxn = float(min(max(cxn, 0.0), 1.0))
            cyn = float(min(max(cyn, 0.0), 1.0))
            wn = float(min(max(wn, 0.0), 1.0))
            hn = float(min(max(hn, 0.0), 1.0))
            self._n = (cxn, cyn, wn, hn)
        else:
            raise ValueError("Box is empty; cannot clip.")
        return self

    @property
    def area(self) -> float:
        _, _, w, h = self.xywh
        return float(w * h)

    @property
    def aspect(self) -> float:
        _, _, w, h = self.xywh
        return float(w / h) if h != 0 else float("inf")

    def __repr__(self) -> str:
        try:
            if self._mode == "a":
                return f"Box(xywh={self._np4(self._a)}, size={self._size})"  # type: ignore[arg-type]
            if self._mode == "n":
                return f"Box(xywhn={self._np4(self._n)}, size={self._size})"  # type: ignore[arg-type]
            return "Box(<empty>)"
        except Exception:
            return "Box(<unavailable>)"


if __name__ == "__main__":
    b = Box(size=(70, 70), wh=(20, 20), xyn=(0.5, 0.5))
    print(b.xywh)  # [35. 35. 20. 20.]
    print(b.xywhn)  # [0.5        0.5        0.28571429 0.28571429]
    print(b.x1y1)  # [25. 25.]
    b.x1y1 = (20, 20)
    print(b.xywhn)  # [0.42857143 0.42857143 0.28571429 0.28571429]
    print(b.x1y1wh)  # (20.0, 20.0, 20.0, 20.0)
    print(b.x2y2n)  # [0.57142857 0.57142857]
    print()

    b = Box()
    b.xywhn = (0.3, 0.8, 0.2, 0.1)
    b.size = (100, 100)
    print(b.xywh)  # [30. 80. 20. 10.]
    print()

    b = Box(xywhn=(0.3, 0.8, 0.2, 0.1))
    print(b.xywhn)  # [0.3 0.8 0.2 0.1]
    b.scale(3)
    print(b.xywhn)  # [0.3 0.8 0.6 0.3]
    b.set_size((100, 100))
    print(b.xywh)  # [30. 80. 60. 30.]
    print(b)
    print()

    b = Box(xywh=(30, 40, 10, 10), size=(100, 100))
    print(b)
    print(b.xywh)  # [30. 40. 10. 10.]
    b.move(10, 20)
    print(b.xywh)  # [40. 60. 10. 10.]
    b.xy = (50, 70)
    print(b.xywh)  # [50. 70. 10. 10.]
    print(b.xy)  # [50. 70.]
    print(b.wh)  # [10. 10.]
    print(b.xyn)  # [0.5 0.7]
    print(b.whn)  # [0.1 0.1]
    print(b.xywhn)  # [0.5 0.7 0.1 0.1]
    b.whn = (0.2, 0.2)
    print(b.xywhn)  # [0.5 0.7 0.2 0.2]
    print(b)  # Box(xywh=[50. 70. 20. 20.], size=(100, 100))
    print()

    b = Box(xy=(50, 70), wh=(20, 20))
    print(b)  # Box(xywh=[50. 70. 20. 20.], size=None)
    b = Box(xy=(50, 70))
    b.wh = (20, 20)
    print(b)  # Box(xywh=[50. 70. 20. 20.], size=None)
    b = Box(wh=(20, 20))
    b.xy = (50, 70)
    print(b)  # Box(xywh=[50. 70. 20. 20.], size=None)
    print()

    b = Box(xyn=(0.5, 0.5), whn=(0.2, 0.2))
    print(b)  # Box(xywhn=[0.5 0.5 0.2 0.2], size=None)
    print(b.xy2whn)  # [0.5 0.6 0.2 0.2]
    print()

    b = Box(size=(70, 70), wh=(20, 20), xyn=(0.5, 0.5))
    print(b)  # Box(xywh=[35. 35. 20. 20.], size=(70, 70))
    print(Box(xywh=(30, 30, 30, 30), size=(100, 100)).xywhn)  # [0.3 0.3 0.3 0.3]
    print()

    print(Box(xyxy=(30, 30, 30, 30)).x1y1wh)  # [30. 30.  0.  0.]
    print(Box(xyxy=(30, 30, 30, 30)).xywh)  # [30. 30.  0.  0.]
    print(Box(xy=(30, 30)).xywh)  # [30. 30.  0.  0.]
    print()

    b = Box(xywhn=(0.3, 0.8, 0.2, 0.1))
    print(b.xywhn)  # [0.3 0.8 0.2 0.1]
    b.scale(3)
    print(b.xywhn)  # [0.3 0.8 0.6 0.3]
    b.set_size((100, 100))
    print(b.xywh)  # [30. 80. 60. 30.]
    b = Box(xywh=(30, 40, 10, 10))
    print(b.xywh)  # [30. 40. 10. 10.]
    b.move(10, 20)
    print(b.xywh)  # [40. 60. 10. 10.]
    print()


def show(box: Box):
    try:
        print('xywhn  ', box.xywhn)
    except Exception as e:
        print('xywhn  ', e)
    try:
        print('xywh   ', box.xywh)
    except Exception as e:
        print('xywh   ', e)
    try:
        print('xyxyn  ', box.xyxyn)
    except Exception as e:
        print('xyxyn  ', e)
    try:
        print('xyxy   ', box.xyxy)
    except Exception as e:
        print('xyxy   ', e)
    try:
        print('pointsn', box.pointsn)
    except Exception as e:
        print('pointsn', e)
    try:
        print('points ', box.points)
    except Exception as e:
        print('points ', e)


def show2(box):
    try:
        print('x1y1n  ', box.x1y1n)
    except Exception as e:
        print('x1y1n  ', e)
    try:
        print('x1y1   ', box.x1y1)
    except Exception as e:
        print('x1y1   ', e)
    try:
        print('x1y2n  ', box.x1y2n)
    except Exception as e:
        print('x1y2n  ', e)
    try:
        print('x1y2   ', box.x1y2)
    except Exception as e:
        print('x1y2   ', e)
    try:
        print('x2y1n  ', box.x2y1n)
    except Exception as e:
        print('x2y1n  ', e)
    try:
        print('x2y1   ', box.x2y1)
    except Exception as e:
        print('x2y1   ', e)
    try:
        print('x2y2n  ', box.x2y2n)
    except Exception as e:
        print('x2y2n  ', e)
    try:
        print('x2y2   ', box.x2y2)
    except Exception as e:
        print('x2y2   ', e)
    try:
        print('xyn    ', box.xyn)
    except Exception as e:
        print('xyn    ', e)
    try:
        print('xy     ', box.xy)
    except Exception as e:
        print('xy     ', e)


if __name__ == "__main__":
    print('\nbox1 set xywhn and size')
    box1 = Box(xywhn=[0.3, 0.3, 0.2, 0.2], size=(100, 100))
    show(box1)

    print('\nbox2 set xywhn')
    box2 = Box(xywhn=[0.3, 0.3, 0.2, 0.2])
    show(box2)

    print('\nbox3 set xywh')
    box3 = Box(xywh=[3, 3, 2, 2])
    show(box3)

    print('\nbox4 set pointsn')
    polygon1 = Polygon(pointsn=[(0.1, 0.1), (0.5, 0.05), (0.3, 0.1), (0.1, 0.2)])
    show(polygon1)

    print('\nbox5 set points')
    polygon2 = Polygon(points=[(50, 50), (100, 20), (150, 100), (100, 200)])
    show(polygon2)

    print('\nbox6 set pointsn')
    polygon3 = Polygon(pointsn=[(0.1, 0.1), (0.5, 0.05), (0.3, 0.1), (0.1, 0.2)])
    polygon3.set_size((100, 100))
    show(polygon3)
    show2(polygon3)

    #
    # def test_2():
    #     import cv2
    #
    #     W, H = 500, 500
    #     img = np.zeros((H, W, 3), dtype=np.uint8)
    #
    #     examples = [
    #         ("xywh", dict(xywh=(300, 300, 100, 100))),
    #         ("xyxy", dict(xyxy=(200, 50, 400, 150))),
    #         ("xywhn", dict(xywhn=(0.7, 0.9, 0.1, 0.1))),
    #         ("xyxyn", dict(xyxyn=(0.2, 0.4, 0.3, 0.6))),
    #         ("points", dict(points=[(50, 50), (100, 20), (150, 100), (100, 200)])),
    #         ("pointsn", dict(pointsn=[(0.1, 0.1), (0.5, 0.05), (0.3, 0.1), (0.1, 0.2)])),
    #     ]
    #
    #     for desc, kw in examples:
    #         box = Box((W, H), **kw)
    #         print(f"{desc:10} → {box}")
    #         color = tuple(int(c) for c in np.random.randint(50, 256, 3))
    #
    #         if box.type == 'polygon':
    #             cv2.polylines(img, [box.points.astype(np.int32)], isClosed=True, color=color, thickness=2)
    #             for point in box.points:
    #                 cv2.circle(img, tuple(map(int, point)), 5, color, -1)
    #         cv2.rectangle(img, tuple(map(int, box.x1y1)), tuple(map(int, box.x2y2)), color, 2)
    #
    #     cv2.imshow("All Modes", img)
    #     cv2.waitKey(0)
    #     cv2.destroyAllWindows()
    #
    #
    # print('=== test 1 ===')
    # test_1()
    # print()
    #
    # print('=== test 2 ===')
    # test_2()
    # print()
