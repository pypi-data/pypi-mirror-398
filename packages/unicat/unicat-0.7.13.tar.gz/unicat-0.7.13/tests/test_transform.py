from unicat.transform import UnicatTransform, mergeTransforms, transformAsOptions


def test_transform():
    transform = UnicatTransform(name="transform-1", optimize=True, resize="fill")
    assert transform.name == "transform-1"
    assert transform.optimize
    assert transform.resize == "fill"
    assert transform.width == 1
    assert transform.height == 1


def test_transform_as_options():
    transform = UnicatTransform(name="transform-1", optimize=True, resize="fill")
    options = transformAsOptions(transform)
    assert options["name"] == "transform-1"
    assert options["optimize"] == "true"
    assert options["fill"] == "1,1"
    transform = UnicatTransform(
        name="transform-2",
        key="key",
        force=False,
        optimize=True,
        resize="fill",
        width=400,
        height=300,
        type="jpg",
        hotspot=(0.6, 0.4),
        crop=(0.8, 0.6),
        padding=(0, "auto", 0, "auto"),
        quality=75,
        background="#123abc",
        dpr=2,
    )
    options = transformAsOptions(transform)
    assert options["name"] == "transform-2"
    assert options["optimize"] == "true"
    assert options["fill"] == "400,300"
    assert options["key"] == "key"
    assert options["type"] == "jpg"
    assert options["force"] == "false"
    assert options["hs"] == "0.60000,0.40000"
    assert options["crop"] == "0.80000,0.60000"
    assert options["padding"] == "0,auto,0,auto"
    assert options["bg"] == "123abc"
    assert options["q"] == "75"
    assert options["dpr"] == "2"


def test_merge_transforms():
    transform1 = UnicatTransform(name="transform-1", optimize=True, resize="fill")
    transform2 = UnicatTransform(resize="fit", width=600, dpr=2)
    transform3 = UnicatTransform(optimize=False, height=300, hotspot=(0.6, 0.4))
    transform = mergeTransforms(transform1, transform2, transform3)
    assert transform.name == "transform-1"
    assert not transform.optimize
    assert transform.resize == "fit"
    assert transform.width == 600
    assert transform.height == 300
    assert transform.dpr == 2
    assert transform.hotspot == [0.6, 0.4]
