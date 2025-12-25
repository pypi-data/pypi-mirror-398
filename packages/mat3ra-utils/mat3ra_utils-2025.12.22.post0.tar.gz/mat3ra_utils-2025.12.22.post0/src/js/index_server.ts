import { sharedUtils } from "./index";
import * as file from "./server/file";
import * as json from "./server/json";
import * as yaml from "./server/yaml";

export const serverUtils = {
    file,
    yaml,
    json,
};

export const Utils = {
    ...sharedUtils,
    ...serverUtils,
};
export default { ...Utils };
