import yaml from "js-yaml";

/**
 * Converts a YAML string to a JSON object.
 * @param {string} YAMLString - The YAML string to convert.
 * @returns {object} - The resulting JSON object.
 */
export function convertYAMLStringToJSON(YAMLString, options = {}) {
    return yaml.load(YAMLString, options);
}

/**
 * Converts a JSON object to a YAML string.
 * @param {object} data - The JSON object to convert.
 * @param {object} options - Options for YAML dump (see js-yaml documentation).
 * @returns {string} - The resulting YAML string.
 */
export function convertJSONToYAMLString(data, options = {}) {
    return yaml.dump(data, { ...options });
}
