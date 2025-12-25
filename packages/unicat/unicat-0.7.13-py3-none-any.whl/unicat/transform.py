import re

rgb_re = re.compile("^#?[0-9a-fA-F]{6}$")


def mergeTransforms(*transforms):
    """Return new transform by merging all given transforms"""
    mergedTransform = UnicatTransform()
    for transform in transforms:
        mergedTransform.merge(transform)
    return mergedTransform


def transformAsOptions(transform):
    if not isinstance(transform, UnicatTransform):
        return None
    options = {}
    if transform.name is not None:
        options["name"] = transform.name
    if transform.key is not None:
        options["key"] = transform.key
    if transform.type is not None:
        options["type"] = transform.type
    if transform.force is not None:
        options["force"] = "true" if transform.force else "false"
    if transform.optimize is not None:
        options["optimize"] = "true" if transform.optimize else "false"
    if transform.resize is not None:
        options[transform.resize] = f"{transform.width},{transform.height}"
        if transform.resize == "width" and not transform.height:
            options[transform.resize] = f"{transform.width}"
        elif transform.resize == "height" and not transform.width:
            options[transform.resize] = f"{transform.height}"
    if transform.hotspot is not None:
        options["hs"] = f"{transform.hotspot[0]:0.5f},{transform.hotspot[1]:0.5f}"
    if transform.crop is not None:
        options["crop"] = f"{transform.crop[0]:0.5f},{transform.crop[1]:0.5f}"
    if transform.padding is not None:
        options["padding"] = (
            f"{transform.padding[0]},{transform.padding[1]},{transform.padding[2]},{transform.padding[3]}"
        )
    if transform.background is not None:
        options["bg"] = transform.background
    if transform.quality is not None:
        options["q"] = f"{transform.quality}"
    if transform.dpr is not None:
        options["dpr"] = f"{transform.dpr}"
    return options


class UnicatTransform:
    name = None
    key = None
    force = None
    optimize = None
    resize = None
    width = None
    height = None
    type = None
    hotspot = None
    crop = None
    padding = None
    quality = None
    background = None
    dpr = None

    def __init__(self, **kwargs):
        setters = {
            "name": self.setName,
            "key": self.setKey,
            "force": self.setForce,
            "optimize": self.setOptimize,
            "resize": self.setResize,
            "width": self.setWidth,
            "height": self.setHeight,
            "type": self.setType,
            "hotspot": self.setHotspot,
            "crop": self.setCrop,
            "padding": self.setPadding,
            "quality": self.setQuality,
            "background": self.setBackground,
            "dpr": self.setDevicePixelRatio,
        }
        for name, value in kwargs.items():
            if name in setters:
                if isinstance(value, (list, tuple)):
                    setters[name](*value)
                else:
                    setters[name](value)

    def setName(self, name):
        self.name = str(name)
        return self

    def setKey(self, key):
        self.key = str(key)
        return self

    def setForce(self, force):
        if not isinstance(force, bool):
            self.force = None
            return self
        self.force = force
        return self

    def setOptimize(self, optimize):
        if not isinstance(optimize, bool):
            self.optimize = None
            return self
        self.optimize = optimize
        return self

    def setResize(self, resize):
        if resize in ["width", "height", "fit", "fill"]:
            self.resize = resize
        else:
            self.resize = "width"
        # to make sure we have valid values
        self.setWidth(self.width)
        self.setHeight(self.height)
        return self

    def setWidth(self, width):
        if not width:
            if self.resize == "height":
                self.width = None
            else:
                self.width = 1
        else:
            self.width = max(1, min(round(width), 5000))
        return self

    def setHeight(self, height):
        if not height:
            if self.resize == "width":
                self.height = None
            else:
                self.height = 1
        else:
            self.height = max(1, min(round(height), 5000))
        return self

    def setType(self, type):
        if type in ["jpg", "png", "gif"]:
            self.type = type
        else:
            self.type = "jpg"
        return self

    def setHotspot(self, x, y):
        if not isinstance(x, (int, float)) or not isinstance(y, (int, float)):
            self.hotspot = None
            return self
        x = max(0.0, min(x, 1.0))
        y = max(0.0, min(y, 1.0))
        self.hotspot = [x, y]
        return self

    def setCrop(self, w, h):
        if not isinstance(w, (int, float)) or not isinstance(h, (int, float)):
            self.crop = None
            return self
        w = max(0.0, min(w, 1.0))
        h = max(0.0, min(h, 1.0))
        floatingpointthreshold = 0.00001
        if w < floatingpointthreshold or h < floatingpointthreshold:
            self.crop = None
        else:
            self.crop = [w, h]
            if not self.hotspot:
                self.setHotspot(0.5, 0.5)
        return self

    def setPadding(self, top, right, bottom, left):
        for pad in (top, right, bottom, left):
            if not (pad == "auto" or isinstance(pad, (int, float))):
                self.padding = None
                return self
        if top != "auto":
            top = max(0, min(top, 1000))
        if right != "auto":
            right = max(0, min(right, 1000))
        if bottom != "auto":
            bottom = max(0, min(bottom, 1000))
        if left != "auto":
            left = max(0, min(left, 1000))
        self.padding = [top, right, bottom, left]
        return self

    def setQuality(self, q):
        if not isinstance(q, (int, float)):
            self.quality = None
            return self
        q = max(0, min(round(q), 100))
        self.quality = q
        return self

    def setBackground(self, background):
        if background in ["white", "transparent"]:
            self.background = background
        else:
            if bool(rgb_re.match(background)):
                self.background = background.replace("#", "")
        return self

    def setDevicePixelRatio(self, dpr):
        if not isinstance(dpr, (int, float)):
            self.dpr = None
            return self
        dpr = max(1, min(round(dpr), 4))
        self.dpr = dpr
        return self

    def merge(self, transform):
        if not isinstance(transform, UnicatTransform):
            return self
        if transform.name is not None:
            self.setName(transform.name)
        if transform.key is not None:
            self.setKey(transform.key)
        if transform.force is not None:
            self.setForce(transform.force)
        if transform.optimize is not None:
            self.setOptimize(transform.optimize)
        if transform.resize is not None:
            self.setResize(transform.resize)
        if transform.width is not None:
            self.setWidth(transform.width)
        if transform.height is not None:
            self.setHeight(transform.height)
        if transform.type is not None:
            self.setType(transform.type)
        if transform.hotspot is not None:
            self.setHotspot(transform.hotspot[0], transform.hotspot[1])
        if transform.crop is not None:
            self.setCrop(transform.crop[0], transform.crop[1])
        if transform.padding is not None:
            self.setPadding(
                transform.padding[0],
                transform.padding[1],
                transform.padding[2],
                transform.padding[3],
            )
        if transform.quality is not None:
            self.setQuality(transform.quality)
        if transform.background is not None:
            self.setBackground(transform.background)
        if transform.dpr is not None:
            self.setDevicePixelRatio(transform.dpr)
        return self
