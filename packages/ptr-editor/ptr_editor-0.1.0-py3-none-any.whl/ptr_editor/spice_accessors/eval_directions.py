from functools import singledispatch

import numpy as np
import spiceypy
from loguru import logger as log
from planetary_coverage import et

from ptr_editor.agm_config import AGMConfiguration
from ptr_editor.elements.agm_config import Object
from ptr_editor.elements.directions import (
    DIRECTIONS,
    CrossProductDirection,
    LonLatDirection,
    NamedDirection,
    OriginTargetDirection,
    ProjectedVectorToPlaneDirection,
    VectorDirection,
)


@singledispatch
def eval_direction(
    dir: DIRECTIONS, time: str, config: AGMConfiguration, frame=None,
) -> np.ndarray:
    """
    Evaluate a direction at a given time and return a numpy array
    in the given frame. If frame is None, use the direction's frame if any.
    """
    msg = f"Cannot evaluate direction of type {type(dir)}"
    raise NotImplementedError(msg)


@eval_direction.register(VectorDirection)
def _(dir: VectorDirection, time: str, config: AGMConfiguration, frame=None):
    log.info(
        f"Evaluating VectorDirection {dir.name} at time {time}, frame is {dir.frame}",
    )
    v_frame = dir.spice.frame
    if not frame:
        frame = v_frame

    v = dir.as_numpy()

    t = et(time)

    if v_frame != frame:
        t = et(time)
        v = spiceypy.mxv(spiceypy.pxform(v_frame, frame, t), v)

    return v


@eval_direction.register(NamedDirection)
def _(dir: NamedDirection, time: str, config: AGMConfiguration, frame=None):
    log.info(f"Evaluating NamedDirection {dir.ref} at time {time}, frame is {frame}")

    got = config.definitions.vector_by_name(dir.ref)

    if not got:
        got = config.cfg.object_by_name(dir.ref)

    if not got:
        msg = f"Named direction '{dir.ref}' not found in AGM configuration"
        raise ValueError(msg)

    return eval_direction(got, time, config, frame)

@eval_direction.register(Object)
def _(dir: Object, time: str, config: AGMConfiguration, frame=None):
    sc_spice_name = config.agm_object_to_spice_name("SC")
    obj_spice_name = config.agm_object_to_spice_name(dir.parser_name)

    t = et(time)

    if frame is None:
        frame = config.agm_frame_to_spice_name("SC")

    pos, _ = spiceypy.spkpos(obj_spice_name, t, frame, "LT+S", sc_spice_name)

    return pos



@eval_direction.register(OriginTargetDirection)
def _(dir: OriginTargetDirection, time: str, config: AGMConfiguration, frame=None):
    log.info(
        f"Evaluating OriginTargetDirection {dir.name} from {dir.origin} to {dir.target} at time {time}",
    )

    frame = "J2000" if frame is None else frame

    operator = dir.operator
    origin = config.cfg.object_by_name(dir.origin.ref).spice_name
    target = config.cfg.object_by_name(dir.target.ref).spice_name

    t = et(time)

    if not operator:
        p1, _ = spiceypy.spkpos(target, t, "J2000", "LT+S", origin)
        return p1

    if operator == "derivative":
        # Get the velocity of the target relative to the origin

        state, _ = spiceypy.spkezr(target, t, "J2000", "LT+S", origin)
        return state[3:]

    msg = f"Operator {operator} not implemented"
    raise NotImplementedError(msg)


@eval_direction.register(CrossProductDirection)
def _(dir: CrossProductDirection, time: str, config: AGMConfiguration, frame=None):
    log.info(
        f"Evaluating CrossProductDirection {dir.name} at time {time}, frame is {frame}",
    )

    v1 = eval_direction(dir.dir1, time, config, frame)
    v2 = eval_direction(dir.dir2, time, config, frame)

    log.info(f"v1: {v1}, v2: {v2}")

    return np.cross(v1, v2)


@eval_direction.register(ProjectedVectorToPlaneDirection)
def _(
    dir: ProjectedVectorToPlaneDirection,
    time: str,
    config: AGMConfiguration,
    frame=None,
):
    log.info(
        f"Evaluating ProjectedVectorToPlaneDirection {dir.name} at time {time}, frame is {frame}",
    )

    v = eval_direction(dir.dir_vector, time, config, frame)
    n = eval_direction(dir.normal_vector, time, config, frame)

    n_normalized = n / np.linalg.norm(n)

    log.info(f"v: {v}, n: {n}")

    return v - np.dot(v, n_normalized) * n_normalized


@eval_direction.register(LonLatDirection)
def _(
    dir: LonLatDirection, time: str, config: AGMConfiguration, frame=None,
) -> LonLatDirection:
    t = et(time)

    latlon_frame = config.agm_frame_to_spice_name(dir.frame)

    if frame is None:
        frame = latlon_frame

    lat = dir.lat.value_to_unit("rad")
    lon = dir.lon.value_to_unit("rad")

    v = spiceypy.latrec(1, lon, lat)

    if latlon_frame != frame:
        v = spiceypy.mxv(spiceypy.pxform(latlon_frame, frame, t), v)
    # return solved
    return v
