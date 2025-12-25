import fs from "fs";

import { convertJSONToYAMLString, convertYAMLStringToJSON } from "../shared/yaml";

/**
 * Reads a YAML file and converts its content to a JSON object.
 * @param {string} filePath - The path to the YAML file.
 * @returns {object} - The resulting JSON object.
 */
export function readYAMLFileSync(filePath: string, options = {}): object {
    const YAMLContent = fs.readFileSync(filePath, "utf8");
    return convertYAMLStringToJSON(YAMLContent, options);
}

export const readYAMLFile = readYAMLFileSync;

/**
 * Writes a JSON object to a YAML file.
 * @param {string} filePath - The path to the YAML file.
 * @param {object} [options] - Options for YAML dump (see js-yaml documentation).
 * @param {object} data - The JSON object to write.
 */
export function writeYAMLFileSync(filePath: string, data: object, options?: object) {
    const YAMLContent = convertJSONToYAMLString(data, options);
    fs.writeFileSync(filePath, YAMLContent);
}

export const writeYAMLFile = writeYAMLFileSync;
