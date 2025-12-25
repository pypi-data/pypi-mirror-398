import * as array from "./shared/array";
import * as assertion from "./shared/assertion";
import * as cls from "./shared/class";
import * as clone from "./shared/clone";
import * as constants from "./shared/constants";
import * as hash from "./shared/hash";
import * as math from "./shared/math";
import * as object from "./shared/object";
import * as selector from "./shared/selector";
import * as specific from "./shared/specific";
import * as str from "./shared/str";
import * as tree from "./shared/tree";
import * as url from "./shared/url";
import * as uuid from "./shared/uuid";
import * as yaml from "./shared/yaml";

export const sharedUtils = {
    array,
    cls,
    clone,
    constants,
    hash,
    math,
    object,
    selector,
    specific,
    str,
    tree,
    url,
    uuid,
    assertion,
    yaml,
};

export const Utils = sharedUtils;
export default { ...Utils };
