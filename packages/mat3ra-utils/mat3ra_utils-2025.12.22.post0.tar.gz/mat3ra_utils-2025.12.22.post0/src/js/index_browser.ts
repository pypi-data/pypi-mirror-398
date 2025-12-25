import * as codemirror from "./browser/specific/codemirror";
import { sharedUtils } from "./index";

export const browserUtils = {
    codemirror,
};

export const Utils = {
    ...sharedUtils,
    ...browserUtils,
};
export default { ...Utils };
